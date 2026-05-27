from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (
    CONTRACT_SUMMARY_HTML_FILENAME,
    CONTRACT_SUMMARY_MARKDOWN_FILENAME,
    CONTRACT_SUMMARY_TEXT_FILENAME,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_html,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_text,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_rows import (
    contract_check_rows,
    contract_check_status_counts,
    contract_check_type_summary,
    failed_contract_check_count,
)


CHECK_STATUS_DOMAIN = ["pass", "fail"]


def summary_field_checks(
    expected: dict[str, Any],
    actual: dict[str, Any],
    compare_keys: Iterable[str],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for key in compare_keys:
        expected_value = stable_value(expected.get(key))
        actual_value = stable_value(actual.get(key))
        status = "pass" if expected_value == actual_value else "fail"
        checks.append(
            {
                "id": f"summary_field.{key}",
                "check_type": "summary_field",
                "target": f"summary.{key}",
                "key": key,
                "status": status,
                "status_domain": CHECK_STATUS_DOMAIN,
                "required": True,
                "expected": expected_value,
                "actual": actual_value,
                "expected_kind": value_kind(expected_value),
                "actual_kind": value_kind(actual_value),
                "detail": "field matches rebuilt summary" if status == "pass" else "field differs from rebuilt summary",
            }
        )
    return checks


def summary_field_issues(checks: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for check in checks:
        if check.get("status") != "pass":
            issues.append(
                f"summary.{check.get('key')} expected {check.get('expected')!r} "
                f"but got {check.get('actual')!r}"
            )
    return issues


def contract_profile_checks(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = contract_check_rows(summary)
    return [
        contract_profile_check(
            "contract_check_count",
            "summary.contract_check_count",
            len(rows),
            summary.get("contract_check_count"),
            "contract check count must match the embedded contract check rows",
        ),
        contract_profile_check(
            "failed_contract_check_count",
            "summary.failed_contract_check_count",
            failed_contract_check_count(rows),
            summary.get("failed_contract_check_count"),
            "failed contract check count must match the embedded contract check rows",
        ),
        contract_profile_check(
            "contract_check_status_counts",
            "summary.contract_check_status_counts",
            contract_check_status_counts(rows),
            summary.get("contract_check_status_counts"),
            "contract check status counts must be derived from the embedded contract check rows",
        ),
        contract_profile_check(
            "contract_check_type_summary",
            "summary.contract_check_type_summary",
            contract_check_type_summary(rows),
            summary.get("contract_check_type_summary"),
            "contract check type summary must be derived from the embedded contract check rows",
        ),
    ]


def contract_profile_check(
    check_id: str,
    target: str,
    expected: Any,
    actual: Any,
    detail: str,
) -> dict[str, Any]:
    expected_value = stable_value(expected)
    actual_value = stable_value(actual)
    status = "pass" if expected_value == actual_value else "fail"
    return {
        "id": f"contract_profile.{check_id}",
        "check_type": "contract_profile_consistency",
        "target": target,
        "key": check_id,
        "status": status,
        "status_domain": CHECK_STATUS_DOMAIN,
        "required": True,
        "expected": expected_value,
        "actual": actual_value,
        "expected_kind": value_kind(expected_value),
        "actual_kind": value_kind(actual_value),
        "detail": detail if status == "pass" else f"{detail}; aggregate differs from rows",
    }


def contract_profile_issues(checks: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for check in checks:
        if check.get("status") != "pass":
            issues.append(
                f"contract profile {check.get('target')} expected {check.get('expected')!r} "
                f"but got {check.get('actual')!r}"
            )
    return issues


def summary_check_family_summary(
    summary_field_checks: list[dict[str, Any]],
    contract_profile_checks: list[dict[str, Any]],
    sidecar_checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        check_family_row("summary_field", "summary.summary_field_checks", summary_field_checks),
        check_family_row("contract_profile", "summary.contract_profile_checks", contract_profile_checks),
        check_family_row("sidecar", "summary.sidecar_checks", sidecar_checks),
    ]


def check_family_row(family: str, target: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    rows = check_rows(checks)
    failed_rows = [row for row in rows if row.get("status") != "pass"]
    failed_targets = sorted({check_target(row) for row in failed_rows if check_target(row)})
    failed_ids = sorted({str(row.get("id")) for row in failed_rows if row.get("id")})
    return {
        "family": family,
        "check_type": "summary_check_family",
        "target": target,
        "status": "pass" if not failed_rows else "fail",
        "status_domain": CHECK_STATUS_DOMAIN,
        "check_count": len(rows),
        "passed_count": len(rows) - len(failed_rows),
        "failed_count": len(failed_rows),
        "required_failed_count": sum(1 for row in failed_rows if row.get("required")),
        "failed_targets": failed_targets,
        "failed_target_count": len(failed_targets),
        "failed_ids": failed_ids,
        "failed_id_count": len(failed_ids),
    }


def summary_check_failed_targets(
    summary_field_checks: list[dict[str, Any]],
    contract_profile_checks: list[dict[str, Any]],
    sidecar_checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, checks in (
        ("summary_field", summary_field_checks),
        ("contract_profile", contract_profile_checks),
        ("sidecar", sidecar_checks),
    ):
        rows.extend(failed_target_row(family, row) for row in check_rows(checks) if row.get("status") != "pass")
    return rows


def failed_target_row(family: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": family,
        "id": row.get("id"),
        "check_type": row.get("check_type"),
        "target": check_target(row),
        "status": row.get("status"),
        "required": row.get("required"),
        "detail": row.get("detail"),
    }


def check_target(row: dict[str, Any]) -> str:
    value = row.get("target") or row.get("path") or row.get("id") or ""
    return str(value)


def check_summary_sidecars(summary_dir: Path, expected: dict[str, Any]) -> dict[str, Any]:
    text_path = summary_dir / CONTRACT_SUMMARY_TEXT_FILENAME
    markdown_path = summary_dir / CONTRACT_SUMMARY_MARKDOWN_FILENAME
    html_path = summary_dir / CONTRACT_SUMMARY_HTML_FILENAME
    checks = [
        sidecar_check(
            "text",
            text_path,
            render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(expected),
        ),
        sidecar_check(
            "markdown",
            markdown_path,
            render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(expected),
        ),
        sidecar_check(
            "html",
            html_path,
            render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(expected),
        ),
    ]
    issues = [str(check.get("detail")) for check in checks if check.get("status") != "pass"]
    return sidecar_payload(text_path, markdown_path, html_path, issues, checks)


def missing_sidecars(summary_dir: Path) -> dict[str, Any]:
    text_path = summary_dir / CONTRACT_SUMMARY_TEXT_FILENAME
    markdown_path = summary_dir / CONTRACT_SUMMARY_MARKDOWN_FILENAME
    html_path = summary_dir / CONTRACT_SUMMARY_HTML_FILENAME
    return sidecar_payload(text_path, markdown_path, html_path, ["expected summary could not be rebuilt"], [])


def sidecar_check(check_id: str, path: Path, expected_text: str) -> dict[str, Any]:
    expected_sha256 = sha256_text(expected_text)
    base = {
        "id": check_id,
        "check_type": "sidecar_digest",
        "target": str(path),
        "required": True,
        "status_domain": CHECK_STATUS_DOMAIN,
        "path": str(path),
        "expected_kind": "sha256",
        "actual_kind": "sha256",
        "expected_sha256": expected_sha256,
    }
    if not path.is_file():
        return {
            **base,
            "status": "fail",
            "exists": False,
            "actual_kind": None,
            "actual_sha256": None,
            "detail": f"{path.name} is missing",
        }
    try:
        actual = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return {
            **base,
            "status": "fail",
            "exists": True,
            "actual_kind": None,
            "actual_sha256": None,
            "detail": f"{path.name} could not be read: {exc}",
        }
    actual_sha256 = sha256_text(actual)
    status = "pass" if actual == expected_text else "fail"
    return {
        **base,
        "status": status,
        "exists": True,
        "actual_sha256": actual_sha256,
        "detail": (
            "content matches rebuilt contract summary"
            if status == "pass"
            else f"{path.name} content does not match rebuilt contract summary"
        ),
    }


def sidecar_payload(
    text_path: Path,
    markdown_path: Path,
    html_path: Path,
    issues: list[str],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": "pass" if not issues else "fail",
        "issue_count": len(issues),
        "issues": issues,
        "checks": checks,
        "text_path": str(text_path),
        "text_exists": text_path.is_file(),
        "markdown_path": str(markdown_path),
        "markdown_exists": markdown_path.is_file(),
        "html_path": str(html_path),
        "html_exists": html_path.is_file(),
    }


def stable_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return value


def check_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def failed_check_count(checks: list[dict[str, Any]]) -> int:
    return sum(1 for check in checks if check.get("status") != "pass")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def value_kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


__all__ = [
    "check_rows",
    "check_summary_sidecars",
    "contract_profile_checks",
    "contract_profile_issues",
    "failed_check_count",
    "json_text",
    "missing_sidecars",
    "summary_check_failed_targets",
    "summary_check_family_summary",
    "summary_field_checks",
    "summary_field_issues",
]
