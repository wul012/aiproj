from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import ci_boundary_plan_check_ready_regression_count
from minigpt.report_utils import positive_int_mapping as _int_mapping
from minigpt.report_utils import string_list as _string_list


def build_seed_handoff_batch_review_summary(baseline: dict[str, Any]) -> dict[str, Any]:
    batch_review = _dict(baseline.get("handoff_batch_review"))
    return {
        "selected_handoff_selected_batch_review_status": batch_review.get(
            "selected_handoff_selected_batch_review_status"
        ),
        "selected_handoff_selected_batch_comparison_review_action_count": batch_review.get(
            "selected_handoff_selected_batch_comparison_review_action_count"
        ),
        "selected_handoff_selected_batch_comparison_blocker_action_count": batch_review.get(
            "selected_handoff_selected_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_selected_batch_maturity_coverage_regression_count": batch_review.get(
            "selected_handoff_selected_batch_maturity_coverage_regression_count"
        ),
        "selected_handoff_batch_comparison_review_action_count": batch_review.get(
            "selected_handoff_batch_comparison_review_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_action_count": batch_review.get(
            "selected_handoff_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_reasons": _string_list(
            batch_review.get("selected_handoff_batch_comparison_blocker_reasons")
        ),
        "comparison_ready_handoff_selected_batch_review_count": batch_review.get(
            "comparison_ready_handoff_selected_batch_review_count"
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": batch_review.get(
            "comparison_ready_handoff_selected_batch_blocker_count"
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": batch_review.get(
            "comparison_ready_handoff_selected_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": batch_review.get(
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_review_action_total": batch_review.get(
            "comparison_ready_handoff_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_action_total": batch_review.get(
            "comparison_ready_handoff_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": _string_list(
            batch_review.get("comparison_ready_handoff_batch_comparison_blocker_reasons")
        ),
    }


def build_seed_handoff_clean_batch_review_summary(baseline: dict[str, Any]) -> dict[str, Any]:
    clean_review = _dict(baseline.get("handoff_clean_batch_review"))
    selected_ci_reasons = _int_mapping(clean_review.get("selected_handoff_batch_maturity_ci_regression_reason_counts"))
    selected_selected_ci_reasons = _int_mapping(
        clean_review.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    handoff_ci_reasons = _int_mapping(clean_review.get("handoff_batch_maturity_ci_regression_reason_counts"))
    handoff_selected_ci_reasons = _int_mapping(
        clean_review.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    ready_ci_reasons = _int_mapping(
        clean_review.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")
    )
    ready_selected_ci_reasons = _int_mapping(
        clean_review.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    return {
        "selected_handoff_require_clean_batch_review": clean_review.get(
            "selected_handoff_require_clean_batch_review"
        ),
        "selected_handoff_clean_batch_review_status": clean_review.get(
            "selected_handoff_clean_batch_review_status"
        ),
        "selected_handoff_batch_maturity_ci_regression_count": clean_review.get(
            "selected_handoff_batch_maturity_ci_regression_count"
        ),
        "selected_handoff_batch_maturity_ci_regression_names": _string_list(
            clean_review.get("selected_handoff_batch_maturity_ci_regression_names")
        ),
        "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": (
            ci_boundary_plan_check_ready_regression_count(
                clean_review.get(
                    "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
                ),
                selected_ci_reasons,
            )
        ),
        "selected_handoff_batch_maturity_ci_regression_reason_counts": selected_ci_reasons,
        "selected_handoff_batch_maturity_suite_design_regression_count": clean_review.get(
            "selected_handoff_batch_maturity_suite_design_regression_count"
        ),
        "selected_handoff_batch_maturity_suite_design_regression_names": _string_list(
            clean_review.get("selected_handoff_batch_maturity_suite_design_regression_names")
        ),
        "selected_handoff_selected_batch_maturity_ci_regression_count": clean_review.get(
            "selected_handoff_selected_batch_maturity_ci_regression_count"
        ),
        "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": (
            ci_boundary_plan_check_ready_regression_count(
                clean_review.get(
                    "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"
                ),
                selected_selected_ci_reasons,
            )
        ),
        "selected_handoff_selected_batch_maturity_ci_regression_reason_counts": selected_selected_ci_reasons,
        "selected_handoff_selected_batch_maturity_suite_design_regression_count": clean_review.get(
            "selected_handoff_selected_batch_maturity_suite_design_regression_count"
        ),
        "selected_handoff_selected_batch_maturity_suite_design_regression_names": _string_list(
            clean_review.get("selected_handoff_selected_batch_maturity_suite_design_regression_names")
        ),
        "selected_comparison_exclusion_reasons": _string_list(
            clean_review.get("selected_comparison_exclusion_reasons")
        ),
        "handoff_require_clean_batch_review_count": clean_review.get(
            "handoff_require_clean_batch_review_count"
        ),
        "handoff_clean_batch_review_count": clean_review.get("handoff_clean_batch_review_count"),
        "handoff_unclean_batch_review_count": clean_review.get("handoff_unclean_batch_review_count"),
        "handoff_batch_maturity_ci_regression_count": clean_review.get(
            "handoff_batch_maturity_ci_regression_count"
        ),
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": (
            ci_boundary_plan_check_ready_regression_count(
                clean_review.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
                handoff_ci_reasons,
            )
        ),
        "handoff_selected_batch_maturity_ci_regression_total": clean_review.get(
            "handoff_selected_batch_maturity_ci_regression_total"
        ),
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": (
            ci_boundary_plan_check_ready_regression_count(
                clean_review.get(
                    "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
                ),
                handoff_selected_ci_reasons,
            )
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(
            clean_review.get("handoff_batch_maturity_ci_regression_names")
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": handoff_ci_reasons,
        "handoff_selected_batch_maturity_ci_regression_reason_counts": handoff_selected_ci_reasons,
        "handoff_batch_maturity_suite_design_regression_count": clean_review.get(
            "handoff_batch_maturity_suite_design_regression_count"
        ),
        "handoff_selected_batch_maturity_suite_design_regression_total": clean_review.get(
            "handoff_selected_batch_maturity_suite_design_regression_total"
        ),
        "handoff_batch_maturity_suite_design_regression_names": _string_list(
            clean_review.get("handoff_batch_maturity_suite_design_regression_names")
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": _string_list(
            clean_review.get("handoff_selected_batch_maturity_suite_design_regression_names")
        ),
        "comparison_exclusion_reasons": _string_list(clean_review.get("comparison_exclusion_reasons")),
        "comparison_ready_handoff_require_clean_batch_review_count": clean_review.get(
            "comparison_ready_handoff_require_clean_batch_review_count"
        ),
        "comparison_ready_handoff_clean_batch_review_count": clean_review.get(
            "comparison_ready_handoff_clean_batch_review_count"
        ),
        "comparison_ready_handoff_unclean_batch_review_count": clean_review.get(
            "comparison_ready_handoff_unclean_batch_review_count"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_count": clean_review.get(
            "comparison_ready_handoff_batch_maturity_ci_regression_count"
        ),
        "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": (
            ci_boundary_plan_check_ready_regression_count(
                clean_review.get(
                    "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
                ),
                ready_ci_reasons,
            )
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": clean_review.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_total"
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": (
            ci_boundary_plan_check_ready_regression_count(
                clean_review.get(
                    "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
                ),
                ready_selected_ci_reasons,
            )
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_names": _string_list(
            clean_review.get("comparison_ready_handoff_batch_maturity_ci_regression_names")
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": ready_ci_reasons,
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": ready_selected_ci_reasons,
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count": clean_review.get(
            "comparison_ready_handoff_batch_maturity_suite_design_regression_count"
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total": clean_review.get(
            "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names": _string_list(
            clean_review.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names")
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names": _string_list(
            clean_review.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names")
        ),
    }


__all__ = [
    "build_seed_handoff_batch_review_summary",
    "build_seed_handoff_clean_batch_review_summary",
]
