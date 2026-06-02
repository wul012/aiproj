from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector import (
    PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_plan.json"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_plan.csv"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_plan.txt"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_plan.md"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_plan.html"
)


def locate_objective_level_contrast_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-level contrast plan input must be a JSON object")
    return dict(payload)


def build_objective_level_contrast_plan(
    selector_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(selector_report.get("summary"))
    selector = as_dict(selector_report.get("selector"))
    route_rows = list_of_dicts(selector_report.get("route_rows"))
    checks = _checks(selector_report, summary, selector, route_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    plan = _plan(status, selector)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-level contrast plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_selector_path": str(source_path or ""),
        "source_selector": {
            "status": selector_report.get("status"),
            "decision": selector_report.get("decision"),
            "summary": summary,
            "selector": selector,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(status, checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _checks(
    selector_report: dict[str, Any],
    summary: dict[str, Any],
    selector: dict[str, Any],
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected_rows = [row for row in route_rows if row.get("selected")]
    return [
        _check("selector_passed", selector_report.get("status") == "pass", selector_report.get("status"), "source selector must pass"),
        _check(
            "selector_decision",
            selector_report.get("decision") == "pair_readiness_objective_or_decoding_alternative_selected",
            selector_report.get("decision"),
            "plan follows only the objective-or-decoding selector",
        ),
        _check("selector_ready", summary.get("selector_ready") is True, summary.get("selector_ready"), "selector must be ready"),
        _check("selected_objective_route", selector.get("selected_route") == "objective_level_contrast", selector.get("selected_route"), "objective-level contrast must be selected"),
        _check("selected_score_high", int(selector.get("selected_score") or 0) >= 90, selector.get("selected_score"), "selected route score must be high enough for contract planning"),
        _check(
            "selected_next_artifact",
            selector.get("proposed_next_artifact") == "pair_readiness_objective_level_contrast_plan",
            selector.get("proposed_next_artifact"),
            "selector must point at this plan artifact",
        ),
        _check("single_selected_route", len(selected_rows) == 1, len(selected_rows), "selector should mark exactly one route as selected"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(status: str, selector: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "selected_route": selector.get("selected_route", ""),
        "proposed_next_artifact": "pair_readiness_objective_level_contrast_contract",
        "objective": {
            "id": "paired_required_terms_exact_response",
            "intent": "teach the tiny model to answer the required-term task, not to copy near-exact prompt surfaces",
            "answer_terms": ["fixed", "loss"],
            "required_pair_order": ["fixed", "loss"],
        },
        "contract_design_rows": [
            _design_row("objective-header", 6, "state the response objective before answer text", "no heldout prompt surface"),
            _design_row("branch-role-contrast", 8, "contrast fixed/loss branch roles under explicit task ids", "balanced by branch"),
            _design_row("pair-answer-contrast", 8, "ask for both answer terms through varied objective labels", "avoid exact heldout pair prompt"),
            _design_row("separator-neutral-answer", 4, "separate answer terms through non-heldout separators", "do not reuse fixed=|loss= as prompt"),
        ],
        "heldout_boundaries": [
            "exact-heldout-pair prompt surface remains eval-only",
            "spaced-heldout-pair prompt surface remains eval-only",
            "arrow-heldout-pair prompt surface remains eval-only",
        ],
        "acceptance_checks": [
            "contract row count is balanced across fixed/loss roles",
            "no training prompt equals a heldout pair prompt",
            "row families expose objective labels before answer text",
            "materializer can consume the contract without special-case code",
        ],
        "non_goals": [
            "do not add another near-exact bridge row patch",
            "do not change model size before the objective contract is replayed",
            "do not promote constrained decoding as model-quality proof",
        ],
    }


def _design_row(row_id: str, planned_count: int, purpose: str, guardrail: str) -> dict[str, Any]:
    return {"row_id": row_id, "planned_count": planned_count, "purpose": purpose, "guardrail": guardrail}


def _summary(status: str, checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    rows = list_of_dicts(plan.get("contract_design_rows"))
    return {
        "plan_ready": status == "pass" and bool(plan.get("ready")),
        "selected_route": plan.get("selected_route"),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "contract_design_row_count": len(rows),
        "planned_training_row_count": sum(int(row.get("planned_count") or 0) for row in rows),
        "heldout_boundary_count": len(plan.get("heldout_boundaries", [])),
        "acceptance_check_count": len(plan.get("acceptance_checks", [])),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_objective_level_contrast_plan_ready"
    return "fix_pair_readiness_objective_level_contrast_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The selector evidence is not sufficient to plan the objective-level contrast contract.",
            "next_action": "repair selector evidence before contract design",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "The selected route changes the training objective while preserving heldout pair-prompt boundaries.",
        "next_action": f"build {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_TEXT_FILENAME",
    "build_objective_level_contrast_plan",
    "locate_objective_level_contrast_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
