from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_route_comparison import (
    PAIR_READINESS_ROUTE_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_JSON_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_plan.json"
PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_CSV_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_plan.csv"
PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_plan.txt"
PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_plan.md"
PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_HTML_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_plan.html"


def locate_objective_structure_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_ROUTE_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-structure plan input must be a JSON object")
    return dict(payload)


def build_objective_structure_plan(
    route_comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(route_comparison.get("summary"))
    route_rows = list_of_dicts(route_comparison.get("route_rows"))
    checks = _checks(route_comparison, summary, route_rows)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    plan = _plan(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-structure plan",
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


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _checks(route_comparison: dict[str, Any], summary: dict[str, Any], route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    capacity_row = _route_row(route_rows, "capacity-probe")
    missed_terms = [str(term) for term in summary.get("capacity_probe_default_missed_terms") or []]
    return [
        _check("route_comparison_passed", route_comparison.get("status") == "pass", route_comparison.get("status"), "source five-route comparison must pass"),
        _check(
            "route_comparison_decision",
            route_comparison.get("decision") == "pair_readiness_capacity_probe_no_improvement_fixed_only",
            route_comparison.get("decision"),
            "objective-structure planning follows only a closed capacity-probe no-improvement result",
        ),
        _check("no_pair_full_route", not summary.get("any_pair_full_observed"), summary.get("any_pair_full_observed"), "no compared route should already be pair-full"),
        _check("five_routes_present", int(summary.get("route_count") or 0) >= 5, summary.get("route_count"), "comparison should include baseline, repairs, and capacity probe"),
        _check("capacity_probe_no_improvement", summary.get("capacity_probe_no_improvement") is True, summary.get("capacity_probe_no_improvement"), "capacity probe must be measured as no improvement"),
        _check("capacity_probe_no_delta", int(summary.get("capacity_probe_vs_fixed_recovery_default_hit_delta") or 0) == 0, summary.get("capacity_probe_vs_fixed_recovery_default_hit_delta"), "capacity probe should not improve default hit count"),
        _check("capacity_probe_still_misses_loss", "loss" in missed_terms, missed_terms, "loss must remain missed before changing objective structure"),
        _check("capacity_probe_row_present", bool(capacity_row), bool(capacity_row), "capacity-probe route row must be present for auditability"),
    ]


def _route_row(route_rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    for row in route_rows:
        if row.get("label") == label:
            return row
    return {}


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "proposed_next_artifact": "pair_readiness_objective_structure_contract",
        "objective_strategy": [
            "separate fixed and loss as explicit task-id objectives before the answer token",
            "add paired block rows that ask both branches in one sample without reusing heldout prompts",
            "keep direct fixed= and loss= probes held out for promotion checks",
            "avoid another capacity increase until the objective contract is materialized and replayed",
        ],
        "contract_requirements": [
            "training rows must not contain the exact heldout direct or pair probes",
            "fixed and loss row families must be balanced by count and template role",
            "paired rows must include both terms in deterministic order and reversed order",
            "contract output must expose row family counts and leakage checks",
        ],
        "success_guard": "train only after contract checks pass, then require direct fixed and loss hits before pair-probe promotion",
        "non_goal": "do not patch another single-sided row family or scale the model before changing objective structure",
    }


def _summary(checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "plan_ready": bool(plan.get("ready")),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "objective_strategy_count": len(plan.get("objective_strategy", [])),
        "contract_requirement_count": len(plan.get("contract_requirements", [])),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_objective_structure_plan_ready"
    return "fix_pair_readiness_objective_structure_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The five-route comparison does not yet justify changing objective structure.",
            "next_action": "repair route-comparison evidence before defining a new objective contract",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "Five-route evidence shows that row patching and a light capacity bump both remain single-branch, so the next change should target objective structure.",
        "next_action": f"build {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_TEXT_FILENAME",
    "build_objective_structure_plan",
    "locate_objective_structure_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
