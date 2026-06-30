from __future__ import annotations

import json
from typing import Any

_JSON = "json"
_JSON_SORTED = "json_sorted"

_ASSURANCE_RENDER_FIELDS: tuple[tuple[str, str, str | None], ...] = (
    ("handoff_assurance_status", "status", None),
    ("handoff_assurance_decision", "decision", None),
    ("handoff_assurance_exit_code", "exit_code", None),
    ("handoff_assurance_checker_exit_code", "checker_exit_code", None),
    ("handoff_assurance_report_path", "handoff_report_path", None),
    ("handoff_assurance_embedded_receipt_check_status", "embedded_receipt_check_status", None),
    ("handoff_assurance_embedded_receipt_check_sidecar_status", "embedded_receipt_check_sidecar_status", None),
    (
        "handoff_assurance_embedded_receipt_check_receipt_schema_version",
        "embedded_receipt_check_receipt_schema_version",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts",
        "embedded_receipt_check_receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts",
        _JSON_SORTED,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count",
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts",
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts",
        _JSON_SORTED,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
        "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
        _JSON_SORTED,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count",
        "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts",
        "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts",
        _JSON_SORTED,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_regression_reason_counts",
        "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_regression_reason_counts",
        _JSON_SORTED,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
        "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count",
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_names",
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_names",
        _JSON,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count",
        "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names",
        "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names",
        _JSON,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count",
        "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
        "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
        _JSON_SORTED,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
        "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
        _JSON_SORTED,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
        "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
        None,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names",
        "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names",
        _JSON,
    ),
    (
        "handoff_assurance_embedded_receipt_check_receipt_comparison_exclusion_reasons",
        "embedded_receipt_check_receipt_comparison_exclusion_reasons",
        _JSON,
    ),
    (
        "handoff_assurance_main_embedded_receipt_check_status",
        "main_embedded_receipt_check_status",
        None,
    ),
    (
        "handoff_assurance_output_json_exists",
        "embedded_receipt_check_output_json_exists",
        None,
    ),
    (
        "handoff_assurance_output_text_exists",
        "embedded_receipt_check_output_text_exists",
        None,
    ),
    ("handoff_assurance_issue_count", "issue_count", None),
    ("handoff_assurance_issues", "issues", _JSON),
)


def render_promoted_training_scale_seed_handoff_assurance_check(check: dict[str, Any]) -> str:
    rows = (
        (output_key, _render_assurance_value(check, source_key, formatter))
        for output_key, source_key, formatter in _ASSURANCE_RENDER_FIELDS
    )
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def _render_assurance_value(check: dict[str, Any], source_key: str, formatter: str | None) -> Any:
    value = check.get(source_key)
    if formatter == _JSON_SORTED:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if formatter == _JSON:
        return json.dumps(value, ensure_ascii=False)
    return value


__all__ = ["render_promoted_training_scale_seed_handoff_assurance_check"]
