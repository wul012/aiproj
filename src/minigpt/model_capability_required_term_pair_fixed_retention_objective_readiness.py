from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic import (
    PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_loss_branch_route_decision import (
    PAIR_LOSS_BRANCH_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_JSON_FILENAME = "model_capability_required_term_pair_fixed_retention_objective_readiness.json"
PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_CSV_FILENAME = "model_capability_required_term_pair_fixed_retention_objective_readiness.csv"
PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_TEXT_FILENAME = "model_capability_required_term_pair_fixed_retention_objective_readiness.txt"
PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_MARKDOWN_FILENAME = "model_capability_required_term_pair_fixed_retention_objective_readiness.md"
PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_HTML_FILENAME = "model_capability_required_term_pair_fixed_retention_objective_readiness.html"


def locate_fixed_retention_route_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_LOSS_BRANCH_ROUTE_DECISION_JSON_FILENAME
    return source


def locate_fixed_retention_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_JSON_FILENAME
    return source


def read_fixed_retention_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("fixed-retention objective readiness input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_fixed_retention_objective_readiness(
    *,
    route_decision: dict[str, Any],
    diagnostic: dict[str, Any],
    route_decision_path: str | Path | None = None,
    diagnostic_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    evidence_rows = _evidence_rows(route_decision, diagnostic, route_decision_path, diagnostic_path)
    requirement_rows = _requirement_rows(route_decision, diagnostic)
    summary = _summary(route_decision, diagnostic, requirement_rows)
    issues = _issues(route_decision, diagnostic, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair fixed-retention objective readiness",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_route_decision": str(route_decision_path or ""),
        "source_diagnostic": str(diagnostic_path or ""),
        "evidence_rows": evidence_rows,
        "requirement_rows": requirement_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _evidence_rows(
    route_decision: dict[str, Any],
    diagnostic: dict[str, Any],
    route_decision_path: str | Path | None,
    diagnostic_path: str | Path | None,
) -> list[dict[str, Any]]:
    route_summary = as_dict(route_decision.get("summary"))
    diag_summary = as_dict(diagnostic.get("summary"))
    return [
        {
            "label": "loss-branch-route-decision",
            "path": str(route_decision_path or ""),
            "status": route_decision.get("status"),
            "decision": route_decision.get("decision"),
            "key_result": f"selected={route_summary.get('selected_stability_route')}; fixed_retention_required={route_summary.get('fixed_retention_objective_required')}",
        },
        {
            "label": "targeted-missed-seed-diagnostic",
            "path": str(diagnostic_path or ""),
            "status": diagnostic.get("status"),
            "decision": diagnostic.get("decision"),
            "key_result": f"missed={diag_summary.get('missed_seed_count')}; first_token_gaps={diag_summary.get('missed_first_token_gap_count')}",
        },
    ]


def _requirement_rows(route_decision: dict[str, Any], diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    route_summary = as_dict(route_decision.get("summary"))
    diag_summary = as_dict(diagnostic.get("summary"))
    rows = [
        {
            "id": "fixed_first_token_retention",
            "required": bool(diag_summary.get("missed_first_token_gap_count")),
            "reason": "fixed first token ranks behind loss/space on missed seeds",
            "acceptance": "fixed_expected_rank must improve before adding more loss weighting",
        },
        {
            "id": "loss_branch_no_extra_weight",
            "required": bool(route_summary.get("fixed_retention_objective_required")),
            "reason": "loss branch already wins while fixed drops",
            "acceptance": "new corpus must not increase loss-only row density without fixed retention rows",
        },
        {
            "id": "pair_full_seed_gate",
            "required": True,
            "reason": "v590-v596 found only residual single-branch evidence",
            "acceptance": "run at least one real seed before calling the objective useful",
        },
    ]
    return rows


def _summary(
    route_decision: dict[str, Any],
    diagnostic: dict[str, Any],
    requirement_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    route_summary = as_dict(route_decision.get("summary"))
    diag_summary = as_dict(diagnostic.get("summary"))
    required_rows = [row for row in requirement_rows if row.get("required")]
    return {
        "fixed_retention_objective_required": bool(route_summary.get("fixed_retention_objective_required")),
        "selected_stability_route": route_summary.get("selected_stability_route"),
        "pair_full_route_count": int(route_summary.get("pair_full_route_count") or 0),
        "missed_seed_count": int(diag_summary.get("missed_seed_count") or 0),
        "missed_first_token_gap_count": int(diag_summary.get("missed_first_token_gap_count") or 0),
        "first_token_gap_confirmed": int(diag_summary.get("missed_first_token_gap_count") or 0) > 0,
        "required_requirement_count": len(required_rows),
        "ready_for_fixed_retention_objective_design": bool(route_summary.get("fixed_retention_objective_required"))
        and int(diag_summary.get("missed_first_token_gap_count") or 0) > 0,
    }


def _issues(route_decision: dict[str, Any], diagnostic: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if route_decision.get("status") != "pass":
        issues.append("route decision status is not pass")
    if diagnostic.get("status") != "pass":
        issues.append("diagnostic status is not pass")
    if not summary.get("fixed_retention_objective_required"):
        issues.append("route decision does not require fixed retention")
    if not summary.get("first_token_gap_confirmed"):
        issues.append("diagnostic does not confirm first-token gap")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_fixed_retention_readiness_inputs"
    if summary.get("ready_for_fixed_retention_objective_design"):
        return "design_fixed_retention_objective_before_more_loss_branch_training"
    return "record_fixed_retention_readiness_only"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The readiness inputs are incomplete or contradictory.",
            "next_action": "repair route decision and diagnostic evidence first",
        }
    return {
        "model_quality_claim": "readiness_only",
        "reason": "Loss branch is strong enough to dominate, while fixed first-token retention is weak across missed seeds.",
        "next_action": "build a fixed-retention corpus objective with balanced first-token rows and a real seed gate",
    }


__all__ = [
    "PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_CSV_FILENAME",
    "PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_HTML_FILENAME",
    "PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_JSON_FILENAME",
    "PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_MARKDOWN_FILENAME",
    "PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_TEXT_FILENAME",
    "build_model_capability_required_term_pair_fixed_retention_objective_readiness",
    "locate_fixed_retention_diagnostic",
    "locate_fixed_retention_route_decision",
    "read_fixed_retention_input",
    "resolve_exit_code",
]
