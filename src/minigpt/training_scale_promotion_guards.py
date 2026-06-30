from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    first_present,
    positive_int_mapping as _int_mapping,
    string_list as _string_list,
)


def suite_guard(handoff: dict[str, Any]) -> dict[str, Any]:
    handoff_summary = _dict(handoff.get("summary"))
    guard = _dict(handoff.get("suite_guard"))
    required = first_present(
        guard.get("decision_require_suite_consistency"),
        guard.get("require_suite_consistency"),
        handoff_summary.get("decision_require_suite_consistency"),
        handoff_summary.get("require_suite_consistency"),
    )
    return {
        "handoff_require_suite_consistency": bool(required),
        "handoff_suite_consistency": first_present(guard.get("suite_consistency"), handoff_summary.get("suite_consistency")),
        "handoff_suite_mismatch_count": first_present(guard.get("suite_mismatch_count"), handoff_summary.get("suite_mismatch_count")),
        "handoff_selected_suite_path": first_present(guard.get("selected_suite_path"), handoff_summary.get("selected_suite_path")),
        "handoff_selected_batch_review_status": _handoff_value(handoff, "selected_batch_review_status"),
        "handoff_selected_batch_comparison_review_action_count": _handoff_value(handoff, "selected_batch_comparison_review_action_count"),
        "handoff_selected_batch_comparison_blocker_action_count": _handoff_value(handoff, "selected_batch_comparison_blocker_action_count"),
        "handoff_selected_batch_maturity_coverage_regression_count": _handoff_value(handoff, "selected_batch_maturity_coverage_regression_count"),
        "handoff_selected_batch_maturity_suite_design_regression_count": _handoff_value(
            handoff, "selected_batch_maturity_suite_design_regression_count"
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": _string_list(
            _handoff_value(handoff, "selected_batch_maturity_suite_design_regression_names")
        ),
        "handoff_selected_batch_maturity_ci_regression_count": _handoff_value(handoff, "selected_batch_maturity_ci_regression_count"),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _int_mapping(
            _handoff_value(handoff, "selected_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_batch_comparison_review_action_count": _handoff_value(handoff, "batch_comparison_review_action_count"),
        "handoff_batch_comparison_blocker_action_count": _handoff_value(handoff, "batch_comparison_blocker_action_count"),
        "handoff_batch_maturity_coverage_regression_count": _handoff_value(handoff, "batch_maturity_coverage_regression_count"),
        "handoff_batch_maturity_suite_design_regression_count": _handoff_value(
            handoff, "batch_maturity_suite_design_regression_count"
        ),
        "handoff_batch_maturity_suite_design_regression_names": _string_list(
            _handoff_value(handoff, "batch_maturity_suite_design_regression_names")
        ),
        "handoff_batch_maturity_ci_regression_count": _handoff_value(handoff, "batch_maturity_ci_regression_count"),
        "handoff_batch_maturity_ci_regression_reason_counts": _int_mapping(
            _handoff_value(handoff, "batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(_handoff_value(handoff, "batch_maturity_ci_regression_names")),
        "handoff_batch_comparison_blocker_reasons": _string_list(_handoff_value(handoff, "batch_comparison_blocker_reasons")),
        "workflow_suite_path": guard.get("workflow_suite_path") or handoff_summary.get("workflow_suite_path"),
        "workflow_suite_name": guard.get("workflow_suite_name") or handoff_summary.get("workflow_suite_name"),
    }


def clean_batch_review_guard(handoff: dict[str, Any]) -> dict[str, Any]:
    handoff_summary = _dict(handoff.get("summary"))
    guard = _dict(handoff.get("clean_batch_review_guard"))
    required = first_present(
        guard.get("decision_require_clean_batch_review"),
        guard.get("require_clean_batch_review"),
        handoff_summary.get("decision_require_clean_batch_review"),
        handoff_summary.get("require_clean_batch_review"),
    )
    return {
        "handoff_require_clean_batch_review": bool(required),
        "handoff_clean_batch_review_status": first_present(
            guard.get("clean_batch_review_status"),
            handoff_summary.get("clean_batch_review_status"),
            handoff_summary.get("selected_batch_review_status"),
        ),
        "handoff_batch_comparison_review_action_count": first_present(
            guard.get("batch_comparison_review_action_count"),
            handoff_summary.get("batch_comparison_review_action_count"),
        ),
        "handoff_batch_comparison_blocker_action_count": first_present(
            guard.get("batch_comparison_blocker_action_count"),
            handoff_summary.get("batch_comparison_blocker_action_count"),
        ),
        "handoff_batch_maturity_coverage_regression_count": first_present(
            guard.get("batch_maturity_coverage_regression_count"),
            handoff_summary.get("batch_maturity_coverage_regression_count"),
        ),
        "handoff_selected_batch_maturity_suite_design_regression_count": first_present(
            guard.get("selected_batch_maturity_suite_design_regression_count"),
            handoff_summary.get("selected_batch_maturity_suite_design_regression_count"),
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": _string_list(
            first_present(
                guard.get("selected_batch_maturity_suite_design_regression_names"),
                handoff_summary.get("selected_batch_maturity_suite_design_regression_names"),
            )
        ),
        "handoff_batch_maturity_suite_design_regression_count": first_present(
            guard.get("batch_maturity_suite_design_regression_count"),
            handoff_summary.get("batch_maturity_suite_design_regression_count"),
        ),
        "handoff_batch_maturity_suite_design_regression_names": _string_list(
            first_present(
                guard.get("batch_maturity_suite_design_regression_names"),
                handoff_summary.get("batch_maturity_suite_design_regression_names"),
            )
        ),
        "handoff_batch_maturity_ci_regression_count": first_present(
            guard.get("batch_maturity_ci_regression_count"),
            handoff_summary.get("batch_maturity_ci_regression_count"),
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": _int_mapping(
            first_present(
                guard.get("batch_maturity_ci_regression_reason_counts"),
                handoff_summary.get("batch_maturity_ci_regression_reason_counts"),
            )
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _int_mapping(
            first_present(
                guard.get("selected_batch_maturity_ci_regression_reason_counts"),
                handoff_summary.get("selected_batch_maturity_ci_regression_reason_counts"),
            )
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(
            first_present(
                guard.get("batch_maturity_ci_regression_names"),
                handoff_summary.get("batch_maturity_ci_regression_names"),
            )
        ),
        "handoff_batch_comparison_blocker_reasons": _string_list(
            first_present(
                guard.get("batch_comparison_blocker_reasons"),
                handoff_summary.get("batch_comparison_blocker_reasons"),
            )
        ),
    }


def reason_detail(value: Any) -> str:
    counts = _int_mapping(value)
    return ", ".join(f"{reason}:{count}" for reason, count in counts.items())


def _handoff_value(handoff: dict[str, Any], key: str) -> Any:
    handoff_summary = _dict(handoff.get("summary"))
    decision_summary = _dict(handoff.get("decision_summary"))
    return first_present(handoff_summary.get(key), decision_summary.get(key))


__all__ = [
    "clean_batch_review_guard",
    "reason_detail",
    "suite_guard",
]
