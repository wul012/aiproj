from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_branch_binding_route_decision import (
    PAIR_BRANCH_BINDING_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_target_anchor_route_decision import (
    PAIR_TARGET_ANCHOR_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_OBJECTIVE_CLOSEOUT_JSON_FILENAME = "model_capability_required_term_pair_objective_closeout.json"
PAIR_OBJECTIVE_CLOSEOUT_CSV_FILENAME = "model_capability_required_term_pair_objective_closeout.csv"
PAIR_OBJECTIVE_CLOSEOUT_TEXT_FILENAME = "model_capability_required_term_pair_objective_closeout.txt"
PAIR_OBJECTIVE_CLOSEOUT_MARKDOWN_FILENAME = "model_capability_required_term_pair_objective_closeout.md"
PAIR_OBJECTIVE_CLOSEOUT_HTML_FILENAME = "model_capability_required_term_pair_objective_closeout.html"


def locate_branch_binding_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_BRANCH_BINDING_ROUTE_DECISION_JSON_FILENAME
    return source


def locate_target_anchor_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_TARGET_ANCHOR_ROUTE_DECISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective closeout input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_objective_closeout(
    *,
    branch_binding_decision: dict[str, Any],
    target_anchor_decision: dict[str, Any],
    branch_binding_path: str | Path | None = None,
    target_anchor_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    evidence_rows = _evidence_rows(branch_binding_decision, target_anchor_decision, branch_binding_path, target_anchor_path)
    summary = _summary(branch_binding_decision, target_anchor_decision)
    issues = _issues(evidence_rows, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair objective closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "summary": summary,
        "evidence_rows": evidence_rows,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _evidence_rows(
    branch_binding_decision: dict[str, Any],
    target_anchor_decision: dict[str, Any],
    branch_binding_path: str | Path | None,
    target_anchor_path: str | Path | None,
) -> list[dict[str, Any]]:
    branch_summary = as_dict(branch_binding_decision.get("summary"))
    target_summary = as_dict(target_anchor_decision.get("summary"))
    return [
        {
            "label": "v583-branch-binding-route-decision",
            "path": str(branch_binding_path or ""),
            "status": branch_binding_decision.get("status"),
            "decision": branch_binding_decision.get("decision"),
            "key_result": f"branch_visible={branch_summary.get('branch_binding_visible_hit_route_count')}",
        },
        {
            "label": "v586-target-anchor-route-decision",
            "path": str(target_anchor_path or ""),
            "status": target_anchor_decision.get("status"),
            "decision": target_anchor_decision.get("decision"),
            "key_result": f"residual={','.join(str(value) for value in target_summary.get('residual_signal_routes', []))}",
        },
    ]


def _summary(branch_binding_decision: dict[str, Any], target_anchor_decision: dict[str, Any]) -> dict[str, Any]:
    branch_summary = as_dict(branch_binding_decision.get("summary"))
    target_summary = as_dict(target_anchor_decision.get("summary"))
    residual_routes = [str(value) for value in target_summary.get("residual_signal_routes", [])]
    return {
        "branch_binding_decision": branch_binding_decision.get("decision"),
        "target_anchor_decision": target_anchor_decision.get("decision"),
        "branch_binding_stopped": branch_binding_decision.get("decision") == "stop_branch_binding_v1_and_keep_residual_baseline",
        "target_anchor_residual_only": target_anchor_decision.get("decision") == "keep_target_anchor_as_residual_not_promoted",
        "residual_signal_routes": residual_routes,
        "residual_signal_route_count": len(residual_routes),
        "loss_branch_required": "loss" not in target_summary.get("union_hit_terms", []),
        "branch_binding_visible_hit_route_count": branch_summary.get("branch_binding_visible_hit_route_count"),
        "target_anchor_loss_hit_route_count": target_summary.get("target_anchor_loss_hit_route_count"),
    }


def _issues(evidence_rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    issues = []
    for row in evidence_rows:
        if row.get("status") != "pass":
            issues.append(f"{row.get('label')} status is not pass")
    if not summary.get("branch_binding_stopped"):
        issues.append("branch-binding route is not stopped")
    if not summary.get("target_anchor_residual_only"):
        issues.append("target-anchor is not classified as residual-only")
    if not summary.get("loss_branch_required"):
        issues.append("loss branch objective is not required by summary")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_objective_closeout_inputs"
    if summary.get("loss_branch_required"):
        return "close_current_objectives_and_design_loss_branch_objective"
    return "record_required_term_pair_objective_closeout"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Objective closeout inputs are incomplete or contradictory.",
            "next_action": "repair branch-binding and target-anchor decisions before closing the route",
        }
    return {
        "model_quality_claim": "objective_closeout_only",
        "reason": "Branch-binding was stopped and target-anchor remains residual-only; loss is still missing.",
        "next_action": "design a loss-branch objective before the next training run",
    }


__all__ = [
    "PAIR_OBJECTIVE_CLOSEOUT_CSV_FILENAME",
    "PAIR_OBJECTIVE_CLOSEOUT_HTML_FILENAME",
    "PAIR_OBJECTIVE_CLOSEOUT_JSON_FILENAME",
    "PAIR_OBJECTIVE_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_OBJECTIVE_CLOSEOUT_TEXT_FILENAME",
    "build_model_capability_required_term_pair_objective_closeout",
    "locate_branch_binding_decision",
    "locate_target_anchor_decision",
    "read_json_report",
    "resolve_exit_code",
]
