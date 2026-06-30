from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    ci_boundary_plan_check_ready_regression_count,
    positive_int_mapping as _int_mapping,
    string_list as _string_list,
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
        "selected_handoff_require_clean_batch_review": None
        if selected is None
        else selected.get("handoff_require_clean_batch_review"),
        "selected_handoff_clean_batch_review_status": None
        if selected is None
        else selected.get("handoff_clean_batch_review_status"),
        "selected_handoff_batch_maturity_ci_regression_count": None
        if selected is None
        else selected.get("handoff_batch_maturity_ci_regression_count"),
        "selected_handoff_batch_maturity_ci_regression_reason_counts": {}
        if selected is None
        else _int_mapping(selected.get("handoff_batch_maturity_ci_regression_reason_counts")),
        "selected_handoff_batch_maturity_ci_regression_names": []
        if selected is None
        else _string_list(selected.get("handoff_batch_maturity_ci_regression_names")),
        "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": None
        if selected is None
        else ci_boundary_plan_check_ready_regression_count(
            selected.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
            selected.get("handoff_batch_maturity_ci_regression_reason_counts"),
        ),
        "selected_handoff_batch_maturity_suite_design_regression_count": None
        if selected is None
        else selected.get("handoff_batch_maturity_suite_design_regression_count"),
        "selected_handoff_batch_maturity_suite_design_regression_names": []
        if selected is None
        else _string_list(selected.get("handoff_batch_maturity_suite_design_regression_names")),
        "selected_handoff_selected_batch_maturity_ci_regression_count": None
        if selected is None
        else selected.get("handoff_selected_batch_maturity_ci_regression_count"),
        "selected_handoff_selected_batch_maturity_ci_regression_reason_counts": {}
        if selected is None
        else _int_mapping(selected.get("handoff_selected_batch_maturity_ci_regression_reason_counts")),
        "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": None
        if selected is None
        else ci_boundary_plan_check_ready_regression_count(
            selected.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
            selected.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
        ),
        "selected_handoff_selected_batch_maturity_suite_design_regression_count": None
        if selected is None
        else selected.get("handoff_selected_batch_maturity_suite_design_regression_count"),
        "selected_handoff_selected_batch_maturity_suite_design_regression_names": []
        if selected is None
        else _string_list(selected.get("handoff_selected_batch_maturity_suite_design_regression_names")),
        "selected_comparison_exclusion_reasons": []
        if selected is None
        else _string_list(selected.get("comparison_exclusion_reasons")),
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
        "handoff_require_clean_batch_review_count": _summary_number(
            comparison_summary,
            "handoff_require_clean_batch_review_count",
            sum(1 for row in promotions if row.get("handoff_require_clean_batch_review")),
        ),
        "handoff_clean_batch_review_count": _summary_number(
            comparison_summary,
            "handoff_clean_batch_review_count",
            sum(
                1
                for row in promotions
                if row.get("handoff_require_clean_batch_review")
                and row.get("handoff_clean_batch_review_status") == "clean"
                and _int(row.get("handoff_batch_maturity_ci_regression_count")) == 0
                and _int(row.get("handoff_batch_maturity_suite_design_regression_count")) == 0
            ),
        ),
        "handoff_unclean_batch_review_count": _summary_number(
            comparison_summary,
            "handoff_unclean_batch_review_count",
            sum(
                1
                for row in promotions
                if row.get("handoff_require_clean_batch_review")
                and (
                    row.get("handoff_clean_batch_review_status") != "clean"
                    or _int(row.get("handoff_batch_maturity_ci_regression_count")) > 0
                    or _int(row.get("handoff_batch_maturity_suite_design_regression_count")) > 0
                )
            ),
        ),
        "handoff_batch_maturity_ci_regression_count": _summary_number(
            comparison_summary,
            "handoff_batch_maturity_ci_regression_count",
            sum(_int(row.get("handoff_batch_maturity_ci_regression_count")) for row in promotions),
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": _summary_mapping(
            comparison_summary,
            "handoff_batch_maturity_ci_regression_reason_counts",
            _sum_reason_counts(row.get("handoff_batch_maturity_ci_regression_reason_counts") for row in promotions),
        ),
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": _summary_number(
            comparison_summary,
            "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            sum(
                ci_boundary_plan_check_ready_regression_count(
                    row.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
                    row.get("handoff_batch_maturity_ci_regression_reason_counts"),
                )
                for row in promotions
            ),
        ),
        "handoff_selected_batch_maturity_ci_regression_total": _summary_number(
            comparison_summary,
            "handoff_selected_batch_maturity_ci_regression_total",
            sum(_int(row.get("handoff_selected_batch_maturity_ci_regression_count")) for row in promotions),
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _summary_mapping(
            comparison_summary,
            "handoff_selected_batch_maturity_ci_regression_reason_counts",
            _sum_reason_counts(
                row.get("handoff_selected_batch_maturity_ci_regression_reason_counts") for row in promotions
            ),
        ),
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": _summary_number(
            comparison_summary,
            "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            sum(
                ci_boundary_plan_check_ready_regression_count(
                    row.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
                    row.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
                )
                for row in promotions
            ),
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(
            comparison_summary.get("handoff_batch_maturity_ci_regression_names")
        )
        or sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_batch_maturity_ci_regression_names"))
            }
        ),
        "handoff_batch_maturity_suite_design_regression_count": _summary_number(
            comparison_summary,
            "handoff_batch_maturity_suite_design_regression_count",
            sum(_int(row.get("handoff_batch_maturity_suite_design_regression_count")) for row in promotions),
        ),
        "handoff_selected_batch_maturity_suite_design_regression_total": _summary_number(
            comparison_summary,
            "handoff_selected_batch_maturity_suite_design_regression_total",
            sum(_int(row.get("handoff_selected_batch_maturity_suite_design_regression_count")) for row in promotions),
        ),
        "handoff_batch_maturity_suite_design_regression_names": _string_list(
            comparison_summary.get("handoff_batch_maturity_suite_design_regression_names")
        )
        or sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_batch_maturity_suite_design_regression_names"))
            }
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": _string_list(
            comparison_summary.get("handoff_selected_batch_maturity_suite_design_regression_names")
        )
        or sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_selected_batch_maturity_suite_design_regression_names"))
            }
        ),
        "comparison_exclusion_reasons": _string_list(comparison_summary.get("comparison_exclusion_reasons"))
        or sorted(
            {
                reason
                for row in promotions
                for reason in _string_list(row.get("comparison_exclusion_reasons"))
            }
        ),
        "comparison_ready_handoff_require_clean_batch_review_count": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_require_clean_batch_review_count",
            sum(1 for row in promotions if row.get("promoted_for_comparison") and row.get("handoff_require_clean_batch_review")),
        ),
        "comparison_ready_handoff_clean_batch_review_count": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_clean_batch_review_count",
            sum(
                1
                for row in promotions
                if row.get("promoted_for_comparison")
                and row.get("handoff_require_clean_batch_review")
                and row.get("handoff_clean_batch_review_status") == "clean"
                and _int(row.get("handoff_batch_maturity_ci_regression_count")) == 0
                and _int(row.get("handoff_batch_maturity_suite_design_regression_count")) == 0
            ),
        ),
        "comparison_ready_handoff_unclean_batch_review_count": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_unclean_batch_review_count",
            sum(
                1
                for row in promotions
                if row.get("promoted_for_comparison")
                and row.get("handoff_require_clean_batch_review")
                and (
                    row.get("handoff_clean_batch_review_status") != "clean"
                    or _int(row.get("handoff_batch_maturity_ci_regression_count")) > 0
                    or _int(row.get("handoff_batch_maturity_suite_design_regression_count")) > 0
                )
            ),
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_count": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_batch_maturity_ci_regression_count",
            sum(
                _int(row.get("handoff_batch_maturity_ci_regression_count"))
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": _summary_mapping(
            comparison_summary,
            "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
            _sum_reason_counts(
                row.get("handoff_batch_maturity_ci_regression_reason_counts")
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            sum(
                ci_boundary_plan_check_ready_regression_count(
                    row.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
                    row.get("handoff_batch_maturity_ci_regression_reason_counts"),
                )
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_total",
            sum(
                _int(row.get("handoff_selected_batch_maturity_ci_regression_count"))
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": _summary_mapping(
            comparison_summary,
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
            _sum_reason_counts(
                row.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            sum(
                ci_boundary_plan_check_ready_regression_count(
                    row.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
                    row.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
                )
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_names": _string_list(
            comparison_summary.get("comparison_ready_handoff_batch_maturity_ci_regression_names")
        )
        or sorted(
            {
                name
                for row in promotions
                if row.get("promoted_for_comparison")
                for name in _string_list(row.get("handoff_batch_maturity_ci_regression_names"))
            }
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_batch_maturity_suite_design_regression_count",
            sum(
                _int(row.get("handoff_batch_maturity_suite_design_regression_count"))
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total": _summary_number(
            comparison_summary,
            "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total",
            sum(
                _int(row.get("handoff_selected_batch_maturity_suite_design_regression_count"))
                for row in promotions
                if row.get("promoted_for_comparison")
            ),
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names": _string_list(
            comparison_summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names")
        )
        or sorted(
            {
                name
                for row in promotions
                if row.get("promoted_for_comparison")
                for name in _string_list(row.get("handoff_batch_maturity_suite_design_regression_names"))
            }
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names": _string_list(
            comparison_summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names")
        )
        or sorted(
            {
                name
                for row in promotions
                if row.get("promoted_for_comparison")
                for name in _string_list(row.get("handoff_selected_batch_maturity_suite_design_regression_names"))
            }
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


def _summary_mapping(summary: dict[str, Any], key: str, fallback: dict[str, int]) -> dict[str, int]:
    value = _int_mapping(summary.get(key))
    return value if value else fallback


def _sum_reason_counts(values: Any) -> dict[str, int]:
    totals: dict[str, int] = {}
    for value in values:
        for reason, count in _int_mapping(value).items():
            totals[reason] = totals.get(reason, 0) + count
    return dict(sorted(totals.items()))


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "build_decision_handoff_review_summary",
]
