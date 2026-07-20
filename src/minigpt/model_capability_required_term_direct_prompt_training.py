from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_prompt_leading_training import (
    REQUIRED_TERM_PROMPT_LEADING_TRAINING_JSON_FILENAME,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_DIRECT_PROMPT_TRAINING_JSON_FILENAME = "model_capability_required_term_direct_prompt_training.json"
REQUIRED_TERM_DIRECT_PROMPT_TRAINING_TEXT_FILENAME = "model_capability_required_term_direct_prompt_training.txt"
REQUIRED_TERM_DIRECT_PROMPT_TRAINING_MARKDOWN_FILENAME = "model_capability_required_term_direct_prompt_training.md"
REQUIRED_TERM_DIRECT_PROMPT_TRAINING_HTML_FILENAME = "model_capability_required_term_direct_prompt_training.html"
REQUIRED_TERM_DIRECT_PROMPT_CORPUS_FILENAME = "required_term_direct_prompt_corpus.txt"

DIRECT_PROMPT_PATTERNS = ("direct", "spaced")


def locate_model_capability_required_term_direct_prompt_training_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PROMPT_LEADING_TRAINING_JSON_FILENAME
    return source


def build_model_capability_required_term_direct_prompt_training(
    prompt_leading_training_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    repeat: int = 96,
    max_iters: int = 900,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 8,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int | None = 1,
    generation_seed: int = 491,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    term_rows = _term_rows(prompt_leading_training_report)
    source_summary = as_dict(prompt_leading_training_report.get("summary"))
    issues = _input_issues(prompt_leading_training_report, term_rows, source_summary)

    corpus_text, direct_rows = build_required_term_direct_prompt_corpus(term_rows, repeat=repeat)
    corpus_path = root / REQUIRED_TERM_DIRECT_PROMPT_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")

    train_dir = root / "direct-prompt-run"
    training: dict[str, Any] = {"status": "skipped", "reason": "input issues prevented training"}
    if not issues:
        training = _train_micro_checkpoint(
            {
                "corpus_path": str(corpus_path),
                "train_dir": str(train_dir),
                "max_iters": max_iters,
                "eval_iters": eval_iters,
                "batch_size": batch_size,
                "block_size": block_size,
                "n_layer": n_layer,
                "n_head": n_head,
                "n_embd": n_embd,
                "learning_rate": learning_rate,
                "seed": generation_seed,
                "device": device,
                "sample_prompt": _sample_prompt(direct_rows),
            },
            train_func,
        )
        if training.get("status") != "pass":
            issues.append("direct prompt training command did not complete successfully")

    generation_rows: list[dict[str, Any]] = []
    if training.get("status") == "pass":
        generation_rows = [
            _generation_row(
                row,
                training,
                index=index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=generation_seed,
                device=device,
                generate_func=generate_func,
            )
            for index, row in enumerate(direct_rows)
        ]

    corpus_summary = summarize_direct_prompt_corpus(corpus_text, direct_rows)
    summary = summarize_required_term_direct_prompt_training(
        direct_rows,
        generation_rows,
        training,
        corpus_summary=corpus_summary,
        previous_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term direct prompt training",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_prompt_leading_training": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "repeat": max(1, int(repeat)),
            "patterns": list(DIRECT_PROMPT_PATTERNS),
            "pattern_count": len(DIRECT_PROMPT_PATTERNS),
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "generation_seed": generation_seed,
            "device": device,
            "experiment_boundary": "remove v489 metadata and extra prompt-leading variants before increasing architecture size",
        },
        "corpus": {
            "path": str(corpus_path),
            "char_count": len(corpus_text),
            "line_count": len(corpus_text.splitlines()),
            "repeat": max(1, int(repeat)),
            "pattern_boundary": "direct and spaced prompt-to-term rows only; no metadata suffixes",
        },
        "previous_baseline": _previous_baseline(source_summary),
        "training": training,
        "summary": summary,
        "term_rows": direct_rows,
        "generation_count": len(generation_rows),
        "generation_rows": generation_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def build_required_term_direct_prompt_corpus(
    term_rows: list[dict[str, Any]],
    *,
    repeat: int,
) -> tuple[str, list[dict[str, Any]]]:
    repeat_count = max(1, int(repeat))
    lines = [
        "MiniGPT required-term direct prompt corpus candidate.",
        "Rows intentionally contain only scaffold prompt plus target term.",
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
        for _ in range(repeat_count):
            lines.append(f"{prompt}{term}")
            lines.append(f"{prompt} {term}")
        rows.append(
            {
                "case": case,
                "term": term,
                "scaffold_prompt": prompt,
                "direct_prompt_line_count": len(lines) - before,
                "direct_prompt_pattern_count": len(DIRECT_PROMPT_PATTERNS),
                "direct_prompt_repeat": repeat_count,
            }
        )
    return "\n".join(lines) + "\n", rows


def summarize_direct_prompt_corpus(corpus_text: str, term_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lines = [line for line in corpus_text.splitlines() if line.strip()]
    unique_lines = set(lines)
    counts = _term_counts(lines, term_rows)
    line_counts = [int(row.get("direct_prompt_line_count") or 0) for row in term_rows]
    pattern_counts = _pattern_counts(lines, term_rows)
    return {
        "term_count": len(term_rows),
        "line_count": len(lines),
        "unique_line_count": len(unique_lines),
        "duplicate_line_count": len(lines) - len(unique_lines),
        "unique_line_rate": round(len(unique_lines) / len(lines), 4) if lines else 0.0,
        "term_line_min": min(line_counts) if line_counts else 0,
        "term_line_max": max(line_counts) if line_counts else 0,
        "term_line_spread": (max(line_counts) - min(line_counts)) if line_counts else 0,
        "direct_prompt_line_count": sum(counts.values()),
        "direct_prompt_ready": bool(term_rows) and all(count > 0 for count in counts.values()),
        "term_direct_prompt_counts": dict(sorted(counts.items())),
        "pattern_counts": dict(sorted(pattern_counts.items())),
    }


def summarize_required_term_direct_prompt_training(
    term_rows: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    training: dict[str, Any],
    *,
    corpus_summary: dict[str, Any] | None = None,
    previous_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in generation_rows)
    generated_hits = sum(int(row.get("generated_hit_count") or 0) for row in generation_rows)
    case_hits = sum(1 for row in generation_rows if int(row.get("continuation_hit_count") or 0) > 0)
    corpus = corpus_summary or {}
    previous = previous_summary or {}
    previous_continuation_hits = int(previous.get("continuation_hit_count") or 0)
    return {
        "direct_prompt_training_decision": _direct_prompt_training_decision(
            term_rows,
            generation_rows,
            continuation_hits,
            previous_continuation_hits,
            training,
        ),
        "term_count": len(term_rows),
        "generation_count": len(generation_rows),
        "continuation_hit_count": continuation_hits,
        "generated_hit_count": generated_hits,
        "prompt_hit_count": sum(int(row.get("prompt_hit_count") or 0) for row in generation_rows),
        "case_with_continuation_hit_count": case_hits,
        "continuation_hit_rate": round(case_hits / len(generation_rows), 4) if generation_rows else 0.0,
        "previous_continuation_hit_count": previous_continuation_hits,
        "continuation_hit_delta": continuation_hits - previous_continuation_hits,
        "improved_over_previous": continuation_hits > previous_continuation_hits,
        "training_status": training.get("status"),
        "training_returncode": training.get("returncode"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "metrics_exists": bool(training.get("metrics_exists")),
        "train_config_exists": bool(training.get("train_config_exists")),
        "direct_prompt_ready": bool(corpus.get("direct_prompt_ready")),
        "direct_prompt_line_count": corpus.get("direct_prompt_line_count", 0),
        "term_line_spread": corpus.get("term_line_spread", 0),
    }


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


def _input_issues(report: dict[str, Any], term_rows: list[dict[str, Any]], source_summary: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source prompt-leading training report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source prompt-leading training report is not pass")
    if not term_rows:
        issues.append("source prompt-leading training report has no usable term rows")
    if report and source_summary.get("training_status") != "pass":
        issues.append("source prompt-leading training did not finish cleanly")
    return issues


def _direct_prompt_training_decision(
    term_rows: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    continuation_hits: int,
    previous_continuation_hits: int,
    training: dict[str, Any],
) -> str:
    if training.get("status") != "pass":
        return "direct_prompt_training_run_failed"
    if not term_rows:
        return "no_required_term_rows"
    if not generation_rows:
        return "direct_prompt_training_generation_missing"
    if continuation_hits > previous_continuation_hits:
        return "direct_prompt_training_improved_over_previous"
    if continuation_hits > 0:
        return "direct_prompt_training_required_term_uptake_observed"
    return "direct_prompt_training_completed_without_uptake"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_direct_prompt_training"
    if summary.get("improved_over_previous"):
        return "required_term_direct_prompt_training_improved"
    if summary.get("continuation_hit_count"):
        return "required_term_direct_prompt_training_uptake_observed"
    return "required_term_direct_prompt_training_completed_without_uptake"


def _previous_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt_leading_training_decision": summary.get("prompt_leading_training_decision"),
        "continuation_hit_count": int(summary.get("continuation_hit_count") or 0),
        "prompt_alignment_ready": summary.get("prompt_alignment_ready"),
        "prompt_leading_line_count": summary.get("prompt_leading_line_count"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("improved_over_previous"):
        return "direct_prompt_training_signal_only"
    if summary.get("continuation_hit_count"):
        return "required_term_training_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The direct prompt training run did not complete cleanly."
    if summary.get("improved_over_previous"):
        return "Simplifying the corpus to direct prompt-to-term rows produced more required-term continuation hits than v490."
    if summary.get("continuation_hit_count"):
        return "The direct prompt corpus produced required-term continuation hits, but not above the previous baseline count."
    return "The direct prompt training run completed, but short continuations still did not include required terms."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair direct prompt training inputs before rerunning capability checks"
    if summary.get("improved_over_previous"):
        return "rerun the direct prompt training across multiple seeds to check stability"
    return "increase repeat or max_iters further, or train one term at a time to isolate capacity limits"


def _term_counts(lines: list[str], term_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in term_rows:
        term = str(row.get("term") or "")
        prompt = str(row.get("scaffold_prompt") or "")
        counts[term] = sum(1 for line in lines if prompt and line.startswith(prompt) and term.casefold() in line.casefold())
    return counts


def _pattern_counts(lines: list[str], term_rows: list[dict[str, Any]]) -> dict[str, int]:
    prompts = {str(row.get("scaffold_prompt") or ""): str(row.get("term") or "") for row in term_rows}
    counts: Counter[str] = Counter()
    for line in lines:
        for prompt, term in prompts.items():
            if not prompt or not line.startswith(prompt):
                continue
            remainder = line[len(prompt) :]
            if remainder == term:
                counts["direct"] += 1
            elif remainder == f" {term}":
                counts["spaced"] += 1
            break
    return dict(counts)


def _sample_prompt(term_rows: list[dict[str, Any]]) -> str:
    for row in term_rows:
        prompt = str(row.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "data:"
