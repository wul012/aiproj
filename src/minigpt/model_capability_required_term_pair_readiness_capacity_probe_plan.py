from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_route_comparison import (
    PAIR_READINESS_ROUTE_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_CAPACITY_PROBE_PLAN_JSON_FILENAME = "model_capability_required_term_pair_readiness_capacity_probe_plan.json"
PAIR_READINESS_CAPACITY_PROBE_PLAN_CSV_FILENAME = "model_capability_required_term_pair_readiness_capacity_probe_plan.csv"
PAIR_READINESS_CAPACITY_PROBE_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_readiness_capacity_probe_plan.txt"
PAIR_READINESS_CAPACITY_PROBE_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_capacity_probe_plan.md"
PAIR_READINESS_CAPACITY_PROBE_PLAN_HTML_FILENAME = "model_capability_required_term_pair_readiness_capacity_probe_plan.html"


CAPACITY_PROBE_TRAINING_CONFIG = {
    "seed": 3535,
    "max_iters": 1800,
    "eval_iters": 2,
    "batch_size": 16,
    "block_size": 16,
    "n_layer": 2,
    "n_head": 2,
    "n_embd": 96,
    "learning_rate": 0.01,
    "max_new_tokens": 12,
    "temperature": 0.2,
    "top_k": 1,
    "device": "cpu",
}


def locate_capacity_probe_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_ROUTE_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("capacity-probe plan input must be a JSON object")
    return dict(payload)


def build_capacity_probe_plan(
    route_comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(route_comparison.get("summary"))
    checks = _checks(route_comparison, summary)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    plan = _plan(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness capacity-probe plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_route_comparison_path": str(source_path or ""),
        "source_route_comparison": {
            "status": route_comparison.get("status"),
            "decision": route_comparison.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def _checks(route_comparison: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("route_comparison_passed", route_comparison.get("status") == "pass", route_comparison.get("status"), "source route comparison must pass"),
        _check(
            "route_comparison_decision",
            route_comparison.get("decision") == "pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full",
            route_comparison.get("decision"),
            "capacity probe follows only the closed fixed/loss row-patching branch",
        ),
        _check("no_pair_full_route", not summary.get("any_pair_full_observed"), summary.get("any_pair_full_observed"), "no route should already be pair-full"),
        _check("fixed_recovery_returned_to_baseline", summary.get("fixed_recovery_returns_to_baseline") is True, summary.get("fixed_recovery_returns_to_baseline"), "fixed-recovery must be confirmed as a baseline return"),
        _check("route_count_four", int(summary.get("route_count") or 0) >= 4, summary.get("route_count"), "comparison should include baseline, loss-retention, structured, and fixed-recovery routes"),
    ]


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "proposed_next_artifact": "pair_readiness_capacity_probe_training_run",
        "corpus_source": "fixed_recovery_corpus_materialization",
        "training_config": CAPACITY_PROBE_TRAINING_CONFIG,
        "probe_focus": "test whether a slightly larger tiny model can hold fixed and loss direct branches together",
        "success_guard": "fixed= and loss= must both hit in heldout direct replay before pair-probe checks",
        "non_goal": "do not add more single-sided fixed/loss rows in this probe",
    }


def _summary(checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    config = as_dict(plan.get("training_config"))
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "plan_ready": bool(plan.get("ready")),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "corpus_source": plan.get("corpus_source"),
        "n_layer": config.get("n_layer"),
        "n_head": config.get("n_head"),
        "n_embd": config.get("n_embd"),
        "max_iters": config.get("max_iters"),
        "learning_rate": config.get("learning_rate"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_capacity_probe_plan_ready"
    return "fix_pair_readiness_capacity_probe_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route comparison does not support a capacity probe yet.",
            "next_action": "repair route-comparison evidence before changing model scale",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "Single-sided fixed/loss row patching returned to baseline, so the next controlled probe should test a slightly larger tiny model on the same corpus.",
        "next_action": f"run {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "CAPACITY_PROBE_TRAINING_CONFIG",
    "PAIR_READINESS_CAPACITY_PROBE_PLAN_CSV_FILENAME",
    "PAIR_READINESS_CAPACITY_PROBE_PLAN_HTML_FILENAME",
    "PAIR_READINESS_CAPACITY_PROBE_PLAN_JSON_FILENAME",
    "PAIR_READINESS_CAPACITY_PROBE_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_CAPACITY_PROBE_PLAN_TEXT_FILENAME",
    "build_capacity_probe_plan",
    "locate_capacity_probe_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
