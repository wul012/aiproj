from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
)
from minigpt.model_capability_required_term_pair_rebalance_seed_stability_core import (
    DEFAULT_PAIR_REBALANCE_STABILITY_SEEDS,
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_HTML_FILENAME as REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_HTML_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_JSON_FILENAME as REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_JSON_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_MARKDOWN_FILENAME as REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_TEXT_FILENAME as REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_TEXT_FILENAME,
    _clean_seeds,
    _decision,
    _input_issues,
    _interpretation_reason,
    _model_quality_claim,
    _next_action,
    _previous_baseline,
    _run_pair_seed,
    resolve_exit_code as resolve_exit_code,
    select_rebalance_seed_stability_pairs,
    summarize_pair_seed_stability,
    summarize_required_term_pair_rebalance_seed_stability,
    summarize_seed_pair_probe_rows,
)
from minigpt.model_capability_required_term_pair_rebalance import (
    REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME,
    read_json_report as read_json_report,
)
from minigpt.report_utils import as_dict, utc_now


def locate_model_capability_required_term_pair_rebalance_seed_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_rebalance_seed_stability(
    pair_rebalance_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = DEFAULT_PAIR_REBALANCE_STABILITY_SEEDS,
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
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_summary = as_dict(pair_rebalance_report.get("summary"))
    selected_pairs = select_rebalance_seed_stability_pairs(pair_rebalance_report, pair_limit=pair_limit)
    resolved_seeds = _clean_seeds(seeds)
    issues = _input_issues(pair_rebalance_report, selected_pairs, resolved_seeds)

    pair_seed_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for pair_index, pair in enumerate(selected_pairs):
            for seed_index, seed in enumerate(resolved_seeds):
                seed_result = _run_pair_seed(
                    root,
                    pair,
                    pair_index=pair_index,
                    seed_index=seed_index,
                    seed=seed,
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
                    device=device,
                    train_func=train_func,
                    generate_func=generate_func,
                )
                pair_seed_rows.append(seed_result["pair_seed_row"])
                probe_rows.extend(seed_result["probe_rows"])

    training_failures = [row for row in pair_seed_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} pair rebalance seed-stability runs did not complete successfully")

    seed_pair_summaries = summarize_seed_pair_probe_rows(selected_pairs, probe_rows, resolved_seeds)
    pair_seed_summaries = summarize_pair_seed_stability(selected_pairs, seed_pair_summaries, resolved_seeds)
    summary = summarize_required_term_pair_rebalance_seed_stability(
        selected_pairs,
        pair_seed_rows,
        probe_rows,
        seed_pair_summaries,
        pair_seed_summaries,
        resolved_seeds,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair rebalance seed stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_rebalance": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seeds": resolved_seeds,
            "seed_count": len(resolved_seeds),
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
            "device": device,
            "experiment_boundary": "repeat v495 full-hit rebalance pairs across seeds before expanding curriculum size",
        },
        "previous_baseline": _previous_baseline(source_summary),
        "summary": summary,
        "selected_pair_count": len(selected_pairs),
        "pairs": selected_pairs,
        "pair_seed_run_count": len(pair_seed_rows),
        "pair_seed_rows": pair_seed_rows,
        "seed_pair_summaries": seed_pair_summaries,
        "pair_seed_summaries": pair_seed_summaries,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


# Execution and aggregation helpers are re-exported from the core module.
