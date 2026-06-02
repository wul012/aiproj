from __future__ import annotations

from typing import Any

from minigpt.report_utils import CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON


CI_STATUS_ORDER = {
    "missing": 0,
    "fail": 0,
    "warn": 1,
    "review": 1,
    "pass": 2,
}

COVERAGE_STATUS_ORDER = {
    "missing": 0,
    "fail": 0,
    "warn": 1,
    "review": 1,
    "pass": 2,
}

BENCHMARK_HISTORY_STATUS_ORDER = {
    "missing": 0,
    "fail": 0,
    "blocked": 0,
    "warn": 1,
    "review": 1,
    "pass": 2,
    "ready": 2,
}


def is_ci_workflow_regression(delta: dict[str, Any]) -> bool:
    return bool(ci_workflow_regression_reasons(delta))


def ci_workflow_regression_reasons(delta: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    failed_delta = delta.get("ci_workflow_failed_check_delta")
    if isinstance(failed_delta, (int, float)) and failed_delta > 0:
        reasons.append("failed_checks_increased")
    if is_ci_workflow_order_regression(delta):
        reasons.append("order_violations_increased")
    if delta.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready_regressed"):
        reasons.append("tiny_scorecard_plan_digest_gate_not_ready")
    if delta.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regressed"):
        reasons.append("boundary_gate_check_not_ready")
    if delta.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed"):
        reasons.append("boundary_gate_plan_check_not_ready")
    if delta.get("ci_workflow_archived_path_portability_check_ready_regressed"):
        reasons.append(CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON)
    if delta.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_regressed"):
        reasons.append("receipt_failure_smoke_plan_check_not_ready")
    if delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regressed"):
        reasons.append("drift_contract_smoke_not_ready")
    if delta.get("ci_workflow_status_changed"):
        if ci_status_score(delta.get("compared_ci_workflow_status")) < ci_status_score(delta.get("baseline_ci_workflow_status")):
            reasons.append("workflow_status_downgraded")
    return reasons


def is_ci_workflow_order_regression(delta: dict[str, Any]) -> bool:
    order_delta = delta.get("ci_workflow_order_violation_delta")
    return isinstance(order_delta, (int, float)) and order_delta > 0


def is_test_coverage_regression(delta: dict[str, Any]) -> bool:
    percent_delta = delta.get("test_coverage_percent_delta")
    if isinstance(percent_delta, (int, float)) and percent_delta < 0:
        return True
    gap_delta = delta.get("test_coverage_gap_delta")
    if isinstance(gap_delta, (int, float)) and gap_delta > 0:
        return True
    if delta.get("test_coverage_status_changed"):
        return coverage_status_score(delta.get("compared_test_coverage_status")) < coverage_status_score(
            delta.get("baseline_test_coverage_status")
        )
    return False


def has_benchmark_history_delta(delta: dict[str, Any]) -> bool:
    if delta.get("benchmark_history_status_changed"):
        return True
    if delta.get("benchmark_history_model_quality_claim_changed") or delta.get("benchmark_history_latest_boundary_changed"):
        return True
    if delta.get("benchmark_history_readiness_requirement_status_changed"):
        return True
    if int(delta.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) > 0:
        return True
    if int(delta.get("benchmark_history_readiness_requirement_failed_reason_removed_count") or 0) > 0:
        return True
    keys = [
        "benchmark_history_entry_delta",
        "benchmark_history_ready_delta",
        "benchmark_history_review_delta",
        "benchmark_history_blocked_delta",
        "benchmark_history_case_regression_delta",
        "benchmark_history_generation_flag_regression_delta",
        "benchmark_history_suite_design_non_comparison_ready_entries_delta",
        "benchmark_history_design_comparison_changed_entries_delta",
        "benchmark_history_readiness_requirement_exit_code_delta",
    ]
    return any(delta.get(key) not in {None, 0, 0.0} for key in keys)


def is_benchmark_history_regression(delta: dict[str, Any]) -> bool:
    if int(delta.get("benchmark_history_status_delta") or 0) < 0:
        return True
    if (
        delta.get("compared_benchmark_history_readiness_requirement_status") == "fail"
        and delta.get("baseline_benchmark_history_readiness_requirement_status") != "fail"
    ):
        return True
    if int(delta.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) > 0:
        return True
    compared_requirement_exit = delta.get("benchmark_history_readiness_requirement_exit_code_delta")
    if isinstance(compared_requirement_exit, (int, float)) and compared_requirement_exit > 0:
        return True
    for key in [
        "benchmark_history_review_delta",
        "benchmark_history_blocked_delta",
        "benchmark_history_case_regression_delta",
        "benchmark_history_generation_flag_regression_delta",
        "benchmark_history_suite_design_non_comparison_ready_entries_delta",
        "benchmark_history_readiness_requirement_exit_code_delta",
    ]:
        value = delta.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return True
    if delta.get("benchmark_history_readiness_requirement_status_changed"):
        return requirement_status_score(
            delta.get("compared_benchmark_history_readiness_requirement_status")
        ) < requirement_status_score(delta.get("baseline_benchmark_history_readiness_requirement_status"))
    ready_delta = delta.get("benchmark_history_ready_delta")
    return isinstance(ready_delta, (int, float)) and ready_delta < 0


def positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and value > 0


def ci_status_score(value: Any) -> int:
    return CI_STATUS_ORDER.get(str(value or "missing"), 0)


def coverage_status_score(value: Any) -> int:
    return COVERAGE_STATUS_ORDER.get(str(value or "missing"), 0)


def benchmark_history_status_score(value: Any) -> int:
    return BENCHMARK_HISTORY_STATUS_ORDER.get(str(value or "missing"), 0)


def requirement_status_score(value: Any) -> int:
    return {"pass": 2, "warn": 1, "review": 1, "fail": 0, "missing": 0}.get(str(value or "missing"), 0)


def max_abs_delta(deltas: list[dict[str, Any]], key: str) -> float | int | None:
    values = [abs(float(delta[key])) for delta in deltas if isinstance(delta.get(key), (int, float))]
    if not values:
        return None
    value = max(values)
    return int(value) if value.is_integer() else round(value, 4)


__all__ = [
    "benchmark_history_status_score",
    "ci_workflow_regression_reasons",
    "has_benchmark_history_delta",
    "is_benchmark_history_regression",
    "is_ci_workflow_order_regression",
    "is_ci_workflow_regression",
    "is_test_coverage_regression",
    "max_abs_delta",
    "positive_number",
]
