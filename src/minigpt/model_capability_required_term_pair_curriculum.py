from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
)
from minigpt.model_capability_required_term_pair_curriculum_core import (
    REQUIRED_TERM_PAIR_CURRICULUM_HTML_FILENAME,
    REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME,
    REQUIRED_TERM_PAIR_CURRICULUM_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_CURRICULUM_TEXT_FILENAME,
    _decision,
    _input_issues,
    _interpretation_reason,
    _model_quality_claim,
    _next_action,
    _previous_baseline,
    _run_pair,
    build_pair_curriculum_pairs,
    build_required_term_pair_curriculum_corpus,
    resolve_exit_code,
    select_pair_curriculum_terms,
    summarize_pair_probe_rows,
    summarize_required_term_pair_curriculum,
)
from minigpt.model_capability_required_term_one_term_seed_stability import (
    REQUIRED_TERM_ONE_TERM_SEED_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, utc_now


def locate_model_capability_required_term_pair_curriculum_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_ONE_TERM_SEED_STABILITY_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_curriculum(
    seed_stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    include_partial_terms: bool = False,
    term_limit: int | None = None,
    pair_limit: int | None = None,
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
    generation_seed: int = 494,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_summary = as_dict(seed_stability_report.get("summary"))
    selected_terms = select_pair_curriculum_terms(
        seed_stability_report,
        include_partial_terms=include_partial_terms,
        term_limit=term_limit,
    )
    pairs = build_pair_curriculum_pairs(selected_terms, pair_limit=pair_limit)
    issues = _input_issues(seed_stability_report, selected_terms, pairs)

    pair_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for pair_index, pair in enumerate(pairs):
            pair_result = _run_pair(
                root,
                pair,
                pair_index=pair_index,
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
            pair_rows.append(pair_result["pair_row"])
            probe_rows.extend(pair_result["probe_rows"])

    training_failures = [row for row in pair_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} pair curriculum training runs did not complete successfully")

    pair_summaries = summarize_pair_probe_rows(pairs, probe_rows)
    summary = summarize_required_term_pair_curriculum(
        selected_terms,
        pairs,
        pair_rows,
        probe_rows,
        pair_summaries,
        previous_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair curriculum",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_one_term_seed_stability": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "include_partial_terms": include_partial_terms,
            "term_limit": term_limit,
            "pair_limit": pair_limit,
            "repeat": max(1, int(repeat)),
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
            "experiment_boundary": "train two stable required terms per checkpoint to inspect multi-target interference",
        },
        "previous_baseline": _previous_baseline(source_summary),
        "summary": summary,
        "selected_term_count": len(selected_terms),
        "selected_terms": selected_terms,
        "pair_count": len(pairs),
        "pairs": pairs,
        "pair_rows": pair_rows,
        "pair_summaries": pair_summaries,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


# Execution and aggregation helpers are re-exported from the core module.
