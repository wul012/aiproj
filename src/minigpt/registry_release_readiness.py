from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def collect_release_readiness_delta_rows(run_dirs: list[str | Path], names: list[str] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, run_dir in enumerate(run_dirs):
        root = Path(run_dir)
        run_name = str(names[index]) if names is not None else root.name
        report = _read_release_readiness_comparison(root)
        if not isinstance(report, dict):
            continue
        report_path = _as_str(report.get("release_readiness_comparison_path"))
        for delta in report.get("deltas", []):
            if not isinstance(delta, dict):
                continue
            changed_panels = _as_str_list(delta.get("changed_panels"))
            baseline_failed_reasons = _as_str_list(delta.get("baseline_benchmark_history_readiness_requirement_failed_reasons"))
            compared_failed_reasons = _as_str_list(delta.get("compared_benchmark_history_readiness_requirement_failed_reasons"))
            added_failed_reasons = _as_str_list(delta.get("benchmark_history_readiness_requirement_failed_reason_added"))
            removed_failed_reasons = _as_str_list(delta.get("benchmark_history_readiness_requirement_failed_reason_removed"))
            if not added_failed_reasons:
                added_failed_reasons = _reason_additions(baseline_failed_reasons, compared_failed_reasons)
            if not removed_failed_reasons:
                removed_failed_reasons = _reason_removals(baseline_failed_reasons, compared_failed_reasons)
            reason_drift_status = _as_str(delta.get("benchmark_history_readiness_requirement_failed_reason_drift_status")) or _reason_drift_status(
                added_failed_reasons,
                removed_failed_reasons,
            )
            rows.append(
                {
                    "run_name": run_name,
                    "run_path": str(root),
                    "baseline_release": _as_str(delta.get("baseline_release")),
                    "compared_release": _as_str(delta.get("compared_release")),
                    "baseline_status": _as_str(delta.get("baseline_status")),
                    "compared_status": _as_str(delta.get("compared_status")),
                    "status_delta": _int_if_whole(_as_optional_float(delta.get("status_delta"))),
                    "delta_status": _as_str(delta.get("delta_status")) or "same",
                    "baseline_ci_workflow_status": _as_str(delta.get("baseline_ci_workflow_status")),
                    "compared_ci_workflow_status": _as_str(delta.get("compared_ci_workflow_status")),
                    "ci_workflow_failed_check_delta": _int_if_whole(_as_optional_float(delta.get("ci_workflow_failed_check_delta"))),
                    "ci_workflow_required_order_delta": _int_if_whole(_as_optional_float(delta.get("ci_workflow_required_order_delta"))),
                    "ci_workflow_order_violation_delta": _int_if_whole(_as_optional_float(delta.get("ci_workflow_order_violation_delta"))),
                    "ci_workflow_status_changed": bool(delta.get("ci_workflow_status_changed")),
                    "baseline_test_coverage_status": _as_str(delta.get("baseline_test_coverage_status")),
                    "compared_test_coverage_status": _as_str(delta.get("compared_test_coverage_status")),
                    "test_coverage_percent_delta": _int_if_whole(_as_optional_float(delta.get("test_coverage_percent_delta"))),
                    "test_coverage_gap_delta": _int_if_whole(_as_optional_float(delta.get("test_coverage_gap_delta"))),
                    "test_coverage_status_changed": bool(delta.get("test_coverage_status_changed")),
                    "baseline_benchmark_history_status": _as_str(delta.get("baseline_benchmark_history_status")),
                    "compared_benchmark_history_status": _as_str(delta.get("compared_benchmark_history_status")),
                    "benchmark_history_status_delta": _int_if_whole(_as_optional_float(delta.get("benchmark_history_status_delta"))),
                    "benchmark_history_status_changed": bool(delta.get("benchmark_history_status_changed")),
                    "benchmark_history_ready_delta": _int_if_whole(_as_optional_float(delta.get("benchmark_history_ready_delta"))),
                    "benchmark_history_review_delta": _int_if_whole(_as_optional_float(delta.get("benchmark_history_review_delta"))),
                    "benchmark_history_blocked_delta": _int_if_whole(_as_optional_float(delta.get("benchmark_history_blocked_delta"))),
                    "benchmark_history_case_regression_delta": _int_if_whole(_as_optional_float(delta.get("benchmark_history_case_regression_delta"))),
                    "benchmark_history_generation_flag_regression_delta": _int_if_whole(
                        _as_optional_float(delta.get("benchmark_history_generation_flag_regression_delta"))
                    ),
                    "baseline_benchmark_history_readiness_requirement_status": _as_str(
                        delta.get("baseline_benchmark_history_readiness_requirement_status")
                    ),
                    "compared_benchmark_history_readiness_requirement_status": _as_str(
                        delta.get("compared_benchmark_history_readiness_requirement_status")
                    ),
                    "benchmark_history_readiness_requirement_status_changed": bool(
                        delta.get("benchmark_history_readiness_requirement_status_changed")
                    ),
                    "benchmark_history_readiness_requirement_exit_code_delta": _int_if_whole(
                        _as_optional_float(delta.get("benchmark_history_readiness_requirement_exit_code_delta"))
                    ),
                    "baseline_benchmark_history_readiness_requirement_failed_reasons": baseline_failed_reasons,
                    "compared_benchmark_history_readiness_requirement_failed_reasons": compared_failed_reasons,
                    "benchmark_history_readiness_requirement_failed_reason_added_count": _as_int(
                        delta.get("benchmark_history_readiness_requirement_failed_reason_added_count")
                    )
                    if delta.get("benchmark_history_readiness_requirement_failed_reason_added_count") is not None
                    else len(added_failed_reasons),
                    "benchmark_history_readiness_requirement_failed_reason_removed_count": _as_int(
                        delta.get("benchmark_history_readiness_requirement_failed_reason_removed_count")
                    )
                    if delta.get("benchmark_history_readiness_requirement_failed_reason_removed_count") is not None
                    else len(removed_failed_reasons),
                    "benchmark_history_readiness_requirement_failed_reason_added": added_failed_reasons,
                    "benchmark_history_readiness_requirement_failed_reason_removed": removed_failed_reasons,
                    "benchmark_history_readiness_requirement_failed_reason_drift_status": reason_drift_status,
                    "benchmark_history_model_quality_claim_changed": bool(delta.get("benchmark_history_model_quality_claim_changed")),
                    "benchmark_history_latest_boundary_changed": bool(delta.get("benchmark_history_latest_boundary_changed")),
                    "baseline_benchmark_history_boundary": _as_str(delta.get("baseline_benchmark_history_boundary")),
                    "compared_benchmark_history_boundary": _as_str(delta.get("compared_benchmark_history_boundary")),
                    "audit_score_delta": _int_if_whole(_as_optional_float(delta.get("audit_score_delta"))),
                    "missing_artifact_delta": _int_if_whole(_as_optional_float(delta.get("missing_artifact_delta"))),
                    "fail_panel_delta": _int_if_whole(_as_optional_float(delta.get("fail_panel_delta"))),
                    "warn_panel_delta": _int_if_whole(_as_optional_float(delta.get("warn_panel_delta"))),
                    "changed_panel_count": len(changed_panels),
                    "changed_panels": changed_panels,
                    "explanation": _as_str(delta.get("explanation")),
                    "report_path": report_path,
                }
            )
    return rows


def release_readiness_delta_leaderboard(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda item: (
            _release_readiness_delta_priority(item),
            -int(bool(item.get("ci_workflow_status_changed"))),
            -abs(_as_optional_float(item.get("ci_workflow_failed_check_delta")) or 0.0),
            -abs(_as_optional_float(item.get("ci_workflow_order_violation_delta")) or 0.0),
            -abs(_as_optional_float(item.get("test_coverage_gap_delta")) or 0.0),
            -abs(_as_optional_float(item.get("test_coverage_percent_delta")) or 0.0),
            -abs(_as_optional_float(item.get("benchmark_history_case_regression_delta")) or 0.0),
            -abs(_as_optional_float(item.get("benchmark_history_generation_flag_regression_delta")) or 0.0),
            -int(bool(item.get("benchmark_history_readiness_requirement_status_changed"))),
            -int(item.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0),
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
        "max_abs_ci_workflow_failed_check_delta": _int_if_whole(max(ci_failed_deltas)) if ci_failed_deltas else None,
        "max_abs_ci_workflow_order_violation_delta": _int_if_whole(max(ci_order_deltas)) if ci_order_deltas else None,
        "test_coverage_regression_count": sum(1 for row in rows if _is_test_coverage_regression_row(row)),
        "test_coverage_status_changed_count": sum(1 for row in rows if bool(row.get("test_coverage_status_changed"))),
        "max_abs_test_coverage_percent_delta": _int_if_whole(max(coverage_percent_deltas)) if coverage_percent_deltas else None,
        "max_abs_test_coverage_gap_delta": _int_if_whole(max(coverage_gap_deltas)) if coverage_gap_deltas else None,
        "benchmark_history_regression_count": sum(1 for row in rows if _is_benchmark_history_regression_row(row)),
        "benchmark_history_status_changed_count": sum(1 for row in rows if bool(row.get("benchmark_history_status_changed"))),
        "benchmark_history_boundary_changed_count": sum(1 for row in rows if bool(row.get("benchmark_history_latest_boundary_changed"))),
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
        "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": _counts(
            row.get("benchmark_history_readiness_requirement_failed_reason_drift_status") or "stable" for row in rows
        ),
        "max_abs_benchmark_history_case_regression_delta": _int_if_whole(max(benchmark_case_regression_deltas))
        if benchmark_case_regression_deltas
        else None,
        "max_abs_benchmark_history_generation_flag_regression_delta": _int_if_whole(max(benchmark_flag_regression_deltas))
        if benchmark_flag_regression_deltas
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
    failed_delta = _as_optional_float(row.get("ci_workflow_failed_check_delta"))
    if failed_delta is not None and failed_delta > 0:
        return True
    if _is_ci_workflow_order_regression_row(row):
        return True
    if not row.get("ci_workflow_status_changed"):
        return False
    return _ci_status_score(row.get("compared_ci_workflow_status")) < _ci_status_score(row.get("baseline_ci_workflow_status"))


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


def _ci_status_score(value: Any) -> int:
    return {"missing": 0, "fail": 0, "warn": 1, "review": 1, "pass": 2}.get(str(value or "missing"), 0)


def _coverage_status_score(value: Any) -> int:
    return {"missing": 0, "fail": 0, "warn": 1, "review": 1, "pass": 2}.get(str(value or "missing"), 0)


def _benchmark_requirement_status_score(value: Any) -> int:
    return {"missing": 0, "fail": 0, "pass": 2}.get(str(value or "missing"), 0)


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_release_readiness_comparison(root: Path) -> dict[str, Any]:
    candidates = [
        root / "release-readiness-comparison" / "release_readiness_comparison.json",
        root / "release_readiness_comparison.json",
    ]
    for path in candidates:
        payload = _read_json(path)
        if isinstance(payload, dict):
            payload["release_readiness_comparison_path"] = str(path)
            return payload
    return {}


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


__all__ = [
    "collect_release_readiness_delta_rows",
    "release_readiness_delta_leaderboard",
    "release_readiness_delta_summary",
]
