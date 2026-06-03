from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_downstream_guard import MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_JSON_FILENAME = "model_capability_route_promotion_consumer_plan.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_CSV_FILENAME = "model_capability_route_promotion_consumer_plan.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_TEXT_FILENAME = "model_capability_route_promotion_consumer_plan.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_MARKDOWN_FILENAME = "model_capability_route_promotion_consumer_plan.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_HTML_FILENAME = "model_capability_route_promotion_consumer_plan.html"


def locate_route_promotion_downstream_guard(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion consumer plan input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_consumer_plan(
    downstream_guard: dict[str, Any],
    *,
    downstream_guard_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion consumer plan",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(downstream_guard.get("summary"))
    access = as_dict(downstream_guard.get("access_decision"))
    request = as_dict(downstream_guard.get("request"))
    checks = _checks(downstream_guard, summary, access, request, required_boundary)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    plan = _plan(status, summary, access, request)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_downstream_guard": str(downstream_guard_path or ""),
        "source_guard_summary": summary,
        "source_guard_request": request,
        "check_rows": checks,
        "consumer_plan": plan,
        "summary": _summary(status, checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def resolve_exit_code(report: dict[str, Any], *, require_ready_plan: bool) -> int:
    return 1 if require_ready_plan and report.get("status") != "pass" else 0


def _checks(
    downstream_guard: dict[str, Any],
    summary: dict[str, Any],
    access: dict[str, Any],
    request: dict[str, Any],
    required_boundary: str,
) -> list[dict[str, Any]]:
    claim = str(summary.get("model_quality_claim") or access.get("model_quality_claim") or "")
    return [
        _check("guard_passed", downstream_guard.get("status") == "pass", downstream_guard.get("status"), "downstream guard must pass"),
        _check(
            "guard_decision_allowed",
            downstream_guard.get("decision") == "model_capability_route_promotion_downstream_guard_allowed",
            downstream_guard.get("decision"),
            "downstream guard decision must allow access",
        ),
        _check("access_allowed", summary.get("access_allowed") is True and access.get("allowed") is True, {"summary": summary.get("access_allowed"), "access": access.get("allowed")}, "access must be allowed"),
        _check("objective_route_selected", summary.get("route_id") == "objective_level_contrast", summary.get("route_id"), "consumer plan currently supports objective_level_contrast route"),
        _check("bounded_scope", summary.get("allowed_scope") == "bounded_model_capability_governance_only", summary.get("allowed_scope"), "consumer plan must stay in bounded governance scope"),
        _check("boundary_scoped", summary.get("boundary") == required_boundary, summary.get("boundary"), "consumer plan boundary must match the required boundary"),
        _check("next_step_matches", summary.get("next_step") == "build_bounded_route_promotion_consumer_plan", summary.get("next_step"), "guard must point at consumer plan construction"),
        _check("claim_bounded", claim.startswith("seed_stable_pair_probe_route"), claim, "consumer plan claim must remain pair-probe scoped"),
        _check("consumer_named", bool(request.get("consumer_name") or summary.get("consumer_name")), request.get("consumer_name") or summary.get("consumer_name"), "consumer name must be explicit"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(status: str, summary: dict[str, Any], access: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    ready = status == "pass"
    route_id = summary.get("route_id") or access.get("route_id")
    consumer_name = summary.get("consumer_name") or request.get("consumer_name")
    return {
        "ready": ready,
        "route_id": route_id,
        "consumer_name": consumer_name,
        "allowed_scope": summary.get("allowed_scope") if ready else "none",
        "boundary": summary.get("boundary") if ready else "",
        "model_quality_claim": summary.get("model_quality_claim") if ready else "not_claimed",
        "proposed_next_artifact": "model_capability_route_promotion_bounded_benchmark_suite",
        "execution_phase": "bounded_route_benchmark_planning",
        "required_inputs": [
            "route_promotion_governance_snapshot",
            "route_promotion_downstream_guard",
            "objective_level_contrast_route_card",
        ],
        "plan_steps": [
            _step("load-verified-route-card", "Load the contract-verified route card from the governance snapshot."),
            _step("preserve-bounded-scope", "Carry only bounded_model_capability_governance_only into downstream artifacts."),
            _step("map-objective-route", "Map objective_level_contrast to the existing objective-level contrast benchmark family."),
            _step("prepare-suite-contract", "Prepare benchmark-suite fields without changing model checkpoints."),
            _step("emit-next-artifact", "Emit a bounded benchmark suite that can be executed or reviewed next."),
        ],
        "non_goals": [
            "do not claim production model release readiness",
            "do not widen beyond tiny required-term pair-probe boundary",
            "do not train or mutate checkpoints in the consumer plan",
        ],
    }


def _step(step_id: str, purpose: str) -> dict[str, str]:
    return {"step_id": step_id, "purpose": purpose}


def _summary(status: str, checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    steps = list_of_dicts(plan.get("plan_steps"))
    return {
        "consumer_plan_ready": status == "pass" and plan.get("ready") is True,
        "route_id": plan.get("route_id"),
        "consumer_name": plan.get("consumer_name"),
        "allowed_scope": plan.get("allowed_scope"),
        "boundary": plan.get("boundary"),
        "model_quality_claim": plan.get("model_quality_claim"),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "plan_step_count": len(steps),
        "required_input_count": len(plan.get("required_inputs", [])),
        "non_goal_count": len(plan.get("non_goals", [])),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_consumer_plan_ready"
    return "fix_model_capability_route_promotion_consumer_plan"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream guard is not sufficient for a bounded route-promotion consumer plan.",
            "next_action": "repair downstream guard evidence",
        }
    return {
        "model_quality_claim": plan.get("model_quality_claim"),
        "reason": "The verified route can feed a bounded benchmark-suite plan without widening the model-quality claim.",
        "next_action": f"build {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_TEXT_FILENAME",
    "build_model_capability_route_promotion_consumer_plan",
    "locate_route_promotion_downstream_guard",
    "read_json_report",
    "resolve_exit_code",
]
