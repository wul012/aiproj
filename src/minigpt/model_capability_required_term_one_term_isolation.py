from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_direct_prompt_training import (
    REQUIRED_TERM_DIRECT_PROMPT_TRAINING_JSON_FILENAME,
)
from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_ONE_TERM_ISOLATION_JSON_FILENAME = "model_capability_required_term_one_term_isolation.json"
REQUIRED_TERM_ONE_TERM_ISOLATION_TEXT_FILENAME = "model_capability_required_term_one_term_isolation.txt"
REQUIRED_TERM_ONE_TERM_ISOLATION_MARKDOWN_FILENAME = "model_capability_required_term_one_term_isolation.md"
REQUIRED_TERM_ONE_TERM_ISOLATION_HTML_FILENAME = "model_capability_required_term_one_term_isolation.html"

ONE_TERM_PATTERNS = ("direct", "spaced")


def locate_model_capability_required_term_one_term_isolation_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_DIRECT_PROMPT_TRAINING_JSON_FILENAME
    return source


def build_model_capability_required_term_one_term_isolation(
    direct_prompt_training_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    repeat: int = 200,
    max_iters: int = 1200,
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
    generation_seed: int = 492,
    device: str = "cpu",
    term_limit: int | None = None,
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_summary = as_dict(direct_prompt_training_report.get("summary"))
    all_terms = _term_rows(direct_prompt_training_report)
    selected_terms = all_terms[:term_limit] if term_limit is not None and term_limit >= 0 else all_terms
    issues = _input_issues(direct_prompt_training_report, selected_terms, source_summary)

    isolation_rows: list[dict[str, Any]] = []
    if not issues:
        for index, term_row in enumerate(selected_terms):
            isolation_rows.append(
                _run_one_term(
                    root,
                    term_row,
                    index=index,
                    repeat=repeat,
                    max_iters=max_iters,
                    eval_iters=eval_iters,
                    batch_size=batch_size,
                    block_size=block_size,
                    n_layer=n_layer,
                    n_head=n_head,
                    n_embd=n_embd,
                    learning_rate=learning_rate,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    generation_seed=generation_seed,
                    device=device,
                    train_func=train_func,
                    generate_func=generate_func,
                )
            )
    training_failures = [row for row in isolation_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} one-term training runs did not complete successfully")

    summary = summarize_required_term_one_term_isolation(
        selected_terms,
        isolation_rows,
        previous_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term one-term isolation",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_direct_prompt_training": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "repeat": max(1, int(repeat)),
            "patterns": list(ONE_TERM_PATTERNS),
            "pattern_count": len(ONE_TERM_PATTERNS),
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
            "term_limit": term_limit,
            "experiment_boundary": "train one checkpoint per required term to isolate single-target capacity",
        },
        "previous_baseline": _previous_baseline(source_summary),
        "summary": summary,
        "term_count": len(selected_terms),
        "term_rows": selected_terms,
        "isolation_count": len(isolation_rows),
        "isolation_rows": isolation_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def build_required_term_one_term_corpus(term_row: dict[str, Any], *, repeat: int) -> str:
    repeat_count = max(1, int(repeat))
    term = str(term_row.get("term") or "").strip()
    prompt = str(term_row.get("scaffold_prompt") or "").strip() or f"{term}:"
    lines = [
        "MiniGPT required-term one-term isolation corpus.",
        "Only one target term is present in this training file.",
    ]
    for _ in range(repeat_count):
        lines.append(f"{prompt}{term}")
        lines.append(f"{prompt} {term}")
    return "\n".join(lines) + "\n"


def summarize_required_term_one_term_isolation(
    term_rows: list[dict[str, Any]],
    isolation_rows: list[dict[str, Any]],
    *,
    previous_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    previous = previous_summary or {}
    previous_hits = int(previous.get("continuation_hit_count") or 0)
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in isolation_rows)
    term_hits = sum(1 for row in isolation_rows if int(row.get("continuation_hit_count") or 0) > 0)
    pass_count = sum(1 for row in isolation_rows if row.get("training_status") == "pass")
    checkpoint_count = sum(1 for row in isolation_rows if row.get("checkpoint_exists"))
    return {
        "one_term_isolation_decision": _one_term_isolation_decision(
            term_rows,
            isolation_rows,
            continuation_hits,
            previous_hits,
            pass_count,
        ),
        "term_count": len(term_rows),
        "isolation_count": len(isolation_rows),
        "training_pass_count": pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "continuation_hit_count": continuation_hits,
        "term_with_continuation_hit_count": term_hits,
        "term_success_rate": round(term_hits / len(isolation_rows), 4) if isolation_rows else 0.0,
        "previous_continuation_hit_count": previous_hits,
        "continuation_hit_delta": continuation_hits - previous_hits,
        "improved_over_previous": continuation_hits > previous_hits,
        "all_terms_hit": bool(isolation_rows) and term_hits == len(isolation_rows),
        "single_term_capacity_observed": term_hits > 0,
        "max_single_term_continuation_hit_count": max(
            (int(row.get("continuation_hit_count") or 0) for row in isolation_rows),
            default=0,
        ),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_one_term(
    root: Path,
    term_row: dict[str, Any],
    *,
    index: int,
    repeat: int,
    max_iters: int,
    eval_iters: int,
    batch_size: int,
    block_size: int,
    n_layer: int,
    n_head: int,
    n_embd: int,
    learning_rate: float,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    generation_seed: int,
    device: str,
    train_func: TrainFunc | None,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    term = str(term_row.get("term") or "").strip()
    slug = _slug(term or f"term-{index + 1}")
    run_id = f"{index + 1:02d}-{slug}"
    corpus_text = build_required_term_one_term_corpus(term_row, repeat=repeat)
    corpus_path = root / "one-term-corpora" / f"{run_id}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "one-term-runs" / run_id
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
            "seed": generation_seed + index,
            "device": device,
            "sample_prompt": str(term_row.get("scaffold_prompt") or f"{term}:"),
        },
        train_func,
    )
    generation: dict[str, Any] = {}
    if training.get("status") == "pass":
        generation = _generation_row(
            {
                **term_row,
                "one_term_run_id": run_id,
                "one_term_corpus_path": str(corpus_path),
                "one_term_line_count": len(corpus_text.splitlines()) - 2,
                "one_term_repeat": max(1, int(repeat)),
            },
            training,
            index=index,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            generation_seed=generation_seed,
            device=device,
            generate_func=generate_func,
        )
    return {
        **term_row,
        "one_term_run_id": run_id,
        "one_term_corpus_path": str(corpus_path),
        "one_term_corpus_exists": corpus_path.is_file(),
        "one_term_line_count": len(corpus_text.splitlines()) - 2,
        "one_term_repeat": max(1, int(repeat)),
        "training_status": training.get("status"),
        "training_returncode": training.get("returncode"),
        "checkpoint_path": training.get("checkpoint_path"),
        "tokenizer_path": training.get("tokenizer_path"),
        "metrics_path": training.get("metrics_path"),
        "train_config_path": training.get("train_config_path"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "metrics_exists": bool(training.get("metrics_exists")),
        "train_config_exists": bool(training.get("train_config_exists")),
        "command_text": training.get("command_text"),
        "generation_seed": generation.get("generation_seed"),
        "generated": generation.get("generated", ""),
        "continuation": generation.get("continuation", ""),
        "prompt_truncated": generation.get("prompt_truncated", False),
        "prompt_hit_count": generation.get("prompt_hit_count", 0),
        "generated_hit_count": generation.get("generated_hit_count", 0),
        "continuation_hit_count": generation.get("continuation_hit_count", 0),
        "generated_preview": generation.get("generated_preview", ""),
        "continuation_preview": generation.get("continuation_preview", ""),
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
        issues.append("source direct prompt training report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source direct prompt training report is not pass")
    if not term_rows:
        issues.append("source direct prompt training report has no usable term rows")
    if report and source_summary.get("training_status") != "pass":
        issues.append("source direct prompt training did not finish cleanly")
    return issues


def _one_term_isolation_decision(
    term_rows: list[dict[str, Any]],
    isolation_rows: list[dict[str, Any]],
    continuation_hits: int,
    previous_hits: int,
    pass_count: int,
) -> str:
    if not term_rows:
        return "no_required_term_rows"
    if pass_count != len(term_rows):
        return "one_term_training_run_failed"
    if not isolation_rows:
        return "one_term_isolation_missing"
    if continuation_hits > previous_hits:
        return "one_term_isolation_capacity_observed"
    return "one_term_isolation_completed_without_uptake"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_one_term_isolation"
    if summary.get("single_term_capacity_observed"):
        return "required_term_one_term_capacity_observed"
    return "required_term_one_term_isolation_completed_without_uptake"


def _previous_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "direct_prompt_training_decision": summary.get("direct_prompt_training_decision"),
        "continuation_hit_count": int(summary.get("continuation_hit_count") or 0),
        "direct_prompt_ready": summary.get("direct_prompt_ready"),
        "direct_prompt_line_count": summary.get("direct_prompt_line_count"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("single_term_capacity_observed"):
        return "one_term_capacity_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "At least one one-term isolation run did not complete cleanly."
    if summary.get("single_term_capacity_observed"):
        return "At least one one-term checkpoint emitted its required term in continuation, isolating single-target capacity."
    return "Even isolated one-term checkpoints did not emit their required terms in short continuations."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed one-term runs before changing model settings"
    if summary.get("single_term_capacity_observed"):
        return "repeat successful one-term cases across seeds before returning to multi-term training"
    return "increase single-term max_iters or inspect tokenizer/generation settings before reintroducing multiple terms"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "term"
