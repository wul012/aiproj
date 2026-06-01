from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_coexistence_refresh import (
    GenerateFunc,
    PAIR_COEXISTENCE_CORPUS_MODES,
    TrainFunc,
    build_model_capability_required_term_pair_coexistence_refresh,
    resolve_exit_code as _refresh_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_internal_alignment_route_decision import (
    PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME = (
    "model_capability_required_term_pair_aligned_candidate_seed_stability.json"
)
PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_CSV_FILENAME = (
    "model_capability_required_term_pair_aligned_candidate_seed_stability.csv"
)
PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_TEXT_FILENAME = (
    "model_capability_required_term_pair_aligned_candidate_seed_stability.txt"
)
PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_aligned_candidate_seed_stability.md"
)
PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_HTML_FILENAME = (
    "model_capability_required_term_pair_aligned_candidate_seed_stability.html"
)


def locate_aligned_candidate_seed_stability_route_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_JSON_FILENAME
    return source


def read_aligned_candidate_seed_stability_route_decision(path: str | Path) -> dict[str, Any]:
    payload = json.loads(locate_aligned_candidate_seed_stability_route_decision(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("aligned candidate route decision must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_aligned_candidate_seed_stability(
    *,
    out_dir: str | Path,
    route_decision: dict[str, Any] | None = None,
    route_decision_path: str | Path | None = None,
    seeds: tuple[int, ...] = (1535, 2535, 3535),
    corpus_mode: str | None = None,
    repeat: int = 220,
    bridge_repeat: int = 16,
    max_iters: int = 2200,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 16,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.005,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_route_decision = _route_decision(route_decision, route_decision_path)
    aligned_route = as_dict(source_route_decision.get("aligned_route"))
    selected_mode = corpus_mode or str(aligned_route.get("corpus_mode") or "")
    issues = _input_issues(source_route_decision, selected_mode, seeds)
    seed_reports: list[dict[str, Any]] = []
    seed_rows: list[dict[str, Any]] = []
    for seed in seeds:
        seed_dir = root / "seed-runs" / f"seed-{seed}"
        report = build_model_capability_required_term_pair_coexistence_refresh(
            out_dir=seed_dir,
            seed=seed,
            corpus_mode=selected_mode,
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
        seed_rows.append(_seed_row(seed, report, seed_dir))
        if report.get("status") != "pass":
            issues.append(f"seed {seed} refresh failed")
    summary = _summary(seed_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair aligned-candidate seed stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "out_dir": str(root),
        "source_route_decision_path": str(route_decision_path or ""),
        "source_route_decision": _route_decision_summary(source_route_decision),
        "aligned_route": aligned_route,
        "settings": {
            "seeds": list(seeds),
            "corpus_mode": selected_mode,
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
            "experiment_boundary": "repeat the aligned generation/internal pair-full candidate across fresh seeds before promotion",
        },
        "seed_rows": seed_rows,
        "seed_reports": seed_reports,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    for seed_report in list_of_dicts(report.get("seed_reports")):
        if _refresh_exit_code(seed_report, require_pass=require_pass):
            return 1
    return 0


def _route_decision(route_decision: dict[str, Any] | None, route_decision_path: str | Path | None) -> dict[str, Any]:
    if route_decision is not None:
        return route_decision
    if route_decision_path is None:
        return {}
    return read_aligned_candidate_seed_stability_route_decision(route_decision_path)


def _input_issues(route_decision: dict[str, Any], corpus_mode: str, seeds: tuple[int, ...]) -> list[str]:
    issues: list[str] = []
    aligned_route = as_dict(route_decision.get("aligned_route"))
    if route_decision and route_decision.get("status") != "pass":
        issues.append("source route decision is not pass")
    if route_decision and not aligned_route:
        issues.append("source route decision has no aligned route")
    if not corpus_mode:
        issues.append("aligned candidate corpus mode is missing")
    elif corpus_mode not in PAIR_COEXISTENCE_CORPUS_MODES:
        issues.append(f"aligned candidate corpus mode is not registered: {corpus_mode}")
    if not seeds:
        issues.append("at least one seed is required")
    return issues


def _seed_row(seed: int, report: dict[str, Any], seed_dir: Path) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    replay_summary = as_dict(as_dict(report.get("replay_report")).get("summary"))
    return {
        "seed": seed,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "pair_full_observed": bool(summary.get("pair_full_observed")),
        "default_pair_full_variant_count": summary.get("default_pair_full_variant_count"),
        "suppression_pair_full_variant_count": summary.get("suppression_pair_full_variant_count"),
        "best_pair_full_variant_count": summary.get("best_pair_full_variant_count"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": summary.get("checkpoint_exists"),
        "default_continuation_hit_count": replay_summary.get("default_continuation_hit_count"),
        "suppression_continuation_hit_count": replay_summary.get("suppression_continuation_hit_count"),
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
        return "fix_required_term_pair_aligned_candidate_seed_stability"
    if summary.get("stable_pair_full"):
        return "required_term_pair_aligned_candidate_stably_pair_full"
    if summary.get("partial_pair_full"):
        return "required_term_pair_aligned_candidate_partial_stability"
    return "required_term_pair_aligned_candidate_not_stable"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "At least one seed execution failed or the aligned candidate source is invalid."
        next_action = "repair seed execution or route-decision input before promotion"
        claim = "not_claimed"
    elif summary.get("stable_pair_full"):
        reason = "Every tested seed reproduced generation pair-full for the aligned candidate corpus."
        next_action = "run forced-choice/internal scoring across the same seed set before promotion"
        claim = "targeted_pair_refresh_stable_signal"
    elif summary.get("partial_pair_full"):
        reason = "Only some tested seeds reproduced generation pair-full for the aligned candidate corpus."
        next_action = "score pair-full seeds internally and inspect missed seeds before promotion"
        claim = "targeted_pair_refresh_partial_signal"
    else:
        reason = "No tested seed reproduced the aligned candidate pair-full signal."
        next_action = "return to corpus design rather than promoting the candidate"
        claim = "not_claimed"
    return {
        "model_quality_claim": claim,
        "reason": reason,
        "next_action": next_action,
    }


def _route_decision_summary(route_decision: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(route_decision.get("summary"))
    return {
        "status": route_decision.get("status"),
        "decision": route_decision.get("decision"),
        "aligned_route_label": summary.get("aligned_route_label") or as_dict(route_decision.get("aligned_route")).get("source_label"),
        "direct_promotion_ready": summary.get("direct_promotion_ready"),
    }


__all__ = [
    "PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_CSV_FILENAME",
    "PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_HTML_FILENAME",
    "PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME",
    "PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_MARKDOWN_FILENAME",
    "PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_aligned_candidate_seed_stability",
    "locate_aligned_candidate_seed_stability_route_decision",
    "read_aligned_candidate_seed_stability_route_decision",
    "resolve_exit_code",
]
