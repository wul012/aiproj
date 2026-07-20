from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison import (
    PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.json"
)
PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.csv"
)
PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.txt"
)
PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.md"
)
PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.html"
)


def locate_exact_surface_repair_route_closeout_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("exact-surface repair route closeout input must be a JSON object")
    return dict(payload)


def build_exact_surface_repair_route_closeout(
    effectiveness_comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    comparison_summary = as_dict(effectiveness_comparison.get("summary"))
    checks = _checks(effectiveness_comparison, comparison_summary)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    closeout = _closeout(comparison_summary)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness exact-surface repair route closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, closeout),
        "failed_count": len(issues),
        "issues": issues,
        "source_effectiveness_comparison_path": str(source_path or ""),
        "source_effectiveness_comparison": {
            "status": effectiveness_comparison.get("status"),
            "decision": effectiveness_comparison.get("decision"),
            "summary": comparison_summary,
        },
        "check_rows": checks,
        "closeout": closeout,
        "summary": _summary(status, closeout, issues),
        "interpretation": _interpretation(status, closeout),
    }


def _checks(comparison: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("comparison_passed", comparison.get("status") == "pass", comparison.get("status"), "effectiveness comparison must pass"),
        _check(
            "comparison_decision",
            comparison.get("decision") == "pair_readiness_exact_surface_repair_ineffective_stop_route",
            comparison.get("decision"),
            "closeout follows only the ineffective exact-surface repair route",
        ),
        _check("repair_ineffective", bool(summary.get("repair_ineffective")), summary.get("repair_ineffective"), "repair must be proven ineffective"),
        _check("exact_hit_delta_zero", int(summary.get("exact_default_hit_delta") or 0) == 0, summary.get("exact_default_hit_delta"), "exact surface should have no hit improvement"),
        _check("exact_pair_full_delta_zero", int(summary.get("exact_pair_full_delta") or 0) == 0, summary.get("exact_pair_full_delta"), "exact pair-full status should have no improvement"),
    ]


def _closeout(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "closed_route": "near_exact_surface_bridge_rows",
        "closed_reason": "independent replay deltas stayed at zero for exact, spaced, and arrow surfaces",
        "do_not_continue": [
            "do not add more near-exact pipe/equals rows without a new objective",
            "do not promote the v755 checkpoint",
            "do not treat training-script pair-full as replay-ready evidence",
        ],
        "recommended_next_route": "objective_or_decoding_alternative_plan",
        "candidate_routes": [
            {
                "route": "objective_level_contrast",
                "why": "the current corpus teaches surface patterns but not a stable required exact response",
                "risk": "may still overfit tiny prompt forms",
            },
            {
                "route": "decode_side_constraint_probe",
                "why": "arrow surface can produce both terms, so decoding may expose whether exact prompt is first-token or separator sensitive",
                "risk": "decode constraints can mask model weakness",
            },
            {
                "route": "fresh_seed_stability",
                "why": "confirm whether the partial pattern is seed-specific before investing in another corpus patch",
                "risk": "costs more training time",
            },
        ],
        "evidence": {
            "baseline_pair_full_count": summary.get("baseline_pair_full_count"),
            "repaired_pair_full_count": summary.get("repaired_pair_full_count"),
            "exact_default_hit_delta": summary.get("exact_default_hit_delta"),
            "exact_pair_full_delta": summary.get("exact_pair_full_delta"),
            "improved_surface_ids": summary.get("improved_surface_ids", []),
        },
    }


def _summary(status: str, closeout: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "closeout_ready": status == "pass",
        "closed_route": closeout.get("closed_route"),
        "recommended_next_route": closeout.get("recommended_next_route"),
        "candidate_route_count": len(closeout.get("candidate_routes", [])),
        "failed_check_count": len(issues),
    }


def _decision(status: str, closeout: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_exact_surface_repair_route_closeout"
    return "pair_readiness_exact_surface_repair_route_closed"


def _interpretation(status: str, closeout: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route cannot be closed until the effectiveness comparison is clean and clearly ineffective.",
            "next_action": "repair comparison evidence before route closeout",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "The near-exact repair route has no independent replay improvement and should be closed.",
        "next_action": "plan objective-level or decoding-side alternatives instead of adding more near-exact rows",
    }


__all__ = [
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_CSV_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_HTML_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_JSON_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_TEXT_FILENAME",
    "build_exact_surface_repair_route_closeout",
    "locate_exact_surface_repair_route_closeout_source",
    "read_json_report",
    "resolve_exit_code",
]
