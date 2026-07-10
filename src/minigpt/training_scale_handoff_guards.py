from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict, first_present, positive_int_mapping, string_list


def build_suite_guard(workflow: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    decision_summary = as_dict(decision.get("summary"))
    workflow_summary = as_dict(workflow.get("summary"))
    required = (
        decision_summary.get("require_suite_consistency")
        if "require_suite_consistency" in decision_summary
        else workflow_summary.get("decision_require_suite_consistency")
    )
    return {
        "decision_require_suite_consistency": bool(required),
        "require_suite_consistency": bool(required),
        "suite_consistency": first_present(
            decision_summary.get("suite_consistency"), workflow_summary.get("suite_consistency")
        ),
        "suite_mismatch_count": first_present(
            decision_summary.get("suite_mismatch_count"), workflow_summary.get("suite_mismatch_count")
        ),
        "selected_suite_path": first_present(
            decision_summary.get("selected_suite_path"), workflow_summary.get("selected_suite_path")
        ),
        "workflow_suite_path": workflow_summary.get("suite_path"),
        "workflow_suite_name": workflow_summary.get("suite_name"),
    }


def build_clean_batch_review_guard(workflow: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    decision_summary = as_dict(decision.get("summary"))
    workflow_summary = as_dict(workflow.get("summary"))
    required = first_present(
        decision_summary.get("require_clean_batch_review"),
        workflow_summary.get("decision_require_clean_batch_review"),
        workflow.get("require_clean_batch_review"),
        workflow.get("decision_require_clean_batch_review"),
    )
    return {
        "decision_require_clean_batch_review": bool(required),
        "require_clean_batch_review": bool(required),
        "clean_batch_review_status": first_present(
            decision_summary.get("clean_batch_review_status"),
            workflow_summary.get("clean_batch_review_status"),
            decision_summary.get("selected_batch_review_status"),
        ),
        "batch_comparison_review_action_count": first_present(
            decision_summary.get("batch_comparison_review_action_count"),
            workflow_summary.get("batch_comparison_review_action_count"),
        ),
        "batch_comparison_blocker_action_count": first_present(
            decision_summary.get("batch_comparison_blocker_action_count"),
            workflow_summary.get("batch_comparison_blocker_action_count"),
        ),
        "batch_maturity_coverage_regression_count": first_present(
            decision_summary.get("batch_maturity_coverage_regression_count"),
            workflow_summary.get("batch_maturity_coverage_regression_count"),
        ),
        "selected_batch_maturity_suite_design_regression_count": first_present(
            decision_summary.get("selected_batch_maturity_suite_design_regression_count"),
            workflow_summary.get("selected_batch_maturity_suite_design_regression_count"),
        ),
        "selected_batch_maturity_suite_design_regression_names": string_list(
            first_present(
                decision_summary.get("selected_batch_maturity_suite_design_regression_names"),
                workflow_summary.get("selected_batch_maturity_suite_design_regression_names"),
            )
        ),
        "batch_maturity_suite_design_regression_count": first_present(
            decision_summary.get("batch_maturity_suite_design_regression_count"),
            workflow_summary.get("batch_maturity_suite_design_regression_count"),
        ),
        "batch_maturity_suite_design_regression_names": string_list(
            first_present(
                decision_summary.get("batch_maturity_suite_design_regression_names"),
                workflow_summary.get("batch_maturity_suite_design_regression_names"),
            )
        ),
        "batch_maturity_ci_regression_count": first_present(
            decision_summary.get("batch_maturity_ci_regression_count"),
            workflow_summary.get("batch_maturity_ci_regression_count"),
        ),
        "batch_maturity_ci_regression_reason_counts": positive_int_mapping(
            first_present(
                decision_summary.get("batch_maturity_ci_regression_reason_counts"),
                workflow_summary.get("batch_maturity_ci_regression_reason_counts"),
            )
        ),
        "selected_batch_maturity_ci_regression_reason_counts": positive_int_mapping(
            first_present(
                decision_summary.get("selected_batch_maturity_ci_regression_reason_counts"),
                workflow_summary.get("selected_batch_maturity_ci_regression_reason_counts"),
            )
        ),
        "batch_maturity_ci_regression_names": string_list(
            first_present(
                decision_summary.get("batch_maturity_ci_regression_names"),
                workflow_summary.get("batch_maturity_ci_regression_names"),
            )
        ),
        "batch_comparison_blocker_reasons": string_list(
            first_present(
                decision_summary.get("batch_comparison_blocker_reasons"),
                workflow_summary.get("batch_comparison_blocker_reasons"),
            )
        ),
    }


__all__ = ["build_clean_batch_review_guard", "build_suite_guard"]
