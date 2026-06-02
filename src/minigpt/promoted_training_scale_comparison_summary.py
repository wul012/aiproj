from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    number_or_default,
    positive_int_mapping as _int_mapping,
    string_list as _string_list,
)


def build_promoted_training_scale_comparison_summary(
    index_summary: dict[str, Any],
    promotions: list[dict[str, Any]],
    comparison_inputs: dict[str, Any],
    comparison_report: dict[str, Any],
    comparison_status: str,
    blocked_reason: str | None,
) -> dict[str, Any]:
    compared = _dict(comparison_report.get("summary"))
    return {
        "comparison_status": comparison_status,
        "promotion_index_status": _index_status(index_summary),
        "promotion_count": len(promotions),
        "promoted_count": sum(1 for row in promotions if row.get("promotion_status") == "promoted"),
        "comparison_ready_count": comparison_inputs.get("run_count"),
        "compared_run_count": _dict(comparison_report.get("summary")).get("run_count"),
        "baseline_name": compared.get("baseline_name") or comparison_inputs.get("baseline_name"),
        "best_by_readiness": _dict(comparison_report.get("best_by_readiness")).get("name"),
        "suite_consistency": compared.get("suite_consistency"),
        "suite_path_count": compared.get("suite_path_count"),
        "suite_paths": compared.get("suite_paths"),
        "suite_mismatch_count": compared.get("suite_mismatch_count"),
        "handoff_require_suite_consistency_count": sum(1 for row in promotions if row.get("handoff_require_suite_consistency")),
        "handoff_suite_consistent_count": sum(1 for row in promotions if row.get("handoff_suite_consistency") == "consistent"),
        "handoff_suite_mismatch_total": sum(_int(row.get("handoff_suite_mismatch_count")) for row in promotions),
        "handoff_selected_suite_path_count": sum(1 for row in promotions if row.get("handoff_selected_suite_path")),
        "handoff_require_clean_batch_review_count": sum(1 for row in promotions if row.get("handoff_require_clean_batch_review")),
        "handoff_clean_batch_review_count": sum(
            1
            for row in promotions
            if row.get("handoff_require_clean_batch_review")
            and row.get("handoff_clean_batch_review_status") == "clean"
            and _int(row.get("handoff_batch_maturity_ci_regression_count")) == 0
            and _int(row.get("handoff_batch_maturity_suite_design_regression_count")) == 0
        ),
        "handoff_unclean_batch_review_count": sum(
            1
            for row in promotions
            if row.get("handoff_require_clean_batch_review")
            and (
                row.get("handoff_clean_batch_review_status") != "clean"
                or _int(row.get("handoff_batch_maturity_ci_regression_count")) > 0
                or _int(row.get("handoff_batch_maturity_suite_design_regression_count")) > 0
            )
        ),
        "handoff_batch_maturity_ci_regression_count": sum(
            _int(row.get("handoff_batch_maturity_ci_regression_count")) for row in promotions
        ),
        "handoff_selected_batch_maturity_ci_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_ci_regression_count")) for row in promotions
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _sum_reason_counts(
            row.get("handoff_selected_batch_maturity_ci_regression_reason_counts") for row in promotions
        ),
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"))
            for row in promotions
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": _sum_reason_counts(
            row.get("handoff_batch_maturity_ci_regression_reason_counts") for row in promotions
        ),
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": sum(
            _int(row.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"))
            for row in promotions
        ),
        "handoff_batch_maturity_ci_regression_names": sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_batch_maturity_ci_regression_names"))
            }
        ),
        "handoff_batch_maturity_suite_design_regression_count": sum(
            _int(row.get("handoff_batch_maturity_suite_design_regression_count")) for row in promotions
        ),
        "handoff_selected_batch_maturity_suite_design_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_suite_design_regression_count")) for row in promotions
        ),
        "handoff_batch_maturity_suite_design_regression_names": sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_batch_maturity_suite_design_regression_names"))
            }
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_selected_batch_maturity_suite_design_regression_names"))
            }
        ),
        "comparison_ready_handoff_selected_batch_review_count": sum(
            1
            for row in promotions
            if row.get("promoted_for_comparison") and row.get("handoff_selected_batch_review_status") == "review"
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": sum(
            1
            for row in promotions
            if row.get("promoted_for_comparison") and row.get("handoff_selected_batch_review_status") == "blocker"
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": sum(
            _int(row.get("handoff_selected_batch_comparison_review_action_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": sum(
            _int(row.get("handoff_selected_batch_comparison_blocker_action_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_comparison_review_action_total": sum(
            _int(row.get("handoff_batch_comparison_review_action_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_comparison_blocker_action_total": sum(
            _int(row.get("handoff_batch_comparison_blocker_action_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": sorted(
            {
                reason
                for row in promotions
                if row.get("promoted_for_comparison")
                for reason in _string_list(row.get("handoff_batch_comparison_blocker_reasons"))
            }
        ),
        "comparison_ready_handoff_require_clean_batch_review_count": sum(
            1 for row in promotions if row.get("promoted_for_comparison") and row.get("handoff_require_clean_batch_review")
        ),
        "comparison_ready_handoff_clean_batch_review_count": sum(
            1
            for row in promotions
            if row.get("promoted_for_comparison")
            and row.get("handoff_require_clean_batch_review")
            and row.get("handoff_clean_batch_review_status") == "clean"
            and _int(row.get("handoff_batch_maturity_ci_regression_count")) == 0
            and _int(row.get("handoff_batch_maturity_suite_design_regression_count")) == 0
        ),
        "comparison_ready_handoff_unclean_batch_review_count": sum(
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
        "comparison_ready_handoff_batch_maturity_ci_regression_count": sum(
            _int(row.get("handoff_batch_maturity_ci_regression_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_ci_regression_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": _sum_reason_counts(
            row.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": _sum_reason_counts(
            row.get("handoff_batch_maturity_ci_regression_reason_counts")
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": sum(
            _int(row.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_names": sorted(
            {
                name
                for row in promotions
                if row.get("promoted_for_comparison")
                for name in _string_list(row.get("handoff_batch_maturity_ci_regression_names"))
            }
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count": sum(
            _int(row.get("handoff_batch_maturity_suite_design_regression_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_suite_design_regression_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names": sorted(
            {
                name
                for row in promotions
                if row.get("promoted_for_comparison")
                for name in _string_list(row.get("handoff_batch_maturity_suite_design_regression_names"))
            }
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names": sorted(
            {
                name
                for row in promotions
                if row.get("promoted_for_comparison")
                for name in _string_list(row.get("handoff_selected_batch_maturity_suite_design_regression_names"))
            }
        ),
        "comparison_ready_handoff_suite_mismatch_total": sum(
            _int(row.get("handoff_suite_mismatch_count")) for row in promotions if row.get("promoted_for_comparison")
        ),
        "allowed_count": compared.get("allowed_count"),
        "blocked_count": compared.get("blocked_count"),
        "gate_warn_count": compared.get("gate_warn_count"),
        "gate_fail_count": compared.get("gate_fail_count"),
        "blocked_reason": blocked_reason,
    }


def _index_status(index_summary: dict[str, Any]) -> str:
    if not index_summary:
        return "unknown"
    if index_summary.get("compare_command_ready"):
        return "compare_ready"
    return "insufficient"


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


def _sum_reason_counts(values: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        for reason, count in _int_mapping(value).items():
            result[reason] = result.get(reason, 0) + count
    return dict(sorted(result.items()))


__all__ = ["build_promoted_training_scale_comparison_summary"]
