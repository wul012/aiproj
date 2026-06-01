from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import TARGET_TERMS
from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison import (
    PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_JSON_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_route_decision.json"
)
PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_CSV_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_route_decision.csv"
)
PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_TEXT_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_route_decision.txt"
)
PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_route_decision.md"
)
PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_HTML_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_route_decision.html"
)


def locate_generation_internal_alignment_route_decision_input(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME
    return source


def read_generation_internal_alignment_route_decision_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("generation/internal alignment route decision input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_generation_internal_alignment_route_decision(
    comparison_report: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    issues = _issues(comparison_report)
    source_rows = list_of_dicts(comparison_report.get("source_rows"))
    selected_generation_route = _first_by_class(source_rows, "generation_pair_full_internal_partial")
    internal_anchor_route = _first_by_class(source_rows, "internal_pair_full_generation_gap")
    aligned_route = _first_by_class(source_rows, "generation_internal_pair_full")
    summary = _summary(source_rows, selected_generation_route, internal_anchor_route, aligned_route)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair generation/internal alignment route decision",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_comparison": {
            "status": comparison_report.get("status"),
            "decision": comparison_report.get("decision"),
            "summary": as_dict(comparison_report.get("summary")),
        },
        "selected_generation_route": selected_generation_route,
        "internal_anchor_route": internal_anchor_route,
        "aligned_route": aligned_route,
        "constraints": _constraints(selected_generation_route, internal_anchor_route, aligned_route),
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _issues(comparison_report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if comparison_report.get("status") != "pass":
        issues.append("alignment comparison status is not pass")
    if not list_of_dicts(comparison_report.get("source_rows")):
        issues.append("alignment comparison has no source rows")
    return issues


def _first_by_class(source_rows: list[dict[str, Any]], alignment_class: str) -> dict[str, Any]:
    for row in source_rows:
        if row.get("alignment_class") == alignment_class:
            return dict(row)
    return {}


def _summary(
    source_rows: list[dict[str, Any]],
    selected_generation_route: dict[str, Any],
    internal_anchor_route: dict[str, Any],
    aligned_route: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_count": len(source_rows),
        "selected_generation_route_label": selected_generation_route.get("source_label", ""),
        "internal_anchor_route_label": internal_anchor_route.get("source_label", ""),
        "aligned_route_label": aligned_route.get("source_label", ""),
        "direct_promotion_ready": bool(aligned_route),
        "requires_internal_repair": bool(selected_generation_route and not aligned_route),
        "requires_generation_preservation": bool(selected_generation_route),
        "expected_target_terms": list(TARGET_TERMS),
    }


def _constraints(
    selected_generation_route: dict[str, Any], internal_anchor_route: dict[str, Any], aligned_route: dict[str, Any]
) -> list[dict[str, Any]]:
    if aligned_route:
        return [
            {
                "id": "repeat_aligned_candidate",
                "status": "required",
                "detail": "An aligned pair-full route exists; repeat it across seeds before promotion.",
            }
        ]
    constraints = [
        {
            "id": "preserve_generation_pair_full",
            "status": "required" if selected_generation_route else "blocked",
            "source": selected_generation_route.get("source_label", ""),
            "detail": "Do not lose fixed/loss generation pair-full while repairing internal preference.",
        },
        {
            "id": "repair_loss_internal_preference",
            "status": "required" if internal_anchor_route else "review",
            "source": internal_anchor_route.get("source_label", ""),
            "detail": "Recover the loss-side forced-choice preference without regressing fixed.",
        },
        {
            "id": "avoid_pair_id_shortcut",
            "status": "required",
            "detail": "Keep explicit pair-id leakage out of the next corpus objective.",
        },
    ]
    return constraints


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_generation_internal_alignment_route_inputs"
    if summary.get("direct_promotion_ready"):
        return "repeat_aligned_pair_full_candidate_before_promotion"
    if summary.get("requires_internal_repair") and summary.get("internal_anchor_route_label"):
        return "repair_internal_preference_preserve_generation_pair_full"
    if summary.get("requires_internal_repair"):
        return "repair_internal_preference_without_anchor"
    return "redesign_required_term_pair_alignment_objective"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route decision input is not trustworthy.",
            "next_action": "repair the alignment comparison before selecting a route",
        }
    if summary.get("direct_promotion_ready"):
        return {
            "model_quality_claim": "targeted_pair_alignment_candidate",
            "reason": "A route already aligns generation and internal pair-full.",
            "next_action": "repeat the aligned candidate across seeds",
        }
    if summary.get("requires_internal_repair"):
        return {
            "model_quality_claim": "route_decision_only",
            "reason": "The best generation route is not internally aligned yet.",
            "next_action": "use the selected generation route as the base and repair internal preference",
        }
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "No compared route is strong enough to anchor the next objective.",
        "next_action": "design a new required-term pair objective",
    }


__all__ = [
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_generation_internal_alignment_route_decision",
    "locate_generation_internal_alignment_route_decision_input",
    "read_generation_internal_alignment_route_decision_input",
    "resolve_exit_code",
]
