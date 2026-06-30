from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    ci_boundary_plan_check_ready_regression_count,
    format_mapping as _fmt_mapping,
    string_list as _string_list,
)
from minigpt.promoted_training_scale_decision_review_summary import (
    build_decision_handoff_review_summary,
)


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


def append_decision_handoff_clean_batch_recommendations(
    recommendations: list[str],
    selected: dict[str, Any] | None,
    comparison_summary: dict[str, Any],
) -> None:
    selected_required = bool(selected.get("handoff_require_clean_batch_review")) if selected else False
    selected_status = str(selected.get("handoff_clean_batch_review_status") or "") if selected else ""
    selected_boundary_plan_regressions = (
        ci_boundary_plan_check_ready_regression_count(
            selected.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
            selected.get("handoff_batch_maturity_ci_regression_reason_counts"),
        )
        if selected
        else 0
    )
    if selected_required and selected_status != "clean":
        recommendations.append(
            "Resolve the selected clean batch-review requirement before using this baseline as clean model-quality evidence."
        )
    elif selected_required and selected_boundary_plan_regressions:
        recommendations.append(
            "Resolve the selected handoff batch CI regression caused by boundary plan-check readiness before using "
            f"this baseline as clean model-quality evidence. Boundary plan regressions: {selected_boundary_plan_regressions}."
        )
    elif _int(comparison_summary.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count")):
        detail = _fmt_mapping(comparison_summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"))
        recommendations.append(
            "Comparison-ready promoted inputs still include handoff batch CI regressions caused by boundary plan-check "
            f"readiness; keep the decision in review until the boundary plan-check evidence is clean. Observed reasons: {detail}."
        )
    elif _int(comparison_summary.get("comparison_ready_handoff_unclean_batch_review_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still include unclean clean-required handoffs; keep the decision in review."
        )
    elif _int(comparison_summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")):
        detail = _fmt_mapping(comparison_summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"))
        recommendations.append(
            "Comparison-ready promoted inputs still include handoff batch CI regressions; "
            f"keep the decision in review. Observed reasons: {detail}."
        )
    elif _int(comparison_summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count")):
        names = ", ".join(_string_list(comparison_summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names")))
        recommendations.append(
            "Comparison-ready promoted inputs still include handoff batch suite-design regressions; "
            f"keep the decision in review. Observed names: {names or 'unknown'}."
        )
    elif _int(comparison_summary.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count")):
        detail = _fmt_mapping(comparison_summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        recommendations.append(
            "Rejected promoted inputs include handoff batch CI regressions caused by boundary plan-check readiness; "
            f"keep them out of baseline selection until the CI boundary evidence is clean. Observed reasons: {detail}."
        )
    elif _int(comparison_summary.get("handoff_batch_maturity_ci_regression_count")):
        detail = _fmt_mapping(comparison_summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        recommendations.append(
            "Rejected promoted inputs include handoff batch CI regressions; "
            f"keep them out of baseline selection until CI evidence is clean. Observed reasons: {detail}."
        )
    elif _int(comparison_summary.get("handoff_batch_maturity_suite_design_regression_count")):
        names = ", ".join(_string_list(comparison_summary.get("handoff_batch_maturity_suite_design_regression_names")))
        recommendations.append(
            "Rejected promoted inputs include handoff batch suite-design regressions; "
            f"keep them out of baseline selection until suite-design evidence is clean. Observed names: {names or 'unknown'}."
        )
    elif _int(comparison_summary.get("handoff_unclean_batch_review_count")):
        recommendations.append(
            "Rejected promoted inputs include unclean clean-required handoffs; keep them out of baseline selection until the review is clean."
        )


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "append_decision_handoff_batch_recommendations",
    "append_decision_handoff_clean_batch_recommendations",
    "build_decision_handoff_review_summary",
]
