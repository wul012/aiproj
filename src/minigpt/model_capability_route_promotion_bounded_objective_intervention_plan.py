from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_rebalanced_intervention_decision import (
    BOUNDED_REBALANCED_INTERVENTION_DECISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_intervention_plan.json"
BOUNDED_OBJECTIVE_INTERVENTION_PLAN_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_intervention_plan.csv"
BOUNDED_OBJECTIVE_INTERVENTION_PLAN_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_intervention_plan.txt"
BOUNDED_OBJECTIVE_INTERVENTION_PLAN_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_intervention_plan.md"
BOUNDED_OBJECTIVE_INTERVENTION_PLAN_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_intervention_plan.html"


def locate_intervention_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_REBALANCED_INTERVENTION_DECISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective intervention plan input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_intervention_plan(
    intervention_decision: dict[str, Any],
    *,
    intervention_decision_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective intervention plan",
    generated_at: str | None = None,
) -> dict[str, Any]:
    decision_summary = as_dict(intervention_decision.get("summary"))
    route = as_dict(intervention_decision.get("route"))
    plan = _plan(route)
    checks = _checks(intervention_decision, decision_summary, route)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_intervention_decision": str(intervention_decision_path or ""),
        "source_decision_summary": decision_summary,
        "objective_contract": plan["objective_contract"] if status == "pass" else {},
        "work_items": plan["work_items"] if status == "pass" else [],
        "acceptance_gates": plan["acceptance_gates"] if status == "pass" else [],
        "non_goals": plan["non_goals"] if status == "pass" else [],
        "check_rows": checks,
        "plan": plan if status == "pass" else {},
        "summary": _summary(status, issues, plan),
        "interpretation": _interpretation(status, plan),
    }


def resolve_exit_code(report: dict[str, Any], *, require_plan_ready: bool) -> int:
    if require_plan_ready and report.get("status") != "pass":
        return 1
    return 0


def _plan(route: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_id": "bounded_objective_contract_intervention_v835",
        "source_closed_route": route.get("closed_route"),
        "selected_intervention_track": route.get("selected_intervention_track"),
        "fallback_intervention_track": route.get("fallback_intervention_track"),
        "objective_contract": {
            "contract_id": "bounded_fixed_loss_direct_completion_contract",
            "target_terms": ["fixed", "loss"],
            "canonical_prompt": "Answer with exactly two tokens: fixed loss\nanswer:",
            "canonical_completion": "fixed loss",
            "allowed_surfaces": [
                "canonical_direct_completion_surface",
                "v803_prompt_surface_replay_as_holdout_check",
            ],
            "blocked_surfaces": [
                "forced_prefix_decoder_anchor_as_quality_claim",
                "carry_forward_only_seed_expansion",
                "more_training_epochs_without_contract_change",
            ],
            "unchanged_suite_check_required": True,
        },
        "work_items": _work_items(),
        "acceptance_gates": _acceptance_gates(),
        "non_goals": [
            "do_not_claim_v803_route_improvement_from_canonical_contract_only",
            "do_not_use_forced_prefix_or_blocked_tokens_as_promotion_evidence",
            "do_not_continue_rebalanced_decoder_profile_rescue",
        ],
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_contract",
        "next_step": "build_bounded_objective_contract",
    }


def _work_items() -> list[dict[str, Any]]:
    return [
        _item("contract_fixture", "define canonical direct-completion prompt and exact target terms", "model_capability_route_promotion_bounded_objective_contract"),
        _item("direct_seed_corpus", "build direct-only seed rows from the contract without carry-forward pollution", "model_capability_route_promotion_bounded_objective_seed"),
        _item("controlled_training", "train a tiny candidate from the objective seed with the same checkpoint evidence discipline", "model_capability_route_promotion_bounded_objective_training_run"),
        _item("dual_replay", "replay both the canonical contract and the unchanged v803 bounded suite", "model_capability_route_promotion_bounded_objective_replay_comparison"),
        _item("fallback_decision", "route to architecture capacity probe if the canonical contract still has zero required-term hits", "model_capability_route_promotion_bounded_architecture_capacity_probe_plan"),
    ]


def _item(item_id: str, action: str, output: str) -> dict[str, Any]:
    return {"item_id": item_id, "action": action, "expected_output": output}


def _acceptance_gates() -> list[dict[str, Any]]:
    return [
        _gate("contract_is_bounded", "contract contains exactly the fixed/loss target terms and no production claim"),
        _gate("canonical_replay_required", "candidate must pass canonical replay before any v803 comparison matters"),
        _gate("unchanged_v803_replay_required", "unchanged v803 replay remains the route-promotion check"),
        _gate("architecture_fallback_defined", "zero-hit canonical replay must trigger capacity probe instead of more seed patching"),
    ]


def _gate(gate_id: str, detail: str) -> dict[str, Any]:
    return {"gate_id": gate_id, "detail": detail}


def _checks(decision: dict[str, Any], summary: dict[str, Any], route: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("intervention_decision_passed", decision.get("status") == "pass", decision.get("status"), "source intervention decision must pass"),
        _check("objective_track_selected", summary.get("selected_intervention_track") == "objective_contract_intervention_first", summary.get("selected_intervention_track"), "source decision must select objective contract intervention"),
        _check("next_artifact_matches", summary.get("recommended_next_artifact") == "model_capability_route_promotion_bounded_objective_intervention_plan", summary.get("recommended_next_artifact"), "source decision must request this plan"),
        _check("promotion_blocked", summary.get("promotion_allowed") is False, summary.get("promotion_allowed"), "plan should only run while promotion is blocked"),
        _check("training_blocked_until_plan", summary.get("new_training_allowed") is False, summary.get("new_training_allowed"), "new training must remain blocked until this plan exists"),
        _check("closed_route_present", bool(route.get("closed_route")), route.get("closed_route"), "source decision must identify the closed route"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, issues: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "objective_intervention_plan_ready": status == "pass",
        "plan_id": plan.get("plan_id"),
        "selected_intervention_track": plan.get("selected_intervention_track"),
        "fallback_intervention_track": plan.get("fallback_intervention_track"),
        "contract_id": as_dict(plan.get("objective_contract")).get("contract_id"),
        "work_item_count": len(plan.get("work_items", [])) if status == "pass" else 0,
        "acceptance_gate_count": len(plan.get("acceptance_gates", [])) if status == "pass" else 0,
        "non_goal_count": len(plan.get("non_goals", [])) if status == "pass" else 0,
        "unchanged_suite_check_required": as_dict(plan.get("objective_contract")).get("unchanged_suite_check_required") is True,
        "proposed_next_artifact": plan.get("proposed_next_artifact") if status == "pass" else "",
        "next_step": plan.get("next_step") if status == "pass" else "repair_bounded_objective_intervention_plan_inputs",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_intervention_plan_ready"
    return "fix_model_capability_route_promotion_bounded_objective_intervention_plan"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Objective intervention plan inputs are incomplete.", "next_action": "repair source intervention decision"}
    return {
        "model_quality_claim": "plan_only",
        "reason": "The rebalanced decoder-rescue branch is closed; this plan defines the bounded objective contract before any new training.",
        "next_action": plan.get("proposed_next_artifact"),
    }


__all__ = [
    "BOUNDED_OBJECTIVE_INTERVENTION_PLAN_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_INTERVENTION_PLAN_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_INTERVENTION_PLAN_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_INTERVENTION_PLAN_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_intervention_plan",
    "locate_intervention_decision",
    "read_json_report",
    "resolve_exit_code",
]
