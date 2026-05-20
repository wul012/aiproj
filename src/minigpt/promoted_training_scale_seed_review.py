from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import first_present
from minigpt.report_utils import string_list as _string_list


def append_seed_handoff_batch_review_recommendation(recommendations: list[str], seed: dict[str, Any]) -> None:
    review = _dict(seed.get("handoff_batch_review"))
    selected_status = str(review.get("selected_handoff_selected_batch_review_status") or "")
    if selected_status == "blocker":
        recommendations.append(
            "Resolve selected handoff batch blocker actions before treating the next-cycle seed as clean model-quality evidence."
        )
    elif selected_status == "review":
        recommendations.append(
            "Review selected handoff batch actions before treating the next-cycle seed as clean model-quality evidence."
        )


def append_seed_handoff_clean_batch_recommendation(recommendations: list[str], seed: dict[str, Any]) -> None:
    review = _dict(seed.get("handoff_clean_batch_review"))
    selected_required = bool(review.get("selected_handoff_require_clean_batch_review"))
    selected_status = str(review.get("selected_handoff_clean_batch_review_status") or "")
    selected_ci_regressions = _int(review.get("selected_handoff_batch_maturity_ci_regression_count"))
    if selected_required and selected_status != "clean":
        recommendations.append(
            "Resolve selected handoff clean batch-review status before treating the next-cycle seed as clean model-quality evidence."
        )
    elif selected_required and selected_ci_regressions:
        recommendations.append(
            "Resolve selected handoff batch CI regressions before treating the next-cycle seed as clean model-quality evidence."
        )
    elif _int(review.get("handoff_batch_maturity_ci_regression_count")):
        recommendations.append(
            "Rejected promoted decision inputs include handoff batch CI regressions; keep them out of the next-cycle seed baseline."
        )
    elif _int(review.get("handoff_unclean_batch_review_count")):
        recommendations.append(
            "Rejected promoted decision inputs include unclean clean-required handoffs; keep them out of the next-cycle seed baseline."
        )


def build_seed_handoff_clean_batch_review(decision: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(decision.get("summary"))
    return {
        "selected_handoff_require_clean_batch_review": first_present(
            summary.get("selected_handoff_require_clean_batch_review"),
            selected.get("handoff_require_clean_batch_review"),
        ),
        "selected_handoff_clean_batch_review_status": first_present(
            summary.get("selected_handoff_clean_batch_review_status"),
            selected.get("handoff_clean_batch_review_status"),
        ),
        "selected_handoff_batch_maturity_ci_regression_count": first_present(
            summary.get("selected_handoff_batch_maturity_ci_regression_count"),
            selected.get("handoff_batch_maturity_ci_regression_count"),
        ),
        "selected_handoff_batch_maturity_ci_regression_names": _string_list(
            first_present(
                summary.get("selected_handoff_batch_maturity_ci_regression_names"),
                selected.get("handoff_batch_maturity_ci_regression_names"),
            )
        ),
        "selected_handoff_selected_batch_maturity_ci_regression_count": first_present(
            summary.get("selected_handoff_selected_batch_maturity_ci_regression_count"),
            selected.get("handoff_selected_batch_maturity_ci_regression_count"),
        ),
        "selected_comparison_exclusion_reasons": _string_list(
            first_present(
                summary.get("selected_comparison_exclusion_reasons"),
                selected.get("comparison_exclusion_reasons"),
            )
        ),
        "handoff_require_clean_batch_review_count": summary.get("handoff_require_clean_batch_review_count"),
        "handoff_clean_batch_review_count": summary.get("handoff_clean_batch_review_count"),
        "handoff_unclean_batch_review_count": summary.get("handoff_unclean_batch_review_count"),
        "handoff_batch_maturity_ci_regression_count": summary.get("handoff_batch_maturity_ci_regression_count"),
        "handoff_selected_batch_maturity_ci_regression_total": summary.get(
            "handoff_selected_batch_maturity_ci_regression_total"
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(
            summary.get("handoff_batch_maturity_ci_regression_names")
        ),
        "comparison_exclusion_reasons": _string_list(summary.get("comparison_exclusion_reasons")),
        "comparison_ready_handoff_require_clean_batch_review_count": summary.get(
            "comparison_ready_handoff_require_clean_batch_review_count"
        ),
        "comparison_ready_handoff_clean_batch_review_count": summary.get(
            "comparison_ready_handoff_clean_batch_review_count"
        ),
        "comparison_ready_handoff_unclean_batch_review_count": summary.get(
            "comparison_ready_handoff_unclean_batch_review_count"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_count": summary.get(
            "comparison_ready_handoff_batch_maturity_ci_regression_count"
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": summary.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_total"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_names": _string_list(
            summary.get("comparison_ready_handoff_batch_maturity_ci_regression_names")
        ),
    }


def build_seed_handoff_clean_batch_review_summary(seed: dict[str, Any]) -> dict[str, Any]:
    review = _dict(seed.get("handoff_clean_batch_review"))
    return {
        "selected_handoff_require_clean_batch_review": review.get("selected_handoff_require_clean_batch_review"),
        "selected_handoff_clean_batch_review_status": review.get("selected_handoff_clean_batch_review_status"),
        "selected_handoff_batch_maturity_ci_regression_count": review.get(
            "selected_handoff_batch_maturity_ci_regression_count"
        ),
        "selected_handoff_batch_maturity_ci_regression_names": review.get(
            "selected_handoff_batch_maturity_ci_regression_names"
        ),
        "selected_handoff_selected_batch_maturity_ci_regression_count": review.get(
            "selected_handoff_selected_batch_maturity_ci_regression_count"
        ),
        "selected_comparison_exclusion_reasons": review.get("selected_comparison_exclusion_reasons"),
        "handoff_require_clean_batch_review_count": review.get("handoff_require_clean_batch_review_count"),
        "handoff_clean_batch_review_count": review.get("handoff_clean_batch_review_count"),
        "handoff_unclean_batch_review_count": review.get("handoff_unclean_batch_review_count"),
        "handoff_batch_maturity_ci_regression_count": review.get("handoff_batch_maturity_ci_regression_count"),
        "handoff_selected_batch_maturity_ci_regression_total": review.get(
            "handoff_selected_batch_maturity_ci_regression_total"
        ),
        "handoff_batch_maturity_ci_regression_names": review.get("handoff_batch_maturity_ci_regression_names"),
        "comparison_exclusion_reasons": review.get("comparison_exclusion_reasons"),
        "comparison_ready_handoff_require_clean_batch_review_count": review.get(
            "comparison_ready_handoff_require_clean_batch_review_count"
        ),
        "comparison_ready_handoff_clean_batch_review_count": review.get(
            "comparison_ready_handoff_clean_batch_review_count"
        ),
        "comparison_ready_handoff_unclean_batch_review_count": review.get(
            "comparison_ready_handoff_unclean_batch_review_count"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_count": review.get(
            "comparison_ready_handoff_batch_maturity_ci_regression_count"
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": review.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_total"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_names": review.get(
            "comparison_ready_handoff_batch_maturity_ci_regression_names"
        ),
    }


def build_seed_handoff_batch_review(decision: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(decision.get("summary"))
    return {
        "selected_handoff_selected_batch_review_status": first_present(
            summary.get("selected_handoff_selected_batch_review_status"),
            selected.get("handoff_selected_batch_review_status"),
        ),
        "selected_handoff_selected_batch_comparison_review_action_count": first_present(
            summary.get("selected_handoff_selected_batch_comparison_review_action_count"),
            selected.get("handoff_selected_batch_comparison_review_action_count"),
        ),
        "selected_handoff_selected_batch_comparison_blocker_action_count": first_present(
            summary.get("selected_handoff_selected_batch_comparison_blocker_action_count"),
            selected.get("handoff_selected_batch_comparison_blocker_action_count"),
        ),
        "selected_handoff_selected_batch_maturity_coverage_regression_count": first_present(
            summary.get("selected_handoff_selected_batch_maturity_coverage_regression_count"),
            selected.get("handoff_selected_batch_maturity_coverage_regression_count"),
        ),
        "selected_handoff_batch_comparison_review_action_count": first_present(
            summary.get("selected_handoff_batch_comparison_review_action_count"),
            selected.get("handoff_batch_comparison_review_action_count"),
        ),
        "selected_handoff_batch_comparison_blocker_action_count": first_present(
            summary.get("selected_handoff_batch_comparison_blocker_action_count"),
            selected.get("handoff_batch_comparison_blocker_action_count"),
        ),
        "selected_handoff_batch_comparison_blocker_reasons": _string_list(
            first_present(
                summary.get("selected_handoff_batch_comparison_blocker_reasons"),
                selected.get("handoff_batch_comparison_blocker_reasons"),
            )
        ),
        "comparison_ready_handoff_selected_batch_review_count": summary.get(
            "comparison_ready_handoff_selected_batch_review_count"
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": summary.get(
            "comparison_ready_handoff_selected_batch_blocker_count"
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": summary.get(
            "comparison_ready_handoff_selected_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": summary.get(
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_review_action_total": summary.get(
            "comparison_ready_handoff_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_action_total": summary.get(
            "comparison_ready_handoff_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": _string_list(
            summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons")
        ),
    }


def build_seed_handoff_batch_review_summary(seed: dict[str, Any]) -> dict[str, Any]:
    review = _dict(seed.get("handoff_batch_review"))
    return {
        "selected_handoff_selected_batch_review_status": review.get(
            "selected_handoff_selected_batch_review_status"
        ),
        "selected_handoff_selected_batch_comparison_review_action_count": review.get(
            "selected_handoff_selected_batch_comparison_review_action_count"
        ),
        "selected_handoff_selected_batch_comparison_blocker_action_count": review.get(
            "selected_handoff_selected_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_selected_batch_maturity_coverage_regression_count": review.get(
            "selected_handoff_selected_batch_maturity_coverage_regression_count"
        ),
        "selected_handoff_batch_comparison_review_action_count": review.get(
            "selected_handoff_batch_comparison_review_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_action_count": review.get(
            "selected_handoff_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_reasons": review.get(
            "selected_handoff_batch_comparison_blocker_reasons"
        ),
        "comparison_ready_handoff_selected_batch_review_count": review.get(
            "comparison_ready_handoff_selected_batch_review_count"
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": review.get(
            "comparison_ready_handoff_selected_batch_blocker_count"
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": review.get(
            "comparison_ready_handoff_selected_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": review.get(
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_review_action_total": review.get(
            "comparison_ready_handoff_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_action_total": review.get(
            "comparison_ready_handoff_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": review.get(
            "comparison_ready_handoff_batch_comparison_blocker_reasons"
        ),
    }


def build_seed_handoff_suite_guard(decision: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(decision.get("summary"))
    return {
        "selected_handoff_require_suite_consistency": first_present(
            summary.get("selected_handoff_require_suite_consistency"),
            selected.get("handoff_require_suite_consistency"),
        ),
        "selected_handoff_suite_consistency": first_present(
            summary.get("selected_handoff_suite_consistency"),
            selected.get("handoff_suite_consistency"),
        ),
        "selected_handoff_suite_mismatch_count": first_present(
            summary.get("selected_handoff_suite_mismatch_count"),
            selected.get("handoff_suite_mismatch_count"),
        ),
        "selected_handoff_selected_suite_path": first_present(
            summary.get("selected_handoff_selected_suite_path"),
            selected.get("handoff_selected_suite_path"),
        ),
        "handoff_require_suite_consistency_count": summary.get("handoff_require_suite_consistency_count"),
        "handoff_suite_consistent_count": summary.get("handoff_suite_consistent_count"),
        "handoff_suite_mismatch_total": summary.get("handoff_suite_mismatch_total"),
        "comparison_ready_handoff_suite_mismatch_total": summary.get("comparison_ready_handoff_suite_mismatch_total"),
    }


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "append_seed_handoff_batch_review_recommendation",
    "append_seed_handoff_clean_batch_recommendation",
    "build_seed_handoff_batch_review",
    "build_seed_handoff_batch_review_summary",
    "build_seed_handoff_clean_batch_review",
    "build_seed_handoff_clean_batch_review_summary",
    "build_seed_handoff_suite_guard",
]
