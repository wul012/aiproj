from __future__ import annotations

from typing import Any

from minigpt.report_utils import format_mapping as _fmt_mapping
from minigpt.report_utils import number_or_default
from minigpt.report_utils import string_list as _string_list


def build_promoted_training_scale_comparison_recommendations(summary: dict[str, Any]) -> list[str]:
    if summary.get("comparison_status") == "compared":
        return _compared_recommendations(summary)
    return _blocked_recommendations(summary)


def _compared_recommendations(summary: dict[str, Any]) -> list[str]:
    recommendations = [
        "Use the compared promoted runs as the baseline for the next training-scale decision.",
        "Keep review and blocked promotions in the index, but do not feed them into comparison runs.",
    ]
    if _int(summary.get("comparison_ready_handoff_unclean_batch_review_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still include unclean clean-required handoffs; resolve them before treating this comparison as clean model-quality evidence."
        )
    elif _int(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")):
        detail = _fmt_mapping(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail != "none" else ""
        recommendations.append(
            "Comparison-ready promoted inputs still include handoff batch CI regressions; resolve them before treating this comparison as clean model-quality evidence."
            + suffix
        )
    elif _int(summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count")):
        names = ", ".join(_string_list(summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names")))
        suffix = f" Affected promotions: {names}." if names else ""
        recommendations.append(
            "Comparison-ready promoted inputs still include handoff batch suite-design regressions; resolve them before treating this comparison as clean model-quality evidence."
            + suffix
        )
    elif _int(summary.get("comparison_ready_handoff_selected_batch_blocker_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still carry selected handoff batch blocker actions; resolve them before treating this comparison as clean model-quality evidence."
        )
    elif _int(summary.get("handoff_batch_maturity_ci_regression_count")):
        detail = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail != "none" else ""
        recommendations.append(
            "CI-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
            + suffix
        )
    elif _int(summary.get("handoff_batch_maturity_suite_design_regression_count")):
        names = ", ".join(_string_list(summary.get("handoff_batch_maturity_suite_design_regression_names")))
        suffix = f" Affected promotions: {names}." if names else ""
        recommendations.append(
            "Suite-design-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
            + suffix
        )
    _append_visible_regression_notes(recommendations, summary)
    reasons = _string_list(summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons"))
    if reasons:
        recommendations.append("Comparison-ready batch blocker reasons: " + ", ".join(reasons))
    elif _int(summary.get("comparison_ready_handoff_selected_batch_review_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still carry selected handoff batch review actions; review them before treating this comparison as clean model-quality evidence."
        )
    if summary.get("suite_consistency") == "mixed":
        recommendations.append(
            "Compared promoted runs use different benchmark suites; review suite paths before treating readiness deltas as clean model-quality deltas."
        )
    return recommendations


def _blocked_recommendations(summary: dict[str, Any]) -> list[str]:
    recommendations = [
        "Add another promoted run or fix the blocked baseline before comparing promoted results.",
        "Use the promotion index to keep review and blocked evidence visible without mixing it into model comparison.",
    ]
    if _int(summary.get("comparison_ready_handoff_unclean_batch_review_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still include unclean clean-required handoffs; clean them before treating later comparisons as baseline evidence."
        )
    elif _int(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")):
        detail = _fmt_mapping(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail != "none" else ""
        recommendations.append(
            "Comparison-ready promoted inputs still include handoff batch CI regressions; clean them before treating later comparisons as baseline evidence."
            + suffix
        )
    elif _int(summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count")):
        names = ", ".join(_string_list(summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names")))
        suffix = f" Affected promotions: {names}." if names else ""
        recommendations.append(
            "Comparison-ready promoted inputs still include handoff batch suite-design regressions; clean them before treating later comparisons as baseline evidence."
            + suffix
        )
    elif _int(summary.get("comparison_ready_handoff_selected_batch_blocker_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still carry selected handoff batch blocker actions; clean them before treating later comparisons as baseline evidence."
        )
    elif _int(summary.get("comparison_ready_handoff_selected_batch_review_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still carry selected handoff batch review actions; review them before treating later comparisons as baseline evidence."
        )
    elif _int(summary.get("handoff_batch_maturity_ci_regression_count")):
        detail = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail != "none" else ""
        recommendations.append(
            "CI-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
            + suffix
        )
    elif _int(summary.get("handoff_batch_maturity_suite_design_regression_count")):
        names = ", ".join(_string_list(summary.get("handoff_batch_maturity_suite_design_regression_names")))
        suffix = f" Affected promotions: {names}." if names else ""
        recommendations.append(
            "Suite-design-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
            + suffix
        )
    return recommendations


def _append_visible_regression_notes(recommendations: list[str], summary: dict[str, Any]) -> None:
    if _int(summary.get("handoff_batch_maturity_ci_regression_count")) and not any(
        "CI-regressed handoff batch evidence remains visible" in item for item in recommendations
    ):
        detail = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail != "none" else ""
        recommendations.append(
            "CI-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
            + suffix
        )
    if _int(summary.get("handoff_batch_maturity_suite_design_regression_count")) and not any(
        "Suite-design-regressed handoff batch evidence remains visible" in item for item in recommendations
    ):
        names = ", ".join(_string_list(summary.get("handoff_batch_maturity_suite_design_regression_names")))
        suffix = f" Affected promotions: {names}." if names else ""
        recommendations.append(
            "Suite-design-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
            + suffix
        )


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


__all__ = ["build_promoted_training_scale_comparison_recommendations"]
