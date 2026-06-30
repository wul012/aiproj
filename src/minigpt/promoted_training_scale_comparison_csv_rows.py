from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    list_of_dicts as _list_of_dicts,
    string_list as _string_list,
)

PROMOTED_COMPARISON_CSV_FIELDNAMES: tuple[str, ...] = (
    "name",
    "promotion_status",
    "promoted_for_comparison",
    "training_scale_run_path",
    "status",
    "allowed",
    "gate_status",
    "batch_status",
    "suite_path",
    "readiness_score",
    "handoff_require_suite_consistency",
    "handoff_suite_consistency",
    "handoff_suite_mismatch_count",
    "handoff_selected_suite_path",
    "handoff_require_clean_batch_review",
    "handoff_clean_batch_review_status",
    "handoff_batch_maturity_ci_regression_count",
    "handoff_batch_maturity_ci_regression_reason_counts",
    "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "handoff_batch_maturity_ci_regression_names",
    "handoff_batch_maturity_suite_design_regression_count",
    "handoff_batch_maturity_suite_design_regression_names",
    "handoff_selected_batch_maturity_ci_regression_count",
    "handoff_selected_batch_maturity_ci_regression_reason_counts",
    "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "handoff_selected_batch_maturity_suite_design_regression_count",
    "handoff_selected_batch_maturity_suite_design_regression_names",
    "comparison_exclusion_reasons",
    "handoff_selected_batch_review_status",
    "handoff_selected_batch_comparison_review_action_count",
    "handoff_selected_batch_comparison_blocker_action_count",
    "handoff_batch_comparison_review_action_count",
    "handoff_batch_comparison_blocker_action_count",
    "baseline_name",
    "is_baseline",
    "readiness_delta",
    "gate_relation",
    "batch_relation",
    "explanation",
)


def promoted_comparison_csv_fieldnames() -> list[str]:
    return list(PROMOTED_COMPARISON_CSV_FIELDNAMES)


def promoted_comparison_csv_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    comparison = _dict(report.get("comparison"))
    deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
    return [
        promoted_comparison_csv_row(row, deltas.get(row.get("name"), {}))
        for row in _list_of_dicts(report.get("promotions"))
    ]


def promoted_comparison_csv_row(row: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row.get("name"),
        "promotion_status": row.get("promotion_status"),
        "promoted_for_comparison": row.get("promoted_for_comparison"),
        "training_scale_run_path": row.get("training_scale_run_path"),
        "status": row.get("comparison_status"),
        "allowed": row.get("allowed"),
        "gate_status": row.get("gate_status"),
        "batch_status": row.get("batch_status"),
        "suite_path": row.get("suite_path"),
        "readiness_score": row.get("readiness_score"),
        "handoff_require_suite_consistency": row.get("handoff_require_suite_consistency"),
        "handoff_suite_consistency": row.get("handoff_suite_consistency"),
        "handoff_suite_mismatch_count": row.get("handoff_suite_mismatch_count"),
        "handoff_selected_suite_path": row.get("handoff_selected_suite_path"),
        "handoff_require_clean_batch_review": row.get("handoff_require_clean_batch_review"),
        "handoff_clean_batch_review_status": row.get("handoff_clean_batch_review_status"),
        "handoff_batch_maturity_ci_regression_count": row.get("handoff_batch_maturity_ci_regression_count"),
        "handoff_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            row.get("handoff_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": row.get(
            "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "handoff_batch_maturity_ci_regression_names": ";".join(
            _string_list(row.get("handoff_batch_maturity_ci_regression_names"))
        ),
        "handoff_batch_maturity_suite_design_regression_count": row.get(
            "handoff_batch_maturity_suite_design_regression_count"
        ),
        "handoff_batch_maturity_suite_design_regression_names": ";".join(
            _string_list(row.get("handoff_batch_maturity_suite_design_regression_names"))
        ),
        "handoff_selected_batch_maturity_ci_regression_count": row.get(
            "handoff_selected_batch_maturity_ci_regression_count"
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            row.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": row.get(
            "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "handoff_selected_batch_maturity_suite_design_regression_count": row.get(
            "handoff_selected_batch_maturity_suite_design_regression_count"
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": ";".join(
            _string_list(row.get("handoff_selected_batch_maturity_suite_design_regression_names"))
        ),
        "comparison_exclusion_reasons": ";".join(_string_list(row.get("comparison_exclusion_reasons"))),
        "handoff_selected_batch_review_status": row.get("handoff_selected_batch_review_status"),
        "handoff_selected_batch_comparison_review_action_count": row.get(
            "handoff_selected_batch_comparison_review_action_count"
        ),
        "handoff_selected_batch_comparison_blocker_action_count": row.get(
            "handoff_selected_batch_comparison_blocker_action_count"
        ),
        "handoff_batch_comparison_review_action_count": row.get(
            "handoff_batch_comparison_review_action_count"
        ),
        "handoff_batch_comparison_blocker_action_count": row.get(
            "handoff_batch_comparison_blocker_action_count"
        ),
        "baseline_name": delta.get("baseline_name"),
        "is_baseline": delta.get("is_baseline"),
        "readiness_delta": delta.get("readiness_delta"),
        "gate_relation": delta.get("gate_relation"),
        "batch_relation": delta.get("batch_relation"),
        "explanation": delta.get("explanation"),
    }


__all__ = [
    "PROMOTED_COMPARISON_CSV_FIELDNAMES",
    "promoted_comparison_csv_fieldnames",
    "promoted_comparison_csv_row",
    "promoted_comparison_csv_rows",
]
