from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.json"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.csv"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.txt"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.md"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.html"
)


def locate_objective_level_contrast_route_comparison_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-level contrast route comparison input must be a JSON object")
    return dict(payload)


def build_objective_level_contrast_route_comparison(
    baseline_replay: dict[str, Any],
    exact_repair_replay: dict[str, Any],
    objective_replay: dict[str, Any],
    *,
    baseline_path: str | Path | None = None,
    exact_repair_path: str | Path | None = None,
    objective_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    route_rows = [
        _route_row("fixed_preserving_baseline", baseline_replay),
        _route_row("near_exact_surface_repair", exact_repair_replay),
        _route_row("objective_level_contrast", objective_replay),
    ]
    checks = _checks(baseline_replay, exact_repair_replay, objective_replay, route_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(route_rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-level contrast route comparison",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_paths": {
            "fixed_preserving_baseline": str(baseline_path or ""),
            "near_exact_surface_repair": str(exact_repair_path or ""),
            "objective_level_contrast": str(objective_path or ""),
        },
        "route_rows": route_rows,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _route_row(route: str, replay: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    rows = list_of_dicts(replay.get("replay_rows"))
    exact = next((row for row in rows if row.get("spec_id") == "exact-heldout-pair"), {})
    return {
        "route": route,
        "status": replay.get("status"),
        "decision": replay.get("decision"),
        "exact_heldout_pair_full": summary.get("exact_heldout_pair_full") is True,
        "required_all_pair_full": summary.get("required_all_pair_full") is True,
        "pair_full_count": int(summary.get("pair_full_count") or 0),
        "exact_default_hit_count": int(exact.get("default_continuation_hit_count") or 0),
        "exact_suppression_hit_count": int(exact.get("suppression_continuation_hit_count") or 0),
        "replay_row_count": len(rows),
        "model_quality_claim": as_dict(replay.get("interpretation")).get("model_quality_claim", ""),
    }


def _checks(
    baseline: dict[str, Any],
    exact_repair: dict[str, Any],
    objective: dict[str, Any],
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    objective_row = _row(route_rows, "objective_level_contrast")
    prior_max = max(_row(route_rows, "fixed_preserving_baseline").get("pair_full_count", 0), _row(route_rows, "near_exact_surface_repair").get("pair_full_count", 0))
    return [
        _check("baseline_passed", baseline.get("status") == "pass", baseline.get("status"), "baseline replay must pass"),
        _check("exact_repair_passed", exact_repair.get("status") == "pass", exact_repair.get("status"), "exact repair replay must pass"),
        _check("objective_passed", objective.get("status") == "pass", objective.get("status"), "objective replay must pass"),
        _check("three_routes_present", len(route_rows) == 3, len(route_rows), "comparison should include baseline, near-exact repair, and objective routes"),
        _check("objective_required_all_pair_full", objective_row.get("required_all_pair_full") is True, objective_row.get("required_all_pair_full"), "objective route must pass all required pair probes"),
        _check("objective_pair_full_count_wins", int(objective_row.get("pair_full_count") or 0) > int(prior_max or 0), f"objective={objective_row.get('pair_full_count')}, prior_max={prior_max}", "objective route should improve pair-full count over prior routes"),
        _check("objective_exact_hits_complete", int(objective_row.get("exact_default_hit_count") or 0) >= 2, objective_row.get("exact_default_hit_count"), "objective route should hit both terms on exact default replay"),
    ]


def _row(route_rows: list[dict[str, Any]], route: str) -> dict[str, Any]:
    for row in route_rows:
        if row.get("route") == route:
            return row
    return {}


def _summary(route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = _row(route_rows, "fixed_preserving_baseline")
    repair = _row(route_rows, "near_exact_surface_repair")
    objective = _row(route_rows, "objective_level_contrast")
    prior_pair_full_max = max(int(baseline.get("pair_full_count") or 0), int(repair.get("pair_full_count") or 0))
    return {
        "selected_route": "objective_level_contrast",
        "objective_route_best": objective.get("required_all_pair_full") is True and int(objective.get("pair_full_count") or 0) > prior_pair_full_max,
        "baseline_pair_full_count": baseline.get("pair_full_count"),
        "exact_repair_pair_full_count": repair.get("pair_full_count"),
        "objective_pair_full_count": objective.get("pair_full_count"),
        "objective_vs_baseline_pair_full_delta": int(objective.get("pair_full_count") or 0) - int(baseline.get("pair_full_count") or 0),
        "objective_vs_exact_repair_pair_full_delta": int(objective.get("pair_full_count") or 0) - int(repair.get("pair_full_count") or 0),
        "objective_exact_heldout_pair_full": objective.get("exact_heldout_pair_full") is True,
        "promotion_guard_required": True,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_objective_level_contrast_route_comparison"
    if summary.get("objective_route_best"):
        return "pair_readiness_objective_level_contrast_replay_wins_needs_promotion_guard"
    return "pair_readiness_objective_level_contrast_not_yet_better_than_prior_routes"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Route replay inputs are incomplete or contradictory.",
            "next_action": "repair replay inputs before route decision",
        }
    if summary.get("objective_route_best"):
        return {
            "model_quality_claim": "route_comparison_winner",
            "reason": "Objective-level contrast reaches all pair replay surfaces while prior fixed-preserving and near-exact routes remain partial.",
            "next_action": "run promotion guard and seed stability before accepting the checkpoint",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "Objective-level contrast does not yet beat prior pair replay routes.",
        "next_action": "close or revise the objective-level contrast route",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_TEXT_FILENAME",
    "build_objective_level_contrast_route_comparison",
    "locate_objective_level_contrast_route_comparison_source",
    "read_json_report",
    "resolve_exit_code",
]
