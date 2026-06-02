from __future__ import annotations

from typing import Any

from minigpt.report_utils import positive_int_mapping, string_list


EMBEDDED_RECEIPT_CHECK_COMPARE_KEYS = (
    "status",
    "decision",
    "exit_code",
    "checker_exit_code",
    "blocking_source",
    "failed_requirements",
    "selected_handoff_batch_maturity_ci_regression_count",
    "selected_handoff_batch_maturity_ci_regression_reason_counts",
    "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
    "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "handoff_batch_maturity_ci_regression_count",
    "handoff_batch_maturity_ci_regression_reason_counts",
    "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "handoff_selected_batch_maturity_ci_regression_reason_counts",
    "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    "selected_handoff_batch_maturity_suite_design_regression_count",
    "selected_handoff_batch_maturity_suite_design_regression_names",
    "handoff_batch_maturity_suite_design_regression_count",
    "handoff_batch_maturity_suite_design_regression_names",
    "comparison_ready_handoff_batch_maturity_suite_design_regression_count",
    "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
    "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
    "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    "comparison_ready_handoff_batch_maturity_suite_design_regression_names",
    "comparison_exclusion_reasons",
    "issue_count",
    "issues",
)

RECEIPT_SCHEMA_V2_REQUIRED_FIELDS = (
    "selected_handoff_batch_maturity_ci_regression_count",
    "handoff_batch_maturity_ci_regression_count",
    "comparison_exclusion_reasons",
)
RECEIPT_SCHEMA_V3_REQUIRED_FIELDS = (
    "selected_handoff_batch_maturity_suite_design_regression_count",
    "selected_handoff_batch_maturity_suite_design_regression_names",
    "handoff_batch_maturity_suite_design_regression_count",
    "handoff_batch_maturity_suite_design_regression_names",
    "comparison_ready_handoff_batch_maturity_suite_design_regression_count",
    "comparison_ready_handoff_batch_maturity_suite_design_regression_names",
)
RECEIPT_SCHEMA_V4_REQUIRED_FIELDS = (
    "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
)
RECEIPT_SCHEMA_V5_REQUIRED_FIELDS = (
    "clean_batch_review_requirement_selected_ci_regression_reason_counts",
    "selected_handoff_batch_maturity_ci_regression_reason_counts",
    "selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
    "handoff_batch_maturity_ci_regression_reason_counts",
    "handoff_selected_batch_maturity_ci_regression_reason_counts",
    "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
    "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
)
RECEIPT_SCHEMA_V5_TEXT_FIELDS = tuple(f"receipt_{field}" for field in RECEIPT_SCHEMA_V5_REQUIRED_FIELDS)
EMBEDDED_RECEIPT_SCHEMA_V5_TEXT_FIELDS = tuple(
    f"embedded_receipt_check_receipt_{field}" for field in RECEIPT_SCHEMA_V5_REQUIRED_FIELDS
)


def receipt_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def normalized_receipt_check_value(key: str, value: Any) -> Any:
    if key in {
        "exit_code",
        "checker_exit_code",
        "issue_count",
        "selected_handoff_batch_maturity_ci_regression_count",
        "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "handoff_batch_maturity_ci_regression_count",
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
        "selected_handoff_batch_maturity_suite_design_regression_count",
        "handoff_batch_maturity_suite_design_regression_count",
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count",
        "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    }:
        return receipt_int(value)
    if key in {
        "failed_requirements",
        "selected_handoff_batch_maturity_suite_design_regression_names",
        "handoff_batch_maturity_suite_design_regression_names",
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names",
        "comparison_exclusion_reasons",
        "issues",
    }:
        return string_list(value)
    if key in {
        "clean_batch_review_requirement_selected_ci_regression_reason_counts",
        "selected_handoff_batch_maturity_ci_regression_reason_counts",
        "selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
        "handoff_batch_maturity_ci_regression_reason_counts",
        "handoff_selected_batch_maturity_ci_regression_reason_counts",
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
    }:
        return positive_int_mapping(value)
    if key == "blocking_source":
        return str(value) if value is not None else None
    return str(value or "")


def v2_receipt_field_issues(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in RECEIPT_SCHEMA_V2_REQUIRED_FIELDS:
        if key not in payload:
            issues.append(f"schema_version >= 2 receipt must include {key}")
    if receipt_int(payload.get("selected_handoff_batch_maturity_ci_regression_count")) < 0:
        issues.append("selected_handoff_batch_maturity_ci_regression_count must be >= 0")
    if receipt_int(payload.get("handoff_batch_maturity_ci_regression_count")) < 0:
        issues.append("handoff_batch_maturity_ci_regression_count must be >= 0")
    if "comparison_exclusion_reasons" in payload and not isinstance(payload.get("comparison_exclusion_reasons"), list):
        issues.append("comparison_exclusion_reasons must be a list")
    return issues


def v3_receipt_field_issues(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in RECEIPT_SCHEMA_V3_REQUIRED_FIELDS:
        if key not in payload:
            issues.append(f"schema_version >= 3 receipt must include {key}")
    for key in (
        "selected_handoff_batch_maturity_suite_design_regression_count",
        "handoff_batch_maturity_suite_design_regression_count",
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count",
    ):
        if receipt_int(payload.get(key)) < 0:
            issues.append(f"{key} must be >= 0")
    for key in (
        "selected_handoff_batch_maturity_suite_design_regression_names",
        "handoff_batch_maturity_suite_design_regression_names",
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names",
    ):
        if key in payload and not isinstance(payload.get(key), list):
            issues.append(f"{key} must be a list")
    return issues


def v4_receipt_field_issues(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in RECEIPT_SCHEMA_V4_REQUIRED_FIELDS:
        if key not in payload:
            issues.append(f"schema_version >= 4 receipt must include {key}")
        elif receipt_int(payload.get(key)) < 0:
            issues.append(f"{key} must be >= 0")
    return issues


def v5_receipt_field_issues(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in RECEIPT_SCHEMA_V5_REQUIRED_FIELDS:
        if key not in payload:
            issues.append(f"schema_version >= 5 receipt must include {key}")
        elif not isinstance(payload.get(key), dict):
            issues.append(f"{key} must be an object")
        else:
            for reason, count in payload[key].items():
                if not str(reason).strip():
                    issues.append(f"{key} must not include blank reason names")
                if receipt_int(count) < 0:
                    issues.append(f"{key}.{reason} must be >= 0")
    return issues


def receipt_check_compare_keys(schema_version: int) -> tuple[str, ...]:
    if schema_version >= 5:
        return EMBEDDED_RECEIPT_CHECK_COMPARE_KEYS
    return tuple(key for key in EMBEDDED_RECEIPT_CHECK_COMPARE_KEYS if key not in RECEIPT_SCHEMA_V5_REQUIRED_FIELDS)


__all__ = [
    "EMBEDDED_RECEIPT_CHECK_COMPARE_KEYS",
    "EMBEDDED_RECEIPT_SCHEMA_V5_TEXT_FIELDS",
    "RECEIPT_SCHEMA_V2_REQUIRED_FIELDS",
    "RECEIPT_SCHEMA_V3_REQUIRED_FIELDS",
    "RECEIPT_SCHEMA_V4_REQUIRED_FIELDS",
    "RECEIPT_SCHEMA_V5_REQUIRED_FIELDS",
    "RECEIPT_SCHEMA_V5_TEXT_FIELDS",
    "normalized_receipt_check_value",
    "receipt_check_compare_keys",
    "receipt_int",
    "v2_receipt_field_issues",
    "v3_receipt_field_issues",
    "v4_receipt_field_issues",
    "v5_receipt_field_issues",
]
