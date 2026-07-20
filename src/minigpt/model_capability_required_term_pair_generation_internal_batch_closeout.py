from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison import (
    PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_generation_internal_alignment_route_decision import (
    PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_JSON_FILENAME = (
    "model_capability_required_term_pair_generation_internal_batch_closeout.json"
)
PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_CSV_FILENAME = (
    "model_capability_required_term_pair_generation_internal_batch_closeout.csv"
)
PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_TEXT_FILENAME = (
    "model_capability_required_term_pair_generation_internal_batch_closeout.txt"
)
PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_generation_internal_batch_closeout.md"
)
PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_HTML_FILENAME = (
    "model_capability_required_term_pair_generation_internal_batch_closeout.html"
)


def locate_generation_internal_batch_closeout_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME
    return source


def locate_generation_internal_batch_closeout_route_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_JSON_FILENAME
    return source


def read_generation_internal_batch_closeout_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("generation/internal batch closeout input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_generation_internal_batch_closeout(
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
    *,
    batch_start: int = 629,
    batch_end: int = 638,
    next_route: str = "joint_cycle_internal_repair",
    generated_at: str | None = None,
) -> dict[str, Any]:
    issues = _issues(comparison_report, route_decision_report)
    summary = _summary(
        comparison_report,
        route_decision_report,
        batch_start=batch_start,
        batch_end=batch_end,
        next_route=next_route,
    )
    closeout_items = _closeout_items(comparison_report, route_decision_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair generation/internal batch closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "included_versions": [f"v{version}" for version in range(batch_start, batch_end + 1)],
        "source_comparison": {
            "status": comparison_report.get("status"),
            "decision": comparison_report.get("decision"),
            "summary": as_dict(comparison_report.get("summary")),
        },
        "source_route_decision": {
            "status": route_decision_report.get("status"),
            "decision": route_decision_report.get("decision"),
            "summary": as_dict(route_decision_report.get("summary")),
        },
        "closeout_items": closeout_items,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _issues(comparison_report: dict[str, Any], route_decision_report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if comparison_report.get("status") != "pass":
        issues.append("alignment comparison status is not pass")
    if route_decision_report.get("status") != "pass":
        issues.append("route decision status is not pass")
    if not list_of_dicts(comparison_report.get("source_rows")):
        issues.append("alignment comparison has no source rows")
    if not as_dict(route_decision_report.get("selected_generation_route")):
        issues.append("route decision has no selected generation route")
    return issues


def _summary(
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
    *,
    batch_start: int,
    batch_end: int,
    next_route: str,
) -> dict[str, Any]:
    comparison_summary = as_dict(comparison_report.get("summary"))
    route_summary = as_dict(route_decision_report.get("summary"))
    return {
        "batch_version_count": max(0, batch_end - batch_start + 1),
        "batch_start": batch_start,
        "batch_end": batch_end,
        "compared_source_count": comparison_summary.get("compared_source_count"),
        "generation_pair_full_count": comparison_summary.get("generation_pair_full_count"),
        "internal_pair_full_count": comparison_summary.get("internal_pair_full_count"),
        "aligned_pair_full_count": comparison_summary.get("aligned_pair_full_count"),
        "direct_promotion_ready": bool(route_summary.get("direct_promotion_ready")),
        "selected_generation_route": route_summary.get("selected_generation_route_label"),
        "internal_anchor_route": route_summary.get("internal_anchor_route_label"),
        "next_route": next_route,
    }


def _closeout_items(comparison_report: dict[str, Any], route_decision_report: dict[str, Any]) -> list[dict[str, Any]]:
    comparison_summary = as_dict(comparison_report.get("summary"))
    route_summary = as_dict(route_decision_report.get("summary"))
    source_rows = list_of_dicts(comparison_report.get("source_rows"))
    source_labels = {str(row.get("source_label") or "") for row in source_rows}
    selected_generation = str(route_summary.get("selected_generation_route_label") or "")
    internal_anchor = str(route_summary.get("internal_anchor_route_label") or "")
    items = [
        {
            "id": "generation_pair_full_route_present",
            "status": "confirmed" if int(comparison_summary.get("generation_pair_full_count") or 0) > 0 else "missing",
            "detail": f"{selected_generation or 'no selected route'} is the selected generation route.",
        },
        {
            "id": "internal_alignment_not_ready",
            "status": "confirmed" if int(comparison_summary.get("aligned_pair_full_count") or 0) == 0 else "cleared",
            "detail": "No route has both generation pair-full and internal pair-full.",
        },
        {
            "id": "internal_anchor_preserved",
            "status": "confirmed" if internal_anchor else "missing",
            "detail": f"{internal_anchor or 'no internal anchor'} is the selected internal anchor.",
        },
        {
            "id": "next_route_selected",
            "status": "confirmed" if selected_generation else "missing",
            "detail": "Preserve the selected generation route while repairing internal preference.",
        },
    ]
    if "joint-cycle-light-merge" in source_labels:
        items.append(
            {
                "id": "light_merge_rejected",
                "status": "confirmed",
                "detail": "v645/v646 light-merge remains a partial tradeoff, not an aligned route.",
            }
        )
    if any("resume" in label for label in source_labels):
        items.append(
            {
                "id": "resume_routes_rejected",
                "status": "confirmed",
                "detail": "Resume routes were compared but did not become aligned pair-full candidates.",
            }
        )
    return items


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_generation_internal_batch_closeout_inputs"
    if summary.get("direct_promotion_ready"):
        return "close_batch_with_aligned_candidate_repeat_required"
    return f"close_batch_and_design_{summary.get('next_route') or 'next_route'}"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The closeout inputs are incomplete.",
            "next_action": "repair comparison and route-decision inputs",
        }
    return {
        "model_quality_claim": "targeted_generation_signal_only",
        "reason": "The batch found a generation pair-full route but no aligned generation/internal route.",
        "next_action": f"design {summary.get('next_route') or 'the next route'}",
    }


__all__ = [
    "PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_CSV_FILENAME",
    "PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_HTML_FILENAME",
    "PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_JSON_FILENAME",
    "PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_TEXT_FILENAME",
    "build_model_capability_required_term_pair_generation_internal_batch_closeout",
    "locate_generation_internal_batch_closeout_comparison",
    "locate_generation_internal_batch_closeout_route_decision",
    "read_generation_internal_batch_closeout_input",
    "resolve_exit_code",
]
