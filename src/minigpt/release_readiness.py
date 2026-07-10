from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    first_present,
    list_of_dicts as _list_of_dicts,
    utc_now,
)
from minigpt.release_readiness_artifacts import (
    render_release_readiness_html,  # noqa: F401
    render_release_readiness_markdown,  # noqa: F401
    write_release_readiness_html,  # noqa: F401
    write_release_readiness_json,  # noqa: F401
    write_release_readiness_markdown,  # noqa: F401
    write_release_readiness_outputs,  # noqa: F401
)
from minigpt.release_readiness_panels import (
    audit_panel as _audit_panel,
    benchmark_history_panel as _benchmark_history_panel,
    bundle_panel as _bundle_panel,
    ci_workflow_panel as _ci_workflow_panel,
    gate_panel as _gate_panel,
    maturity_panel as _maturity_panel,
    registry_panel as _registry_panel,
    request_history_panel as _request_history_panel,
    test_coverage_panel as _test_coverage_panel,
)


def build_release_readiness_dashboard(
    bundle_path: str | Path,
    *,
    gate_path: str | Path | None = None,
    audit_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    maturity_path: str | Path | None = None,
    ci_workflow_hygiene_path: str | Path | None = None,
    test_coverage_report_path: str | Path | None = None,
    title: str = "MiniGPT release readiness dashboard",
    generated_at: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    bundle_file = Path(bundle_path)
    bundle = _read_required_json(bundle_file)
    inputs = _dict(bundle.get("inputs"))
    root = bundle_file.parent.parent

    registry_file = _resolve_path(inputs.get("registry_path"))
    audit_file = _resolve_optional_path(audit_path, inputs.get("project_audit_path"), _candidate(root, "audit", "project_audit.json"))
    request_file = _resolve_optional_path(
        request_history_summary_path,
        inputs.get("request_history_summary_path"),
        _candidate(root, "request-history-summary", "request_history_summary.json"),
    )
    gate_file = _resolve_optional_path(gate_path, None, _candidate(root, "release-gate", "gate_report.json"))
    maturity_file = _resolve_optional_path(maturity_path, None, _candidate(root, "maturity-summary", "maturity_summary.json"))
    ci_file = _resolve_optional_path(
        ci_workflow_hygiene_path,
        inputs.get("ci_workflow_hygiene_path"),
        _candidate(root, "ci-workflow-hygiene", "ci_workflow_hygiene.json"),
    )
    coverage_file = _resolve_optional_path(
        test_coverage_report_path,
        inputs.get("test_coverage_report_path"),
        _candidate(root, "test-coverage", "test_coverage_report.json"),
    )

    registry = _read_json(registry_file, warnings, "registry") if registry_file is not None else None
    audit = _read_json(audit_file, warnings, "project audit") if audit_file is not None else None
    request_history = _read_json(request_file, warnings, "request history summary") if request_file is not None else None
    gate = _read_json(gate_file, warnings, "release gate") if gate_file is not None else None
    maturity = _read_json(maturity_file, warnings, "maturity summary") if maturity_file is not None else None
    ci_workflow = _read_json(ci_file, warnings, "CI workflow hygiene") if ci_file is not None else None
    test_coverage = _read_json(coverage_file, warnings, "test coverage report") if coverage_file is not None else None

    panels = [
        _registry_panel(registry_file, registry),
        _bundle_panel(bundle_file, bundle),
        _audit_panel(audit_file, audit),
        _gate_panel(gate_file, gate),
        _request_history_panel(request_file, request_history),
        _benchmark_history_panel(bundle, gate if isinstance(gate, dict) else None),
        _maturity_panel(maturity_file, maturity),
        _ci_workflow_panel(ci_file, ci_workflow, bundle),
        _test_coverage_panel(coverage_file, test_coverage, bundle),
    ]
    actions = _actions(bundle, gate if isinstance(gate, dict) else None, audit if isinstance(audit, dict) else None, panels)
    summary = _summary(
        bundle,
        gate if isinstance(gate, dict) else None,
        audit if isinstance(audit, dict) else None,
        request_history if isinstance(request_history, dict) else None,
        maturity if isinstance(maturity, dict) else None,
        ci_workflow if isinstance(ci_workflow, dict) else None,
        test_coverage if isinstance(test_coverage, dict) else None,
        panels,
    )
    evidence = _evidence(bundle)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "bundle_path": str(bundle_file),
        "inputs": {
            "registry_path": None if registry_file is None else str(registry_file),
            "project_audit_path": None if audit_file is None else str(audit_file),
            "release_gate_path": None if gate_file is None else str(gate_file),
            "request_history_summary_path": None if request_file is None else str(request_file),
            "maturity_summary_path": None if maturity_file is None else str(maturity_file),
            "ci_workflow_hygiene_path": None if ci_file is None else str(ci_file),
            "test_coverage_report_path": None if coverage_file is None else str(coverage_file),
        },
        "summary": summary,
        "panels": panels,
        "actions": actions,
        "evidence": evidence,
        "warnings": warnings,
    }


def _summary(
    bundle: dict[str, Any],
    gate: dict[str, Any] | None,
    audit: dict[str, Any] | None,
    request_history: dict[str, Any] | None,
    maturity: dict[str, Any] | None,
    ci_workflow: dict[str, Any] | None,
    test_coverage: dict[str, Any] | None,
    panels: list[dict[str, Any]],
) -> dict[str, Any]:
    bundle_summary = _dict(bundle.get("summary"))
    gate_summary = _dict(gate.get("summary")) if isinstance(gate, dict) else {}
    audit_summary = _dict(audit.get("summary")) if isinstance(audit, dict) else {}
    request_summary = _dict(request_history.get("summary")) if isinstance(request_history, dict) else {}
    maturity_summary = _dict(maturity.get("summary")) if isinstance(maturity, dict) else {}
    ci_summary = _dict(ci_workflow.get("summary")) if isinstance(ci_workflow, dict) else {}
    ci_context = _dict(bundle.get("ci_workflow_context"))
    coverage_summary = _dict(test_coverage.get("summary")) if isinstance(test_coverage, dict) else {}
    coverage_context = _dict(bundle.get("test_coverage_context"))
    benchmark_summary = _benchmark_history_summary(bundle_summary, gate_summary)
    status = _readiness_status(panels, gate)
    return {
        "readiness_status": status,
        "decision": _decision(status),
        "release_name": bundle.get("release_name"),
        "release_status": bundle_summary.get("release_status"),
        "gate_status": gate_summary.get("gate_status"),
        "gate_decision": gate_summary.get("decision"),
        "audit_status": audit_summary.get("overall_status") or bundle_summary.get("audit_status"),
        "audit_score_percent": audit_summary.get("score_percent") or bundle_summary.get("audit_score_percent"),
        "request_history_status": request_summary.get("status") or bundle_summary.get("request_history_status"),
        "request_history_records": request_summary.get("total_log_records") or bundle_summary.get("request_history_records"),
        **benchmark_summary,
        "maturity_status": maturity_summary.get("overall_status"),
        "current_version": maturity_summary.get("current_version"),
        "ci_workflow_status": ci_summary.get("status") or bundle_summary.get("ci_workflow_status") or ci_context.get("status"),
        "ci_workflow_failed_checks": first_present(
            ci_summary.get("failed_check_count"),
            bundle_summary.get("ci_workflow_failed_checks"),
            ci_context.get("failed_check_count"),
        ),
        "ci_workflow_node24_actions": first_present(
            ci_summary.get("node24_native_actions"),
            ci_summary.get("node24_native_action_count"),
            bundle_summary.get("ci_workflow_node24_actions"),
            ci_context.get("node24_native_actions"),
            ci_context.get("node24_native_action_count"),
        ),
        "ci_workflow_required_order_count": first_present(
            ci_summary.get("required_order_count"),
            bundle_summary.get("ci_workflow_required_order_count"),
            ci_context.get("required_order_count"),
        ),
        "ci_workflow_order_violation_count": first_present(
            ci_summary.get("order_violation_count"),
            bundle_summary.get("ci_workflow_order_violation_count"),
            ci_context.get("order_violation_count"),
        ),
        "ci_workflow_tiny_scorecard_plan_digest_gate_ready": first_present(
            ci_summary.get("tiny_scorecard_plan_digest_gate_ready"),
            bundle_summary.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready"),
            ci_context.get("tiny_scorecard_plan_digest_gate_ready"),
        ),
        "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready": first_present(
            ci_summary.get("baseline_candidate_threshold_boundary_gate_check_ready"),
            bundle_summary.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready"),
            ci_context.get("baseline_candidate_threshold_boundary_gate_check_ready"),
        ),
        "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready": first_present(
            ci_summary.get("baseline_candidate_threshold_boundary_gate_plan_check_ready"),
            bundle_summary.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready"),
            ci_context.get("baseline_candidate_threshold_boundary_gate_plan_check_ready"),
        ),
        "ci_workflow_archived_path_portability_check_ready": first_present(
            ci_summary.get("archived_path_portability_check_ready"),
            bundle_summary.get("ci_workflow_archived_path_portability_check_ready"),
            ci_context.get("archived_path_portability_check_ready"),
        ),
        "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": first_present(
            ci_summary.get("promoted_seed_receipt_contract_failure_smoke_plan_check_ready"),
            bundle_summary.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready"),
            ci_context.get("promoted_seed_receipt_contract_failure_smoke_plan_check_ready"),
        ),
        "ci_workflow_release_readiness_drift_contract_smoke_ready": first_present(
            ci_summary.get("release_readiness_drift_contract_smoke_ready"),
            bundle_summary.get("ci_workflow_release_readiness_drift_contract_smoke_ready"),
            ci_context.get("release_readiness_drift_contract_smoke_ready"),
        ),
        "test_coverage_status": coverage_summary.get("status") or bundle_summary.get("test_coverage_status") or coverage_context.get("status"),
        "test_coverage_percent": first_present(
            coverage_summary.get("line_coverage_percent"),
            bundle_summary.get("test_coverage_percent"),
            coverage_context.get("line_coverage_percent"),
        ),
        "test_coverage_fail_under": first_present(
            coverage_summary.get("fail_under"),
            bundle_summary.get("test_coverage_fail_under"),
            coverage_context.get("fail_under"),
        ),
        "test_coverage_gap": first_present(
            coverage_summary.get("coverage_gap"),
            bundle_summary.get("test_coverage_gap"),
            coverage_context.get("coverage_gap"),
        ),
        "ready_runs": bundle_summary.get("ready_runs") or audit_summary.get("ready_runs"),
        "missing_artifacts": bundle_summary.get("missing_artifacts"),
        "panel_count": len(panels),
        "fail_panel_count": sum(1 for panel in panels if panel.get("status") == "fail"),
        "warn_panel_count": sum(1 for panel in panels if panel.get("status") == "warn"),
    }


def _readiness_status(panels: list[dict[str, Any]], gate: dict[str, Any] | None) -> str:
    if not isinstance(gate, dict):
        return "incomplete"
    statuses = [panel.get("status") for panel in panels]
    if "fail" in statuses:
        return "blocked"
    if "warn" in statuses:
        return "review"
    return "ready"


def _decision(status: str) -> str:
    return {
        "ready": "ship",
        "review": "review",
        "blocked": "block",
        "incomplete": "collect-evidence",
    }.get(status, "review")


def _actions(bundle: dict[str, Any], gate: dict[str, Any] | None, audit: dict[str, Any] | None, panels: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    has_issue = False
    for panel in panels:
        if panel.get("status") == "fail":
            has_issue = True
            items.append(f"Fix failing panel: {panel.get('title')} ({panel.get('detail')}).")
        elif panel.get("status") == "warn":
            has_issue = True
            items.append(f"Review warning panel: {panel.get('title')} ({panel.get('detail')}).")
    if isinstance(gate, dict):
        for check in _list_of_dicts(gate.get("checks")):
            if check.get("status") in {"fail", "warn"}:
                has_issue = True
                items.append(f"Gate {check.get('status')}: {check.get('id')} - {check.get('detail')}")
    if not has_issue:
        items.append("All readiness panels are clean; keep this dashboard with the release evidence.")
    if isinstance(audit, dict):
        for item in _string_list(audit.get("recommendations")):
            if item not in items:
                items.append(item)
    for item in _string_list(bundle.get("recommendations")):
        if item not in items:
            items.append(item)
    return items


def _benchmark_history_summary(bundle_summary: dict[str, Any], gate_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "benchmark_history_status": first_present(gate_summary.get("benchmark_history_status"), bundle_summary.get("benchmark_history_status")),
        "benchmark_history_entries": first_present(gate_summary.get("benchmark_history_entries"), bundle_summary.get("benchmark_history_entries")),
        "benchmark_history_ready": first_present(gate_summary.get("benchmark_history_ready"), bundle_summary.get("benchmark_history_ready")),
        "benchmark_history_review": first_present(gate_summary.get("benchmark_history_review"), bundle_summary.get("benchmark_history_review")),
        "benchmark_history_blocked": first_present(gate_summary.get("benchmark_history_blocked"), bundle_summary.get("benchmark_history_blocked")),
        "benchmark_history_case_regressions": first_present(
            gate_summary.get("benchmark_history_case_regressions"),
            bundle_summary.get("benchmark_history_case_regressions"),
        ),
        "benchmark_history_generation_flag_regressions": first_present(
            gate_summary.get("benchmark_history_generation_flag_regressions"),
            bundle_summary.get("benchmark_history_generation_flag_regressions"),
        ),
        "benchmark_history_suite_design_non_comparison_ready_entries": first_present(
            gate_summary.get("benchmark_history_suite_design_non_comparison_ready_entries"),
            bundle_summary.get("benchmark_history_suite_design_non_comparison_ready_entries"),
        ),
        "benchmark_history_design_comparison_changed_entries": first_present(
            gate_summary.get("benchmark_history_design_comparison_changed_entries"),
            bundle_summary.get("benchmark_history_design_comparison_changed_entries"),
        ),
        "benchmark_history_readiness_requirement_status": first_present(
            gate_summary.get("benchmark_history_readiness_requirement_status"),
            bundle_summary.get("benchmark_history_readiness_requirement_status"),
        ),
        "benchmark_history_readiness_requirement_exit_code": first_present(
            gate_summary.get("benchmark_history_readiness_requirement_exit_code"),
            bundle_summary.get("benchmark_history_readiness_requirement_exit_code"),
        ),
        "benchmark_history_readiness_requirement_failed_reasons": first_present(
            gate_summary.get("benchmark_history_readiness_requirement_failed_reasons"),
            bundle_summary.get("benchmark_history_readiness_requirement_failed_reasons"),
        ),
        "benchmark_history_model_quality_claim": first_present(
            gate_summary.get("benchmark_history_model_quality_claim"),
            bundle_summary.get("benchmark_history_model_quality_claim"),
        ),
        "benchmark_history_latest_boundary": first_present(
            gate_summary.get("benchmark_history_latest_boundary"),
            bundle_summary.get("benchmark_history_latest_boundary"),
        ),
    }


def _evidence(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for artifact in _list_of_dicts(bundle.get("artifacts")):
        rows.append(
            {
                "key": artifact.get("key"),
                "title": artifact.get("title"),
                "path": artifact.get("path"),
                "kind": artifact.get("kind"),
                "exists": artifact.get("exists"),
                "size_bytes": artifact.get("size_bytes"),
            }
        )
    return rows


def _resolve_optional_path(explicit: str | Path | None, hinted: Any, candidate: Path) -> Path | None:
    if explicit is not None:
        return Path(explicit)
    resolved = _resolve_path(hinted)
    if resolved is not None:
        return resolved
    return candidate if candidate.exists() else None


def _resolve_path(value: Any) -> Path | None:
    if value in {None, ""}:
        return None
    return Path(str(value))


def _candidate(root: Path, directory: str, filename: str) -> Path:
    return root / directory / filename


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release readiness input must be a JSON object: {path}")
    return payload


def _read_json(path: Path, warnings: list[str], label: str) -> dict[str, Any] | None:
    if not path.exists():
        warnings.append(f"{label} not found: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"{path} must contain a JSON object")
        return None
    return payload


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
