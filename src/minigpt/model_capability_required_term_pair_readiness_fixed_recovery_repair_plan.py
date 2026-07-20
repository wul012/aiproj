from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_route_comparison import (
    PAIR_READINESS_ROUTE_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_strs, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_JSON_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_repair_plan.json"
PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_CSV_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_repair_plan.csv"
PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_repair_plan.txt"
PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_repair_plan.md"
PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_HTML_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_repair_plan.html"


def locate_fixed_recovery_repair_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_ROUTE_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("fixed-recovery repair plan input must be a JSON object")
    return dict(payload)


def build_fixed_recovery_repair_plan(
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
        "title": "MiniGPT pair-readiness fixed-recovery repair plan",
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
        "summary": _summary(checks, plan, summary),
        "interpretation": _interpretation(status, plan),
    }


def _checks(route_comparison: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    structured_hits = list_of_strs(summary.get("structured_default_hit_terms"))
    structured_misses = list_of_strs(summary.get("structured_default_missed_terms"))
    best_routes = list_of_strs(summary.get("best_routes"))
    return [
        _check("route_comparison_passed", route_comparison.get("status") == "pass", route_comparison.get("status"), "source route comparison must pass"),
        _check(
            "route_comparison_decision",
            route_comparison.get("decision") == "pair_readiness_structured_template_changes_failure_shape_without_pair_full",
            route_comparison.get("decision"),
            "fixed recovery follows only a structured-template failure-shape change",
        ),
        _check("failure_shape_changed", summary.get("failure_shape_changed") is True, summary.get("failure_shape_changed"), "structured route must change failure shape"),
        _check("structured_hits_loss", "loss" in structured_hits, structured_hits, "structured route should retain loss before fixed recovery"),
        _check("structured_misses_fixed", "fixed" in structured_misses, structured_misses, "structured route should miss fixed before fixed recovery"),
        _check("no_pair_full_route", not summary.get("any_pair_full_observed"), summary.get("any_pair_full_observed"), "no route should already be pair-full"),
        _check("structured_not_above_baseline", int(summary.get("structured_vs_baseline_default_hit_delta") or 0) == 0, summary.get("structured_vs_baseline_default_hit_delta"), "structured route should be a shape change, not an improvement"),
        _check("structured_and_baseline_best", {"baseline-split", "structured-template"}.issubset(set(best_routes)), best_routes, "baseline and structured routes should be tied best evidence"),
    ]


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "proposed_next_artifact": "pair_readiness_fixed_recovery_contract_patch",
        "repair_focus": "restore fixed direct retention while preserving the structured route's recovered loss hit",
        "contract_patch": [
            "add fixed answer confirmation rows after structured prompt-answer rows",
            "add fixed anti-loss contamination rows",
            "preserve loss structured rows from v714 because loss recovered in v716",
            "keep heldout pair probe excluded from training rows",
            "compare fixed-recovery run against v707 baseline and v716 structured-template before any promotion",
        ],
        "training_policy": "materialize the patched contract and rerun the same tiny training configuration",
        "success_guard": "fixed= and loss= must both hit in heldout direct replay before pair-probe checks",
    }


def _summary(checks: list[dict[str, Any]], plan: dict[str, Any], source_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "plan_ready": bool(plan.get("ready")),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "repair_focus": plan.get("repair_focus"),
        "source_structured_hit_terms": source_summary.get("structured_default_hit_terms"),
        "source_structured_missed_terms": source_summary.get("structured_default_missed_terms"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_fixed_recovery_repair_plan_ready"
    return "fix_pair_readiness_fixed_recovery_repair_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route comparison does not support a fixed-recovery plan.",
            "next_action": "repair route comparison evidence before patching the contract",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "The structured-template route recovered loss but missed fixed, so the next patch should restore fixed without discarding the recovered loss behavior.",
        "next_action": f"build {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_CSV_FILENAME",
    "PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_HTML_FILENAME",
    "PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_JSON_FILENAME",
    "PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_TEXT_FILENAME",
    "build_fixed_recovery_repair_plan",
    "locate_fixed_recovery_repair_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
