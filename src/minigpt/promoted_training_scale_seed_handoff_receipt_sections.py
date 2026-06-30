from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    html_escape as _e,
    string_list as _string_list,
)


def _receipt_check_section(report: dict[str, Any]) -> str:
    receipt_check = _dict(report.get("receipt_check"))
    if not receipt_check:
        return ""
    receipt_check_outputs = _dict(report.get("receipt_check_outputs"))
    rows = [
        ("Status", receipt_check.get("status")),
        ("Decision", receipt_check.get("decision")),
        ("Exit code", receipt_check.get("exit_code")),
        ("Checker exit code", receipt_check.get("checker_exit_code")),
        ("Blocking source", receipt_check.get("blocking_source")),
        ("Failed requirements", ", ".join(_string_list(receipt_check.get("failed_requirements")))),
        ("Issue count", receipt_check.get("issue_count")),
        ("Issues", ", ".join(_string_list(receipt_check.get("issues")))),
        ("Receipt path", receipt_check.get("receipt_path")),
        ("Receipt check JSON", receipt_check_outputs.get("json")),
        ("Receipt check text", receipt_check_outputs.get("text")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return f'<section><h2>Receipt Check</h2><div class="table-wrap"><table>{body}</table></div></section>'


def _embedded_receipt_check_section(report: dict[str, Any]) -> str:
    embedded_check = _dict(report.get("embedded_receipt_check"))
    if not embedded_check:
        return ""
    embedded_outputs = _dict(report.get("embedded_receipt_check_outputs"))
    rows = [
        ("Status", embedded_check.get("status")),
        ("Decision", embedded_check.get("decision")),
        ("Exit code", embedded_check.get("exit_code")),
        ("Checker exit code", embedded_check.get("checker_exit_code")),
        ("Sidecar status", embedded_check.get("sidecar_status")),
        ("Issue count", embedded_check.get("issue_count")),
        ("Issues", ", ".join(_string_list(embedded_check.get("issues")))),
        ("Receipt path", embedded_check.get("receipt_path")),
        ("Receipt path exists", embedded_check.get("receipt_path_exists")),
        ("Receipt check JSON", embedded_check.get("receipt_check_json")),
        ("Receipt check JSON exists", embedded_check.get("receipt_check_json_exists")),
        ("Receipt check text", embedded_check.get("receipt_check_text")),
        ("Receipt check text exists", embedded_check.get("receipt_check_text_exists")),
        ("Embedded check JSON", embedded_outputs.get("json")),
        ("Embedded check text", embedded_outputs.get("text")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return '<section><h2>Embedded Receipt Check</h2><div class="table-wrap"><table>' + body + "</table></div></section>"


def _handoff_assurance_section(report: dict[str, Any]) -> str:
    assurance = _dict(report.get("handoff_assurance"))
    if not assurance:
        return ""
    outputs = _dict(report.get("handoff_assurance_outputs"))
    rows = [
        ("Status", assurance.get("status")),
        ("Decision", assurance.get("decision")),
        ("Exit code", assurance.get("exit_code")),
        ("Checker exit code", assurance.get("checker_exit_code")),
        ("Embedded receipt check", assurance.get("embedded_receipt_check_status")),
        ("Embedded receipt sidecars", assurance.get("embedded_receipt_check_sidecar_status")),
        ("Receipt schema version", assurance.get("embedded_receipt_check_receipt_schema_version")),
        (
            "Receipt selected CI regressions",
            assurance.get("embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "Receipt selected CI reasons",
            _fmt_mapping(
                assurance.get(
                    "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts"
                )
            ),
        ),
        (
            "Receipt selected CI boundary plan",
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Receipt selected selected CI boundary plan",
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Receipt CI regressions",
            assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "Receipt CI reasons",
            _fmt_mapping(assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Receipt CI boundary plan",
            assurance.get(
                "embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Receipt selected total CI boundary plan",
            assurance.get(
                "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
            ),
        ),
        (
            "Receipt selected suite-design regressions",
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count"
            ),
        ),
        (
            "Receipt suite-design regressions",
            assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Receipt ready suite-design regressions",
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"
            ),
        ),
        (
            "Receipt ready CI boundary plan",
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Receipt ready CI reasons",
            _fmt_mapping(
                assurance.get(
                    "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"
                )
            ),
        ),
        (
            "Receipt ready selected CI boundary plan",
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
            ),
        ),
        (
            "Receipt comparison exclusions",
            ", ".join(_string_list(assurance.get("embedded_receipt_check_receipt_comparison_exclusion_reasons"))),
        ),
        ("Output JSON exists", assurance.get("embedded_receipt_check_output_json_exists")),
        ("Output text exists", assurance.get("embedded_receipt_check_output_text_exists")),
        ("Issue count", assurance.get("issue_count")),
        ("Issues", ", ".join(_string_list(assurance.get("issues")))),
        ("Assurance JSON", outputs.get("json")),
        ("Assurance text", outputs.get("text")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return '<section><h2>Handoff Assurance</h2><div class="table-wrap"><table>' + body + "</table></div></section>"


__all__ = [
    "_embedded_receipt_check_section",
    "_handoff_assurance_section",
    "_receipt_check_section",
]
