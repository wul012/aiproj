from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_intervention_plan import (
    BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_contract.json"
BOUNDED_OBJECTIVE_CONTRACT_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_contract.csv"
BOUNDED_OBJECTIVE_CONTRACT_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_contract.txt"
BOUNDED_OBJECTIVE_CONTRACT_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_contract.md"
BOUNDED_OBJECTIVE_CONTRACT_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_contract.html"


def locate_objective_intervention_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective contract input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_contract(
    objective_intervention_plan: dict[str, Any],
    *,
    objective_intervention_plan_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective contract",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(objective_intervention_plan.get("summary"))
    plan = as_dict(objective_intervention_plan.get("plan"))
    source_contract = as_dict(objective_intervention_plan.get("objective_contract")) or as_dict(plan.get("objective_contract"))
    normalized_contract = _normalized_contract(source_contract)
    contract_cases = _contract_cases(normalized_contract)
    seed_blueprint = _seed_blueprint(contract_cases)
    holdout_rule = _holdout_rule(normalized_contract)
    checks = _checks(objective_intervention_plan, summary, plan, normalized_contract, contract_cases, seed_blueprint)
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
        "source_objective_intervention_plan": str(objective_intervention_plan_path or ""),
        "source_plan_summary": summary,
        "objective_contract": normalized_contract if status == "pass" else {},
        "contract_cases": contract_cases if status == "pass" else [],
        "seed_blueprint": seed_blueprint if status == "pass" else {},
        "holdout_rule": holdout_rule if status == "pass" else {},
        "check_rows": checks,
        "summary": _summary(status, issues, normalized_contract, contract_cases, seed_blueprint, holdout_rule),
        "interpretation": _interpretation(status, normalized_contract),
    }


def resolve_exit_code(report: dict[str, Any], *, require_contract_ready: bool) -> int:
    if require_contract_ready and report.get("status") != "pass":
        return 1
    return 0


def _normalized_contract(contract: dict[str, Any]) -> dict[str, Any]:
    target_terms = [str(item).strip().lower() for item in contract.get("target_terms", []) if str(item).strip()]
    allowed_surfaces = [str(item) for item in contract.get("allowed_surfaces", [])]
    blocked_surfaces = [str(item) for item in contract.get("blocked_surfaces", [])]
    return {
        "contract_id": contract.get("contract_id"),
        "target_terms": target_terms,
        "canonical_prompt": contract.get("canonical_prompt"),
        "canonical_completion": contract.get("canonical_completion"),
        "expected_token_count": 2,
        "required_exact_completion": "fixed loss",
        "allowed_surfaces": allowed_surfaces,
        "blocked_surfaces": blocked_surfaces,
        "unchanged_suite_check_required": contract.get("unchanged_suite_check_required") is True,
        "promotion_claim_allowed": False,
    }


def _contract_cases(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _case(
            "canonical_direct_completion",
            contract.get("canonical_prompt"),
            contract.get("canonical_completion"),
            "canonical_direct_completion_surface",
            True,
        ),
        _case(
            "minimal_direct_completion",
            "Answer with exactly two words: fixed loss\nanswer:",
            "fixed loss",
            "canonical_direct_completion_surface",
            False,
        ),
        _case(
            "completion_label_surface",
            "Complete with exactly two tokens: fixed loss\ncompletion:",
            "fixed loss",
            "canonical_direct_completion_surface",
            False,
        ),
    ]


def _case(case_id: str, prompt: Any, completion: Any, surface: str, canonical: bool) -> dict[str, Any]:
    completion_text = str(completion or "")
    return {
        "case_id": case_id,
        "prompt": str(prompt or ""),
        "expected_completion": completion_text,
        "required_terms": ["fixed", "loss"],
        "surface": surface,
        "canonical": canonical,
        "exact_completion_required": completion_text == "fixed loss",
    }


def _seed_blueprint(contract_cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "blueprint_id": "bounded_objective_direct_seed_v837_blueprint",
        "source_contract_case_count": len(contract_cases),
        "examples_per_case": 6,
        "planned_example_count": len(contract_cases) * 6,
        "allowed_example_modes": [
            "direct_prompt_completion",
            "minimal_surface_repeat",
            "label_surface_repeat",
        ],
        "blocked_example_modes": [
            "carry_forward_fragment",
            "forced_prefix_anchor",
            "unbounded_generation_target",
        ],
        "next_artifact": "model_capability_route_promotion_bounded_objective_seed",
    }


def _holdout_rule(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "holdout_id": "unchanged_v803_bounded_suite_holdout",
        "unchanged_suite_check_required": contract.get("unchanged_suite_check_required") is True,
        "purpose": "canonical contract success is not enough for route promotion; unchanged v803 bounded replay must remain visible",
        "promotion_gate": "dual_replay_required_before_quality_claim",
    }


def _checks(
    source: dict[str, Any],
    summary: dict[str, Any],
    plan: dict[str, Any],
    contract: dict[str, Any],
    contract_cases: list[dict[str, Any]],
    seed_blueprint: dict[str, Any],
) -> list[dict[str, Any]]:
    work_items = {str(row.get("item_id")) for row in list_of_dicts(source.get("work_items")) or list_of_dicts(plan.get("work_items"))}
    blocked_surfaces = set(contract.get("blocked_surfaces", []))
    allowed_surfaces = set(contract.get("allowed_surfaces", []))
    return [
        _check("plan_passed", source.get("status") == "pass", source.get("status"), "source objective intervention plan must pass"),
        _check("plan_ready", summary.get("objective_intervention_plan_ready") is True, summary.get("objective_intervention_plan_ready"), "source plan must be ready"),
        _check("next_artifact_matches", summary.get("proposed_next_artifact") == "model_capability_route_promotion_bounded_objective_contract", summary.get("proposed_next_artifact"), "source plan must request this contract artifact"),
        _check("contract_id_matches", contract.get("contract_id") == "bounded_fixed_loss_direct_completion_contract", contract.get("contract_id"), "contract id must match v835 plan"),
        _check("target_terms_exact", contract.get("target_terms") == ["fixed", "loss"], contract.get("target_terms"), "contract must target exactly fixed/loss"),
        _check("canonical_completion_exact", contract.get("canonical_completion") == "fixed loss", contract.get("canonical_completion"), "source canonical completion must remain fixed loss"),
        _check("completion_exact", contract.get("required_exact_completion") == "fixed loss", contract.get("required_exact_completion"), "contract must require fixed loss completion"),
        _check("canonical_prompt_present", bool(contract.get("canonical_prompt")), contract.get("canonical_prompt"), "canonical prompt must be present"),
        _check("canonical_surface_allowed", "canonical_direct_completion_surface" in allowed_surfaces, sorted(allowed_surfaces), "canonical direct completion surface must be allowed"),
        _check("blocked_rescue_surfaces_present", {"forced_prefix_decoder_anchor_as_quality_claim", "more_training_epochs_without_contract_change"}.issubset(blocked_surfaces), sorted(blocked_surfaces), "contract must block rescue surfaces that caused drift"),
        _check("unchanged_holdout_required", contract.get("unchanged_suite_check_required") is True, contract.get("unchanged_suite_check_required"), "unchanged v803 holdout must remain required"),
        _check("contract_cases_present", len(contract_cases) >= 3, len(contract_cases), "contract must define canonical plus support surfaces"),
        _check("seed_blueprint_ready", seed_blueprint.get("planned_example_count") == 18, seed_blueprint.get("planned_example_count"), "seed blueprint must have deterministic planned examples"),
        _check("direct_seed_work_item_present", "direct_seed_corpus" in work_items, sorted(work_items), "plan must include direct seed work item"),
        _check("dual_replay_work_item_present", "dual_replay" in work_items, sorted(work_items), "plan must include dual replay work item"),
    ]


def _summary(
    status: str,
    issues: list[dict[str, Any]],
    contract: dict[str, Any],
    contract_cases: list[dict[str, Any]],
    seed_blueprint: dict[str, Any],
    holdout_rule: dict[str, Any],
) -> dict[str, Any]:
    return {
        "bounded_objective_contract_ready": status == "pass",
        "contract_id": contract.get("contract_id") if status == "pass" else "",
        "target_terms": contract.get("target_terms") if status == "pass" else [],
        "contract_case_count": len(contract_cases) if status == "pass" else 0,
        "planned_seed_example_count": seed_blueprint.get("planned_example_count") if status == "pass" else 0,
        "unchanged_suite_check_required": holdout_rule.get("unchanged_suite_check_required") is True if status == "pass" else False,
        "promotion_claim_allowed": False,
        "proposed_next_artifact": seed_blueprint.get("next_artifact") if status == "pass" else "",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_contract_ready"
    return "fix_model_capability_route_promotion_bounded_objective_contract"


def _interpretation(status: str, contract: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Objective contract inputs are incomplete.", "next_action": "repair objective intervention plan"}
    return {
        "model_quality_claim": "contract_only",
        "reason": "The contract fixes the direct completion target before creating any new seed corpus or checkpoint.",
        "next_action": "model_capability_route_promotion_bounded_objective_seed",
        "contract": contract.get("contract_id"),
    }


__all__ = [
    "BOUNDED_OBJECTIVE_CONTRACT_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_CONTRACT_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_CONTRACT_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_CONTRACT_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_contract",
    "locate_objective_intervention_plan",
    "read_json_report",
    "resolve_exit_code",
]
