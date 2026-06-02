from __future__ import annotations

from typing import Any

from minigpt.report_utils import CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON
from minigpt.report_utils import as_dict as _dict


def release_readiness_delta_explanation(delta: dict[str, Any]) -> str:
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
    _append_ci_readiness_notes(parts, delta)
    ci_reasons = _string_list(delta.get("ci_workflow_regression_reasons"))
    if ci_reasons:
        parts.append("CI workflow regression reason(s): " + ", ".join(_ci_workflow_reason_label(reason) for reason in ci_reasons) + ".")
    _append_test_and_benchmark_notes(parts, delta)
    if status == "same" and not changed:
        parts.append("No readiness status or panel delta is present.")
    return " ".join(parts)


def status_delta_label(value: Any) -> str:
    delta = int(value or 0)
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def build_release_readiness_comparison_recommendations(
    summary: dict[str, Any],
    deltas: list[dict[str, Any]],
) -> list[str]:
    if int(summary.get("test_coverage_regression_count") or 0):
        return ["At least one readiness comparison shows test coverage regression; inspect coverage percent and gap deltas before release handoff."]
    if int(summary.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count") or 0):
        return [
            "At least one readiness comparison shows mixed benchmark readiness failed-reason drift; inspect newly added reasons even when some reasons were removed."
        ]
    if int(summary.get("benchmark_history_suite_design_non_comparison_ready_regression_count") or 0):
        return [
            "At least one readiness comparison shows benchmark suite-design not-ready regression; inspect prompt-suite design evidence before release handoff."
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


def _append_ci_readiness_notes(parts: list[str], delta: dict[str, Any]) -> None:
    if delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_changed"):
        parts.append(
            "CI workflow release readiness drift-contract smoke ready changed from "
            f"{delta.get('baseline_ci_workflow_release_readiness_drift_contract_smoke_ready')} to "
            f"{delta.get('compared_ci_workflow_release_readiness_drift_contract_smoke_ready')}."
        )
    if delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regressed"):
        parts.append("CI workflow release readiness drift-contract smoke ready regressed.")
    if delta.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_changed"):
        parts.append(
            "CI workflow baseline-candidate threshold boundary gate check ready changed from "
            f"{delta.get('baseline_ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready')} to "
            f"{delta.get('compared_ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready')}."
        )
    if delta.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_changed"):
        parts.append(
            "CI workflow baseline-candidate threshold boundary gate plan check ready changed from "
            f"{delta.get('baseline_ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready')} to "
            f"{delta.get('compared_ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready')}."
        )
    if delta.get("ci_workflow_archived_path_portability_check_ready_changed"):
        parts.append(
            "CI workflow archived path portability check ready changed from "
            f"{delta.get('baseline_ci_workflow_archived_path_portability_check_ready')} to "
            f"{delta.get('compared_ci_workflow_archived_path_portability_check_ready')}."
        )
    if delta.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_changed"):
        parts.append(
            "CI workflow promoted seed receipt failure-smoke plan check ready changed from "
            f"{delta.get('baseline_ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready')} to "
            f"{delta.get('compared_ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready')}."
        )


def _append_test_and_benchmark_notes(parts: list[str], delta: dict[str, Any]) -> None:
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
    if delta.get("benchmark_history_suite_design_non_comparison_ready_entries_delta") not in {None, 0, 0.0}:
        parts.append(
            "Benchmark history suite-design not-ready delta is "
            f"{delta.get('benchmark_history_suite_design_non_comparison_ready_entries_delta')}."
        )
    if delta.get("benchmark_history_design_comparison_changed_entries_delta") not in {None, 0, 0.0}:
        parts.append(
            "Benchmark history design-comparison changed delta is "
            f"{delta.get('benchmark_history_design_comparison_changed_entries_delta')}."
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


def _ci_workflow_reason_summary(value: Any) -> str:
    counts = _dict(value)
    if not counts:
        return "reason unspecified"
    return ", ".join(f"{_ci_workflow_reason_label(key)}={counts[key]}" for key in sorted(counts))


def _ci_workflow_reason_label(value: Any) -> str:
    return {
        "drift_contract_smoke_not_ready": "drift-contract smoke readiness",
        "tiny_scorecard_plan_digest_gate_not_ready": "tiny scorecard plan digest gate readiness",
        "boundary_gate_check_not_ready": "baseline-candidate boundary gate check readiness",
        "boundary_gate_plan_check_not_ready": "baseline-candidate boundary plan check readiness",
        CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON: "archived path portability check readiness",
        "receipt_failure_smoke_plan_check_not_ready": "receipt failure-smoke plan check readiness",
        "failed_checks_increased": "failed checks increased",
        "order_violations_increased": "order violations increased",
        "workflow_status_downgraded": "workflow status downgraded",
    }.get(str(value), str(value))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


__all__ = [
    "build_release_readiness_comparison_recommendations",
    "release_readiness_delta_explanation",
    "status_delta_label",
]
