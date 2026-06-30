from __future__ import annotations

from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_validation import (
    receipt_int as _int,
    v2_receipt_field_issues as _v2_receipt_field_issues,
    v3_receipt_field_issues as _v3_receipt_field_issues,
    v4_receipt_field_issues as _v4_receipt_field_issues,
    v5_receipt_field_issues as _v5_receipt_field_issues,
)
from minigpt.report_utils import as_dict
from minigpt.report_utils import positive_int_mapping
from minigpt.report_utils import string_list


RECEIPT_TYPE = "promoted_training_scale_seed_handoff_automation"


def check_promoted_training_scale_seed_handoff_automation_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    payload = as_dict(receipt)
    receipt_type = str(payload.get("receipt_type") or "")
    decision = str(payload.get("automation_decision") or "")
    blocking_source = payload.get("automation_blocking_source")
    failed_requirements = string_list(payload.get("failed_requirements"))
    schema_version = _int(payload.get("schema_version"))
    exit_code = _int(payload.get("automation_exit_code"))
    selected_ci_regressions = _int(payload.get("selected_handoff_batch_maturity_ci_regression_count"))
    selected_ci_reason_counts = positive_int_mapping(
        payload.get("selected_handoff_batch_maturity_ci_regression_reason_counts")
    )
    selected_boundary_plan_regressions = _int(
        payload.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count")
    )
    selected_selected_ci_reason_counts = positive_int_mapping(
        payload.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    selected_selected_boundary_plan_regressions = _int(
        payload.get("selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count")
    )
    handoff_ci_regressions = _int(payload.get("handoff_batch_maturity_ci_regression_count"))
    handoff_ci_reason_counts = positive_int_mapping(payload.get("handoff_batch_maturity_ci_regression_reason_counts"))
    handoff_boundary_plan_regressions = _int(
        payload.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count")
    )
    handoff_selected_ci_reason_counts = positive_int_mapping(
        payload.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    handoff_selected_boundary_plan_regressions = _int(
        payload.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total")
    )
    clean_batch_selected_ci_reason_counts = positive_int_mapping(
        payload.get("clean_batch_review_requirement_selected_ci_regression_reason_counts")
    )
    selected_suite_design_regressions = _int(
        payload.get("selected_handoff_batch_maturity_suite_design_regression_count")
    )
    selected_suite_design_names = string_list(
        payload.get("selected_handoff_batch_maturity_suite_design_regression_names")
    )
    handoff_suite_design_regressions = _int(payload.get("handoff_batch_maturity_suite_design_regression_count"))
    handoff_suite_design_names = string_list(payload.get("handoff_batch_maturity_suite_design_regression_names"))
    ready_suite_design_regressions = _int(
        payload.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count")
    )
    ready_boundary_plan_regressions = _int(
        payload.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count")
    )
    ready_ci_reason_counts = positive_int_mapping(
        payload.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")
    )
    ready_selected_boundary_plan_regressions = _int(
        payload.get("comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total")
    )
    ready_selected_ci_reason_counts = positive_int_mapping(
        payload.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    ready_suite_design_names = string_list(
        payload.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names")
    )
    comparison_exclusion_reasons = string_list(payload.get("comparison_exclusion_reasons"))
    issues: list[str] = []
    if receipt_type != RECEIPT_TYPE:
        issues.append(f"receipt_type must be {RECEIPT_TYPE}")
    if schema_version < 1:
        issues.append("schema_version must be >= 1")
    if decision not in {"continue", "stop"}:
        issues.append("automation_decision must be continue or stop")
    if decision == "stop" and exit_code == 0:
        issues.append("stop decision must carry a non-zero automation_exit_code")
    if decision == "continue" and exit_code != 0:
        issues.append("continue decision must carry automation_exit_code=0")
    if decision == "stop" and not blocking_source:
        issues.append("stop decision must carry automation_blocking_source")
    if decision == "continue" and blocking_source:
        issues.append("continue decision must not carry automation_blocking_source")
    if blocking_source == "automation_gate" and not failed_requirements:
        issues.append("automation_gate blocking source must include failed_requirements")
    if schema_version >= 2:
        issues.extend(_v2_receipt_field_issues(payload))
    if schema_version >= 3:
        issues.extend(_v3_receipt_field_issues(payload))
    if schema_version >= 4:
        issues.extend(_v4_receipt_field_issues(payload))
    if schema_version >= 5:
        issues.extend(_v5_receipt_field_issues(payload))
    status = "pass" if not issues else "fail"
    checker_exit_code = 0 if status == "pass" and decision == "continue" else 1
    return {
        "schema_version": schema_version,
        "receipt_type": receipt_type,
        "status": status,
        "decision": decision,
        "exit_code": exit_code,
        "checker_exit_code": checker_exit_code,
        "blocking_source": str(blocking_source) if blocking_source is not None else None,
        "failed_requirements": failed_requirements,
        "clean_batch_review_requirement_selected_ci_regression_reason_counts": clean_batch_selected_ci_reason_counts,
        "selected_handoff_batch_maturity_ci_regression_count": selected_ci_regressions,
        "selected_handoff_batch_maturity_ci_regression_reason_counts": selected_ci_reason_counts,
        "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": selected_boundary_plan_regressions,
        "selected_handoff_selected_batch_maturity_ci_regression_reason_counts": selected_selected_ci_reason_counts,
        "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": (
            selected_selected_boundary_plan_regressions
        ),
        "handoff_batch_maturity_ci_regression_count": handoff_ci_regressions,
        "handoff_batch_maturity_ci_regression_reason_counts": handoff_ci_reason_counts,
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": handoff_boundary_plan_regressions,
        "handoff_selected_batch_maturity_ci_regression_reason_counts": handoff_selected_ci_reason_counts,
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": (
            handoff_selected_boundary_plan_regressions
        ),
        "selected_handoff_batch_maturity_suite_design_regression_count": selected_suite_design_regressions,
        "selected_handoff_batch_maturity_suite_design_regression_names": selected_suite_design_names,
        "handoff_batch_maturity_suite_design_regression_count": handoff_suite_design_regressions,
        "handoff_batch_maturity_suite_design_regression_names": handoff_suite_design_names,
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count": ready_suite_design_regressions,
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": ready_ci_reason_counts,
        "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": ready_boundary_plan_regressions,
        "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": (
            ready_selected_boundary_plan_regressions
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": ready_selected_ci_reason_counts,
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names": ready_suite_design_names,
        "comparison_exclusion_reasons": comparison_exclusion_reasons,
        "issue_count": len(issues),
        "issues": issues,
    }


__all__ = [
    "RECEIPT_TYPE",
    "check_promoted_training_scale_seed_handoff_automation_receipt",
]
