from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import list_of_dicts as _list_of_dicts


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
    order_violations = summary.get("order_violation_count")
    plan_digest_gate_ready = summary.get("tiny_scorecard_plan_digest_gate_ready")
    forbidden_env = summary.get("forbidden_env_count")
    audit_status = "pass" if status == "pass" else "warn"
    detail = (
        f"status={status}; actions={_fmt_any(action_count)}; node24_native={_fmt_any(node24_actions)}; "
        f"failed_checks={_fmt_any(failed_checks)}; forbidden_env={_fmt_any(forbidden_env)}; "
        f"missing_steps={_fmt_any(missing_steps)}; order_violations={_fmt_any(order_violations)}; "
        f"tiny_scorecard_plan_digest_gate_ready={_fmt_any(plan_digest_gate_ready)}."
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
            "required_order_count": summary.get("required_order_count"),
            "order_violation_count": order_violations,
            "tiny_scorecard_plan_digest_gate_present": summary.get("tiny_scorecard_plan_digest_gate_present"),
            "tiny_scorecard_plan_digest_gate_order_ready": summary.get("tiny_scorecard_plan_digest_gate_order_ready"),
            "tiny_scorecard_plan_digest_gate_ready": plan_digest_gate_ready,
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
            "required_order_count": None,
            "order_violation_count": None,
            "tiny_scorecard_plan_digest_gate_present": None,
            "tiny_scorecard_plan_digest_gate_order_ready": None,
            "tiny_scorecard_plan_digest_gate_ready": None,
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
        "required_order_count": summary.get("required_order_count"),
        "order_violation_count": summary.get("order_violation_count"),
        "tiny_scorecard_plan_digest_gate_present": summary.get("tiny_scorecard_plan_digest_gate_present"),
        "tiny_scorecard_plan_digest_gate_order_ready": summary.get("tiny_scorecard_plan_digest_gate_order_ready"),
        "tiny_scorecard_plan_digest_gate_ready": summary.get("tiny_scorecard_plan_digest_gate_ready"),
        "python_version": summary.get("python_version"),
    }


def build_test_coverage_check(
    test_coverage_report: dict[str, Any] | None,
    test_coverage_report_path: Path | None,
) -> dict[str, Any]:
    if not isinstance(test_coverage_report, dict):
        detail = (
            f"test_coverage_report.json missing at {test_coverage_report_path}"
            if test_coverage_report_path is not None
            else "test_coverage_report.json missing; coverage gate evidence was not summarized."
        )
        return _check("test_coverage_report", "Test coverage gate is clean", "warn", detail)
    summary = _dict(test_coverage_report.get("summary"))
    status = str(summary.get("status") or "missing")
    decision = summary.get("decision")
    percent = summary.get("line_coverage_percent")
    fail_under = summary.get("fail_under")
    threshold_enabled = summary.get("threshold_enabled")
    coverage_gap = summary.get("coverage_gap")
    audit_status = "pass" if status == "pass" and threshold_enabled else "warn"
    detail = (
        f"status={status}; decision={_fmt_any(decision)}; line_coverage={_fmt_any(percent)}; "
        f"fail_under={_fmt_any(fail_under)}; coverage_gap={_fmt_any(coverage_gap)}; "
        f"threshold_enabled={_fmt_any(threshold_enabled)}."
    )
    return _check(
        "test_coverage_report",
        "Test coverage gate is clean",
        audit_status,
        detail,
        {
            "status": status,
            "decision": decision,
            "line_coverage_percent": percent,
            "covered_lines": summary.get("covered_lines"),
            "num_statements": summary.get("num_statements"),
            "missing_lines": summary.get("missing_lines"),
            "file_count": summary.get("file_count"),
            "threshold_enabled": threshold_enabled,
            "fail_under": fail_under,
            "coverage_gap": coverage_gap,
            "path": None if test_coverage_report_path is None else str(test_coverage_report_path),
        },
    )


def build_test_coverage_context(test_coverage_report: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(test_coverage_report, dict):
        return {
            "available": False,
            "status": None,
            "decision": None,
            "line_coverage_percent": None,
            "threshold_enabled": None,
            "fail_under": None,
            "coverage_gap": None,
        }
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


def build_benchmark_history_check(
    benchmark_history: dict[str, Any] | None,
    benchmark_history_path: Path | None,
) -> dict[str, Any]:
    if not isinstance(benchmark_history, dict):
        detail = (
            f"benchmark_history.json missing at {benchmark_history_path}"
            if benchmark_history_path is not None
            else "benchmark_history.json missing; repeated benchmark evidence was not summarized."
        )
        return _check("benchmark_history", "Benchmark history is audit-ready", "warn", detail)
    context = build_benchmark_history_context(benchmark_history)
    entry_count = _int(context.get("entry_count"))
    ready_count = _int(context.get("ready_count"))
    review_count = _int(context.get("review_count"))
    blocked_count = _int(context.get("blocked_count"))
    case_regressions = _int(context.get("case_regression_entry_count"))
    flag_regressions = _int(context.get("generation_quality_flag_regression_entry_count"))
    readiness_status = context.get("readiness_requirement_status")
    readiness_exit_code = _int(context.get("readiness_requirement_exit_code"))
    readiness_failed_reasons = _string_list(context.get("readiness_requirement_failed_reasons"))
    model_claim = context.get("model_quality_claim")
    status = "pass"
    if (
        entry_count <= 0
        or ready_count <= 0
        or review_count > 0
        or blocked_count > 0
        or case_regressions > 0
        or flag_regressions > 0
        or readiness_status == "fail"
        or readiness_exit_code > 0
        or model_claim == "not_claimed"
    ):
        status = "warn"
    detail = (
        f"entries={entry_count}; ready={ready_count}; review={review_count}; blocked={blocked_count}; "
        f"case_regressions={case_regressions}; generation_flag_regressions={flag_regressions}; "
        f"readiness_requirement={_fmt_any(readiness_status)}; readiness_exit={_fmt_any(context.get('readiness_requirement_exit_code'))}; "
        f"readiness_failed_reasons={_fmt_any(', '.join(readiness_failed_reasons) if readiness_failed_reasons else 'none')}; "
        f"model_quality_claim={_fmt_any(model_claim)}; latest_boundary={_fmt_any(context.get('latest_boundary'))}."
    )
    evidence = {
        **context,
        "path": None if benchmark_history_path is None else str(benchmark_history_path),
    }
    return _check("benchmark_history", "Benchmark history is audit-ready", status, detail, evidence)


def build_benchmark_history_context(benchmark_history: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(benchmark_history, dict):
        return {
            "available": False,
            "entry_count": None,
            "ready_count": None,
            "review_count": None,
            "blocked_count": None,
            "case_regression_entry_count": None,
            "generation_quality_flag_regression_entry_count": None,
            "readiness_requirement_status": None,
            "readiness_requirement_decision": None,
            "readiness_requirement_exit_code": None,
            "readiness_requirement_failed_reasons": [],
            "model_quality_claim": None,
            "latest_boundary": None,
        }
    summary = _dict(benchmark_history.get("summary"))
    readiness = _dict(benchmark_history.get("readiness_requirement"))
    entries = _list_of_dicts(benchmark_history.get("entries"))
    latest = entries[-1] if entries else {}
    return {
        "available": True,
        "evidence_kind": benchmark_history.get("evidence_kind"),
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
        "readiness_requirement_status": readiness.get("status"),
        "readiness_requirement_decision": readiness.get("decision"),
        "readiness_requirement_exit_code": readiness.get("exit_code"),
        "readiness_requirement_failed_reasons": _string_list(readiness.get("failed_reasons")),
        "latest_boundary": latest.get("boundary"),
        "latest_decision_status": latest.get("decision_status"),
        "latest_promotion_readiness": latest.get("promotion_readiness"),
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


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


__all__ = [
    "build_benchmark_history_check",
    "build_benchmark_history_context",
    "build_ci_workflow_context",
    "build_ci_workflow_hygiene_check",
    "build_request_history_context",
    "build_request_history_summary_check",
    "build_test_coverage_check",
    "build_test_coverage_context",
]
