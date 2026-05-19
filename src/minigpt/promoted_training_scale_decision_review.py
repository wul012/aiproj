from __future__ import annotations

from typing import Any

from minigpt.report_utils import string_list as _string_list


def append_decision_handoff_batch_recommendations(
    recommendations: list[str],
    selected: dict[str, Any] | None,
    comparison_summary: dict[str, Any],
) -> None:
    selected_status = str(selected.get("handoff_selected_batch_review_status") or "") if selected else ""
    if selected_status == "blocker":
        recommendations.append(
            "Resolve selected handoff batch blocker actions before using this baseline as clean model-quality evidence."
        )
    elif selected_status == "review":
        recommendations.append(
            "Review selected handoff batch actions before using this baseline as clean model-quality evidence."
        )
    elif _int(comparison_summary.get("comparison_ready_handoff_selected_batch_blocker_count")):
        recommendations.append(
            "Other comparison-ready promoted inputs carry handoff batch blockers; keep them as review context for this baseline."
        )


def build_decision_handoff_review_summary(
    comparison_summary: dict[str, Any],
    promotions: list[dict[str, Any]],
    selected: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "selected_handoff_require_suite_consistency": None
        if selected is None
        else selected.get("handoff_require_suite_consistency"),
        "selected_handoff_suite_consistency": None if selected is None else selected.get("handoff_suite_consistency"),
        "selected_handoff_suite_mismatch_count": None
        if selected is None
        else selected.get("handoff_suite_mismatch_count"),
        "selected_handoff_selected_suite_path": None
        if selected is None
        else selected.get("handoff_selected_suite_path"),
        "selected_handoff_selected_batch_review_status": None
        if selected is None
        else selected.get("handoff_selected_batch_review_status"),
        "selected_handoff_selected_batch_comparison_review_action_count": None
        if selected is None
        else selected.get("handoff_selected_batch_comparison_review_action_count"),
        "selected_handoff_selected_batch_comparison_blocker_action_count": None
        if selected is None
        else selected.get("handoff_selected_batch_comparison_blocker_action_count"),
        "selected_handoff_selected_batch_maturity_coverage_regression_count": None
        if selected is None
        else selected.get("handoff_selected_batch_maturity_coverage_regression_count"),
        "selected_handoff_batch_comparison_review_action_count": None
        if selected is None
        else selected.get("handoff_batch_comparison_review_action_count"),
        "selected_handoff_batch_comparison_blocker_action_count": None
        if selected is None
        else selected.get("handoff_batch_comparison_blocker_action_count"),
        "selected_handoff_batch_comparison_blocker_reasons": []
        if selected is None
        else _string_list(selected.get("handoff_batch_comparison_blocker_reasons")),
        "handoff_require_suite_consistency_count": comparison_summary.get("handoff_require_suite_consistency_count")
        or sum(1 for row in promotions if row.get("handoff_require_suite_consistency")),
        "handoff_suite_consistent_count": comparison_summary.get("handoff_suite_consistent_count")
        or sum(1 for row in promotions if row.get("handoff_suite_consistency") == "consistent"),
        "handoff_suite_mismatch_total": comparison_summary.get("handoff_suite_mismatch_total")
        if comparison_summary.get("handoff_suite_mismatch_total") is not None
        else sum(_int(row.get("handoff_suite_mismatch_count")) for row in promotions),
        "comparison_ready_handoff_suite_mismatch_total": comparison_summary.get(
            "comparison_ready_handoff_suite_mismatch_total"
        ),
        "comparison_ready_handoff_selected_batch_review_count": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_selected_batch_review_count",
            sum(
                1
                for row in promotions
                if row.get("promoted_for_comparison") and row.get("handoff_selected_batch_review_status") == "review"
            ),
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_selected_batch_blocker_count",
            sum(
                1
                for row in promotions
                if row.get("promoted_for_comparison") and row.get("handoff_selected_batch_review_status") == "blocker"
            ),
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_selected_batch_comparison_review_action_total",
            sum(
                _int(row.get("handoff_selected_batch_comparison_review_action_count"))
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total",
            sum(
                _int(row.get("handoff_selected_batch_comparison_blocker_action_count"))
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_batch_comparison_review_action_total": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_batch_comparison_review_action_total",
            sum(
                _int(row.get("handoff_batch_comparison_review_action_count"))
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_batch_comparison_blocker_action_total": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_batch_comparison_blocker_action_total",
            sum(
                _int(row.get("handoff_batch_comparison_blocker_action_count"))
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": _string_list(
            comparison_summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons")
        )
        or sorted(
            {
                reason
                for row in promotions
                if row.get("promoted_for_comparison")
                for reason in _string_list(row.get("handoff_batch_comparison_blocker_reasons"))
            }
        ),
    }


def _summary_number(summary: dict[str, Any], key: str, fallback: int) -> Any:
    return summary.get(key) if summary.get(key) is not None else fallback


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "append_decision_handoff_batch_recommendations",
    "build_decision_handoff_review_summary",
]
