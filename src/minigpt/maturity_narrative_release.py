from __future__ import annotations

from typing import Any


def build_maturity_narrative_release_summary(
    maturity_summary: dict[str, Any],
    release_context: dict[str, Any],
) -> dict[str, Any]:
    trend_status = _coalesce(release_context.get("trend_status"), maturity_summary.get("release_readiness_trend_status"))
    requirement_status_changed_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_status_changed_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_status_changed_count"),
    )
    requirement_exit_code_delta = _coalesce(
        release_context.get("max_abs_benchmark_history_readiness_requirement_exit_code_delta"),
        maturity_summary.get("release_readiness_benchmark_requirement_exit_code_delta_max"),
    )
    requirement_reason_added_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_added_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_added_count"),
    )
    requirement_reason_removed_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_removed_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_removed_count"),
    )
    requirement_reason_added = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_added"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_added"),
        [],
    )
    requirement_reason_removed = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_removed"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_removed"),
        [],
    )
    requirement_reason_recovery_delta_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_recovery_delta_count"),
    )
    requirement_reason_mixed_delta_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_mixed_delta_count"),
    )
    requirement_reason_drift_status_counts = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_drift_status_counts"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_drift_status_counts"),
        {},
    )
    ci_regression_reasons = _coalesce(
        release_context.get("ci_workflow_regression_reasons"),
        maturity_summary.get("release_readiness_ci_workflow_regression_reasons"),
        [],
    )
    ci_regression_reason_counts = _coalesce(
        release_context.get("ci_workflow_regression_reason_counts"),
        maturity_summary.get("release_readiness_ci_workflow_regression_reason_counts"),
        {},
    )
    ci_tiny_plan_regression_count = _coalesce(
        release_context.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count"),
        maturity_summary.get("release_readiness_ci_tiny_plan_digest_gate_ready_regression_count"),
    )
    ci_boundary_gate_regression_count = _coalesce(
        release_context.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count"),
        maturity_summary.get("release_readiness_ci_boundary_gate_check_ready_regression_count"),
    )
    ci_boundary_plan_regression_count = _coalesce(
        release_context.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count"),
        maturity_summary.get("release_readiness_ci_boundary_plan_check_ready_regression_count"),
    )
    ci_archived_path_regression_count = _coalesce(
        release_context.get("ci_workflow_archived_path_portability_check_ready_regression_count"),
        maturity_summary.get("release_readiness_ci_archived_path_portability_check_ready_regression_count"),
    )
    ci_drift_smoke_regression_count = _coalesce(
        release_context.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count"),
        maturity_summary.get("release_readiness_ci_drift_smoke_ready_regression_count"),
    )
    suite_design_delta_count = _coalesce(
        release_context.get("benchmark_history_suite_design_non_comparison_ready_delta_count"),
        maturity_summary.get("release_readiness_benchmark_suite_design_delta_count"),
    )
    suite_design_regression_count = _coalesce(
        release_context.get("benchmark_history_suite_design_non_comparison_ready_regression_count"),
        maturity_summary.get("release_readiness_benchmark_suite_design_regression_count"),
    )
    design_change_delta_count = _coalesce(
        release_context.get("benchmark_history_design_comparison_changed_delta_count"),
        maturity_summary.get("release_readiness_benchmark_design_change_delta_count"),
    )
    max_suite_design_delta = _coalesce(
        release_context.get("max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta"),
        maturity_summary.get("release_readiness_max_benchmark_suite_design_delta"),
    )
    max_design_change_delta = _coalesce(
        release_context.get("max_abs_benchmark_history_design_comparison_changed_entries_delta"),
        maturity_summary.get("release_readiness_max_benchmark_design_change_delta"),
    )
    if (
        int(requirement_status_changed_count or 0) > 0
        or int(requirement_reason_mixed_delta_count or 0) > 0
        or int(requirement_reason_added_count or 0) > 0
        or int(suite_design_regression_count or 0) > 0
    ):
        trend_status = "benchmark-regressed"
    return {
        **release_context,
        "trend_status": trend_status,
        "regressed_count": _coalesce(release_context.get("regressed_count"), maturity_summary.get("release_readiness_regressed_count")),
        "improved_count": _coalesce(release_context.get("improved_count"), maturity_summary.get("release_readiness_improved_count")),
        "ci_workflow_regression_count": _coalesce(
            release_context.get("ci_workflow_regression_count"),
            maturity_summary.get("release_readiness_ci_workflow_regression_count"),
        ),
        "ci_workflow_order_regression_count": _coalesce(
            release_context.get("ci_workflow_order_regression_count"),
            maturity_summary.get("release_readiness_ci_workflow_order_regression_count"),
        ),
        "ci_workflow_status_changed_count": _coalesce(
            release_context.get("ci_workflow_status_changed_count"),
            maturity_summary.get("release_readiness_ci_workflow_status_changed_count"),
        ),
        "ci_workflow_regression_reasons": _string_list(ci_regression_reasons),
        "ci_workflow_regression_reason_counts": _dict(ci_regression_reason_counts),
        "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count": ci_tiny_plan_regression_count,
        "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count": ci_boundary_gate_regression_count,
        "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count": ci_boundary_plan_regression_count,
        "ci_workflow_archived_path_portability_check_ready_regression_count": ci_archived_path_regression_count,
        "ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count": ci_drift_smoke_regression_count,
        "max_abs_ci_workflow_failed_check_delta": _coalesce(
            release_context.get("max_abs_ci_workflow_failed_check_delta"),
            maturity_summary.get("release_readiness_max_ci_workflow_failed_check_delta"),
        ),
        "max_abs_ci_workflow_order_violation_delta": _coalesce(
            release_context.get("max_abs_ci_workflow_order_violation_delta"),
            maturity_summary.get("release_readiness_max_ci_workflow_order_violation_delta"),
        ),
        "test_coverage_regression_count": _coalesce(
            release_context.get("test_coverage_regression_count"),
            maturity_summary.get("release_readiness_test_coverage_regression_count"),
        ),
        "test_coverage_status_changed_count": _coalesce(
            release_context.get("test_coverage_status_changed_count"),
            maturity_summary.get("release_readiness_test_coverage_status_changed_count"),
        ),
        "max_abs_test_coverage_percent_delta": _coalesce(
            release_context.get("max_abs_test_coverage_percent_delta"),
            maturity_summary.get("release_readiness_max_test_coverage_percent_delta"),
        ),
        "max_abs_test_coverage_gap_delta": _coalesce(
            release_context.get("max_abs_test_coverage_gap_delta"),
            maturity_summary.get("release_readiness_max_test_coverage_gap_delta"),
        ),
        "benchmark_history_regression_count": _coalesce(
            release_context.get("benchmark_history_regression_count"),
            maturity_summary.get("release_readiness_benchmark_history_regression_count"),
        ),
        "benchmark_history_status_changed_count": _coalesce(
            release_context.get("benchmark_history_status_changed_count"),
            maturity_summary.get("release_readiness_benchmark_history_status_changed_count"),
        ),
        "benchmark_history_boundary_changed_count": _coalesce(
            release_context.get("benchmark_history_boundary_changed_count"),
            maturity_summary.get("release_readiness_benchmark_history_boundary_changed_count"),
        ),
        "benchmark_history_suite_design_non_comparison_ready_delta_count": suite_design_delta_count,
        "benchmark_history_suite_design_non_comparison_ready_regression_count": suite_design_regression_count,
        "benchmark_history_design_comparison_changed_delta_count": design_change_delta_count,
        "benchmark_history_readiness_requirement_status_changed_count": requirement_status_changed_count,
        "max_abs_benchmark_history_readiness_requirement_exit_code_delta": requirement_exit_code_delta,
        "benchmark_history_readiness_requirement_failed_reason_added_count": requirement_reason_added_count,
        "benchmark_history_readiness_requirement_failed_reason_removed_count": requirement_reason_removed_count,
        "benchmark_history_readiness_requirement_failed_reason_added": _string_list(requirement_reason_added),
        "benchmark_history_readiness_requirement_failed_reason_removed": _string_list(requirement_reason_removed),
        "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": requirement_reason_recovery_delta_count,
        "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": requirement_reason_mixed_delta_count,
        "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": _dict(requirement_reason_drift_status_counts),
        "max_abs_benchmark_history_case_regression_delta": _coalesce(
            release_context.get("max_abs_benchmark_history_case_regression_delta"),
            maturity_summary.get("release_readiness_max_benchmark_history_case_regression_delta"),
        ),
        "max_abs_benchmark_history_generation_flag_regression_delta": _coalesce(
            release_context.get("max_abs_benchmark_history_generation_flag_regression_delta"),
            maturity_summary.get("release_readiness_max_benchmark_history_generation_flag_regression_delta"),
        ),
        "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta": max_suite_design_delta,
        "max_abs_benchmark_history_design_comparison_changed_entries_delta": max_design_change_delta,
    }


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


__all__ = ["build_maturity_narrative_release_summary"]
