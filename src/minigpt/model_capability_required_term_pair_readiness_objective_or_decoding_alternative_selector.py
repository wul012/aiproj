from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout import (
    PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.json"
)
PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.csv"
)
PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.txt"
)
PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.md"
)
PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.html"
)


def locate_objective_or_decoding_alternative_selector_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-or-decoding alternative selector input must be a JSON object")
    return dict(payload)


def build_objective_or_decoding_alternative_selector(
    closeout_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(closeout_report.get("summary"))
    closeout = as_dict(closeout_report.get("closeout"))
    candidates = list_of_dicts(closeout.get("candidate_routes"))
    checks = _checks(closeout_report, summary, closeout, candidates)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    route_rows = _route_rows(candidates)
    selected = _selected_route(route_rows) if status == "pass" else {}
    selector = _selector(status, selected, route_rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-or-decoding alternative selector",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_closeout_path": str(source_path or ""),
        "source_closeout": {
            "status": closeout_report.get("status"),
            "decision": closeout_report.get("decision"),
            "summary": summary,
            "closeout": {
                "closed_route": closeout.get("closed_route"),
                "recommended_next_route": closeout.get("recommended_next_route"),
                "closed_reason": closeout.get("closed_reason"),
            },
        },
        "check_rows": checks,
        "route_rows": route_rows,
        "selector": selector,
        "summary": _summary(status, checks, selector, route_rows),
        "interpretation": _interpretation(status, selector),
    }


def _checks(
    closeout_report: dict[str, Any],
    summary: dict[str, Any],
    closeout: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    route_names = {str(row.get("route")) for row in candidates}
    evidence = as_dict(closeout.get("evidence"))
    return [
        _check("closeout_passed", closeout_report.get("status") == "pass", closeout_report.get("status"), "source closeout must pass"),
        _check(
            "closeout_decision",
            closeout_report.get("decision") == "pair_readiness_exact_surface_repair_route_closed",
            closeout_report.get("decision"),
            "selector follows only the exact-surface repair route closeout",
        ),
        _check("closeout_ready", summary.get("closeout_ready") is True, summary.get("closeout_ready"), "closeout must be ready"),
        _check(
            "closed_near_exact_route",
            closeout.get("closed_route") == "near_exact_surface_bridge_rows",
            closeout.get("closed_route"),
            "near-exact bridge rows must be the closed route",
        ),
        _check(
            "recommended_alternative_plan",
            closeout.get("recommended_next_route") == "objective_or_decoding_alternative_plan",
            closeout.get("recommended_next_route"),
            "selector should only run after the objective-or-decoding recommendation",
        ),
        _check("candidate_count", len(candidates) >= 3, len(candidates), "closeout should provide objective, decoding, and fresh-seed candidates"),
        _check("objective_candidate_present", "objective_level_contrast" in route_names, sorted(route_names), "objective route must be available"),
        _check("decoding_candidate_present", "decode_side_constraint_probe" in route_names, sorted(route_names), "decoding route must be available"),
        _check("fresh_seed_candidate_present", "fresh_seed_stability" in route_names, sorted(route_names), "fresh-seed route must be available"),
        _check("no_repair_improvement", not evidence.get("improved_surface_ids"), evidence.get("improved_surface_ids"), "closed route should have no improved replay surfaces"),
    ]


def _route_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [_score_route(row) for row in candidates]
    rows.sort(key=lambda row: (-int(row.get("score") or 0), str(row.get("route"))))
    if rows:
        rows[0]["selected"] = True
    return rows


def _score_route(candidate: dict[str, Any]) -> dict[str, Any]:
    route = str(candidate.get("route") or "")
    presets = {
        "objective_level_contrast": {
            "score": 92,
            "next_artifact": "pair_readiness_objective_level_contrast_plan",
            "selection_reason": "changes the learning objective instead of adding more near-exact surface rows",
            "risk_control": "keep heldout exact pair prompts out of training rows",
        },
        "decode_side_constraint_probe": {
            "score": 78,
            "next_artifact": "pair_readiness_decode_side_constraint_probe",
            "selection_reason": "can diagnose first-token or separator sensitivity before another training run",
            "risk_control": "report as diagnostic only; do not treat constrained hits as promotion",
        },
        "fresh_seed_stability": {
            "score": 64,
            "next_artifact": "pair_readiness_fresh_seed_stability_replay",
            "selection_reason": "checks whether partial pair-readiness is seed-specific",
            "risk_control": "run after a selected objective/decoding route has a concrete hypothesis",
        },
    }
    preset = presets.get(
        route,
        {
            "score": 40,
            "next_artifact": "pair_readiness_manual_route_review",
            "selection_reason": "unrecognized route needs manual review",
            "risk_control": "do not run training until the route is classified",
        },
    )
    return {
        "route": route,
        "score": preset["score"],
        "selected": False,
        "next_artifact": preset["next_artifact"],
        "selection_reason": preset["selection_reason"],
        "risk_control": preset["risk_control"],
        "source_why": candidate.get("why", ""),
        "source_risk": candidate.get("risk", ""),
    }


def _selected_route(route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in route_rows:
        if row.get("selected"):
            return row
    return {}


def _selector(status: str, selected: dict[str, Any], route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ready": status == "pass" and bool(selected),
        "selected_route": selected.get("route", ""),
        "selected_score": selected.get("score", 0),
        "proposed_next_artifact": selected.get("next_artifact", ""),
        "route_order": [row.get("route") for row in route_rows],
        "non_goals": [
            "do not add more near-exact surface rows",
            "do not promote constrained decoding as model-quality proof",
            "do not start fresh-seed training without a sharper route hypothesis",
        ],
    }


def _summary(status: str, checks: list[dict[str, Any]], selector: dict[str, Any], route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "selector_ready": status == "pass" and bool(selector.get("ready")),
        "selected_route": selector.get("selected_route"),
        "selected_score": selector.get("selected_score"),
        "proposed_next_artifact": selector.get("proposed_next_artifact"),
        "route_count": len(route_rows),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_objective_or_decoding_alternative_selected"
    return "fix_pair_readiness_objective_or_decoding_alternative_selector_input"


def _interpretation(status: str, selector: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The exact-surface repair closeout is not sufficient to select the next route.",
            "next_action": "repair route closeout evidence before selecting an alternative",
        }
    return {
        "model_quality_claim": "selection_only",
        "reason": "Near-exact surface rows are closed; the next route should change the objective before more training data is added.",
        "next_action": f"build {selector.get('proposed_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_TEXT_FILENAME",
    "build_objective_or_decoding_alternative_selector",
    "locate_objective_or_decoding_alternative_selector_source",
    "read_json_report",
    "resolve_exit_code",
]
