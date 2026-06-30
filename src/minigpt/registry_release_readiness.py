from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.registry_release_readiness_delta_stats import (
    CI_READY_REGRESSION_REASON_FIELDS,
    _as_int,
    _as_optional_float,
    _as_str,
    _as_str_list,
    _ci_workflow_regression_reasons,
    _int_if_whole,
    _reason_additions,
    _reason_drift_status,
    _reason_removals,
    release_readiness_delta_leaderboard,
    release_readiness_delta_summary,
)


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
            ci_regression_reasons = _ci_workflow_regression_reasons(delta)
            ci_ready_regression_flags = {
                key: bool(delta.get(key))
                for key in CI_READY_REGRESSION_REASON_FIELDS
            }
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
                    "ci_workflow_regression_reasons": ci_regression_reasons,
                    **ci_ready_regression_flags,
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
                    "benchmark_history_suite_design_non_comparison_ready_entries_delta": _int_if_whole(
                        _as_optional_float(delta.get("benchmark_history_suite_design_non_comparison_ready_entries_delta"))
                    ),
                    "benchmark_history_design_comparison_changed_entries_delta": _int_if_whole(
                        _as_optional_float(delta.get("benchmark_history_design_comparison_changed_entries_delta"))
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


__all__ = [
    "collect_release_readiness_delta_rows",
    "release_readiness_delta_leaderboard",
    "release_readiness_delta_summary",
]
