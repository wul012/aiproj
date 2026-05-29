from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_balanced_training import (
    REQUIRED_TERM_BALANCED_TRAINING_JSON_FILENAME,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PROMPT_LEADING_CORPUS_JSON_FILENAME = "model_capability_required_term_prompt_leading_corpus.json"
REQUIRED_TERM_PROMPT_LEADING_CORPUS_TEXT_FILENAME = "model_capability_required_term_prompt_leading_corpus.txt"
REQUIRED_TERM_PROMPT_LEADING_CORPUS_MARKDOWN_FILENAME = "model_capability_required_term_prompt_leading_corpus.md"
REQUIRED_TERM_PROMPT_LEADING_CORPUS_HTML_FILENAME = "model_capability_required_term_prompt_leading_corpus.html"
REQUIRED_TERM_PROMPT_LEADING_CORPUS_FILENAME = "required_term_prompt_leading_corpus.txt"

PROMPT_LEADING_PATTERNS = (
    "direct",
    "spaced",
    "answer",
    "case_tag",
)


def locate_model_capability_required_term_prompt_leading_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        for filename in (
            REQUIRED_TERM_BALANCED_TRAINING_JSON_FILENAME,
            "model_capability_required_term_balanced_corpus.json",
        ):
            candidate = source / filename
            if candidate.is_file():
                return candidate
    return source


def build_model_capability_required_term_prompt_leading_corpus(
    source_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    repeat: int = 10,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    repeat_count = max(1, int(repeat))
    balanced_corpus_report = _resolve_balanced_corpus_report(source_report, source_path)
    term_rows = _term_rows(balanced_corpus_report or source_report)
    issues = _input_issues(source_report, balanced_corpus_report, term_rows)

    corpus_text, rows = build_required_term_prompt_leading_corpus(term_rows, repeat=repeat_count)
    corpus_path = root / REQUIRED_TERM_PROMPT_LEADING_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")

    previous = _previous_alignment(source_report, balanced_corpus_report)
    summary = summarize_required_term_prompt_leading_corpus(corpus_text, rows, repeat=repeat_count, previous=previous)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term prompt-leading corpus",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_report": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "repeat": repeat_count,
            "patterns": list(PROMPT_LEADING_PATTERNS),
            "pattern_count": len(PROMPT_LEADING_PATTERNS),
            "selection_strategy": "reuse v487 unique required-term rows and force every training row to start with the scaffold prompt",
            "training_boundary": "candidate corpus only; downstream training and holdout checks must still be rerun",
        },
        "corpus": {
            "path": str(corpus_path),
            "char_count": len(corpus_text),
            "line_count": len(corpus_text.splitlines()),
            "repeat": repeat_count,
            "vocab_boundary": "all selected terms are visible because this is a training candidate, not a held-out evaluation corpus",
        },
        "summary": summary,
        "term_rows": rows,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def build_required_term_prompt_leading_corpus(
    term_rows: list[dict[str, Any]],
    *,
    repeat: int,
) -> tuple[str, list[dict[str, Any]]]:
    repeat_count = max(1, int(repeat))
    lines = [
        "MiniGPT required-term prompt-leading corpus candidate.",
        "Every training row starts with the scaffold prompt so short continuation probes see the same prefix shape.",
        "Boundary: this is training input only; held-out prompt-to-term pairs must still be hidden in evaluation.",
    ]
    rows: list[dict[str, Any]] = []
    for item in term_rows:
        term = str(item.get("term") or "").strip()
        prompt = str(item.get("scaffold_prompt") or "").strip()
        if not term:
            continue
        prompt = prompt or f"{term}:"
        case = str(item.get("case") or "unknown-case").strip()
        before = len(lines)
        for cycle in range(1, repeat_count + 1):
            for pattern in PROMPT_LEADING_PATTERNS:
                lines.append(_prompt_leading_line(pattern, cycle=cycle, case=case, prompt=prompt, term=term))
        rows.append(
            {
                "case": case,
                "term": term,
                "scaffold_prompt": prompt,
                "line_count": len(lines) - before,
                "expected_line_count": repeat_count * len(PROMPT_LEADING_PATTERNS),
                "pattern_count": len(PROMPT_LEADING_PATTERNS),
                "repeat": repeat_count,
            }
        )
    return "\n".join(lines) + "\n", rows


def summarize_required_term_prompt_leading_corpus(
    corpus_text: str,
    term_rows: list[dict[str, Any]],
    *,
    repeat: int,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lines = [line for line in corpus_text.splitlines() if line.strip()]
    unique_lines = set(lines)
    prompt_counts = _prompt_leading_counts(lines, term_rows)
    term_counts = [int(row.get("line_count") or 0) for row in term_rows]
    pattern_counts = _pattern_counts(lines)
    prompt_ready = bool(term_rows) and all(count > 0 for count in prompt_counts.values())
    term_line_min = min(term_counts) if term_counts else 0
    term_line_max = max(term_counts) if term_counts else 0
    unique_line_rate = round(len(unique_lines) / len(lines), 4) if lines else 0.0
    previous_alignment = previous or {}
    return {
        "prompt_leading_corpus_decision": _prompt_leading_decision(
            lines=lines,
            prompt_ready=prompt_ready,
            term_line_min=term_line_min,
            term_line_max=term_line_max,
            pattern_counts=pattern_counts,
        ),
        "term_count": len(term_rows),
        "unique_term_count": len({str(row.get("term")) for row in term_rows if row.get("term")}),
        "repeat": max(1, int(repeat)),
        "pattern_count": len(pattern_counts),
        "line_count": len(lines),
        "unique_line_count": len(unique_lines),
        "duplicate_line_count": len(lines) - len(unique_lines),
        "unique_line_rate": unique_line_rate,
        "term_line_min": term_line_min,
        "term_line_max": term_line_max,
        "term_line_spread": term_line_max - term_line_min if term_counts else 0,
        "term_line_balance_ready": bool(term_counts) and term_line_min == term_line_max,
        "prompt_leading_line_count": sum(prompt_counts.values()),
        "prompt_aligned_term_count": sum(1 for count in prompt_counts.values() if count > 0),
        "prompt_alignment_ready": prompt_ready,
        "previous_prompt_alignment_ready": previous_alignment.get("prompt_alignment_ready"),
        "previous_prompt_leading_line_count": previous_alignment.get("prompt_leading_line_count"),
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "term_prompt_leading_counts": dict(sorted(prompt_counts.items())),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _resolve_balanced_corpus_report(source_report: dict[str, Any], source_path: str | Path | None) -> dict[str, Any]:
    if source_report.get("term_rows") and as_dict(source_report.get("corpus")).get("path"):
        return source_report
    raw = source_report.get("source_required_term_balanced_corpus")
    if not raw:
        return {}
    candidate = Path(str(raw).replace("\\", "/"))
    candidates = [candidate, Path.cwd() / candidate]
    if source_path is not None:
        source_parent = Path(source_path).parent
        candidates.extend(anchor / candidate for anchor in (source_parent, *source_parent.parents))
    for item in candidates:
        if item.is_file():
            return read_json_report(item)
        if item.is_dir():
            nested = item / "model_capability_required_term_balanced_corpus.json"
            if nested.is_file():
                return read_json_report(nested)
    return {}


def _term_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in list_of_dicts(report.get("term_rows")):
        term = str(row.get("term") or "").strip()
        prompt = str(row.get("scaffold_prompt") or "").strip()
        if not term or term in seen:
            continue
        seen.add(term)
        rows.append(
            {
                "case": row.get("case"),
                "term": term,
                "scaffold_prompt": prompt or f"{term}:",
            }
        )
    rows.sort(key=lambda item: (str(item.get("case") or ""), str(item.get("term") or "")))
    return rows


def _input_issues(
    source_report: dict[str, Any],
    balanced_corpus_report: dict[str, Any],
    term_rows: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not source_report:
        issues.append("source report is missing or invalid")
    if source_report and source_report.get("status") != "pass":
        issues.append("source report is not pass")
    if not balanced_corpus_report:
        issues.append("source balanced corpus report could not be resolved")
    if balanced_corpus_report and balanced_corpus_report.get("status") != "pass":
        issues.append("source balanced corpus report is not pass")
    if not term_rows:
        issues.append("source report has no usable required-term rows")
    return issues


def _previous_alignment(source_report: dict[str, Any], balanced_corpus_report: dict[str, Any]) -> dict[str, Any]:
    source_summary = as_dict(source_report.get("summary"))
    source_corpus = as_dict(source_report.get("source_corpus"))
    if source_summary.get("prompt_alignment_ready") is not None:
        return {
            "prompt_alignment_ready": source_summary.get("prompt_alignment_ready"),
            "prompt_leading_line_count": source_summary.get("prompt_leading_line_count"),
        }
    return {
        "prompt_alignment_ready": source_corpus.get("prompt_alignment_ready"),
        "prompt_leading_line_count": source_corpus.get("prompt_leading_line_count"),
        "balanced_unique_line_rate": as_dict(balanced_corpus_report.get("summary")).get("unique_line_rate"),
    }


def _prompt_leading_line(pattern: str, *, cycle: int, case: str, prompt: str, term: str) -> str:
    meta = f"|pattern={pattern}|cycle={cycle:02d}|case={case}"
    if pattern == "direct":
        return f"{prompt}{term}{meta}"
    if pattern == "spaced":
        return f"{prompt} {term}{meta}"
    if pattern == "answer":
        return f"{prompt} answer={term}{meta}"
    return f"{prompt} case={case}; term={term}{meta}"


def _prompt_leading_counts(lines: list[str], term_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in term_rows:
        term = str(row.get("term") or "")
        prompt = str(row.get("scaffold_prompt") or "")
        counts[term] = sum(1 for line in lines if prompt and line.startswith(prompt) and term.casefold() in line.casefold())
    return counts


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


def _prompt_leading_decision(
    *,
    lines: list[str],
    prompt_ready: bool,
    term_line_min: int,
    term_line_max: int,
    pattern_counts: dict[str, int],
) -> str:
    if not lines:
        return "no_prompt_leading_corpus_lines"
    if prompt_ready and term_line_min == term_line_max and len(pattern_counts) == len(PROMPT_LEADING_PATTERNS):
        return "prompt_leading_corpus_candidate_ready"
    return "prompt_leading_corpus_candidate_needs_review"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_prompt_leading_corpus"
    if summary.get("prompt_leading_corpus_decision") == "prompt_leading_corpus_candidate_ready":
        return "required_term_prompt_leading_corpus_candidate_ready"
    return "required_term_prompt_leading_corpus_candidate_needs_review"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The prompt-leading corpus candidate could not be built from clean source evidence."
    if summary.get("prompt_alignment_ready"):
        return "Every selected scaffold prompt now appears at the start of training rows while term exposure stays balanced."
    return "The corpus was produced, but at least one required term still lacks prompt-leading rows."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair prompt-leading corpus inputs before rerunning balanced training"
    if summary.get("prompt_alignment_ready"):
        return "train a tiny checkpoint on this prompt-leading corpus and compare continuation uptake"
    return "adjust prompt-leading pattern generation before training"
