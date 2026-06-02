from __future__ import annotations

from typing import Any


def build_release_readiness_context(registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {
            "available": False,
            "trend_status": None,
            "comparison_counts": {},
            "delta_count": None,
            "run_count": None,
            "regressed_count": None,
            "improved_count": None,
            "panel_changed_count": None,
            "changed_panel_delta_count": None,
            "max_abs_status_delta": None,
            "ci_workflow_regression_count": None,
            "ci_workflow_order_regression_count": None,
            "ci_workflow_status_changed_count": None,
            "ci_workflow_regression_reasons": [],
            "ci_workflow_regression_reason_counts": {},
            "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count": None,
            "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count": None,
            "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count": None,
            "ci_workflow_archived_path_portability_check_ready_regression_count": None,
            "ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count": None,
            "max_abs_ci_workflow_failed_check_delta": None,
            "max_abs_ci_workflow_order_violation_delta": None,
            "test_coverage_regression_count": None,
            "test_coverage_status_changed_count": None,
            "max_abs_test_coverage_percent_delta": None,
            "max_abs_test_coverage_gap_delta": None,
            "benchmark_history_regression_count": None,
            "benchmark_history_status_changed_count": None,
            "benchmark_history_boundary_changed_count": None,
            "benchmark_history_suite_design_non_comparison_ready_delta_count": None,
            "benchmark_history_suite_design_non_comparison_ready_regression_count": None,
            "benchmark_history_design_comparison_changed_delta_count": None,
            "benchmark_history_readiness_requirement_status_changed_count": None,
            "benchmark_history_readiness_requirement_failed_reason_added_count": None,
            "benchmark_history_readiness_requirement_failed_reason_removed_count": None,
            "benchmark_history_readiness_requirement_failed_reason_added": [],
            "benchmark_history_readiness_requirement_failed_reason_removed": [],
            "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": None,
            "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": None,
            "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": {},
            "max_abs_benchmark_history_case_regression_delta": None,
            "max_abs_benchmark_history_generation_flag_regression_delta": None,
            "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta": None,
            "max_abs_benchmark_history_design_comparison_changed_entries_delta": None,
            "max_abs_benchmark_history_readiness_requirement_exit_code_delta": None,
        }
    counts = registry.get("release_readiness_comparison_counts")
    delta_summary = _dict(registry.get("release_readiness_delta_summary"))
    context = {
        "available": bool(delta_summary) or isinstance(counts, dict),
        "comparison_counts": counts if isinstance(counts, dict) else {},
        "delta_count": delta_summary.get("delta_count"),
        "run_count": delta_summary.get("run_count"),
        "regressed_count": delta_summary.get("regressed_count"),
        "improved_count": delta_summary.get("improved_count"),
        "panel_changed_count": delta_summary.get("panel_changed_count"),
        "same_count": delta_summary.get("same_count"),
        "changed_panel_delta_count": delta_summary.get("changed_panel_delta_count"),
        "max_abs_status_delta": delta_summary.get("max_abs_status_delta"),
        "ci_workflow_regression_count": delta_summary.get("ci_workflow_regression_count"),
        "ci_workflow_order_regression_count": delta_summary.get("ci_workflow_order_regression_count"),
        "ci_workflow_status_changed_count": delta_summary.get("ci_workflow_status_changed_count"),
        "ci_workflow_regression_reasons": _string_list(delta_summary.get("ci_workflow_regression_reasons")),
        "ci_workflow_regression_reason_counts": _dict(delta_summary.get("ci_workflow_regression_reason_counts")),
        "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count": delta_summary.get(
            "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count"
        ),
        "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count": delta_summary.get(
            "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count"
        ),
        "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count": delta_summary.get(
            "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count"
        ),
        "ci_workflow_archived_path_portability_check_ready_regression_count": delta_summary.get(
            "ci_workflow_archived_path_portability_check_ready_regression_count"
        ),
        "ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count": delta_summary.get(
            "ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count"
        ),
        "max_abs_ci_workflow_failed_check_delta": delta_summary.get("max_abs_ci_workflow_failed_check_delta"),
        "max_abs_ci_workflow_order_violation_delta": delta_summary.get("max_abs_ci_workflow_order_violation_delta"),
        "test_coverage_regression_count": delta_summary.get("test_coverage_regression_count"),
        "test_coverage_status_changed_count": delta_summary.get("test_coverage_status_changed_count"),
        "max_abs_test_coverage_percent_delta": delta_summary.get("max_abs_test_coverage_percent_delta"),
        "max_abs_test_coverage_gap_delta": delta_summary.get("max_abs_test_coverage_gap_delta"),
        "benchmark_history_regression_count": delta_summary.get("benchmark_history_regression_count"),
        "benchmark_history_status_changed_count": delta_summary.get("benchmark_history_status_changed_count"),
        "benchmark_history_boundary_changed_count": delta_summary.get("benchmark_history_boundary_changed_count"),
        "benchmark_history_suite_design_non_comparison_ready_delta_count": delta_summary.get(
            "benchmark_history_suite_design_non_comparison_ready_delta_count"
        ),
        "benchmark_history_suite_design_non_comparison_ready_regression_count": delta_summary.get(
            "benchmark_history_suite_design_non_comparison_ready_regression_count"
        ),
        "benchmark_history_design_comparison_changed_delta_count": delta_summary.get("benchmark_history_design_comparison_changed_delta_count"),
        "benchmark_history_readiness_requirement_status_changed_count": delta_summary.get(
            "benchmark_history_readiness_requirement_status_changed_count"
        ),
        "benchmark_history_readiness_requirement_failed_reason_added_count": delta_summary.get(
            "benchmark_history_readiness_requirement_failed_reason_added_count"
        ),
        "benchmark_history_readiness_requirement_failed_reason_removed_count": delta_summary.get(
            "benchmark_history_readiness_requirement_failed_reason_removed_count"
        ),
        "benchmark_history_readiness_requirement_failed_reason_added": _string_list(
            delta_summary.get("benchmark_history_readiness_requirement_failed_reason_added")
        ),
        "benchmark_history_readiness_requirement_failed_reason_removed": _string_list(
            delta_summary.get("benchmark_history_readiness_requirement_failed_reason_removed")
        ),
        "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": delta_summary.get(
            "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"
        ),
        "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": delta_summary.get(
            "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"
        ),
        "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": _dict(
            delta_summary.get("benchmark_history_readiness_requirement_failed_reason_drift_status_counts")
        ),
        "max_abs_benchmark_history_case_regression_delta": delta_summary.get("max_abs_benchmark_history_case_regression_delta"),
        "max_abs_benchmark_history_generation_flag_regression_delta": delta_summary.get(
            "max_abs_benchmark_history_generation_flag_regression_delta"
        ),
        "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta": delta_summary.get(
            "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta"
        ),
        "max_abs_benchmark_history_design_comparison_changed_entries_delta": delta_summary.get(
            "max_abs_benchmark_history_design_comparison_changed_entries_delta"
        ),
        "max_abs_benchmark_history_readiness_requirement_exit_code_delta": delta_summary.get(
            "max_abs_benchmark_history_readiness_requirement_exit_code_delta"
        ),
    }
    context["trend_status"] = release_readiness_trend_status(context)
    return context


def release_readiness_trend_status(context: dict[str, Any]) -> str | None:
    if not context.get("available"):
        return None
    if int(context.get("test_coverage_regression_count") or 0) > 0:
        return "coverage-regressed"
    if int(context.get("benchmark_history_readiness_requirement_status_changed_count") or 0) > 0:
        return "benchmark-regressed"
    if int(context.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count") or 0) > 0:
        return "benchmark-regressed"
    if int(context.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) > 0:
        return "benchmark-regressed"
    if int(context.get("benchmark_history_suite_design_non_comparison_ready_regression_count") or 0) > 0:
        return "benchmark-regressed"
    if int(context.get("benchmark_history_regression_count") or 0) > 0:
        return "benchmark-regressed"
    if int(context.get("regressed_count") or 0) > 0:
        return "regressed"
    if int(context.get("ci_workflow_regression_count") or 0) > 0 or int(context.get("ci_workflow_order_regression_count") or 0) > 0:
        return "ci-regressed"
    if int(context.get("improved_count") or 0) > 0:
        return "improved"
    if int(context.get("panel_changed_count") or 0) > 0 or int(context.get("changed_panel_delta_count") or 0) > 0:
        return "panel-changed"
    if int(context.get("delta_count") or 0) > 0:
        return "stable"
    counts = _dict(context.get("comparison_counts"))
    if counts:
        return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))
    return None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


__all__ = [
    "build_release_readiness_context",
    "release_readiness_trend_status",
]
