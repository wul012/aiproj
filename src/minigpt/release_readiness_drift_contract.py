from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict,
    list_of_dicts,
    string_list,
    write_json_payload,
)


COMPARISON_JSON_FILENAME = "release_readiness_comparison.json"
CHECK_JSON_FILENAME = "release_readiness_drift_contract_check.json"
CHECK_TEXT_FILENAME = "release_readiness_drift_contract_check.txt"

BASELINE_REASONS_FIELD = "baseline_benchmark_history_readiness_requirement_failed_reasons"
COMPARED_REASONS_FIELD = "compared_benchmark_history_readiness_requirement_failed_reasons"
ADDED_COUNT_FIELD = "benchmark_history_readiness_requirement_failed_reason_added_count"
REMOVED_COUNT_FIELD = "benchmark_history_readiness_requirement_failed_reason_removed_count"
ADDED_FIELD = "benchmark_history_readiness_requirement_failed_reason_added"
REMOVED_FIELD = "benchmark_history_readiness_requirement_failed_reason_removed"
DRIFT_STATUS_FIELD = "benchmark_history_readiness_requirement_failed_reason_drift_status"
RECOVERY_DELTA_COUNT_FIELD = "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"
MIXED_DELTA_COUNT_FIELD = "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"
DRIFT_STATUS_COUNTS_FIELD = "benchmark_history_readiness_requirement_failed_reason_drift_status_counts"

VALID_DRIFT_STATUSES = {"stable", "regressed", "recovered", "mixed"}


def resolve_release_readiness_comparison_path(path: str | Path) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    candidate = source / COMPARISON_JSON_FILENAME
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"release readiness comparison JSON not found: {source}")


def load_release_readiness_comparison(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release readiness comparison JSON must contain an object: {source}")
    return dict(payload)


def check_release_readiness_drift_contract(
    comparison: dict[str, Any],
    *,
    comparison_path: str | Path | None = None,
) -> dict[str, Any]:
    deltas = list_of_dicts(comparison.get("deltas"))
    summary = as_dict(comparison.get("summary"))
    delta_checks = [_delta_check(index, delta) for index, delta in enumerate(deltas)]
    expected_summary = _expected_summary(delta_checks)
    issues = _delta_issues(delta_checks) + _summary_issues(summary, expected_summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "continue" if status == "pass" else "fix-release-readiness-drift-contract",
        "comparison_path": "" if comparison_path is None else str(comparison_path),
        "delta_count": len(deltas),
        "delta_pass_count": sum(1 for check in delta_checks if check.get("status") == "pass"),
        "delta_fail_count": sum(1 for check in delta_checks if check.get("status") == "fail"),
        "expected_summary": expected_summary,
        "actual_summary": _actual_summary(summary),
        "delta_checks": delta_checks,
        "issue_count": len(issues),
        "issues": issues,
    }


def render_release_readiness_drift_contract_check(report: dict[str, Any]) -> str:
    expected_summary = as_dict(report.get("expected_summary"))
    actual_summary = as_dict(report.get("actual_summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("comparison_path", report.get("comparison_path")),
        ("delta_count", report.get("delta_count")),
        ("delta_pass_count", report.get("delta_pass_count")),
        ("delta_fail_count", report.get("delta_fail_count")),
        ("expected_added_count", expected_summary.get(ADDED_COUNT_FIELD)),
        ("actual_added_count", actual_summary.get(ADDED_COUNT_FIELD)),
        ("expected_removed_count", expected_summary.get(REMOVED_COUNT_FIELD)),
        ("actual_removed_count", actual_summary.get(REMOVED_COUNT_FIELD)),
        ("expected_recovery_delta_count", expected_summary.get(RECOVERY_DELTA_COUNT_FIELD)),
        ("actual_recovery_delta_count", actual_summary.get(RECOVERY_DELTA_COUNT_FIELD)),
        ("expected_mixed_delta_count", expected_summary.get(MIXED_DELTA_COUNT_FIELD)),
        ("actual_mixed_delta_count", actual_summary.get(MIXED_DELTA_COUNT_FIELD)),
        ("expected_drift_status_counts", json.dumps(expected_summary.get(DRIFT_STATUS_COUNTS_FIELD) or {}, sort_keys=True)),
        ("actual_drift_status_counts", json.dumps(actual_summary.get(DRIFT_STATUS_COUNTS_FIELD) or {}, sort_keys=True)),
        ("issue_count", report.get("issue_count")),
    ]
    issues = list_of_dicts(report.get("issues"))
    if issues:
        first = issues[0]
        rows.extend(
            [
                ("first_issue_code", first.get("code")),
                ("first_issue_target", first.get("target")),
                ("first_issue_detail", first.get("detail")),
            ]
        )
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_release_readiness_drift_contract_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": target / CHECK_JSON_FILENAME,
        "text": target / CHECK_TEXT_FILENAME,
    }
    write_json_payload(report, paths["json"])
    paths["text"].write_text(render_release_readiness_drift_contract_check(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _delta_check(index: int, delta: dict[str, Any]) -> dict[str, Any]:
    expected_added = _reason_additions(delta.get(BASELINE_REASONS_FIELD), delta.get(COMPARED_REASONS_FIELD))
    expected_removed = _reason_removals(delta.get(BASELINE_REASONS_FIELD), delta.get(COMPARED_REASONS_FIELD))
    expected_status = _reason_drift_status(expected_added, expected_removed)
    actual_added = _clean_strings(delta.get(ADDED_FIELD))
    actual_removed = _clean_strings(delta.get(REMOVED_FIELD))
    actual_status = _string_or_empty(delta.get(DRIFT_STATUS_FIELD))
    mismatches = []
    if _optional_int(delta.get(ADDED_COUNT_FIELD)) != len(expected_added):
        mismatches.append(ADDED_COUNT_FIELD)
    if _optional_int(delta.get(REMOVED_COUNT_FIELD)) != len(expected_removed):
        mismatches.append(REMOVED_COUNT_FIELD)
    if actual_added != expected_added:
        mismatches.append(ADDED_FIELD)
    if actual_removed != expected_removed:
        mismatches.append(REMOVED_FIELD)
    if actual_status != expected_status:
        mismatches.append(DRIFT_STATUS_FIELD)
    return {
        "delta_index": index,
        "baseline_release": delta.get("baseline_release"),
        "compared_release": delta.get("compared_release"),
        "status": "pass" if not mismatches else "fail",
        "mismatches": mismatches,
        "expected_added_count": len(expected_added),
        "actual_added_count": _optional_int(delta.get(ADDED_COUNT_FIELD)),
        "expected_removed_count": len(expected_removed),
        "actual_removed_count": _optional_int(delta.get(REMOVED_COUNT_FIELD)),
        "expected_added": expected_added,
        "actual_added": actual_added,
        "expected_removed": expected_removed,
        "actual_removed": actual_removed,
        "expected_drift_status": expected_status,
        "actual_drift_status": actual_status,
    }


def _delta_issues(delta_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for check in delta_checks:
        target_prefix = f"deltas[{check['delta_index']}]"
        if check.get("actual_drift_status") and check.get("actual_drift_status") not in VALID_DRIFT_STATUSES:
            issues.append(
                _issue(
                    "delta_failed_reason_drift_status_invalid",
                    f"{target_prefix}.{DRIFT_STATUS_FIELD}",
                    sorted(VALID_DRIFT_STATUSES),
                    check.get("actual_drift_status"),
                )
            )
        if ADDED_COUNT_FIELD in check.get("mismatches", []):
            issues.append(
                _issue(
                    "delta_failed_reason_added_count_mismatch",
                    f"{target_prefix}.{ADDED_COUNT_FIELD}",
                    check.get("expected_added_count"),
                    check.get("actual_added_count"),
                )
            )
        if REMOVED_COUNT_FIELD in check.get("mismatches", []):
            issues.append(
                _issue(
                    "delta_failed_reason_removed_count_mismatch",
                    f"{target_prefix}.{REMOVED_COUNT_FIELD}",
                    check.get("expected_removed_count"),
                    check.get("actual_removed_count"),
                )
            )
        if ADDED_FIELD in check.get("mismatches", []):
            issues.append(
                _issue(
                    "delta_failed_reason_added_mismatch",
                    f"{target_prefix}.{ADDED_FIELD}",
                    check.get("expected_added"),
                    check.get("actual_added"),
                )
            )
        if REMOVED_FIELD in check.get("mismatches", []):
            issues.append(
                _issue(
                    "delta_failed_reason_removed_mismatch",
                    f"{target_prefix}.{REMOVED_FIELD}",
                    check.get("expected_removed"),
                    check.get("actual_removed"),
                )
            )
        if DRIFT_STATUS_FIELD in check.get("mismatches", []):
            issues.append(
                _issue(
                    "delta_failed_reason_drift_status_mismatch",
                    f"{target_prefix}.{DRIFT_STATUS_FIELD}",
                    check.get("expected_drift_status"),
                    check.get("actual_drift_status"),
                )
            )
    return issues


def _summary_issues(summary: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    actual = _actual_summary(summary)
    checks = [
        ("summary_failed_reason_added_count_mismatch", ADDED_COUNT_FIELD),
        ("summary_failed_reason_removed_count_mismatch", REMOVED_COUNT_FIELD),
        ("summary_failed_reason_added_mismatch", ADDED_FIELD),
        ("summary_failed_reason_removed_mismatch", REMOVED_FIELD),
        ("summary_recovery_delta_count_mismatch", RECOVERY_DELTA_COUNT_FIELD),
        ("summary_mixed_delta_count_mismatch", MIXED_DELTA_COUNT_FIELD),
        ("summary_drift_status_counts_mismatch", DRIFT_STATUS_COUNTS_FIELD),
    ]
    return [
        _issue(code, f"summary.{field}", expected.get(field), actual.get(field))
        for code, field in checks
        if actual.get(field) != expected.get(field)
    ]


def _actual_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        ADDED_COUNT_FIELD: _optional_int(summary.get(ADDED_COUNT_FIELD)),
        REMOVED_COUNT_FIELD: _optional_int(summary.get(REMOVED_COUNT_FIELD)),
        ADDED_FIELD: _clean_strings(summary.get(ADDED_FIELD)),
        REMOVED_FIELD: _clean_strings(summary.get(REMOVED_FIELD)),
        RECOVERY_DELTA_COUNT_FIELD: _optional_int(summary.get(RECOVERY_DELTA_COUNT_FIELD)),
        MIXED_DELTA_COUNT_FIELD: _optional_int(summary.get(MIXED_DELTA_COUNT_FIELD)),
        DRIFT_STATUS_COUNTS_FIELD: _count_map(summary.get(DRIFT_STATUS_COUNTS_FIELD)),
    }


def _expected_summary(delta_checks: list[dict[str, Any]]) -> dict[str, Any]:
    expected_statuses = [_string_or_empty(check.get("expected_drift_status")) or "stable" for check in delta_checks]
    return {
        ADDED_COUNT_FIELD: sum(int(check.get("expected_added_count") or 0) for check in delta_checks),
        REMOVED_COUNT_FIELD: sum(int(check.get("expected_removed_count") or 0) for check in delta_checks),
        ADDED_FIELD: _unique_strings(reason for check in delta_checks for reason in string_list(check.get("expected_added"))),
        REMOVED_FIELD: _unique_strings(reason for check in delta_checks for reason in string_list(check.get("expected_removed"))),
        RECOVERY_DELTA_COUNT_FIELD: sum(1 for status in expected_statuses if status == "recovered"),
        MIXED_DELTA_COUNT_FIELD: sum(1 for status in expected_statuses if status == "mixed"),
        DRIFT_STATUS_COUNTS_FIELD: _counts(expected_statuses),
    }


def _reason_additions(baseline: Any, compared: Any) -> list[str]:
    baseline_reasons = set(_clean_strings(baseline))
    return [reason for reason in _clean_strings(compared) if reason not in baseline_reasons]


def _reason_removals(baseline: Any, compared: Any) -> list[str]:
    compared_reasons = set(_clean_strings(compared))
    return [reason for reason in _clean_strings(baseline) if reason not in compared_reasons]


def _reason_drift_status(added: list[str], removed: list[str]) -> str:
    if added and removed:
        return "mixed"
    if added:
        return "regressed"
    if removed:
        return "recovered"
    return "stable"


def _issue(code: str, target: str, expected: Any, actual: Any) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "blocker",
        "target": target,
        "expected": expected,
        "actual": actual,
        "detail": "release readiness failed-reason drift must match the baseline/compared requirement reason lists",
    }


def _clean_strings(value: Any) -> list[str]:
    return [item.strip() for item in string_list(value) if item.strip()]


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_or_empty(value: Any) -> str:
    return "" if value is None else str(value)


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


def _count_map(value: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, count in as_dict(value).items():
        number = _optional_int(count)
        if number is not None:
            result[str(key)] = number
    return result


__all__ = [
    "check_release_readiness_drift_contract",
    "load_release_readiness_comparison",
    "render_release_readiness_drift_contract_check",
    "resolve_release_readiness_comparison_path",
    "write_release_readiness_drift_contract_outputs",
]
