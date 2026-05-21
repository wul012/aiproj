from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.release_readiness_comparison_artifacts import (
    render_release_readiness_comparison_html,
    render_release_readiness_comparison_markdown,
    write_release_readiness_comparison_csv,
    write_release_readiness_comparison_html,
    write_release_readiness_comparison_json,
    write_release_readiness_comparison_markdown,
    write_release_readiness_comparison_outputs,
    write_release_readiness_delta_csv,
)
from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    utc_now,
)


STATUS_ORDER = {
    "blocked": 0,
    "incomplete": 1,
    "review": 2,
    "ready": 3,
}

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


def build_release_readiness_comparison(
    readiness_paths: list[str | Path],
    *,
    baseline_path: str | Path | None = None,
    title: str = "MiniGPT release readiness comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    paths = [Path(path) for path in readiness_paths]
    if baseline_path is not None:
        baseline = Path(baseline_path)
        paths = [baseline] + [path for path in paths if path != baseline]
    if not paths:
        raise ValueError("at least one release_readiness.json path is required")
    reports = [_read_required_json(path) for path in paths]
    rows = [_row_from_report(path, report) for path, report in zip(paths, reports)]
    baseline_row = rows[0]
    deltas = [_delta_from_baseline(baseline_row, row) for row in rows[1:]]
    summary = _summary(rows, deltas, baseline_row)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "baseline_path": str(paths[0]),
        "readiness_paths": [str(path) for path in paths],
        "summary": summary,
        "rows": rows,
        "deltas": deltas,
        "recommendations": _recommendations(summary, deltas),
    }


def _row_from_report(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    panels = _list_of_dicts(report.get("panels"))
    status = str(summary.get("readiness_status") or "missing")
    return {
        "readiness_path": str(path),
        "release_name": summary.get("release_name"),
        "readiness_status": status,
        "decision": summary.get("decision"),
        "readiness_score": STATUS_ORDER.get(status, -1),
        "gate_status": summary.get("gate_status"),
        "audit_status": summary.get("audit_status"),
        "audit_score_percent": summary.get("audit_score_percent"),
        "ci_workflow_status": summary.get("ci_workflow_status"),
        "ci_workflow_failed_checks": summary.get("ci_workflow_failed_checks"),
        "ci_workflow_node24_actions": summary.get("ci_workflow_node24_actions"),
        "ci_workflow_required_order_count": summary.get("ci_workflow_required_order_count"),
        "ci_workflow_order_violation_count": summary.get("ci_workflow_order_violation_count"),
        "ci_workflow_release_readiness_drift_contract_smoke_ready": summary.get(
            "ci_workflow_release_readiness_drift_contract_smoke_ready"
        ),
        "request_history_status": summary.get("request_history_status"),
        "test_coverage_status": summary.get("test_coverage_status"),
        "test_coverage_percent": summary.get("test_coverage_percent"),
        "test_coverage_fail_under": summary.get("test_coverage_fail_under"),
        "test_coverage_gap": summary.get("test_coverage_gap"),
        "benchmark_history_status": summary.get("benchmark_history_status"),
        "benchmark_history_entries": summary.get("benchmark_history_entries"),
        "benchmark_history_ready": summary.get("benchmark_history_ready"),
        "benchmark_history_review": summary.get("benchmark_history_review"),
        "benchmark_history_blocked": summary.get("benchmark_history_blocked"),
        "benchmark_history_case_regressions": summary.get("benchmark_history_case_regressions"),
        "benchmark_history_generation_flag_regressions": summary.get("benchmark_history_generation_flag_regressions"),
        "benchmark_history_readiness_requirement_status": summary.get("benchmark_history_readiness_requirement_status"),
        "benchmark_history_readiness_requirement_exit_code": summary.get("benchmark_history_readiness_requirement_exit_code"),
        "benchmark_history_readiness_requirement_failed_reasons": summary.get("benchmark_history_readiness_requirement_failed_reasons"),
        "benchmark_history_model_quality_claim": summary.get("benchmark_history_model_quality_claim"),
        "benchmark_history_latest_boundary": summary.get("benchmark_history_latest_boundary"),
        "maturity_status": summary.get("maturity_status"),
        "ready_runs": summary.get("ready_runs"),
        "missing_artifacts": summary.get("missing_artifacts"),
        "fail_panel_count": summary.get("fail_panel_count"),
        "warn_panel_count": summary.get("warn_panel_count"),
        "action_count": len(_string_list(report.get("actions"))),
        "panel_statuses": {str(panel.get("key")): panel.get("status") for panel in panels if panel.get("key")},
    }


def _delta_from_baseline(baseline: dict[str, Any], compared: dict[str, Any]) -> dict[str, Any]:
    status_delta = int(compared.get("readiness_score") or 0) - int(baseline.get("readiness_score") or 0)
    baseline_panels = _dict(baseline.get("panel_statuses"))
    compared_panels = _dict(compared.get("panel_statuses"))
    added_failed_reasons = _reason_additions(
        baseline.get("benchmark_history_readiness_requirement_failed_reasons"),
        compared.get("benchmark_history_readiness_requirement_failed_reasons"),
    )
    removed_failed_reasons = _reason_removals(
        baseline.get("benchmark_history_readiness_requirement_failed_reasons"),
        compared.get("benchmark_history_readiness_requirement_failed_reasons"),
    )
    changed = []
    for key in sorted(set(baseline_panels) | set(compared_panels)):
        before = baseline_panels.get(key)
        after = compared_panels.get(key)
        if before != after:
            changed.append(f"{key}:{before}->{after}")
    baseline_drift_smoke_ready = baseline.get("ci_workflow_release_readiness_drift_contract_smoke_ready")
    compared_drift_smoke_ready = compared.get("ci_workflow_release_readiness_drift_contract_smoke_ready")
    delta = {
        "baseline_path": baseline.get("readiness_path"),
        "compared_path": compared.get("readiness_path"),
        "baseline_release": baseline.get("release_name"),
        "compared_release": compared.get("release_name"),
        "baseline_status": baseline.get("readiness_status"),
        "compared_status": compared.get("readiness_status"),
        "baseline_ci_workflow_status": baseline.get("ci_workflow_status"),
        "compared_ci_workflow_status": compared.get("ci_workflow_status"),
        "baseline_test_coverage_status": baseline.get("test_coverage_status"),
        "compared_test_coverage_status": compared.get("test_coverage_status"),
        "baseline_benchmark_history_status": baseline.get("benchmark_history_status"),
        "compared_benchmark_history_status": compared.get("benchmark_history_status"),
        "status_delta": status_delta,
        "delta_status": _delta_status(status_delta, changed),
        "audit_score_delta": _number_delta(compared.get("audit_score_percent"), baseline.get("audit_score_percent")),
        "ci_workflow_failed_check_delta": _number_delta(compared.get("ci_workflow_failed_checks"), baseline.get("ci_workflow_failed_checks")),
        "ci_workflow_required_order_delta": _number_delta(compared.get("ci_workflow_required_order_count"), baseline.get("ci_workflow_required_order_count")),
        "ci_workflow_order_violation_delta": _number_delta(compared.get("ci_workflow_order_violation_count"), baseline.get("ci_workflow_order_violation_count")),
        "ci_workflow_status_changed": compared.get("ci_workflow_status") != baseline.get("ci_workflow_status"),
        "baseline_ci_workflow_release_readiness_drift_contract_smoke_ready": baseline_drift_smoke_ready,
        "compared_ci_workflow_release_readiness_drift_contract_smoke_ready": compared_drift_smoke_ready,
        "ci_workflow_release_readiness_drift_contract_smoke_ready_changed": compared_drift_smoke_ready != baseline_drift_smoke_ready,
        "ci_workflow_release_readiness_drift_contract_smoke_ready_regressed": baseline_drift_smoke_ready is True
        and compared_drift_smoke_ready is not True,
        "test_coverage_percent_delta": _number_delta(compared.get("test_coverage_percent"), baseline.get("test_coverage_percent")),
        "test_coverage_gap_delta": _number_delta(compared.get("test_coverage_gap"), baseline.get("test_coverage_gap")),
        "test_coverage_status_changed": compared.get("test_coverage_status") != baseline.get("test_coverage_status"),
        "benchmark_history_status_delta": _benchmark_history_status_score(compared.get("benchmark_history_status"))
        - _benchmark_history_status_score(baseline.get("benchmark_history_status")),
        "benchmark_history_status_changed": compared.get("benchmark_history_status") != baseline.get("benchmark_history_status"),
        "benchmark_history_entry_delta": _number_delta(compared.get("benchmark_history_entries"), baseline.get("benchmark_history_entries")),
        "benchmark_history_ready_delta": _number_delta(compared.get("benchmark_history_ready"), baseline.get("benchmark_history_ready")),
        "benchmark_history_review_delta": _number_delta(compared.get("benchmark_history_review"), baseline.get("benchmark_history_review")),
        "benchmark_history_blocked_delta": _number_delta(compared.get("benchmark_history_blocked"), baseline.get("benchmark_history_blocked")),
        "benchmark_history_case_regression_delta": _number_delta(
            compared.get("benchmark_history_case_regressions"),
            baseline.get("benchmark_history_case_regressions"),
        ),
        "benchmark_history_generation_flag_regression_delta": _number_delta(
            compared.get("benchmark_history_generation_flag_regressions"),
            baseline.get("benchmark_history_generation_flag_regressions"),
        ),
        "benchmark_history_readiness_requirement_status_changed": compared.get("benchmark_history_readiness_requirement_status")
        != baseline.get("benchmark_history_readiness_requirement_status"),
        "baseline_benchmark_history_readiness_requirement_status": baseline.get("benchmark_history_readiness_requirement_status"),
        "compared_benchmark_history_readiness_requirement_status": compared.get("benchmark_history_readiness_requirement_status"),
        "benchmark_history_readiness_requirement_exit_code_delta": _number_delta(
            compared.get("benchmark_history_readiness_requirement_exit_code"),
            baseline.get("benchmark_history_readiness_requirement_exit_code"),
        ),
        "baseline_benchmark_history_readiness_requirement_failed_reasons": baseline.get(
            "benchmark_history_readiness_requirement_failed_reasons"
        ),
        "compared_benchmark_history_readiness_requirement_failed_reasons": compared.get(
            "benchmark_history_readiness_requirement_failed_reasons"
        ),
        "benchmark_history_readiness_requirement_failed_reason_added_count": len(added_failed_reasons),
        "benchmark_history_readiness_requirement_failed_reason_removed_count": len(removed_failed_reasons),
        "benchmark_history_readiness_requirement_failed_reason_added": added_failed_reasons,
        "benchmark_history_readiness_requirement_failed_reason_removed": removed_failed_reasons,
        "benchmark_history_readiness_requirement_failed_reason_drift_status": _reason_drift_status(
            added_failed_reasons,
            removed_failed_reasons,
        ),
        "benchmark_history_model_quality_claim_changed": compared.get("benchmark_history_model_quality_claim")
        != baseline.get("benchmark_history_model_quality_claim"),
        "benchmark_history_latest_boundary_changed": compared.get("benchmark_history_latest_boundary")
        != baseline.get("benchmark_history_latest_boundary"),
        "baseline_benchmark_history_boundary": baseline.get("benchmark_history_latest_boundary"),
        "compared_benchmark_history_boundary": compared.get("benchmark_history_latest_boundary"),
        "missing_artifact_delta": _number_delta(compared.get("missing_artifacts"), baseline.get("missing_artifacts")),
        "fail_panel_delta": _number_delta(compared.get("fail_panel_count"), baseline.get("fail_panel_count")),
        "warn_panel_delta": _number_delta(compared.get("warn_panel_count"), baseline.get("warn_panel_count")),
        "changed_panels": changed,
    }
    delta["ci_workflow_regression_reasons"] = _ci_workflow_regression_reasons(delta)
    delta["explanation"] = _delta_explanation(delta)
    return delta


def _delta_status(status_delta: int, changed_panels: list[str]) -> str:
    if status_delta > 0:
        return "improved"
    if status_delta < 0:
        return "regressed"
    if changed_panels:
        return "panel-changed"
    return "same"


def _delta_explanation(delta: dict[str, Any]) -> str:
    compared = delta.get("compared_release") or delta.get("compared_path")
    status = delta.get("delta_status")
    parts = [
        f"{compared} moves from {delta.get('baseline_status')} to {delta.get('compared_status')} ({status_delta_label(delta.get('status_delta'))})."
    ]
    changed = _string_list(delta.get("changed_panels"))
    if changed:
        parts.append("Changed panel(s): " + ", ".join(changed) + ".")
    if delta.get("audit_score_delta") not in {None, 0, 0.0}:
        parts.append(f"Audit score delta is {delta.get('audit_score_delta')}.")
    if delta.get("ci_workflow_status_changed"):
        parts.append("CI workflow status changed.")
    if delta.get("ci_workflow_failed_check_delta") not in {None, 0, 0.0}:
        parts.append(f"CI workflow failed check delta is {delta.get('ci_workflow_failed_check_delta')}.")
    if delta.get("ci_workflow_order_violation_delta") not in {None, 0, 0.0}:
        parts.append(f"CI workflow order violation delta is {delta.get('ci_workflow_order_violation_delta')}.")
    if delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_changed"):
        parts.append(
            "CI workflow release readiness drift-contract smoke ready changed from "
            f"{delta.get('baseline_ci_workflow_release_readiness_drift_contract_smoke_ready')} to "
            f"{delta.get('compared_ci_workflow_release_readiness_drift_contract_smoke_ready')}."
        )
    if delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regressed"):
        parts.append("CI workflow release readiness drift-contract smoke ready regressed.")
    ci_reasons = _string_list(delta.get("ci_workflow_regression_reasons"))
    if ci_reasons:
        parts.append("CI workflow regression reason(s): " + ", ".join(_ci_workflow_reason_label(reason) for reason in ci_reasons) + ".")
    if delta.get("test_coverage_status_changed"):
        parts.append("Test coverage status changed.")
    if delta.get("test_coverage_percent_delta") not in {None, 0, 0.0}:
        parts.append(f"Test coverage percent delta is {delta.get('test_coverage_percent_delta')}.")
    if delta.get("test_coverage_gap_delta") not in {None, 0, 0.0}:
        parts.append(f"Test coverage gap delta is {delta.get('test_coverage_gap_delta')}.")
    if delta.get("benchmark_history_status_changed"):
        parts.append(
            f"Benchmark history status changed from {delta.get('baseline_benchmark_history_status')} to {delta.get('compared_benchmark_history_status')}."
        )
    if delta.get("benchmark_history_case_regression_delta") not in {None, 0, 0.0}:
        parts.append(f"Benchmark history case regression delta is {delta.get('benchmark_history_case_regression_delta')}.")
    if delta.get("benchmark_history_generation_flag_regression_delta") not in {None, 0, 0.0}:
        parts.append(
            f"Benchmark history generation-flag regression delta is {delta.get('benchmark_history_generation_flag_regression_delta')}."
        )
    if delta.get("benchmark_history_readiness_requirement_status_changed"):
        parts.append(
            "Benchmark history readiness requirement changed from "
            f"{delta.get('baseline_benchmark_history_readiness_requirement_status')} to "
            f"{delta.get('compared_benchmark_history_readiness_requirement_status')}."
        )
    if delta.get("benchmark_history_readiness_requirement_exit_code_delta") not in {None, 0, 0.0}:
        parts.append(
            "Benchmark history readiness requirement exit-code delta is "
            f"{delta.get('benchmark_history_readiness_requirement_exit_code_delta')}."
        )
    added_reasons = _string_list(delta.get("benchmark_history_readiness_requirement_failed_reason_added"))
    removed_reasons = _string_list(delta.get("benchmark_history_readiness_requirement_failed_reason_removed"))
    if added_reasons:
        parts.append("Benchmark readiness requirement added failed reason(s): " + ", ".join(added_reasons) + ".")
    if removed_reasons:
        parts.append("Benchmark readiness requirement removed failed reason(s): " + ", ".join(removed_reasons) + ".")
    if delta.get("benchmark_history_latest_boundary_changed"):
        parts.append(
            f"Benchmark history boundary changed from {delta.get('baseline_benchmark_history_boundary')} to {delta.get('compared_benchmark_history_boundary')}."
        )
    if status == "same" and not changed:
        parts.append("No readiness status or panel delta is present.")
    return " ".join(parts)


def status_delta_label(value: Any) -> str:
    delta = int(value or 0)
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def _summary(rows: list[dict[str, Any]], deltas: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "readiness_count": len(rows),
        "baseline_release": baseline.get("release_name"),
        "baseline_status": baseline.get("readiness_status"),
        "ready_count": sum(1 for row in rows if row.get("readiness_status") == "ready"),
        "review_count": sum(1 for row in rows if row.get("readiness_status") == "review"),
        "blocked_count": sum(1 for row in rows if row.get("readiness_status") == "blocked"),
        "incomplete_count": sum(1 for row in rows if row.get("readiness_status") == "incomplete"),
        "improved_count": sum(1 for delta in deltas if delta.get("delta_status") == "improved"),
        "regressed_count": sum(1 for delta in deltas if delta.get("delta_status") == "regressed"),
        "changed_panel_delta_count": sum(1 for delta in deltas if delta.get("changed_panels")),
        "ci_workflow_regression_count": sum(1 for delta in deltas if _is_ci_workflow_regression(delta)),
        "ci_workflow_order_regression_count": sum(1 for delta in deltas if _is_ci_workflow_order_regression(delta)),
        "ci_workflow_release_readiness_drift_contract_smoke_ready_changed_count": sum(
            1 for delta in deltas if delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_changed")
        ),
        "ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count": sum(
            1 for delta in deltas if delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regressed")
        ),
        "ci_workflow_regression_reasons": _unique_strings(
            reason for delta in deltas for reason in _string_list(delta.get("ci_workflow_regression_reasons"))
        ),
        "ci_workflow_regression_reason_counts": _counts(
            reason for delta in deltas for reason in _string_list(delta.get("ci_workflow_regression_reasons"))
        ),
        "max_abs_ci_workflow_order_violation_delta": _max_abs_delta(deltas, "ci_workflow_order_violation_delta"),
        "test_coverage_regression_count": sum(1 for delta in deltas if _is_test_coverage_regression(delta)),
        "benchmark_history_delta_count": sum(1 for delta in deltas if _has_benchmark_history_delta(delta)),
        "benchmark_history_regression_count": sum(1 for delta in deltas if _is_benchmark_history_regression(delta)),
        "benchmark_history_readiness_requirement_failed_reason_added_count": sum(
            int(delta.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) for delta in deltas
        ),
        "benchmark_history_readiness_requirement_failed_reason_removed_count": sum(
            int(delta.get("benchmark_history_readiness_requirement_failed_reason_removed_count") or 0) for delta in deltas
        ),
        "benchmark_history_readiness_requirement_failed_reason_added": _unique_strings(
            reason
            for delta in deltas
            for reason in _string_list(delta.get("benchmark_history_readiness_requirement_failed_reason_added"))
        ),
        "benchmark_history_readiness_requirement_failed_reason_removed": _unique_strings(
            reason
            for delta in deltas
            for reason in _string_list(delta.get("benchmark_history_readiness_requirement_failed_reason_removed"))
        ),
        "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": sum(
            1 for delta in deltas if delta.get("benchmark_history_readiness_requirement_failed_reason_drift_status") == "recovered"
        ),
        "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": sum(
            1 for delta in deltas if delta.get("benchmark_history_readiness_requirement_failed_reason_drift_status") == "mixed"
        ),
        "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": _counts(
            delta.get("benchmark_history_readiness_requirement_failed_reason_drift_status") or "stable" for delta in deltas
        ),
    }


def _recommendations(summary: dict[str, Any], deltas: list[dict[str, Any]]) -> list[str]:
    if int(summary.get("test_coverage_regression_count") or 0):
        return ["At least one readiness comparison shows test coverage regression; inspect coverage percent and gap deltas before release handoff."]
    if int(summary.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count") or 0):
        return [
            "At least one readiness comparison shows mixed benchmark readiness failed-reason drift; inspect newly added reasons even when some reasons were removed."
        ]
    if int(summary.get("benchmark_history_regression_count") or 0):
        return [
            "At least one readiness comparison shows benchmark history regression; inspect benchmark status, readiness requirement, case-regression, and boundary deltas before release handoff."
        ]
    if int(summary.get("ci_workflow_regression_count") or 0):
        reason_text = _ci_workflow_reason_summary(summary.get("ci_workflow_regression_reason_counts"))
        return [
            "At least one readiness comparison shows CI workflow hygiene regression"
            f" ({reason_text}); inspect CI status deltas, failed-check deltas, order-violation deltas, "
            "and drift-smoke readiness deltas before release handoff."
        ]
    if int(summary.get("regressed_count") or 0):
        return ["At least one readiness report regressed from the baseline; inspect delta explanations before release handoff."]
    if int(summary.get("improved_count") or 0):
        return ["Readiness improved against the baseline; keep the comparison report with release evidence."]
    if int(summary.get("benchmark_history_readiness_requirement_failed_reason_recovery_delta_count") or 0):
        return ["Benchmark readiness failed reasons were removed; keep this recovery evidence with release handoff."]
    if int(summary.get("blocked_count") or 0):
        return ["At least one readiness report is blocked; fix failed panels before comparing release quality as improved."]
    if any(delta.get("changed_panels") for delta in deltas):
        return ["Readiness status stayed stable, but panel-level changes should be reviewed."]
    return ["Readiness reports are stable against the baseline."]


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release readiness comparison input must be a JSON object: {path}")
    return payload


def _number_delta(left: Any, right: Any) -> float | int | None:
    if left is None or right is None:
        return None
    delta = float(left) - float(right)
    return int(delta) if delta.is_integer() else round(delta, 4)


def _is_ci_workflow_regression(delta: dict[str, Any]) -> bool:
    return bool(_ci_workflow_regression_reasons(delta))


def _ci_workflow_regression_reasons(delta: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    failed_delta = delta.get("ci_workflow_failed_check_delta")
    if isinstance(failed_delta, (int, float)) and failed_delta > 0:
        reasons.append("failed_checks_increased")
    if _is_ci_workflow_order_regression(delta):
        reasons.append("order_violations_increased")
    if delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regressed"):
        reasons.append("drift_contract_smoke_not_ready")
    if delta.get("ci_workflow_status_changed"):
        if _ci_status_score(delta.get("compared_ci_workflow_status")) < _ci_status_score(delta.get("baseline_ci_workflow_status")):
            reasons.append("workflow_status_downgraded")
    return reasons


def _is_ci_workflow_order_regression(delta: dict[str, Any]) -> bool:
    order_delta = delta.get("ci_workflow_order_violation_delta")
    return isinstance(order_delta, (int, float)) and order_delta > 0


def _is_test_coverage_regression(delta: dict[str, Any]) -> bool:
    percent_delta = delta.get("test_coverage_percent_delta")
    if isinstance(percent_delta, (int, float)) and percent_delta < 0:
        return True
    gap_delta = delta.get("test_coverage_gap_delta")
    if isinstance(gap_delta, (int, float)) and gap_delta > 0:
        return True
    if delta.get("test_coverage_status_changed"):
        return _coverage_status_score(delta.get("compared_test_coverage_status")) < _coverage_status_score(delta.get("baseline_test_coverage_status"))
    return False


def _has_benchmark_history_delta(delta: dict[str, Any]) -> bool:
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
        "benchmark_history_readiness_requirement_exit_code_delta",
    ]
    return any(delta.get(key) not in {None, 0, 0.0} for key in keys)


def _is_benchmark_history_regression(delta: dict[str, Any]) -> bool:
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
        "benchmark_history_readiness_requirement_exit_code_delta",
    ]:
        value = delta.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return True
    if delta.get("benchmark_history_readiness_requirement_status_changed"):
        return _requirement_status_score(delta.get("compared_benchmark_history_readiness_requirement_status")) < _requirement_status_score(
            delta.get("baseline_benchmark_history_readiness_requirement_status")
        )
    ready_delta = delta.get("benchmark_history_ready_delta")
    return isinstance(ready_delta, (int, float)) and ready_delta < 0


def _ci_status_score(value: Any) -> int:
    return CI_STATUS_ORDER.get(str(value or "missing"), 0)


def _coverage_status_score(value: Any) -> int:
    return COVERAGE_STATUS_ORDER.get(str(value or "missing"), 0)


def _benchmark_history_status_score(value: Any) -> int:
    return BENCHMARK_HISTORY_STATUS_ORDER.get(str(value or "missing"), 0)


def _requirement_status_score(value: Any) -> int:
    return {"pass": 2, "warn": 1, "review": 1, "fail": 0, "missing": 0}.get(str(value or "missing"), 0)


def _max_abs_delta(deltas: list[dict[str, Any]], key: str) -> float | int | None:
    values = [abs(float(delta[key])) for delta in deltas if isinstance(delta.get(key), (int, float))]
    if not values:
        return None
    value = max(values)
    return int(value) if value.is_integer() else round(value, 4)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _reason_additions(baseline: Any, compared: Any) -> list[str]:
    baseline_reasons = set(_string_list(baseline))
    return [reason for reason in _string_list(compared) if reason not in baseline_reasons]


def _reason_removals(baseline: Any, compared: Any) -> list[str]:
    compared_reasons = set(_string_list(compared))
    return [reason for reason in _string_list(baseline) if reason not in compared_reasons]


def _reason_drift_status(added: list[str], removed: list[str]) -> str:
    if added and removed:
        return "mixed"
    if added:
        return "regressed"
    if removed:
        return "recovered"
    return "stable"


def _ci_workflow_reason_summary(value: Any) -> str:
    counts = _dict(value)
    if not counts:
        return "reason unspecified"
    return ", ".join(f"{_ci_workflow_reason_label(key)}={counts[key]}" for key in sorted(counts))


def _ci_workflow_reason_label(value: Any) -> str:
    return {
        "drift_contract_smoke_not_ready": "drift-contract smoke readiness",
        "failed_checks_increased": "failed checks increased",
        "order_violations_increased": "order violations increased",
        "workflow_status_downgraded": "workflow status downgraded",
    }.get(str(value), str(value))


def _unique_strings(values: Any) -> list[str]:
    items: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in items:
            items.append(text)
    return items


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


__all__ = [
    "build_release_readiness_comparison",
    "render_release_readiness_comparison_html",
    "render_release_readiness_comparison_markdown",
    "status_delta_label",
    "write_release_readiness_comparison_csv",
    "write_release_readiness_comparison_html",
    "write_release_readiness_comparison_json",
    "write_release_readiness_comparison_markdown",
    "write_release_readiness_comparison_outputs",
    "write_release_readiness_delta_csv",
]
