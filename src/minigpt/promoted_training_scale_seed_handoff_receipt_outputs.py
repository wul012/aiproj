from __future__ import annotations

import json
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_validation import (
    EMBEDDED_RECEIPT_SCHEMA_V5_TEXT_FIELDS,
    RECEIPT_SCHEMA_V5_TEXT_FIELDS,
    receipt_int as _int,
)


def render_promoted_training_scale_seed_handoff_automation_receipt_check(check: dict[str, Any]) -> str:
    rows = [
        ("receipt_check_status", check.get("status")),
        ("receipt_decision", check.get("decision")),
        ("receipt_exit_code", check.get("exit_code")),
        ("receipt_checker_exit_code", check.get("checker_exit_code")),
        ("receipt_blocking_source", check.get("blocking_source")),
        ("receipt_failed_requirements", json.dumps(check.get("failed_requirements"), ensure_ascii=False)),
        (
            "receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts",
            json.dumps(
                check.get("clean_batch_review_requirement_selected_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_selected_handoff_batch_maturity_ci_regression_count",
            check.get("selected_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "receipt_selected_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("selected_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "receipt_handoff_batch_maturity_ci_regression_count",
            check.get("handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "receipt_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "receipt_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            check.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "receipt_selected_handoff_batch_maturity_suite_design_regression_count",
            check.get("selected_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "receipt_selected_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(check.get("selected_handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False),
        ),
        (
            "receipt_handoff_batch_maturity_suite_design_regression_count",
            check.get("handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "receipt_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(check.get("handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False),
        ),
        (
            "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count",
            check.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            check.get("comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(
                check.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names"),
                ensure_ascii=False,
            ),
        ),
        ("receipt_comparison_exclusion_reasons", json.dumps(check.get("comparison_exclusion_reasons"), ensure_ascii=False)),
        ("receipt_issue_count", check.get("issue_count")),
        ("receipt_issues", json.dumps(check.get("issues"), ensure_ascii=False)),
    ]
    if _int(check.get("schema_version")) < 5:
        rows = [row for row in rows if row[0] not in RECEIPT_SCHEMA_V5_TEXT_FIELDS]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_promoted_training_scale_seed_handoff_embedded_receipt_check(check: dict[str, Any]) -> str:
    rows = [
        ("embedded_receipt_check_status", check.get("status")),
        ("embedded_receipt_check_decision", check.get("decision")),
        ("embedded_receipt_check_exit_code", check.get("exit_code")),
        ("embedded_receipt_check_checker_exit_code", check.get("checker_exit_code")),
        ("embedded_receipt_check_receipt_schema_version", check.get("receipt_schema_version")),
        (
            "embedded_receipt_check_receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count",
            check.get("receipt_selected_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_selected_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count",
            check.get("receipt_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            check.get("receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count",
            check.get("receipt_selected_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(check.get("receipt_selected_handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count",
            check.get("receipt_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(check.get("receipt_handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count",
            check.get("receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            check.get("receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(
                check.get("receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names"),
                ensure_ascii=False,
            ),
        ),
        (
            "embedded_receipt_check_receipt_comparison_exclusion_reasons",
            json.dumps(check.get("receipt_comparison_exclusion_reasons"), ensure_ascii=False),
        ),
        ("embedded_receipt_check_receipt_path", check.get("receipt_path")),
        ("embedded_receipt_check_json", check.get("receipt_check_json")),
        ("embedded_receipt_check_text", check.get("receipt_check_text")),
        ("embedded_receipt_check_sidecar_status", check.get("sidecar_status")),
        ("embedded_receipt_check_receipt_path_exists", check.get("receipt_path_exists")),
        ("embedded_receipt_check_json_exists", check.get("receipt_check_json_exists")),
        ("embedded_receipt_check_text_exists", check.get("receipt_check_text_exists")),
        ("embedded_receipt_check_issue_count", check.get("issue_count")),
        ("embedded_receipt_check_issues", json.dumps(check.get("issues"), ensure_ascii=False)),
    ]
    if _int(check.get("receipt_schema_version")) < 5:
        rows = [row for row in rows if row[0] not in EMBEDDED_RECEIPT_SCHEMA_V5_TEXT_FIELDS]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


__all__ = [
    "render_promoted_training_scale_seed_handoff_embedded_receipt_check",
    "render_promoted_training_scale_seed_handoff_automation_receipt_check",
]
