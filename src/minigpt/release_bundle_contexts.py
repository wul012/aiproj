from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict as _dict, first_present, list_of_dicts as _list_of_dicts


def _request_history_context(request_history_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        return {"available": False, "status": None, "total_log_records": None}
    summary = _dict(request_history_summary.get("summary"))
    return {
        "available": True,
        "request_log": request_history_summary.get("request_log"),
        "status": summary.get("status"),
        "total_log_records": summary.get("total_log_records"),
        "invalid_record_count": summary.get("invalid_record_count"),
        "timeout_rate": summary.get("timeout_rate"),
        "bad_request_rate": summary.get("bad_request_rate"),
        "error_rate": summary.get("error_rate"),
        "latest_timestamp": summary.get("latest_timestamp"),
    }


def _benchmark_history_context(benchmark_history: dict[str, Any] | None, audit: dict[str, Any] | None) -> dict[str, Any]:
    audit_context = _dict(audit.get("benchmark_history_context")) if isinstance(audit, dict) else {}
    if isinstance(benchmark_history, dict):
        summary = _dict(benchmark_history.get("summary"))
        readiness = _dict(benchmark_history.get("readiness_requirement"))
        entries = _list_of_dicts(benchmark_history.get("entries"))
        latest = entries[-1] if entries else {}
        return {
            "available": True,
            "evidence_kind": benchmark_history.get("evidence_kind") or audit_context.get("evidence_kind"),
            "entry_count": summary.get("entry_count") if summary else len(entries),
            "promote_count": summary.get("promote_count"),
            "ready_count": summary.get("ready_count"),
            "review_count": summary.get("review_count"),
            "blocked_count": summary.get("blocked_count"),
            "case_regression_entry_count": summary.get("case_regression_entry_count"),
            "generation_quality_flag_regression_entry_count": summary.get("generation_quality_flag_regression_entry_count"),
            "best_candidate_name": summary.get("best_candidate_name"),
            "best_entry_name": summary.get("best_entry_name"),
            "model_quality_claim": summary.get("model_quality_claim"),
            "readiness_requirement_status": first_present(readiness.get("status"), audit_context.get("readiness_requirement_status")),
            "readiness_requirement_decision": first_present(readiness.get("decision"), audit_context.get("readiness_requirement_decision")),
            "readiness_requirement_exit_code": first_present(readiness.get("exit_code"), audit_context.get("readiness_requirement_exit_code")),
            "readiness_requirement_failed_reasons": _string_list(readiness.get("failed_reasons"))
            or _string_list(audit_context.get("readiness_requirement_failed_reasons")),
            "latest_boundary": latest.get("boundary") or audit_context.get("latest_boundary"),
            "latest_decision_status": latest.get("decision_status") or audit_context.get("latest_decision_status"),
            "latest_promotion_readiness": latest.get("promotion_readiness") or audit_context.get("latest_promotion_readiness"),
        }
    if audit_context:
        return dict(audit_context)
    return {
        "available": False,
        "entry_count": None,
        "ready_count": None,
        "readiness_requirement_status": None,
        "readiness_requirement_exit_code": None,
        "readiness_requirement_failed_reasons": [],
        "model_quality_claim": None,
        "latest_boundary": None,
    }


def _status_from_benchmark_context(context: dict[str, Any]) -> str | None:
    if not context.get("available"):
        return None
    regression_keys = (
        "review_count",
        "blocked_count",
        "case_regression_entry_count",
        "generation_quality_flag_regression_entry_count",
    )
    if any(_int(context.get(key)) > 0 for key in regression_keys):
        return "warn"
    if context.get("readiness_requirement_status") == "fail" or _int(context.get("readiness_requirement_exit_code")) > 0:
        return "warn"
    if _int(context.get("entry_count")) == 0 or _int(context.get("ready_count")) == 0:
        return "warn"
    if context.get("model_quality_claim") == "not_claimed":
        return "warn"
    return "pass"


def _benchmark_history_summary_status(audit_status: Any, context: dict[str, Any]) -> str | None:
    context_status = _status_from_benchmark_context(context)
    if audit_status == "warn" or context_status == "warn":
        return "warn"
    return audit_status or context_status


def _ci_workflow_context(ci_workflow_hygiene: dict[str, Any] | None, audit: dict[str, Any] | None) -> dict[str, Any]:
    audit_context = _dict(audit.get("ci_workflow_context")) if isinstance(audit, dict) else {}
    if isinstance(ci_workflow_hygiene, dict):
        summary = _dict(ci_workflow_hygiene.get("summary"))
        return {
            "available": True,
            "workflow_path": ci_workflow_hygiene.get("workflow_path") or audit_context.get("workflow_path"),
            "status": summary.get("status"),
            "decision": summary.get("decision"),
            "check_count": summary.get("check_count"),
            "failed_check_count": summary.get("failed_check_count"),
            "action_count": summary.get("action_count"),
            "node24_native_action_count": summary.get("node24_native_action_count"),
            "forbidden_env_count": summary.get("forbidden_env_count"),
            "missing_step_count": summary.get("missing_step_count"),
            "required_order_count": summary.get("required_order_count"),
            "order_violation_count": summary.get("order_violation_count"),
            "release_readiness_drift_contract_smoke_present": summary.get("release_readiness_drift_contract_smoke_present")
            or audit_context.get("release_readiness_drift_contract_smoke_present"),
            "release_readiness_drift_contract_smoke_order_ready": summary.get("release_readiness_drift_contract_smoke_order_ready")
            or audit_context.get("release_readiness_drift_contract_smoke_order_ready"),
            "release_readiness_drift_contract_smoke_ready": summary.get("release_readiness_drift_contract_smoke_ready")
            or audit_context.get("release_readiness_drift_contract_smoke_ready"),
            "python_version": summary.get("python_version"),
        }
    if audit_context:
        return dict(audit_context)
    return {
        "available": False,
        "status": None,
        "failed_check_count": None,
        "required_order_count": None,
        "order_violation_count": None,
        "release_readiness_drift_contract_smoke_present": None,
        "release_readiness_drift_contract_smoke_order_ready": None,
        "release_readiness_drift_contract_smoke_ready": None,
    }


def _test_coverage_context(test_coverage_report: dict[str, Any] | None, audit: dict[str, Any] | None) -> dict[str, Any]:
    audit_context = _dict(audit.get("test_coverage_context")) if isinstance(audit, dict) else {}
    if isinstance(test_coverage_report, dict):
        summary = _dict(test_coverage_report.get("summary"))
        return {
            "available": True,
            "status": summary.get("status"),
            "decision": summary.get("decision"),
            "line_coverage_percent": summary.get("line_coverage_percent"),
            "covered_lines": summary.get("covered_lines"),
            "num_statements": summary.get("num_statements"),
            "missing_lines": summary.get("missing_lines"),
            "file_count": summary.get("file_count"),
            "threshold_enabled": summary.get("threshold_enabled"),
            "fail_under": summary.get("fail_under"),
            "coverage_gap": summary.get("coverage_gap"),
        }
    if audit_context:
        return dict(audit_context)
    return {"available": False, "status": None, "line_coverage_percent": None, "coverage_gap": None}


def _top_runs(registry: dict[str, Any], model_card: dict[str, Any] | None) -> list[dict[str, Any]]:
    if model_card and isinstance(model_card.get("top_runs"), list):
        return _list_of_dicts(model_card.get("top_runs"))[:5]
    by_name = {str(run.get("name")): run for run in _list_of_dicts(registry.get("runs"))}
    rows = []
    for item in _list_of_dicts(registry.get("loss_leaderboard")):
        run = by_name.get(str(item.get("name")), item)
        rows.append(run)
    return rows[:5] or _list_of_dicts(registry.get("runs"))[:5]


def _audit_checks(audit: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not audit:
        return []
    return _list_of_dicts(audit.get("checks"))


def _recommendations(model_card: dict[str, Any] | None, audit: dict[str, Any] | None, summary: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if audit:
        items.extend(_string_list(audit.get("recommendations")))
    if model_card:
        for item in _string_list(model_card.get("recommendations")):
            if item not in items:
                items.append(item)
    if summary.get("release_status") == "release-ready":
        items.insert(0, "Release evidence is complete; keep this bundle with the tagged version.")
    elif summary.get("release_status") == "blocked":
        items.insert(0, "Do not present this release as complete until failed audit checks are fixed.")
    elif summary.get("release_status") == "needs-audit":
        items.insert(0, "Generate project_audit.json before treating this as a release bundle.")
    return items or ["Review release evidence before sharing the project externally."]


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
