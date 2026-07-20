from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    string_list as _string_list,
)


def build_promoted_training_scale_seed_html_stats(report: dict[str, Any]) -> list[tuple[str, Any]]:
    seed = _dict(report.get("baseline_seed"))
    summary = _dict(report.get("summary"))
    return [
        ("Status", report.get("seed_status")),
        ("Baseline", seed.get("selected_name")),
        ("Decision", seed.get("decision_status")),
        ("Gate", seed.get("gate_status")),
        ("Batch", seed.get("batch_status")),
        ("Score", seed.get("readiness_score")),
        ("Sources", summary.get("source_count")),
        ("Missing", summary.get("missing_source_count")),
        ("Selected handoff suite", summary.get("selected_handoff_suite_consistency")),
        ("Selected handoff mismatch", summary.get("selected_handoff_suite_mismatch_count")),
        ("Selected clean required", summary.get("selected_handoff_require_clean_batch_review")),
        ("Selected clean batch", summary.get("selected_handoff_clean_batch_review_status")),
        ("Selected CI regressions", summary.get("selected_handoff_batch_maturity_ci_regression_count")),
        (
            "Selected CI boundary plan",
            summary.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Selected CI reasons", _fmt_mapping(summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts"))),
        (
            "Selected suite-design regressions",
            summary.get("selected_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Selected suite-design names",
            ", ".join(_string_list(summary.get("selected_handoff_batch_maturity_suite_design_regression_names"))),
        ),
        ("Selected selected CI regressions", summary.get("selected_handoff_selected_batch_maturity_ci_regression_count")),
        (
            "Selected selected CI boundary plan",
            summary.get("selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Selected selected CI reasons",
            _fmt_mapping(summary.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Selected selected suite-design regressions",
            summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Selected selected suite-design names",
            ", ".join(
                _string_list(summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_names"))
            ),
        ),
        ("Handoff clean required", summary.get("handoff_require_clean_batch_review_count")),
        ("Handoff clean", summary.get("handoff_clean_batch_review_count")),
        ("Handoff unclean", summary.get("handoff_unclean_batch_review_count")),
        ("Handoff CI regressions", summary.get("handoff_batch_maturity_ci_regression_count")),
        (
            "Handoff CI boundary plan",
            summary.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Handoff CI reasons", _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))),
        ("Handoff selected CI regressions", summary.get("handoff_selected_batch_maturity_ci_regression_total")),
        (
            "Handoff selected CI boundary plan",
            summary.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "Handoff selected CI reasons",
            _fmt_mapping(summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        ("Handoff suite-design regressions", summary.get("handoff_batch_maturity_suite_design_regression_count")),
        (
            "Handoff selected suite-design regressions",
            summary.get("handoff_selected_batch_maturity_suite_design_regression_total"),
        ),
        (
            "Suite-design names",
            ", ".join(_string_list(summary.get("handoff_batch_maturity_suite_design_regression_names"))),
        ),
        (
            "Selected suite-design names",
            ", ".join(_string_list(summary.get("handoff_selected_batch_maturity_suite_design_regression_names"))),
        ),
        ("Ready clean-required", summary.get("comparison_ready_handoff_require_clean_batch_review_count")),
        ("Ready clean batch", summary.get("comparison_ready_handoff_clean_batch_review_count")),
        ("Ready unclean batch", summary.get("comparison_ready_handoff_unclean_batch_review_count")),
        ("Ready CI regressions", summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")),
        (
            "Ready CI boundary plan",
            summary.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Ready CI reasons",
            _fmt_mapping(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Ready selected CI regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_total"),
        ),
        (
            "Ready selected CI boundary plan",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "Ready selected CI reasons",
            _fmt_mapping(summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Ready suite-design regressions",
            summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Ready selected suite-design regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"),
        ),
        (
            "Ready suite-design names",
            ", ".join(_string_list(summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names"))),
        ),
        (
            "Ready selected suite-design names",
            ", ".join(
                _string_list(summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names"))
            ),
        ),
        ("Selected handoff batch", summary.get("selected_handoff_selected_batch_review_status")),
        ("Selected batch blockers", summary.get("selected_handoff_selected_batch_comparison_blocker_action_count")),
        ("Ready batch reviews", summary.get("comparison_ready_handoff_selected_batch_review_count")),
        ("Ready batch blockers", summary.get("comparison_ready_handoff_selected_batch_blocker_count")),
        ("Handoff suite mismatches", summary.get("handoff_suite_mismatch_total")),
        ("Next suite", summary.get("next_suite_path")),
    ]


__all__ = ["build_promoted_training_scale_seed_html_stats"]
