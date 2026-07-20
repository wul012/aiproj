from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    REQUIRED_TERM_MICRO_TRAINING_JSON_FILENAME,
    build_required_term_micro_corpus,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.model_capability_required_term_split_seed_stability import (
    REQUIRED_TERM_SPLIT_SEED_STABILITY_JSON_FILENAME,
)
from minigpt.report_utils import list_of_dicts, utc_now


REQUIRED_TERM_BALANCED_CORPUS_JSON_FILENAME = "model_capability_required_term_balanced_corpus.json"
REQUIRED_TERM_BALANCED_CORPUS_TEXT_FILENAME = "model_capability_required_term_balanced_corpus.txt"
REQUIRED_TERM_BALANCED_CORPUS_MARKDOWN_FILENAME = "model_capability_required_term_balanced_corpus.md"
REQUIRED_TERM_BALANCED_CORPUS_HTML_FILENAME = "model_capability_required_term_balanced_corpus.html"
REQUIRED_TERM_BALANCED_CORPUS_FILENAME = "required_term_balanced_corpus.txt"

BALANCED_CORPUS_PATTERNS = (
    "direct_cue",
    "spaced_cue",
    "case_binding",
    "instruction_binding",
    "question_answer",
    "contrastive_boundary",
)


def locate_model_capability_required_term_balanced_corpus_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        for filename in (REQUIRED_TERM_SPLIT_SEED_STABILITY_JSON_FILENAME, REQUIRED_TERM_MICRO_TRAINING_JSON_FILENAME):
            candidate = source / filename
            if candidate.is_file():
                return candidate
    return source


def build_model_capability_required_term_balanced_corpus(
    source_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    repeat: int = 8,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    repeat_count = max(1, int(repeat))
    micro_path = _resolve_micro_report_path(source_report, source_path)
    micro_report = source_report if _looks_like_micro_training_report(source_report) else read_json_report(micro_path or "")
    examples = _source_examples(micro_report)
    source_example_count = len(list_of_dicts(micro_report.get("examples")))
    issues = _input_issues(source_report, micro_report, examples)

    corpus_text, term_rows = build_required_term_balanced_corpus(examples, repeat=repeat_count)
    corpus_path = root / REQUIRED_TERM_BALANCED_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")

    legacy_text = build_required_term_micro_corpus(examples, repeat=repeat_count) if examples else ""
    summary = summarize_required_term_balanced_corpus(
        corpus_text,
        term_rows,
        legacy_text,
        repeat=repeat_count,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term balanced corpus",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_report": str(source_path) if source_path else None,
        "source_required_term_micro_training": str(micro_path) if micro_path else None,
        "out_dir": str(root),
        "settings": {
            "repeat": repeat_count,
            "patterns": list(BALANCED_CORPUS_PATTERNS),
            "pattern_count": len(BALANCED_CORPUS_PATTERNS),
            "selection_strategy": "one representative row per unique required term",
            "training_boundary": "candidate corpus only; downstream holdout checks must still exclude held-out prompt-to-term pairs",
        },
        "corpus": {
            "path": str(corpus_path),
            "char_count": len(corpus_text),
            "line_count": len(corpus_text.splitlines()),
            "repeat": repeat_count,
            "vocab_boundary": "all terms may appear because this is a construction candidate, not a held-out evaluation corpus",
        },
        "summary": summary,
        "source_example_count": source_example_count,
        "term_rows": term_rows,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def build_required_term_balanced_corpus(
    examples: list[dict[str, Any]],
    *,
    repeat: int,
) -> tuple[str, list[dict[str, Any]]]:
    repeat_count = max(1, int(repeat))
    lines = [
        "MiniGPT required-term balanced corpus candidate.",
        "This corpus diversifies prompt-to-term contexts before the next real tiny-training check.",
        "Boundary: this is not held-out evidence; future holdout runs must still hide prompt-to-term pairs.",
    ]
    term_rows: list[dict[str, Any]] = []
    for example in examples:
        term = str(example.get("term") or "").strip()
        if not term:
            continue
        prompt = str(example.get("scaffold_prompt") or f"{term}:").strip()
        case = str(example.get("case") or "unknown-case").strip()
        before = len(lines)
        for cycle in range(1, repeat_count + 1):
            for pattern in BALANCED_CORPUS_PATTERNS:
                lines.append(_pattern_line(pattern, cycle=cycle, case=case, prompt=prompt, term=term))
        term_rows.append(
            {
                "case": case,
                "term": term,
                "scaffold_prompt": prompt,
                "line_count": len(lines) - before,
                "expected_line_count": repeat_count * len(BALANCED_CORPUS_PATTERNS),
                "pattern_count": len(BALANCED_CORPUS_PATTERNS),
                "repeat": repeat_count,
            }
        )
    return "\n".join(lines) + "\n", term_rows


def summarize_required_term_balanced_corpus(
    corpus_text: str,
    term_rows: list[dict[str, Any]],
    legacy_text: str,
    *,
    repeat: int,
) -> dict[str, Any]:
    lines = [line for line in corpus_text.splitlines() if line.strip()]
    unique_lines = set(lines)
    legacy_lines = [line for line in legacy_text.splitlines() if line.strip()]
    legacy_unique_lines = set(legacy_lines)
    term_counts = [int(row.get("line_count") or 0) for row in term_rows]
    pattern_counts = _pattern_counts(lines)
    unique_line_rate = round(len(unique_lines) / len(lines), 4) if lines else 0.0
    legacy_unique_line_rate = round(len(legacy_unique_lines) / len(legacy_lines), 4) if legacy_lines else 0.0
    term_line_min = min(term_counts) if term_counts else 0
    term_line_max = max(term_counts) if term_counts else 0
    return {
        "balanced_corpus_decision": _balanced_corpus_decision(
            line_count=len(lines),
            unique_line_rate=unique_line_rate,
            term_line_min=term_line_min,
            term_line_max=term_line_max,
            pattern_counts=pattern_counts,
        ),
        "example_count": len(term_rows),
        "selected_example_count": len(term_rows),
        "unique_term_count": len({str(row.get("term")) for row in term_rows if row.get("term")}),
        "repeat": max(1, int(repeat)),
        "pattern_count": len(pattern_counts),
        "line_count": len(lines),
        "unique_line_count": len(unique_lines),
        "duplicate_line_count": len(lines) - len(unique_lines),
        "unique_line_rate": unique_line_rate,
        "legacy_line_count": len(legacy_lines),
        "legacy_unique_line_count": len(legacy_unique_lines),
        "legacy_unique_line_rate": legacy_unique_line_rate,
        "unique_line_rate_delta": round(unique_line_rate - legacy_unique_line_rate, 4),
        "term_line_min": term_line_min,
        "term_line_max": term_line_max,
        "term_line_spread": term_line_max - term_line_min if term_counts else 0,
        "term_line_balance_ready": bool(term_counts) and term_line_min == term_line_max,
        "pattern_counts": dict(sorted(pattern_counts.items())),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _source_examples(micro_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_terms: set[str] = set()
    for row in list_of_dicts(micro_report.get("examples")):
        term = str(row.get("term") or "").strip()
        prompt = str(row.get("scaffold_prompt") or "").strip()
        if not term or term in seen_terms:
            continue
        seen_terms.add(term)
        rows.append(
            {
                "seed": row.get("seed"),
                "case": row.get("case"),
                "task_type": row.get("task_type"),
                "term": term,
                "scaffold_prompt": prompt or f"{term}:",
            }
        )
    rows.sort(key=lambda item: (str(item.get("case") or ""), str(item.get("term") or "")))
    return rows


def _looks_like_micro_training_report(report: dict[str, Any]) -> bool:
    title = str(report.get("title") or "").replace("_", "-")
    return bool(report.get("examples")) and "micro-training" in title


def _resolve_micro_report_path(report: dict[str, Any], source_path: str | Path | None) -> Path | None:
    if _looks_like_micro_training_report(report) and source_path is not None:
        return Path(source_path)
    raw = report.get("source_required_term_micro_training")
    if not raw:
        return None
    candidate = Path(str(raw).replace("\\", "/"))
    candidates = [candidate, Path.cwd() / candidate]
    if source_path is not None:
        source_parent = Path(source_path).parent
        candidates.extend(anchor / candidate for anchor in (source_parent, *source_parent.parents))
    for item in candidates:
        if item.is_file():
            return item
        if item.is_dir():
            nested = item / REQUIRED_TERM_MICRO_TRAINING_JSON_FILENAME
            if nested.is_file():
                return nested
    return candidate


def _input_issues(
    source_report: dict[str, Any],
    micro_report: dict[str, Any],
    examples: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not source_report:
        issues.append("source report is missing or invalid")
    if not micro_report:
        issues.append("source required-term micro-training report could not be resolved")
    if micro_report and micro_report.get("status") != "pass":
        issues.append("source required-term micro-training report is not pass")
    if not examples:
        issues.append("source required-term micro-training report has no usable examples")
    return issues


def _pattern_line(pattern: str, *, cycle: int, case: str, prompt: str, term: str) -> str:
    prefix = f"cycle={cycle:02d}|pattern={pattern}|case={case}"
    if pattern == "direct_cue":
        return f"{prefix}|{prompt}{term}"
    if pattern == "spaced_cue":
        return f"{prefix}|{prompt} {term}"
    if pattern == "case_binding":
        return f"{prefix}|prompt={prompt}|continuation={term}"
    if pattern == "instruction_binding":
        return f'{prefix}|when_prompt="{prompt}"|next_required_term="{term}"'
    if pattern == "question_answer":
        return f"{prefix}|question=what term follows {prompt}|answer={term}"
    return f"{prefix}|not_holdout_claim=true|target_term={term}|cue={prompt}"


def _pattern_counts(lines: list[str]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for line in lines:
        marker = "pattern="
        if marker not in line:
            continue
        pattern = line.split(marker, 1)[1].split("|", 1)[0]
        if pattern:
            counts[pattern] += 1
    return dict(counts)


def _balanced_corpus_decision(
    *,
    line_count: int,
    unique_line_rate: float,
    term_line_min: int,
    term_line_max: int,
    pattern_counts: dict[str, int],
) -> str:
    if not line_count:
        return "no_balanced_corpus_lines"
    if term_line_min == term_line_max and unique_line_rate >= 0.98 and len(pattern_counts) >= 5:
        return "balanced_corpus_candidate_ready"
    return "balanced_corpus_candidate_needs_review"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_balanced_corpus"
    if summary.get("balanced_corpus_decision") == "balanced_corpus_candidate_ready":
        return "required_term_balanced_corpus_candidate_ready"
    return "required_term_balanced_corpus_candidate_needs_review"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The balanced corpus candidate could not be built from a clean micro-training source."
    if summary.get("balanced_corpus_decision") == "balanced_corpus_candidate_ready":
        return "The candidate corpus keeps term exposure balanced while increasing line uniqueness versus the legacy repeated corpus."
    return "The candidate corpus was produced, but balance or uniqueness checks still need review."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair corpus source resolution before rerunning model capability training"
    if summary.get("balanced_corpus_decision") == "balanced_corpus_candidate_ready":
        return "train a tiny checkpoint on this balanced corpus and rerun split/seed stability"
    return "adjust corpus patterns or repeat count before the next training run"
