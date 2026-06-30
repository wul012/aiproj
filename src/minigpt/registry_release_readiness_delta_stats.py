from __future__ import annotations

from typing import Any

from minigpt.report_utils import CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON


CI_READY_REGRESSION_REASON_FIELDS = {
    "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regressed": "tiny_scorecard_plan_digest_gate_not_ready",
    "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regressed": "boundary_gate_check_not_ready",
    "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed": "boundary_gate_plan_check_not_ready",
    "ci_workflow_archived_path_portability_check_ready_regressed": (
        CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON
    ),
    "ci_workflow_release_readiness_drift_contract_smoke_ready_regressed": "drift_contract_smoke_not_ready",
}


def release_readiness_delta_leaderboard(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda item: (
            _release_readiness_delta_priority(item),
            -int(bool(item.get("ci_workflow_status_changed"))),
            -int(bool(item.get("ci_workflow_regression_reasons"))),
            -abs(_as_optional_float(item.get("ci_workflow_failed_check_delta")) or 0.0),
            -abs(_as_optional_float(item.get("ci_workflow_order_violation_delta")) or 0.0),
            -abs(_as_optional_float(item.get("test_coverage_gap_delta")) or 0.0),
            -abs(_as_optional_float(item.get("test_coverage_percent_delta")) or 0.0),
            -abs(_as_optional_float(item.get("benchmark_history_case_regression_delta")) or 0.0),
            -abs(_as_optional_float(item.get("benchmark_history_generation_flag_regression_delta")) or 0.0),
            -abs(_as_optional_float(item.get("benchmark_history_suite_design_non_comparison_ready_entries_delta")) or 0.0),
            -abs(_as_optional_float(item.get("benchmark_history_design_comparison_changed_entries_delta")) or 0.0),
            -int(bool(item.get("benchmark_history_readiness_requirement_status_changed"))),
            -int(item.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0),
            -int(item.get("benchmark_history_readiness_requirement_failed_reason_drift_status") == "mixed"),
            -abs(_as_optional_float(item.get("benchmark_history_readiness_requirement_exit_code_delta")) or 0.0),
            -abs(_as_optional_float(item.get("benchmark_history_status_delta")) or 0.0),
            -abs(_as_optional_float(item.get("status_delta")) or 0.0),
            -int(item.get("changed_panel_count") or 0),
            str(item.get("run_name") or ""),
            str(item.get("compared_release") or ""),
        ),
    )
    return ordered[:limit]


def release_readiness_delta_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    run_names = {str(row.get("run_name")) for row in rows if row.get("run_name")}
    result_counts = _counts(row.get("delta_status") or "missing" for row in rows)
    status_deltas = [abs(value) for value in (_as_optional_float(row.get("status_delta")) for row in rows) if value is not None]
    ci_failed_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("ci_workflow_failed_check_delta")) for row in rows)
        if value is not None
    ]
    ci_order_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("ci_workflow_order_violation_delta")) for row in rows)
        if value is not None
    ]
    coverage_percent_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("test_coverage_percent_delta")) for row in rows)
        if value is not None
    ]
    coverage_gap_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("test_coverage_gap_delta")) for row in rows)
        if value is not None
    ]
    benchmark_case_regression_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("benchmark_history_case_regression_delta")) for row in rows)
        if value is not None
    ]
    benchmark_flag_regression_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("benchmark_history_generation_flag_regression_delta")) for row in rows)
        if value is not None
    ]
    benchmark_suite_design_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("benchmark_history_suite_design_non_comparison_ready_entries_delta")) for row in rows)
        if value is not None
    ]
    benchmark_design_change_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("benchmark_history_design_comparison_changed_entries_delta")) for row in rows)
        if value is not None
    ]
    benchmark_requirement_exit_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("benchmark_history_readiness_requirement_exit_code_delta")) for row in rows)
        if value is not None
    ]
    return {
        "delta_count": len(rows),
        "run_count": len(run_names),
        "regressed_count": result_counts.get("regressed", 0),
        "improved_count": result_counts.get("improved", 0),
        "panel_changed_count": result_counts.get("panel-changed", 0),
        "same_count": result_counts.get("same", 0),
        "changed_panel_delta_count": sum(1 for row in rows if int(row.get("changed_panel_count") or 0) > 0),
        "ci_workflow_regression_count": sum(1 for row in rows if _is_ci_workflow_regression_row(row)),
        "ci_workflow_order_regression_count": sum(1 for row in rows if _is_ci_workflow_order_regression_row(row)),
        "ci_workflow_status_changed_count": sum(1 for row in rows if bool(row.get("ci_workflow_status_changed"))),
        "ci_workflow_regression_reasons": _unique_strings(
            reason for row in rows for reason in _as_str_list(row.get("ci_workflow_regression_reasons"))
        ),
        "ci_workflow_regression_reason_counts": _counts(
            reason for row in rows for reason in _as_str_list(row.get("ci_workflow_regression_reasons"))
        ),
        "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count": _true_count(
            rows,
            "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regressed",
        ),
        "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count": _true_count(
            rows,
            "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regressed",
        ),
        "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count": _true_count(
            rows,
            "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed",
        ),
        "ci_workflow_archived_path_portability_check_ready_regression_count": _true_count(
            rows,
            "ci_workflow_archived_path_portability_check_ready_regressed",
        ),
        "ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count": _true_count(
            rows,
            "ci_workflow_release_readiness_drift_contract_smoke_ready_regressed",
        ),
        "max_abs_ci_workflow_failed_check_delta": _int_if_whole(max(ci_failed_deltas)) if ci_failed_deltas else None,
        "max_abs_ci_workflow_order_violation_delta": _int_if_whole(max(ci_order_deltas)) if ci_order_deltas else None,
        "test_coverage_regression_count": sum(1 for row in rows if _is_test_coverage_regression_row(row)),
        "test_coverage_status_changed_count": sum(1 for row in rows if bool(row.get("test_coverage_status_changed"))),
        "max_abs_test_coverage_percent_delta": _int_if_whole(max(coverage_percent_deltas)) if coverage_percent_deltas else None,
        "max_abs_test_coverage_gap_delta": _int_if_whole(max(coverage_gap_deltas)) if coverage_gap_deltas else None,
        "benchmark_history_regression_count": sum(1 for row in rows if _is_benchmark_history_regression_row(row)),
        "benchmark_history_status_changed_count": sum(1 for row in rows if bool(row.get("benchmark_history_status_changed"))),
        "benchmark_history_boundary_changed_count": sum(1 for row in rows if bool(row.get("benchmark_history_latest_boundary_changed"))),
        "benchmark_history_suite_design_non_comparison_ready_delta_count": sum(
            1
            for row in rows
            if row.get("benchmark_history_suite_design_non_comparison_ready_entries_delta") not in {None, 0, 0.0}
        ),
        "benchmark_history_suite_design_non_comparison_ready_regression_count": sum(
            1
            for row in rows
            if _positive_number(row.get("benchmark_history_suite_design_non_comparison_ready_entries_delta"))
        ),
        "benchmark_history_design_comparison_changed_delta_count": sum(
            1 for row in rows if row.get("benchmark_history_design_comparison_changed_entries_delta") not in {None, 0, 0.0}
        ),
        "benchmark_history_readiness_requirement_status_changed_count": sum(
            1 for row in rows if bool(row.get("benchmark_history_readiness_requirement_status_changed"))
        ),
        "benchmark_history_readiness_requirement_failed_reason_added_count": sum(
            int(row.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) for row in rows
        ),
        "benchmark_history_readiness_requirement_failed_reason_removed_count": sum(
            int(row.get("benchmark_history_readiness_requirement_failed_reason_removed_count") or 0) for row in rows
        ),
        "benchmark_history_readiness_requirement_failed_reason_added": _unique_strings(
            reason
            for row in rows
            for reason in _as_str_list(row.get("benchmark_history_readiness_requirement_failed_reason_added"))
        ),
        "benchmark_history_readiness_requirement_failed_reason_removed": _unique_strings(
            reason
            for row in rows
            for reason in _as_str_list(row.get("benchmark_history_readiness_requirement_failed_reason_removed"))
        ),
        "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": sum(
            1 for row in rows if row.get("benchmark_history_readiness_requirement_failed_reason_drift_status") == "recovered"
        ),
        "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": sum(
            1 for row in rows if row.get("benchmark_history_readiness_requirement_failed_reason_drift_status") == "mixed"
        ),
        "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": _counts(
            row.get("benchmark_history_readiness_requirement_failed_reason_drift_status") or "stable" for row in rows
        ),
        "max_abs_benchmark_history_case_regression_delta": _int_if_whole(max(benchmark_case_regression_deltas))
        if benchmark_case_regression_deltas
        else None,
        "max_abs_benchmark_history_generation_flag_regression_delta": _int_if_whole(max(benchmark_flag_regression_deltas))
        if benchmark_flag_regression_deltas
        else None,
        "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta": _int_if_whole(max(benchmark_suite_design_deltas))
        if benchmark_suite_design_deltas
        else None,
        "max_abs_benchmark_history_design_comparison_changed_entries_delta": _int_if_whole(max(benchmark_design_change_deltas))
        if benchmark_design_change_deltas
        else None,
        "max_abs_benchmark_history_readiness_requirement_exit_code_delta": _int_if_whole(max(benchmark_requirement_exit_deltas))
        if benchmark_requirement_exit_deltas
        else None,
        "max_abs_status_delta": _int_if_whole(max(status_deltas)) if status_deltas else None,
    }


def _release_readiness_delta_priority(row: dict[str, Any]) -> int:
    if _is_test_coverage_regression_row(row):
        return 0
    if _is_benchmark_history_regression_row(row):
        return 1
    if _is_ci_workflow_regression_row(row):
        return 2
    status_priority = {"regressed": 3, "improved": 4, "panel-changed": 5, "same": 6}
    return status_priority.get(str(row.get("delta_status") or ""), 6)


def _is_ci_workflow_regression_row(row: dict[str, Any]) -> bool:
    if _as_str_list(row.get("ci_workflow_regression_reasons")):
        return True
    failed_delta = _as_optional_float(row.get("ci_workflow_failed_check_delta"))
    if failed_delta is not None and failed_delta > 0:
        return True
    if _is_ci_workflow_order_regression_row(row):
        return True
    if not row.get("ci_workflow_status_changed"):
        return False
    return _ci_status_score(row.get("compared_ci_workflow_status")) < _ci_status_score(row.get("baseline_ci_workflow_status"))


def _ci_workflow_regression_reasons(delta: dict[str, Any]) -> list[str]:
    direct = _as_str_list(delta.get("ci_workflow_regression_reasons"))
    if direct:
        return direct
    reasons: list[str] = []
    failed_delta = _as_optional_float(delta.get("ci_workflow_failed_check_delta"))
    if failed_delta is not None and failed_delta > 0:
        reasons.append("failed_checks_increased")
    order_delta = _as_optional_float(delta.get("ci_workflow_order_violation_delta"))
    if order_delta is not None and order_delta > 0:
        reasons.append("order_violations_increased")
    for field, reason in CI_READY_REGRESSION_REASON_FIELDS.items():
        if delta.get(field):
            reasons.append(reason)
    if delta.get("ci_workflow_status_changed"):
        if _ci_status_score(delta.get("compared_ci_workflow_status")) < _ci_status_score(delta.get("baseline_ci_workflow_status")):
            reasons.append("workflow_status_downgraded")
    return reasons


def _is_ci_workflow_order_regression_row(row: dict[str, Any]) -> bool:
    order_delta = _as_optional_float(row.get("ci_workflow_order_violation_delta"))
    return order_delta is not None and order_delta > 0


def _is_test_coverage_regression_row(row: dict[str, Any]) -> bool:
    percent_delta = _as_optional_float(row.get("test_coverage_percent_delta"))
    if percent_delta is not None and percent_delta < 0:
        return True
    gap_delta = _as_optional_float(row.get("test_coverage_gap_delta"))
    if gap_delta is not None and gap_delta > 0:
        return True
    if not row.get("test_coverage_status_changed"):
        return False
    return _coverage_status_score(row.get("compared_test_coverage_status")) < _coverage_status_score(row.get("baseline_test_coverage_status"))


def _is_benchmark_history_regression_row(row: dict[str, Any]) -> bool:
    status_delta = _as_optional_float(row.get("benchmark_history_status_delta"))
    if status_delta is not None and status_delta < 0:
        return True
    if int(row.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) > 0:
        return True
    ready_delta = _as_optional_float(row.get("benchmark_history_ready_delta"))
    if ready_delta is not None and ready_delta < 0:
        return True
    for key in [
        "benchmark_history_review_delta",
        "benchmark_history_blocked_delta",
        "benchmark_history_case_regression_delta",
        "benchmark_history_generation_flag_regression_delta",
        "benchmark_history_suite_design_non_comparison_ready_entries_delta",
        "benchmark_history_readiness_requirement_exit_code_delta",
    ]:
        value = _as_optional_float(row.get(key))
        if value is not None and value > 0:
            return True
    if row.get("benchmark_history_readiness_requirement_status_changed"):
        return _benchmark_requirement_status_score(
            row.get("compared_benchmark_history_readiness_requirement_status")
        ) < _benchmark_requirement_status_score(row.get("baseline_benchmark_history_readiness_requirement_status"))
    return False


def _positive_number(value: Any) -> bool:
    number = _as_optional_float(value)
    return number is not None and number > 0


def _ci_status_score(value: Any) -> int:
    return {"missing": 0, "fail": 0, "warn": 1, "review": 1, "pass": 2}.get(str(value or "missing"), 0)


def _coverage_status_score(value: Any) -> int:
    return {"missing": 0, "fail": 0, "warn": 1, "review": 1, "pass": 2}.get(str(value or "missing"), 0)


def _benchmark_requirement_status_score(value: Any) -> int:
    return {"missing": 0, "fail": 0, "pass": 2}.get(str(value or "missing"), 0)


def _as_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    number = _as_optional_float(value)
    return int(number) if number is not None else None


def _int_if_whole(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _reason_additions(baseline: Any, compared: Any) -> list[str]:
    baseline_reasons = set(_as_str_list(baseline))
    return [reason for reason in _as_str_list(compared) if reason not in baseline_reasons]


def _reason_removals(baseline: Any, compared: Any) -> list[str]:
    compared_reasons = set(_as_str_list(compared))
    return [reason for reason in _as_str_list(baseline) if reason not in compared_reasons]


def _reason_drift_status(added: list[str], removed: list[str]) -> str:
    if added and removed:
        return "mixed"
    if added:
        return "regressed"
    if removed:
        return "recovered"
    return "stable"


def _unique_strings(values: Any) -> list[str]:
    items: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in items:
            items.append(text)
    return items


def _counts(values: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        key = str(value)
        result[key] = result.get(key, 0) + 1
    return result


def _true_count(rows: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if bool(row.get(key)))


__all__ = [
    "CI_READY_REGRESSION_REASON_FIELDS",
    "release_readiness_delta_leaderboard",
    "release_readiness_delta_summary",
]
