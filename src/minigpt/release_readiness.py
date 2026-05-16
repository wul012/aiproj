from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    utc_now,
)
from minigpt.release_readiness_artifacts import (
    render_release_readiness_html,
    render_release_readiness_markdown,
    write_release_readiness_html,
    write_release_readiness_json,
    write_release_readiness_markdown,
    write_release_readiness_outputs,
)


def build_release_readiness_dashboard(
    bundle_path: str | Path,
    *,
    gate_path: str | Path | None = None,
    audit_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    maturity_path: str | Path | None = None,
    ci_workflow_hygiene_path: str | Path | None = None,
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

    registry = _read_json(registry_file, warnings, "registry") if registry_file is not None else None
    audit = _read_json(audit_file, warnings, "project audit") if audit_file is not None else None
    request_history = _read_json(request_file, warnings, "request history summary") if request_file is not None else None
    gate = _read_json(gate_file, warnings, "release gate") if gate_file is not None else None
    maturity = _read_json(maturity_file, warnings, "maturity summary") if maturity_file is not None else None
    ci_workflow = _read_json(ci_file, warnings, "CI workflow hygiene") if ci_file is not None else None

    panels = [
        _registry_panel(registry_file, registry),
        _bundle_panel(bundle_file, bundle),
        _audit_panel(audit_file, audit),
        _gate_panel(gate_file, gate),
        _request_history_panel(request_file, request_history),
        _maturity_panel(maturity_file, maturity),
        _ci_workflow_panel(ci_file, ci_workflow, bundle),
    ]
    actions = _actions(bundle, gate if isinstance(gate, dict) else None, audit if isinstance(audit, dict) else None, panels)
    summary = _summary(
        bundle,
        gate if isinstance(gate, dict) else None,
        audit if isinstance(audit, dict) else None,
        request_history if isinstance(request_history, dict) else None,
        maturity if isinstance(maturity, dict) else None,
        ci_workflow if isinstance(ci_workflow, dict) else None,
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
    panels: list[dict[str, Any]],
) -> dict[str, Any]:
    bundle_summary = _dict(bundle.get("summary"))
    gate_summary = _dict(gate.get("summary")) if isinstance(gate, dict) else {}
    audit_summary = _dict(audit.get("summary")) if isinstance(audit, dict) else {}
    request_summary = _dict(request_history.get("summary")) if isinstance(request_history, dict) else {}
    maturity_summary = _dict(maturity.get("summary")) if isinstance(maturity, dict) else {}
    ci_summary = _dict(ci_workflow.get("summary")) if isinstance(ci_workflow, dict) else {}
    ci_context = _dict(bundle.get("ci_workflow_context"))
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
        "maturity_status": maturity_summary.get("overall_status"),
        "current_version": maturity_summary.get("current_version"),
        "ci_workflow_status": ci_summary.get("status") or bundle_summary.get("ci_workflow_status") or ci_context.get("status"),
        "ci_workflow_failed_checks": _first_present(
            ci_summary.get("failed_check_count"),
            bundle_summary.get("ci_workflow_failed_checks"),
            ci_context.get("failed_check_count"),
        ),
        "ci_workflow_node24_actions": _first_present(
            ci_summary.get("node24_native_actions"),
            ci_summary.get("node24_native_action_count"),
            bundle_summary.get("ci_workflow_node24_actions"),
            ci_context.get("node24_native_actions"),
            ci_context.get("node24_native_action_count"),
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


def _registry_panel(path: Path | None, registry: dict[str, Any] | None) -> dict[str, Any]:
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


def _bundle_panel(path: Path, bundle: dict[str, Any]) -> dict[str, Any]:
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


def _audit_panel(path: Path | None, audit: dict[str, Any] | None) -> dict[str, Any]:
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


def _gate_panel(path: Path | None, gate: dict[str, Any] | None) -> dict[str, Any]:
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


def _request_history_panel(path: Path | None, request_history: dict[str, Any] | None) -> dict[str, Any]:
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


def _maturity_panel(path: Path | None, maturity: dict[str, Any] | None) -> dict[str, Any]:
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


def _ci_workflow_panel(path: Path | None, ci_workflow: dict[str, Any] | None, bundle: dict[str, Any]) -> dict[str, Any]:
    if isinstance(ci_workflow, dict):
        summary = _dict(ci_workflow.get("summary"))
        ci_status = str(summary.get("status") or "missing")
        return _panel(
            "ci_workflow_hygiene",
            "CI Workflow Hygiene",
            "pass" if ci_status == "pass" else "warn",
            "status="
            + ci_status
            + f"; failed_checks={_fmt(summary.get('failed_check_count'))}; node24_native={_fmt(_first_present(summary.get('node24_native_actions'), summary.get('node24_native_action_count')))}",
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
            + _fmt(_first_present(bundle_summary.get("ci_workflow_failed_checks"), bundle_context.get("failed_check_count")))
            + "; node24_native="
            + _fmt(
                _first_present(
                    bundle_summary.get("ci_workflow_node24_actions"),
                    bundle_context.get("node24_native_actions"),
                    bundle_context.get("node24_native_action_count"),
                )
            )
            + "; source=bundle summary/context",
            path,
        )
    return _panel("ci_workflow_hygiene", "CI Workflow Hygiene", "warn", "ci_workflow_hygiene.json missing", path)


def _panel(key: str, title: str, status: str, detail: str, source_path: Path | None) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "status": status,
        "detail": detail,
        "source_path": None if source_path is None else str(source_path),
    }


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


def _status_from_check_status(value: str) -> str:
    if value == "pass":
        return "pass"
    if value == "fail" or value == "blocked":
        return "fail"
    return "warn"


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


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


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
