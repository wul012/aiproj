from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    string_list as _string_list,
    write_json_payload,
)


def build_promoted_training_scale_seed_handoff_automation_receipt(report: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    clean_requirement = _dict(report.get("clean_evidence_requirement"))
    clean_batch_requirement = _dict(report.get("clean_batch_review_requirement"))
    automation_gate = _dict(report.get("automation_gate"))
    automation_summary = _dict(report.get("automation_summary"))
    return {
        "schema_version": 2,
        "receipt_type": "promoted_training_scale_seed_handoff_automation",
        "generated_at": report.get("generated_at"),
        "seed_path": report.get("seed_path"),
        "seed_status": report.get("seed_status"),
        "handoff_status": summary.get("handoff_status"),
        "execute": report.get("execute"),
        "returncode": execution.get("returncode"),
        "plan_status": summary.get("plan_status"),
        "plan_report_path": report.get("plan_report_path"),
        "next_batch_command_available": summary.get("next_batch_command_available"),
        "automation_decision": automation_summary.get("decision"),
        "automation_exit_code": automation_summary.get("exit_code"),
        "automation_blocking_source": automation_summary.get("blocking_source"),
        "automation_detail": automation_summary.get("detail"),
        "gate_status": automation_gate.get("status"),
        "gate_decision": automation_gate.get("decision"),
        "gate_required": automation_gate.get("required"),
        "gate_blocking_requirement_count": automation_gate.get("blocking_requirement_count"),
        "failed_requirements": automation_summary.get("failed_requirements"),
        "passed_requirements": automation_gate.get("passed_requirements"),
        "clean_evidence_requirement_status": clean_requirement.get("status"),
        "clean_batch_review_requirement_status": clean_batch_requirement.get("status"),
        "selected_handoff_batch_maturity_ci_regression_count": summary.get(
            "selected_handoff_batch_maturity_ci_regression_count"
        ),
        "handoff_batch_maturity_ci_regression_count": summary.get("handoff_batch_maturity_ci_regression_count"),
        "comparison_exclusion_reasons": summary.get("comparison_exclusion_reasons"),
    }


def _receipt_check(report: dict[str, Any]) -> dict[str, Any]:
    return _dict(report.get("receipt_check"))


def _receipt_check_outputs(report: dict[str, Any]) -> dict[str, Any]:
    return _dict(report.get("receipt_check_outputs"))


def _embedded_receipt_check(report: dict[str, Any]) -> dict[str, Any]:
    return _dict(report.get("embedded_receipt_check"))


def _embedded_receipt_check_outputs(report: dict[str, Any]) -> dict[str, Any]:
    return _dict(report.get("embedded_receipt_check_outputs"))


def _handoff_assurance(report: dict[str, Any]) -> dict[str, Any]:
    return _dict(report.get("handoff_assurance"))


def _handoff_assurance_outputs(report: dict[str, Any]) -> dict[str, Any]:
    return _dict(report.get("handoff_assurance_outputs"))


def _receipt_check_fields(report: dict[str, Any]) -> dict[str, Any]:
    receipt_check = _receipt_check(report)
    receipt_check_outputs = _receipt_check_outputs(report)
    return {
        "receipt_check_status": receipt_check.get("status"),
        "receipt_check_decision": receipt_check.get("decision"),
        "receipt_check_exit_code": receipt_check.get("exit_code"),
        "receipt_check_checker_exit_code": receipt_check.get("checker_exit_code"),
        "receipt_check_blocking_source": receipt_check.get("blocking_source"),
        "receipt_check_failed_requirements": "; ".join(_string_list(receipt_check.get("failed_requirements"))),
        "receipt_check_issue_count": receipt_check.get("issue_count"),
        "receipt_check_issues": "; ".join(_string_list(receipt_check.get("issues"))),
        "receipt_check_receipt_path": receipt_check.get("receipt_path"),
        "receipt_check_json": receipt_check_outputs.get("json"),
        "receipt_check_text": receipt_check_outputs.get("text"),
    }


def _embedded_receipt_check_fields(report: dict[str, Any]) -> dict[str, Any]:
    embedded_check = _embedded_receipt_check(report)
    embedded_outputs = _embedded_receipt_check_outputs(report)
    return {
        "embedded_receipt_check_status": embedded_check.get("status"),
        "embedded_receipt_check_decision": embedded_check.get("decision"),
        "embedded_receipt_check_exit_code": embedded_check.get("exit_code"),
        "embedded_receipt_check_checker_exit_code": embedded_check.get("checker_exit_code"),
        "embedded_receipt_check_sidecar_status": embedded_check.get("sidecar_status"),
        "embedded_receipt_check_issue_count": embedded_check.get("issue_count"),
        "embedded_receipt_check_issues": "; ".join(_string_list(embedded_check.get("issues"))),
        "embedded_receipt_check_receipt_path": embedded_check.get("receipt_path"),
        "embedded_receipt_check_receipt_path_exists": embedded_check.get("receipt_path_exists"),
        "embedded_receipt_check_json": embedded_check.get("receipt_check_json"),
        "embedded_receipt_check_json_exists": embedded_check.get("receipt_check_json_exists"),
        "embedded_receipt_check_text": embedded_check.get("receipt_check_text"),
        "embedded_receipt_check_text_exists": embedded_check.get("receipt_check_text_exists"),
        "embedded_receipt_check_output_json": embedded_outputs.get("json"),
        "embedded_receipt_check_output_text": embedded_outputs.get("text"),
    }


def _handoff_assurance_fields(report: dict[str, Any]) -> dict[str, Any]:
    assurance = _handoff_assurance(report)
    outputs = _handoff_assurance_outputs(report)
    return {
        "handoff_assurance_status": assurance.get("status"),
        "handoff_assurance_decision": assurance.get("decision"),
        "handoff_assurance_exit_code": assurance.get("exit_code"),
        "handoff_assurance_checker_exit_code": assurance.get("checker_exit_code"),
        "handoff_assurance_embedded_receipt_check_status": assurance.get("embedded_receipt_check_status"),
        "handoff_assurance_embedded_receipt_check_sidecar_status": assurance.get(
            "embedded_receipt_check_sidecar_status"
        ),
        "handoff_assurance_embedded_receipt_check_receipt_schema_version": assurance.get(
            "embedded_receipt_check_receipt_schema_version"
        ),
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count": assurance.get(
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count"
        ),
        "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count": assurance.get(
            "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count"
        ),
        "handoff_assurance_embedded_receipt_check_receipt_comparison_exclusion_reasons": "; ".join(
            _string_list(assurance.get("embedded_receipt_check_receipt_comparison_exclusion_reasons"))
        ),
        "handoff_assurance_output_json_exists": assurance.get("embedded_receipt_check_output_json_exists"),
        "handoff_assurance_output_text_exists": assurance.get("embedded_receipt_check_output_text_exists"),
        "handoff_assurance_issue_count": assurance.get("issue_count"),
        "handoff_assurance_issues": "; ".join(_string_list(assurance.get("issues"))),
        "handoff_assurance_json": outputs.get("json"),
        "handoff_assurance_text": outputs.get("text"),
    }


def render_promoted_training_scale_seed_handoff_automation_receipt_text(report: dict[str, Any]) -> str:
    receipt = build_promoted_training_scale_seed_handoff_automation_receipt(report)
    keys = [
        "receipt_type",
        "generated_at",
        "seed_path",
        "handoff_status",
        "plan_status",
        "automation_decision",
        "automation_exit_code",
        "automation_blocking_source",
        "gate_decision",
        "gate_blocking_requirement_count",
        "failed_requirements",
        "passed_requirements",
        "clean_evidence_requirement_status",
        "clean_batch_review_requirement_status",
        "selected_handoff_batch_maturity_ci_regression_count",
        "handoff_batch_maturity_ci_regression_count",
        "comparison_exclusion_reasons",
    ]
    return "\n".join(f"{key}={receipt.get(key)}" for key in keys) + "\n"


def write_promoted_training_scale_seed_handoff_automation_receipt_json(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    write_json_payload(build_promoted_training_scale_seed_handoff_automation_receipt(report), path)


def write_promoted_training_scale_seed_handoff_automation_receipt_text(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_promoted_training_scale_seed_handoff_automation_receipt_text(report),
        encoding="utf-8",
    )


def _receipt_check_section(report: dict[str, Any]) -> str:
    receipt_check = _receipt_check(report)
    if not receipt_check:
        return ""
    receipt_check_outputs = _receipt_check_outputs(report)
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
    embedded_check = _embedded_receipt_check(report)
    if not embedded_check:
        return ""
    embedded_outputs = _embedded_receipt_check_outputs(report)
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
    assurance = _handoff_assurance(report)
    if not assurance:
        return ""
    outputs = _handoff_assurance_outputs(report)
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
            "Receipt CI regressions",
            assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count"),
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
    "build_promoted_training_scale_seed_handoff_automation_receipt",
    "render_promoted_training_scale_seed_handoff_automation_receipt_text",
    "write_promoted_training_scale_seed_handoff_automation_receipt_json",
    "write_promoted_training_scale_seed_handoff_automation_receipt_text",
]
