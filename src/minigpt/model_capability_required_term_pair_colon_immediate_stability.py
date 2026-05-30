from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_coexistence_refresh import (
    GenerateFunc,
    TrainFunc,
    build_model_capability_required_term_pair_coexistence_refresh,
    resolve_exit_code as _refresh_exit_code,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME = "model_capability_required_term_pair_colon_immediate_stability.json"
PAIR_COLON_IMMEDIATE_STABILITY_CSV_FILENAME = "model_capability_required_term_pair_colon_immediate_stability.csv"
PAIR_COLON_IMMEDIATE_STABILITY_TEXT_FILENAME = "model_capability_required_term_pair_colon_immediate_stability.txt"
PAIR_COLON_IMMEDIATE_STABILITY_MARKDOWN_FILENAME = "model_capability_required_term_pair_colon_immediate_stability.md"
PAIR_COLON_IMMEDIATE_STABILITY_HTML_FILENAME = "model_capability_required_term_pair_colon_immediate_stability.html"


def build_model_capability_required_term_pair_colon_immediate_stability(
    *,
    out_dir: str | Path,
    seeds: tuple[int, ...] = (535, 1535, 2535),
    repeat: int = 260,
    bridge_repeat: int = 20,
    max_iters: int = 1400,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 16,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    seed_reports: list[dict[str, Any]] = []
    seed_rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for seed in seeds:
        seed_dir = root / "seed-runs" / f"seed-{seed}"
        report = build_model_capability_required_term_pair_coexistence_refresh(
            out_dir=seed_dir,
            seed=seed,
            corpus_mode="colon_immediate",
            repeat=repeat,
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
            generated_at=generated_at,
            train_func=train_func,
            generate_func=generate_func,
        )
        seed_reports.append(report)
        row = _seed_row(seed, report, seed_dir)
        seed_rows.append(row)
        if report.get("status") != "pass":
            issues.append(f"seed {seed} refresh failed")
    summary = _summary(seed_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair colon-immediate stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "out_dir": str(root),
        "settings": {
            "seeds": list(seeds),
            "repeat": repeat,
            "bridge_repeat": bridge_repeat,
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
            "corpus_mode": "colon_immediate",
            "experiment_boundary": "repeat the v535 colon-immediate fixed/loss pair-full signal across seeds before promoting stability",
        },
        "seed_rows": seed_rows,
        "seed_reports": seed_reports,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    for seed_report in report.get("seed_reports", []):
        if isinstance(seed_report, dict) and _refresh_exit_code(seed_report, require_pass=require_pass):
            return 1
    return 0


def _seed_row(seed: int, report: dict[str, Any], seed_dir: Path) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    replay = as_dict(report.get("replay_report"))
    return {
        "seed": seed,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "pair_full_observed": bool(summary.get("pair_full_observed")),
        "default_pair_full_variant_count": summary.get("default_pair_full_variant_count"),
        "suppression_pair_full_variant_count": summary.get("suppression_pair_full_variant_count"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": summary.get("checkpoint_exists"),
        "continuation_hit_count": as_dict(replay.get("summary")).get("default_continuation_hit_count"),
        "out_dir": str(seed_dir),
    }


def _summary(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(seed_rows)
    pair_full_seed_count = sum(1 for row in seed_rows if row.get("pair_full_observed"))
    failed_seed_count = sum(1 for row in seed_rows if row.get("status") != "pass")
    return {
        "seed_count": seed_count,
        "pair_full_seed_count": pair_full_seed_count,
        "failed_seed_count": failed_seed_count,
        "pair_full_seed_rate": round(pair_full_seed_count / seed_count, 4) if seed_count else 0.0,
        "stable_pair_full": bool(seed_rows) and pair_full_seed_count == seed_count,
        "partial_pair_full": 0 < pair_full_seed_count < seed_count,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_colon_immediate_stability"
    if summary.get("stable_pair_full"):
        return "required_term_pair_colon_immediate_stably_pair_full"
    if summary.get("partial_pair_full"):
        return "required_term_pair_colon_immediate_partial_stability"
    return "required_term_pair_colon_immediate_not_stable"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "At least one seed refresh failed, so stability cannot be judged."
        next_action = "repair failed seed execution before changing training setup"
        claim = "not_claimed"
    elif summary.get("stable_pair_full"):
        reason = "Every tested colon-immediate seed produced fixed/loss pair-full coverage."
        next_action = "promote colon-immediate as the current pair objective baseline and test held-out aliases"
        claim = "targeted_pair_refresh_stable_signal"
    elif summary.get("partial_pair_full"):
        reason = "Some but not all colon-immediate seeds produced pair-full coverage."
        next_action = "inspect missed seeds before increasing corpus or model size"
        claim = "targeted_pair_refresh_partial_signal"
    else:
        reason = "No tested colon-immediate seed reproduced the v535 pair-full signal."
        next_action = "return to corpus design before further seed sweeps"
        claim = "not_claimed"
    return {
        "model_quality_claim": claim,
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_COLON_IMMEDIATE_STABILITY_CSV_FILENAME",
    "PAIR_COLON_IMMEDIATE_STABILITY_HTML_FILENAME",
    "PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME",
    "PAIR_COLON_IMMEDIATE_STABILITY_MARKDOWN_FILENAME",
    "PAIR_COLON_IMMEDIATE_STABILITY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_colon_immediate_stability",
    "resolve_exit_code",
]
