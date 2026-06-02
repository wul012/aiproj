from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    first_present,
    list_of_dicts as _list_of_dicts,
)


def registry_panel(path: Path | None, registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return _panel("registry", "Registry", "warn", "registry evidence missing", path)
    best = _dict(registry.get("best_by_best_val_loss"))
    return _panel(
        "registry",
        "Registry",
        "pass" if registry.get("run_count") else "warn",
        f"runs={_fmt(registry.get('run_count'))}; best={best.get('name') or 'missing'}; best_val_loss={_fmt(best.get('best_val_loss'))}",
        path,
    )


def bundle_panel(path: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(bundle.get("summary"))
    release_status = summary.get("release_status")
    status = "pass" if release_status == "release-ready" else "fail"
    return _panel(
        "release_bundle",
        "Release Bundle",
        status,
        f"release_status={release_status or 'missing'}; artifacts={_fmt(summary.get('available_artifacts'))} available/{_fmt(summary.get('missing_artifacts'))} missing",
        path,
    )


def audit_panel(path: Path | None, audit: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(audit, dict):
        return _panel("project_audit", "Project Audit", "warn", "project_audit.json missing", path)
    summary = _dict(audit.get("summary"))
    audit_status = str(summary.get("overall_status") or "missing")
    return _panel(
        "project_audit",
        "Project Audit",
        _status_from_check_status(audit_status),
        f"overall={audit_status}; score={_fmt(summary.get('score_percent'))}; checks={_fmt(summary.get('pass_count'))} pass/{_fmt(summary.get('warn_count'))} warn/{_fmt(summary.get('fail_count'))} fail",
        path,
    )


def gate_panel(path: Path | None, gate: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(gate, dict):
        return _panel("release_gate", "Release Gate", "warn", "gate_report.json missing", path)
    summary = _dict(gate.get("summary"))
    gate_status = str(summary.get("gate_status") or "missing")
    return _panel(
        "release_gate",
        "Release Gate",
        _status_from_check_status(gate_status),
        f"gate={gate_status}; decision={summary.get('decision') or 'missing'}; checks={_fmt(summary.get('pass_count'))} pass/{_fmt(summary.get('warn_count'))} warn/{_fmt(summary.get('fail_count'))} fail",
        path,
    )


def request_history_panel(path: Path | None, request_history: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history, dict):
        return _panel("request_history", "Request History Summary", "warn", "request_history_summary.json missing", path)
    summary = _dict(request_history.get("summary"))
    request_status = str(summary.get("status") or "missing")
    return _panel(
        "request_history",
        "Request History Summary",
        "pass" if request_status == "pass" else "warn",
        f"status={request_status}; records={_fmt(summary.get('total_log_records'))}; invalid={_fmt(summary.get('invalid_record_count'))}; timeout_rate={_fmt(summary.get('timeout_rate'))}",
        path,
    )


def benchmark_history_panel(bundle: dict[str, Any], gate: dict[str, Any] | None) -> dict[str, Any]:
    bundle_summary = _dict(bundle.get("summary"))
    gate_summary = _dict(gate.get("summary")) if isinstance(gate, dict) else {}
    check = _gate_check(gate, "benchmark_history_gate_check")
    status = first_present(check.get("status"), gate_summary.get("benchmark_history_status"), bundle_summary.get("benchmark_history_status"))
    if status is None:
        return _panel("benchmark_history", "Benchmark History", "warn", "benchmark history release evidence missing", None)
    requirement_status = first_present(
        gate_summary.get("benchmark_history_readiness_requirement_status"),
        bundle_summary.get("benchmark_history_readiness_requirement_status"),
    )
    requirement_exit = first_present(
        gate_summary.get("benchmark_history_readiness_requirement_exit_code"),
        bundle_summary.get("benchmark_history_readiness_requirement_exit_code"),
    )
    suite_design_not_ready = first_present(
        gate_summary.get("benchmark_history_suite_design_non_comparison_ready_entries"),
        bundle_summary.get("benchmark_history_suite_design_non_comparison_ready_entries"),
    )
    design_comparison_changed = first_present(
        gate_summary.get("benchmark_history_design_comparison_changed_entries"),
        bundle_summary.get("benchmark_history_design_comparison_changed_entries"),
    )
    detail = (
        f"status={status}; entries={_fmt(first_present(gate_summary.get('benchmark_history_entries'), bundle_summary.get('benchmark_history_entries')))}; "
        f"ready={_fmt(first_present(gate_summary.get('benchmark_history_ready'), bundle_summary.get('benchmark_history_ready')))}; "
        f"review={_fmt(first_present(gate_summary.get('benchmark_history_review'), bundle_summary.get('benchmark_history_review')))}; "
        f"blocked={_fmt(first_present(gate_summary.get('benchmark_history_blocked'), bundle_summary.get('benchmark_history_blocked')))}; "
        f"case_regressions={_fmt(first_present(gate_summary.get('benchmark_history_case_regressions'), bundle_summary.get('benchmark_history_case_regressions')))}; "
        f"generation_flag_regressions={_fmt(first_present(gate_summary.get('benchmark_history_generation_flag_regressions'), bundle_summary.get('benchmark_history_generation_flag_regressions')))}; "
        f"suite_design_not_ready={_fmt(suite_design_not_ready)}; "
        f"design_comparison_changed={_fmt(design_comparison_changed)}; "
        f"readiness_requirement={_fmt(requirement_status)}; "
        f"readiness_exit={_fmt(requirement_exit)}; "
        "readiness_failed_reasons="
        + _fmt_reasons(
            first_present(
                gate_summary.get("benchmark_history_readiness_requirement_failed_reasons"),
                bundle_summary.get("benchmark_history_readiness_requirement_failed_reasons"),
            )
        )
        + "; "
        f"model_quality_claim={_fmt(first_present(gate_summary.get('benchmark_history_model_quality_claim'), bundle_summary.get('benchmark_history_model_quality_claim')))}; "
        f"boundary={_fmt(first_present(gate_summary.get('benchmark_history_latest_boundary'), bundle_summary.get('benchmark_history_latest_boundary')))}"
    )
    if check:
        detail += f"; gate_check={check.get('status') or 'missing'}"
    return _panel(
        "benchmark_history",
        "Benchmark History",
        _benchmark_history_panel_status(status, requirement_status, requirement_exit, suite_design_not_ready),
        detail,
        None,
    )


def maturity_panel(path: Path | None, maturity: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(maturity, dict):
        return _panel("maturity", "Maturity Summary", "warn", "maturity_summary.json missing", path)
    summary = _dict(maturity.get("summary"))
    status = str(summary.get("overall_status") or "missing")
    return _panel(
        "maturity",
        "Maturity Summary",
        _status_from_check_status(status),
        f"overall={status}; current_version={_fmt(summary.get('current_version'))}; average_level={_fmt(summary.get('average_maturity_level'))}",
        path,
    )


def ci_workflow_panel(path: Path | None, ci_workflow: dict[str, Any] | None, bundle: dict[str, Any]) -> dict[str, Any]:
    if isinstance(ci_workflow, dict):
        summary = _dict(ci_workflow.get("summary"))
        ci_status = str(summary.get("status") or "missing")
        return _panel(
            "ci_workflow_hygiene",
            "CI Workflow Hygiene",
            "pass" if ci_status == "pass" else "warn",
            "status="
            + ci_status
            + f"; failed_checks={_fmt(summary.get('failed_check_count'))}; node24_native={_fmt(first_present(summary.get('node24_native_actions'), summary.get('node24_native_action_count')))}"
            + f"; required_order={_fmt(summary.get('required_order_count'))}; order_violations={_fmt(summary.get('order_violation_count'))}"
            + f"; plan_digest_gate_ready={_fmt(summary.get('tiny_scorecard_plan_digest_gate_ready'))}"
            + f"; boundary_gate_check_ready={_fmt(summary.get('baseline_candidate_threshold_boundary_gate_check_ready'))}"
            + f"; boundary_gate_plan_check_ready={_fmt(summary.get('baseline_candidate_threshold_boundary_gate_plan_check_ready'))}"
            + f"; archived_path_portability_check_ready={_fmt(summary.get('archived_path_portability_check_ready'))}"
            + f"; receipt_failure_smoke_plan_check_ready={_fmt(summary.get('promoted_seed_receipt_contract_failure_smoke_plan_check_ready'))}"
            + f"; drift_contract_smoke_ready={_fmt(summary.get('release_readiness_drift_contract_smoke_ready'))}",
            path,
        )
    bundle_summary = _dict(bundle.get("summary"))
    bundle_context = _dict(bundle.get("ci_workflow_context"))
    ci_status = bundle_summary.get("ci_workflow_status") or bundle_context.get("status")
    if ci_status:
        return _panel(
            "ci_workflow_hygiene",
            "CI Workflow Hygiene",
            "pass" if ci_status == "pass" else "warn",
            "status="
            + str(ci_status)
            + "; failed_checks="
            + _fmt(first_present(bundle_summary.get("ci_workflow_failed_checks"), bundle_context.get("failed_check_count")))
            + "; node24_native="
            + _fmt(
                first_present(
                    bundle_summary.get("ci_workflow_node24_actions"),
                    bundle_context.get("node24_native_actions"),
                    bundle_context.get("node24_native_action_count"),
                )
            )
            + "; required_order="
            + _fmt(first_present(bundle_summary.get("ci_workflow_required_order_count"), bundle_context.get("required_order_count")))
            + "; order_violations="
            + _fmt(first_present(bundle_summary.get("ci_workflow_order_violation_count"), bundle_context.get("order_violation_count")))
            + "; plan_digest_gate_ready="
            + _fmt(
                first_present(
                    bundle_summary.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready"),
                    bundle_context.get("tiny_scorecard_plan_digest_gate_ready"),
                )
            )
            + "; boundary_gate_check_ready="
            + _fmt(
                first_present(
                    bundle_summary.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready"),
                    bundle_context.get("baseline_candidate_threshold_boundary_gate_check_ready"),
                )
            )
            + "; boundary_gate_plan_check_ready="
            + _fmt(
                first_present(
                    bundle_summary.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready"),
                    bundle_context.get("baseline_candidate_threshold_boundary_gate_plan_check_ready"),
                )
            )
            + "; archived_path_portability_check_ready="
            + _fmt(
                first_present(
                    bundle_summary.get("ci_workflow_archived_path_portability_check_ready"),
                    bundle_context.get("archived_path_portability_check_ready"),
                )
            )
            + "; receipt_failure_smoke_plan_check_ready="
            + _fmt(
                first_present(
                    bundle_summary.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready"),
                    bundle_context.get("promoted_seed_receipt_contract_failure_smoke_plan_check_ready"),
                )
            )
            + "; drift_contract_smoke_ready="
            + _fmt(
                first_present(
                    bundle_summary.get("ci_workflow_release_readiness_drift_contract_smoke_ready"),
                    bundle_context.get("release_readiness_drift_contract_smoke_ready"),
                )
            )
            + "; source=bundle summary/context",
            path,
        )
    return _panel("ci_workflow_hygiene", "CI Workflow Hygiene", "warn", "ci_workflow_hygiene.json missing", path)


def test_coverage_panel(path: Path | None, test_coverage: dict[str, Any] | None, bundle: dict[str, Any]) -> dict[str, Any]:
    if isinstance(test_coverage, dict):
        summary = _dict(test_coverage.get("summary"))
        coverage_status = str(summary.get("status") or "missing")
        return _panel(
            "test_coverage",
            "Test Coverage Gate",
            "pass" if coverage_status == "pass" else "warn",
            "status="
            + coverage_status
            + f"; coverage={_fmt(summary.get('line_coverage_percent'))}; fail_under={_fmt(summary.get('fail_under'))}; gap={_fmt(summary.get('coverage_gap'))}",
            path,
        )
    bundle_summary = _dict(bundle.get("summary"))
    bundle_context = _dict(bundle.get("test_coverage_context"))
    coverage_status = bundle_summary.get("test_coverage_status") or bundle_context.get("status")
    if coverage_status:
        return _panel(
            "test_coverage",
            "Test Coverage Gate",
            "pass" if coverage_status == "pass" else "warn",
            "status="
            + str(coverage_status)
            + "; coverage="
            + _fmt(first_present(bundle_summary.get("test_coverage_percent"), bundle_context.get("line_coverage_percent")))
            + "; fail_under="
            + _fmt(first_present(bundle_summary.get("test_coverage_fail_under"), bundle_context.get("fail_under")))
            + "; gap="
            + _fmt(first_present(bundle_summary.get("test_coverage_gap"), bundle_context.get("coverage_gap")))
            + "; source=bundle summary/context",
            path,
        )
    return _panel("test_coverage", "Test Coverage Gate", "warn", "test_coverage_report.json missing", path)


def _panel(key: str, title: str, status: str, detail: str, source_path: Path | None) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "status": status,
        "detail": detail,
        "source_path": None if source_path is None else str(source_path),
    }


def _gate_check(gate: dict[str, Any] | None, check_id: str) -> dict[str, Any]:
    if not isinstance(gate, dict):
        return {}
    for check in _list_of_dicts(gate.get("checks")):
        if check.get("id") == check_id:
            return check
    return {}


def _status_from_check_status(value: str) -> str:
    if value == "pass":
        return "pass"
    if value == "fail" or value == "blocked":
        return "fail"
    return "warn"


def _benchmark_history_panel_status(status: Any, requirement_status: Any, requirement_exit: Any, suite_design_not_ready: Any) -> str:
    if str(requirement_status or "") == "fail" or _int(requirement_exit) > 0:
        return "warn"
    if _int(suite_design_not_ready) > 0:
        return "warn"
    return _status_from_check_status(str(status))


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_reasons(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "none"
    return ",".join(str(item) for item in value if str(item).strip()) or "none"


__all__ = [
    "audit_panel",
    "benchmark_history_panel",
    "bundle_panel",
    "ci_workflow_panel",
    "gate_panel",
    "maturity_panel",
    "registry_panel",
    "request_history_panel",
    "test_coverage_panel",
]
