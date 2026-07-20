from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
)
from minigpt.model_capability_required_term_pair_rebalance_core import (
    REQUIRED_TERM_PAIR_REBALANCE_HTML_FILENAME as REQUIRED_TERM_PAIR_REBALANCE_HTML_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME as REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_MARKDOWN_FILENAME as REQUIRED_TERM_PAIR_REBALANCE_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_TEXT_FILENAME as REQUIRED_TERM_PAIR_REBALANCE_TEXT_FILENAME,
    _decision,
    _input_issues,
    _interpretation_reason,
    _model_quality_claim,
    _next_action,
    _previous_baseline,
    _run_rebalance_pair,
    build_required_term_pair_rebalance_corpus as build_required_term_pair_rebalance_corpus,
    compare_rebalance_pairs,
    resolve_exit_code as resolve_exit_code,
    select_rebalance_pairs,
    summarize_rebalance_probe_rows,
    summarize_required_term_pair_rebalance,
)
from minigpt.model_capability_required_term_pair_curriculum import (
    REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME,
    read_json_report as read_json_report,
)
from minigpt.report_utils import as_dict, utc_now


def locate_model_capability_required_term_pair_rebalance_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_rebalance(
    pair_curriculum_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    pair_limit: int | None = None,
    repeat: int = 240,
    isolated_repeat: int = 2,
    max_iters: int = 1600,
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
    generation_seed: int = 495,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_summary = as_dict(pair_curriculum_report.get("summary"))
    pairs = select_rebalance_pairs(pair_curriculum_report, pair_limit=pair_limit)
    issues = _input_issues(pair_curriculum_report, pairs)

    pair_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for pair_index, pair in enumerate(pairs):
            pair_result = _run_rebalance_pair(
                root,
                pair,
                pair_index=pair_index,
                repeat=repeat,
                isolated_repeat=isolated_repeat,
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
            pair_rows.append(pair_result["pair_row"])
            probe_rows.extend(pair_result["probe_rows"])

    training_failures = [row for row in pair_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} pair rebalance training runs did not complete successfully")

    pair_summaries = summarize_rebalance_probe_rows(pairs, probe_rows)
    compare_rows = compare_rebalance_pairs(pairs, pair_summaries)
    summary = summarize_required_term_pair_rebalance(
        pairs,
        pair_rows,
        probe_rows,
        pair_summaries,
        compare_rows,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair rebalance",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_curriculum": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "pair_limit": pair_limit,
            "repeat": max(1, int(repeat)),
            "isolated_repeat": max(1, int(isolated_repeat)),
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
            "experiment_boundary": "rebalance partial two-term curricula before expanding to larger target groups",
        },
        "previous_baseline": _previous_baseline(source_summary),
        "summary": summary,
        "selected_pair_count": len(pairs),
        "pairs": pairs,
        "pair_rows": pair_rows,
        "pair_summaries": pair_summaries,
        "compare_rows": compare_rows,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


# Execution and aggregation helpers are re-exported from the core module.
