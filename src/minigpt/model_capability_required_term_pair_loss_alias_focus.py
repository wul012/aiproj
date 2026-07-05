from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc, TrainFunc
from minigpt.model_capability_required_term_pair_loss_alias_focus_core import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_CORPUS_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_HTML_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_TEXT_FILENAME,
    _clean_seeds,
    _decision,
    _input_issues,
    _model_quality_claim,
    _next_action,
    _reason,
    _run_focus_seed,
    build_loss_alias_focus_corpus,
    resolve_exit_code,
    select_loss_alias_focus_cases,
    select_loss_alias_support_cases,
    summarize_loss_alias_focus,
    summarize_loss_alias_focus_seed_rows,
)
from minigpt.model_capability_required_term_pair_loss_alias_stability import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME,
    read_json_report,
)
from minigpt.report_utils import utc_now


def locate_model_capability_required_term_pair_loss_alias_focus_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_loss_alias_focus(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = (515,),
    base_repeat: int = 180,
    focus_repeat: int = 180,
    bridge_repeat: int = 4,
    max_iters: int = 900,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 16,
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
    clean_seeds = _clean_seeds(seeds)
    support_cases = select_loss_alias_support_cases(stability_report)
    focus_cases = select_loss_alias_focus_cases(stability_report)
    issues = _input_issues(stability_report, clean_seeds, support_cases, focus_cases)
    seed_reports: list[dict[str, Any]] = []
    if not issues:
        for index, seed in enumerate(clean_seeds):
            seed_reports.append(
                _run_focus_seed(
                    support_cases,
                    focus_cases,
                    out_dir=root / "seed-runs" / f"seed-{seed}",
                    seed=seed,
                    base_repeat=base_repeat,
                    focus_repeat=focus_repeat,
                    bridge_repeat=bridge_repeat,
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
            )
            if seed_reports[index].get("status") != "pass":
                issues.append(f"seed {seed} loss-alias focus run did not pass structurally")

    seed_rows = summarize_loss_alias_focus_seed_rows(clean_seeds, seed_reports)
    summary = summarize_loss_alias_focus(seed_rows, support_cases, focus_cases)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias focus",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_loss_alias_stability": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seeds": clean_seeds,
            "base_repeat": max(1, int(base_repeat)),
            "focus_repeat": max(1, int(focus_repeat)),
            "bridge_repeat": max(0, int(bridge_repeat)),
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
            "experiment_boundary": "boost only the loss alias rows missed by v515 before recombining fixed and loss",
        },
        "support_cases": support_cases,
        "focus_cases": focus_cases,
        "seed_rows": seed_rows,
        "seed_reports": seed_reports,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


# Execution, aggregation, and interpretation helpers are re-exported from the core module.
