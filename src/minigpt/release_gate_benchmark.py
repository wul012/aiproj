from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import number_or_default


def benchmark_history_gate_result(
    audit_checks: list[dict[str, Any]],
    summary: dict[str, Any],
    require_benchmark_history: bool,
) -> str:
    if not require_benchmark_history:
        return "pass"
    statuses = _benchmark_history_statuses(audit_checks, summary)
    if not statuses:
        return "fail"
    if "fail" in statuses or "missing" in statuses:
        return "fail"
    summary_status = _benchmark_history_summary_result(summary)
    if summary_status == "fail":
        return "fail"
    if "warn" in statuses or summary_status == "warn":
        return "warn"
    return "pass"


def benchmark_history_gate_detail(
    audit_checks: list[dict[str, Any]],
    summary: dict[str, Any],
    require_benchmark_history: bool,
) -> str:
    if not require_benchmark_history:
        return "benchmark history release evidence is not required by policy."
    by_id = _audit_checks_by_id(audit_checks)
    check = _dict(by_id.get("benchmark_history"))
    summary_status = summary.get("benchmark_history_status")
    if not check and not summary_status:
        return "missing required benchmark_history audit check or benchmark history bundle summary."
    return (
        f"benchmark_history={check.get('status') or 'missing'}; "
        f"summary_status={summary_status or 'missing'}; "
        f"entries={_integer(summary.get('benchmark_history_entries'))}; "
        f"ready={_integer(summary.get('benchmark_history_ready'))}; "
        f"review={_integer(summary.get('benchmark_history_review'))}; "
        f"blocked={_integer(summary.get('benchmark_history_blocked'))}; "
        f"case_regressions={_integer(summary.get('benchmark_history_case_regressions'))}; "
        f"generation_flag_regressions={_integer(summary.get('benchmark_history_generation_flag_regressions'))}; "
        f"suite_design_not_ready={_integer(summary.get('benchmark_history_suite_design_non_comparison_ready_entries'))}; "
        f"design_comparison_changed={_integer(summary.get('benchmark_history_design_comparison_changed_entries'))}; "
        f"readiness_requirement={summary.get('benchmark_history_readiness_requirement_status') or 'missing'}; "
        f"readiness_exit={_integer(summary.get('benchmark_history_readiness_requirement_exit_code'))}; "
        f"readiness_failed_reasons={_failed_reasons(summary)}; "
        f"model_quality_claim={summary.get('benchmark_history_model_quality_claim') or 'missing'}; "
        f"latest_boundary={summary.get('benchmark_history_latest_boundary') or 'missing'}."
    )


def _benchmark_history_statuses(audit_checks: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    by_id = _audit_checks_by_id(audit_checks)
    check = _dict(by_id.get("benchmark_history"))
    statuses = []
    if check:
        statuses.append(str(check.get("status") or "missing"))
    if summary.get("benchmark_history_status") is not None:
        statuses.append(str(summary.get("benchmark_history_status") or "missing"))
    return statuses


def _benchmark_history_summary_result(summary: dict[str, Any]) -> str:
    status = str(summary.get("benchmark_history_status") or "")
    if status == "fail" or _integer(summary.get("benchmark_history_blocked")) > 0:
        return "fail"
    warn_keys = (
        "benchmark_history_review",
        "benchmark_history_case_regressions",
        "benchmark_history_generation_flag_regressions",
        "benchmark_history_suite_design_non_comparison_ready_entries",
    )
    if status == "warn" or any(_integer(summary.get(key)) > 0 for key in warn_keys):
        return "warn"
    if (
        summary.get("benchmark_history_readiness_requirement_status") == "fail"
        or _integer(summary.get("benchmark_history_readiness_requirement_exit_code")) > 0
    ):
        return "warn"
    if summary.get("benchmark_history_status") is not None:
        entries = _integer(summary.get("benchmark_history_entries"))
        ready = _integer(summary.get("benchmark_history_ready"))
        if entries <= 0 or ready <= 0:
            return "warn"
    if summary.get("benchmark_history_model_quality_claim") == "not_claimed":
        return "warn"
    return "pass"


def _failed_reasons(summary: dict[str, Any]) -> str:
    reasons = summary.get("benchmark_history_readiness_requirement_failed_reasons")
    if not isinstance(reasons, list) or not reasons:
        return "none"
    return ",".join(str(item) for item in reasons if str(item).strip()) or "none"


def _audit_checks_by_id(audit_checks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(check.get("id")): check for check in audit_checks if check.get("id")}


def _integer(value: Any) -> int:
    return int(number_or_default(value, 0, int))
