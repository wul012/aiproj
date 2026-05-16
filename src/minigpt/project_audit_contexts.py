from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict as _dict


def build_request_history_summary_check(
    request_history_summary: dict[str, Any] | None,
    request_history_summary_path: Path | None,
) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        detail = (
            f"request_history_summary.json missing at {request_history_summary_path}"
            if request_history_summary_path is not None
            else "request_history_summary.json missing; local inference stability was not summarized."
        )
        return _check("request_history_summary", "Request history summary is clean", "warn", detail)
    summary = _dict(request_history_summary.get("summary"))
    status = str(summary.get("status") or "missing")
    records = summary.get("total_log_records")
    invalid = summary.get("invalid_record_count")
    timeout_rate = summary.get("timeout_rate")
    error_rate = summary.get("error_rate")
    audit_status = "pass" if status == "pass" else "warn"
    detail = (
        f"status={status}; records={_fmt_any(records)}; invalid={_fmt_any(invalid)}; "
        f"timeout_rate={_fmt_any(timeout_rate)}; error_rate={_fmt_any(error_rate)}."
    )
    return _check(
        "request_history_summary",
        "Request history summary is clean",
        audit_status,
        detail,
        {
            "status": status,
            "total_log_records": records,
            "invalid_record_count": invalid,
            "timeout_rate": timeout_rate,
            "bad_request_rate": summary.get("bad_request_rate"),
            "error_rate": error_rate,
            "path": None if request_history_summary_path is None else str(request_history_summary_path),
        },
    )


def build_request_history_context(request_history_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        return {
            "available": False,
            "status": None,
            "total_log_records": None,
            "timeout_rate": None,
            "error_rate": None,
        }
    summary = _dict(request_history_summary.get("summary"))
    return {
        "available": True,
        "request_log": request_history_summary.get("request_log"),
        "status": summary.get("status"),
        "total_log_records": summary.get("total_log_records"),
        "invalid_record_count": summary.get("invalid_record_count"),
        "timeout_count": summary.get("timeout_count"),
        "bad_request_count": summary.get("bad_request_count"),
        "error_count": summary.get("error_count"),
        "timeout_rate": summary.get("timeout_rate"),
        "bad_request_rate": summary.get("bad_request_rate"),
        "error_rate": summary.get("error_rate"),
        "unique_checkpoint_count": summary.get("unique_checkpoint_count"),
        "latest_timestamp": summary.get("latest_timestamp"),
    }


def build_ci_workflow_hygiene_check(
    ci_workflow_hygiene: dict[str, Any] | None,
    ci_workflow_hygiene_path: Path | None,
) -> dict[str, Any]:
    if not isinstance(ci_workflow_hygiene, dict):
        detail = (
            f"ci_workflow_hygiene.json missing at {ci_workflow_hygiene_path}"
            if ci_workflow_hygiene_path is not None
            else "ci_workflow_hygiene.json missing; CI workflow policy was not summarized."
        )
        return _check("ci_workflow_hygiene", "CI workflow hygiene is clean", "warn", detail)
    summary = _dict(ci_workflow_hygiene.get("summary"))
    status = str(summary.get("status") or "missing")
    action_count = summary.get("action_count")
    node24_actions = summary.get("node24_native_action_count")
    failed_checks = summary.get("failed_check_count")
    missing_steps = summary.get("missing_step_count")
    forbidden_env = summary.get("forbidden_env_count")
    audit_status = "pass" if status == "pass" else "warn"
    detail = (
        f"status={status}; actions={_fmt_any(action_count)}; node24_native={_fmt_any(node24_actions)}; "
        f"failed_checks={_fmt_any(failed_checks)}; forbidden_env={_fmt_any(forbidden_env)}; "
        f"missing_steps={_fmt_any(missing_steps)}."
    )
    return _check(
        "ci_workflow_hygiene",
        "CI workflow hygiene is clean",
        audit_status,
        detail,
        {
            "status": status,
            "decision": summary.get("decision"),
            "action_count": action_count,
            "node24_native_action_count": node24_actions,
            "failed_check_count": failed_checks,
            "forbidden_env_count": forbidden_env,
            "missing_step_count": missing_steps,
            "python_version": summary.get("python_version"),
            "path": None if ci_workflow_hygiene_path is None else str(ci_workflow_hygiene_path),
        },
    )


def build_ci_workflow_context(ci_workflow_hygiene: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(ci_workflow_hygiene, dict):
        return {
            "available": False,
            "status": None,
            "decision": None,
            "action_count": None,
            "node24_native_action_count": None,
            "failed_check_count": None,
        }
    summary = _dict(ci_workflow_hygiene.get("summary"))
    return {
        "available": True,
        "workflow_path": ci_workflow_hygiene.get("workflow_path"),
        "status": summary.get("status"),
        "decision": summary.get("decision"),
        "check_count": summary.get("check_count"),
        "failed_check_count": summary.get("failed_check_count"),
        "action_count": summary.get("action_count"),
        "node24_native_action_count": summary.get("node24_native_action_count"),
        "forbidden_env_count": summary.get("forbidden_env_count"),
        "missing_step_count": summary.get("missing_step_count"),
        "python_version": summary.get("python_version"),
    }


def _check(
    check_id: str,
    title: str,
    status: str,
    detail: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "title": title,
        "status": status,
        "detail": detail,
        "evidence": evidence or {},
    }


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


__all__ = [
    "build_ci_workflow_context",
    "build_ci_workflow_hygiene_check",
    "build_request_history_context",
    "build_request_history_summary_check",
]
