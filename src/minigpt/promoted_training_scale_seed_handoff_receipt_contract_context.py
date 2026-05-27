from __future__ import annotations

from typing import Any

from minigpt.report_utils import string_list


def suite_design_scopes(assurance: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        suite_design_scope(
            "selected",
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_"
                "suite_design_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_"
                "suite_design_regression_names"
            ),
        ),
        suite_design_scope(
            "handoff",
            assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count"),
            assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names"),
        ),
        suite_design_scope(
            "comparison_ready",
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names"
            ),
        ),
    ]


def suite_design_scope(scope: str, count: Any, names: Any) -> dict[str, Any]:
    resolved_count = int_value(count)
    resolved_names = string_list(names)
    return {
        "scope": scope,
        "count": resolved_count,
        "names": resolved_names,
        "name_count": len(resolved_names),
        "count_matches_names": resolved_count == len(resolved_names),
    }


def ci_boundary_plan_check_scopes(assurance: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        ci_boundary_plan_check_scope(
            "selected",
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_"
                "ci_boundary_plan_check_ready_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_"
                "ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        ci_boundary_plan_check_scope(
            "handoff",
            assurance.get(
                "embedded_receipt_check_receipt_handoff_batch_maturity_"
                "ci_boundary_plan_check_ready_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_handoff_selected_batch_maturity_"
                "ci_boundary_plan_check_ready_regression_total"
            ),
        ),
        ci_boundary_plan_check_scope(
            "comparison_ready",
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_"
                "ci_boundary_plan_check_ready_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_"
                "ci_boundary_plan_check_ready_regression_total"
            ),
        ),
    ]


def ci_boundary_plan_check_scope(scope: str, handoff_count: Any, selected_count: Any) -> dict[str, Any]:
    resolved_handoff_count = int_value(handoff_count)
    resolved_selected_count = int_value(selected_count)
    return {
        "scope": scope,
        "handoff_count": resolved_handoff_count,
        "selected_count": resolved_selected_count,
        "selected_within_handoff": 0 <= resolved_selected_count <= resolved_handoff_count,
    }


def contract_issues(
    assurance: dict[str, Any],
    scopes: list[dict[str, Any]],
    boundary_scopes: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    receipt_schema_version = int_value(assurance.get("embedded_receipt_check_receipt_schema_version"))
    if assurance.get("status") != "pass":
        issues.append("handoff assurance must pass")
        issues.extend(f"assurance.{issue}" for issue in string_list(assurance.get("issues")))
    if receipt_schema_version < 3:
        issues.append("receipt schema version must be >= 3 for suite-design name contract")
    if receipt_schema_version < 4:
        issues.append("receipt schema version must be >= 4 for CI boundary plan-check contract")
    if assurance.get("embedded_receipt_check_sidecar_status") != "pass":
        issues.append("embedded receipt-check sidecar status must pass")
    for scope in scopes:
        if not scope.get("count_matches_names"):
            issues.append(
                f"{scope.get('scope')} suite-design regression count {scope.get('count')} "
                f"does not match name count {scope.get('name_count')}"
            )
    for scope in boundary_scopes:
        if not scope.get("selected_within_handoff"):
            issues.append(
                f"{scope.get('scope')} CI boundary plan-check selected count {scope.get('selected_count')} "
                f"exceeds handoff count {scope.get('handoff_count')}"
            )
    return issues


def row_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "ci_boundary_plan_check_scopes",
    "contract_issues",
    "int_value",
    "row_list",
    "suite_design_scopes",
]
