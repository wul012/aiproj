from __future__ import annotations

from typing import Any


CONTRACT_CHECK_STATUS_DOMAIN = ["pass", "fail"]


def build_contract_checks(
    assurance: dict[str, Any],
    scopes: list[dict[str, Any]],
    boundary_scopes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    receipt_schema_version = _int(assurance.get("embedded_receipt_check_receipt_schema_version"))
    checks = [
        contract_check(
            "assurance_status_pass",
            "status_equals",
            "assurance.status",
            "assurance",
            "pass",
            assurance.get("status"),
            "handoff assurance must pass",
        ),
        contract_check(
            "schema_v3_ready",
            "schema_readiness",
            "receipt.schema_v3_ready",
            "receipt",
            True,
            receipt_schema_version >= 3,
            "receipt schema must support suite-design name contract",
        ),
        contract_check(
            "schema_v4_ready",
            "schema_readiness",
            "receipt.schema_v4_ready",
            "receipt",
            True,
            receipt_schema_version >= 4,
            "receipt schema must support CI boundary plan-check contract",
        ),
        contract_check(
            "embedded_receipt_check_sidecar_pass",
            "status_equals",
            "embedded_receipt_check.sidecar_status",
            "embedded_receipt_check",
            "pass",
            assurance.get("embedded_receipt_check_sidecar_status"),
            "embedded receipt-check sidecar must pass",
        ),
    ]
    checks.extend(
        contract_check(
            f"suite_design_{scope.get('scope')}_count_matches_names",
            "count_consistency",
            f"suite_design.{scope.get('scope')}.count_matches_names",
            str(scope.get("scope")),
            True,
            bool(scope.get("count_matches_names")),
            "suite-design regression count must match name count",
        )
        for scope in scopes
    )
    checks.extend(
        contract_check(
            f"ci_boundary_plan_check_{scope.get('scope')}_selected_within_handoff",
            "selected_within_handoff",
            f"ci_boundary_plan_check.{scope.get('scope')}.selected_within_handoff",
            str(scope.get("scope")),
            True,
            bool(scope.get("selected_within_handoff")),
            "selected CI boundary plan-check count must not exceed handoff count",
        )
        for scope in boundary_scopes
    )
    return checks


def contract_check(
    check_id: str,
    check_type: str,
    target: str,
    scope: str,
    expected: Any,
    actual: Any,
    detail: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "check_type": check_type,
        "target": target,
        "scope": scope,
        "status": "pass" if actual == expected else "fail",
        "status_domain": CONTRACT_CHECK_STATUS_DOMAIN,
        "required": True,
        "expected": expected,
        "actual": actual,
        "expected_kind": value_kind(expected),
        "actual_kind": value_kind(actual),
        "detail": detail,
    }


def failed_contract_check_count(checks: list[dict[str, Any]]) -> int:
    return sum(1 for check in checks if check.get("status") != "pass")


def contract_check_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    value = summary.get("contract_checks")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


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


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "build_contract_checks",
    "contract_check",
    "contract_check_rows",
    "failed_contract_check_count",
]
