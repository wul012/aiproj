from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    display_command as _display_command,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_csv_row,
    write_json_payload,
)


def write_promoted_training_scale_seed_handoff_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


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


def write_promoted_training_scale_seed_handoff_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    clean_requirement = _dict(report.get("clean_evidence_requirement"))
    clean_batch_requirement = _dict(report.get("clean_batch_review_requirement"))
    automation_gate = _dict(report.get("automation_gate"))
    automation_summary = _dict(report.get("automation_summary"))
    receipt_check_fields = _receipt_check_fields(report)
    embedded_receipt_check_fields = _embedded_receipt_check_fields(report)
    handoff_assurance_fields = _handoff_assurance_fields(report)
    fieldnames = [
        "handoff_status",
        "seed_status",
        "decision_status",
        "execute",
        "returncode",
        "elapsed_seconds",
        "seed_suite_path",
        "selected_handoff_suite_consistency",
        "selected_handoff_suite_mismatch_count",
        "selected_handoff_selected_suite_path",
        "selected_handoff_require_clean_batch_review",
        "selected_handoff_clean_batch_review_status",
        "selected_handoff_batch_maturity_ci_regression_count",
        "selected_handoff_batch_maturity_ci_regression_names",
        "selected_handoff_selected_batch_maturity_ci_regression_count",
        "selected_comparison_exclusion_reasons",
        "handoff_require_clean_batch_review_count",
        "handoff_clean_batch_review_count",
        "handoff_unclean_batch_review_count",
        "handoff_batch_maturity_ci_regression_count",
        "handoff_selected_batch_maturity_ci_regression_total",
        "handoff_batch_maturity_ci_regression_names",
        "comparison_exclusion_reasons",
        "comparison_ready_handoff_require_clean_batch_review_count",
        "comparison_ready_handoff_clean_batch_review_count",
        "comparison_ready_handoff_unclean_batch_review_count",
        "comparison_ready_handoff_batch_maturity_ci_regression_count",
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total",
        "comparison_ready_handoff_batch_maturity_ci_regression_names",
        "selected_handoff_selected_batch_review_status",
        "selected_handoff_selected_batch_comparison_review_action_count",
        "selected_handoff_selected_batch_comparison_blocker_action_count",
        "selected_handoff_batch_comparison_blocker_reasons",
        "comparison_ready_handoff_selected_batch_review_count",
        "comparison_ready_handoff_selected_batch_blocker_count",
        "comparison_ready_handoff_selected_batch_comparison_review_action_total",
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total",
        "comparison_ready_handoff_batch_comparison_blocker_reasons",
        "handoff_suite_mismatch_total",
        "plan_suite_path",
        "seed_handoff_suite_alignment_status",
        "seed_handoff_suite_alignment_mismatch_count",
        "seed_handoff_suite_alignment_missing_count",
        "seed_handoff_clean_evidence_ready",
        "seed_handoff_clean_evidence_status",
        "seed_handoff_clean_evidence_status_domain",
        "clean_evidence_requirement_required",
        "clean_evidence_requirement_status",
        "clean_evidence_requirement_ready",
        "clean_evidence_requirement_readiness_status",
        "clean_evidence_requirement_status_domain",
        "clean_batch_review_requirement_required",
        "clean_batch_review_requirement_status",
        "clean_batch_review_requirement_clean",
        "clean_batch_review_requirement_selected_required",
        "clean_batch_review_requirement_selected_status",
        "clean_batch_review_requirement_selected_ci_regression_count",
        "clean_batch_review_requirement_status_domain",
        "automation_gate_required",
        "automation_gate_status",
        "automation_gate_decision",
        "automation_gate_exit_code",
        "automation_gate_required_requirement_count",
        "automation_gate_passed_requirement_count",
        "automation_gate_failed_requirement_count",
        "automation_gate_blocking_requirement_count",
        "automation_gate_failed_requirements",
        "automation_gate_passed_requirements",
        "automation_gate_status_domain",
        "automation_gate_decision_domain",
        "automation_summary_decision",
        "automation_summary_exit_code",
        "automation_summary_blocking_source",
        "automation_summary_gate_decision",
        "automation_summary_gate_blocking_requirement_count",
        "automation_summary_failed_requirements",
        "automation_summary_decision_domain",
        "receipt_check_status",
        "receipt_check_decision",
        "receipt_check_exit_code",
        "receipt_check_checker_exit_code",
        "receipt_check_blocking_source",
        "receipt_check_failed_requirements",
        "receipt_check_issue_count",
        "receipt_check_issues",
        "receipt_check_receipt_path",
        "receipt_check_json",
        "receipt_check_text",
        "embedded_receipt_check_status",
        "embedded_receipt_check_decision",
        "embedded_receipt_check_exit_code",
        "embedded_receipt_check_checker_exit_code",
        "embedded_receipt_check_sidecar_status",
        "embedded_receipt_check_issue_count",
        "embedded_receipt_check_issues",
        "embedded_receipt_check_receipt_path",
        "embedded_receipt_check_receipt_path_exists",
        "embedded_receipt_check_json",
        "embedded_receipt_check_json_exists",
        "embedded_receipt_check_text",
        "embedded_receipt_check_text_exists",
        "embedded_receipt_check_output_json",
        "embedded_receipt_check_output_text",
        "handoff_assurance_status",
        "handoff_assurance_decision",
        "handoff_assurance_exit_code",
        "handoff_assurance_checker_exit_code",
        "handoff_assurance_embedded_receipt_check_status",
        "handoff_assurance_embedded_receipt_check_sidecar_status",
        "handoff_assurance_embedded_receipt_check_receipt_schema_version",
        "handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count",
        "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count",
        "handoff_assurance_embedded_receipt_check_receipt_comparison_exclusion_reasons",
        "handoff_assurance_output_json_exists",
        "handoff_assurance_output_text_exists",
        "handoff_assurance_issue_count",
        "handoff_assurance_issues",
        "handoff_assurance_json",
        "handoff_assurance_text",
        "artifact_count",
        "available_artifact_count",
        "plan_status",
        "plan_variant_count",
        "next_batch_command_available",
        "blocked_reason",
    ]
    write_csv_row(
        {
            "handoff_status": summary.get("handoff_status"),
            "seed_status": report.get("seed_status"),
            "decision_status": summary.get("decision_status"),
            "execute": report.get("execute"),
            "returncode": execution.get("returncode"),
            "elapsed_seconds": execution.get("elapsed_seconds"),
            "seed_suite_path": summary.get("seed_suite_path"),
            "selected_handoff_suite_consistency": summary.get("selected_handoff_suite_consistency"),
            "selected_handoff_suite_mismatch_count": summary.get("selected_handoff_suite_mismatch_count"),
            "selected_handoff_selected_suite_path": summary.get("selected_handoff_selected_suite_path"),
            "selected_handoff_require_clean_batch_review": summary.get(
                "selected_handoff_require_clean_batch_review"
            ),
            "selected_handoff_clean_batch_review_status": summary.get(
                "selected_handoff_clean_batch_review_status"
            ),
            "selected_handoff_batch_maturity_ci_regression_count": summary.get(
                "selected_handoff_batch_maturity_ci_regression_count"
            ),
            "selected_handoff_batch_maturity_ci_regression_names": "; ".join(
                _string_list(summary.get("selected_handoff_batch_maturity_ci_regression_names"))
            ),
            "selected_handoff_selected_batch_maturity_ci_regression_count": summary.get(
                "selected_handoff_selected_batch_maturity_ci_regression_count"
            ),
            "selected_comparison_exclusion_reasons": "; ".join(
                _string_list(summary.get("selected_comparison_exclusion_reasons"))
            ),
            "handoff_require_clean_batch_review_count": summary.get("handoff_require_clean_batch_review_count"),
            "handoff_clean_batch_review_count": summary.get("handoff_clean_batch_review_count"),
            "handoff_unclean_batch_review_count": summary.get("handoff_unclean_batch_review_count"),
            "handoff_batch_maturity_ci_regression_count": summary.get("handoff_batch_maturity_ci_regression_count"),
            "handoff_selected_batch_maturity_ci_regression_total": summary.get(
                "handoff_selected_batch_maturity_ci_regression_total"
            ),
            "handoff_batch_maturity_ci_regression_names": "; ".join(
                _string_list(summary.get("handoff_batch_maturity_ci_regression_names"))
            ),
            "comparison_exclusion_reasons": "; ".join(_string_list(summary.get("comparison_exclusion_reasons"))),
            "comparison_ready_handoff_require_clean_batch_review_count": summary.get(
                "comparison_ready_handoff_require_clean_batch_review_count"
            ),
            "comparison_ready_handoff_clean_batch_review_count": summary.get(
                "comparison_ready_handoff_clean_batch_review_count"
            ),
            "comparison_ready_handoff_unclean_batch_review_count": summary.get(
                "comparison_ready_handoff_unclean_batch_review_count"
            ),
            "comparison_ready_handoff_batch_maturity_ci_regression_count": summary.get(
                "comparison_ready_handoff_batch_maturity_ci_regression_count"
            ),
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": summary.get(
                "comparison_ready_handoff_selected_batch_maturity_ci_regression_total"
            ),
            "comparison_ready_handoff_batch_maturity_ci_regression_names": "; ".join(
                _string_list(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_names"))
            ),
            "selected_handoff_selected_batch_review_status": summary.get("selected_handoff_selected_batch_review_status"),
            "selected_handoff_selected_batch_comparison_review_action_count": summary.get(
                "selected_handoff_selected_batch_comparison_review_action_count"
            ),
            "selected_handoff_selected_batch_comparison_blocker_action_count": summary.get(
                "selected_handoff_selected_batch_comparison_blocker_action_count"
            ),
            "selected_handoff_batch_comparison_blocker_reasons": "; ".join(
                _string_list(summary.get("selected_handoff_batch_comparison_blocker_reasons"))
            ),
            "comparison_ready_handoff_selected_batch_review_count": summary.get(
                "comparison_ready_handoff_selected_batch_review_count"
            ),
            "comparison_ready_handoff_selected_batch_blocker_count": summary.get(
                "comparison_ready_handoff_selected_batch_blocker_count"
            ),
            "comparison_ready_handoff_selected_batch_comparison_review_action_total": summary.get(
                "comparison_ready_handoff_selected_batch_comparison_review_action_total"
            ),
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": summary.get(
                "comparison_ready_handoff_selected_batch_comparison_blocker_action_total"
            ),
            "comparison_ready_handoff_batch_comparison_blocker_reasons": "; ".join(
                _string_list(summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons"))
            ),
            "handoff_suite_mismatch_total": summary.get("handoff_suite_mismatch_total"),
            "plan_suite_path": summary.get("plan_suite_path"),
            "seed_handoff_suite_alignment_status": summary.get("seed_handoff_suite_alignment_status"),
            "seed_handoff_suite_alignment_mismatch_count": summary.get("seed_handoff_suite_alignment_mismatch_count"),
            "seed_handoff_suite_alignment_missing_count": summary.get("seed_handoff_suite_alignment_missing_count"),
            "seed_handoff_clean_evidence_ready": summary.get("seed_handoff_clean_evidence_ready"),
            "seed_handoff_clean_evidence_status": summary.get("seed_handoff_clean_evidence_status"),
            "seed_handoff_clean_evidence_status_domain": summary.get("seed_handoff_clean_evidence_status_domain"),
            "clean_evidence_requirement_required": clean_requirement.get("required"),
            "clean_evidence_requirement_status": clean_requirement.get("status"),
            "clean_evidence_requirement_ready": clean_requirement.get("ready"),
            "clean_evidence_requirement_readiness_status": clean_requirement.get("readiness_status"),
            "clean_evidence_requirement_status_domain": clean_requirement.get("status_domain"),
            "clean_batch_review_requirement_required": clean_batch_requirement.get("required"),
            "clean_batch_review_requirement_status": clean_batch_requirement.get("status"),
            "clean_batch_review_requirement_clean": clean_batch_requirement.get("clean"),
            "clean_batch_review_requirement_selected_required": clean_batch_requirement.get("selected_required"),
            "clean_batch_review_requirement_selected_status": clean_batch_requirement.get("selected_status"),
            "clean_batch_review_requirement_selected_ci_regression_count": clean_batch_requirement.get(
                "selected_ci_regression_count"
            ),
            "clean_batch_review_requirement_status_domain": clean_batch_requirement.get("status_domain"),
            "automation_gate_required": automation_gate.get("required"),
            "automation_gate_status": automation_gate.get("status"),
            "automation_gate_decision": automation_gate.get("decision"),
            "automation_gate_exit_code": automation_gate.get("exit_code"),
            "automation_gate_required_requirement_count": automation_gate.get("required_requirement_count"),
            "automation_gate_passed_requirement_count": automation_gate.get("passed_requirement_count"),
            "automation_gate_failed_requirement_count": automation_gate.get("failed_requirement_count"),
            "automation_gate_blocking_requirement_count": automation_gate.get("blocking_requirement_count"),
            "automation_gate_failed_requirements": automation_gate.get("failed_requirements"),
            "automation_gate_passed_requirements": automation_gate.get("passed_requirements"),
            "automation_gate_status_domain": automation_gate.get("status_domain"),
            "automation_gate_decision_domain": automation_gate.get("decision_domain"),
            "automation_summary_decision": automation_summary.get("decision"),
            "automation_summary_exit_code": automation_summary.get("exit_code"),
            "automation_summary_blocking_source": automation_summary.get("blocking_source"),
            "automation_summary_gate_decision": automation_summary.get("gate_decision"),
            "automation_summary_gate_blocking_requirement_count": automation_summary.get(
                "gate_blocking_requirement_count"
            ),
            "automation_summary_failed_requirements": automation_summary.get("failed_requirements"),
            "automation_summary_decision_domain": automation_summary.get("decision_domain"),
            **receipt_check_fields,
            **embedded_receipt_check_fields,
            **handoff_assurance_fields,
            "artifact_count": summary.get("artifact_count"),
            "available_artifact_count": summary.get("available_artifact_count"),
            "plan_status": summary.get("plan_status"),
            "plan_variant_count": summary.get("plan_variant_count"),
            "next_batch_command_available": summary.get("next_batch_command_available"),
            "blocked_reason": report.get("blocked_reason"),
        },
        out_path,
        fieldnames,
    )


def render_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    clean_requirement = _dict(report.get("clean_evidence_requirement"))
    clean_batch_requirement = _dict(report.get("clean_batch_review_requirement"))
    automation_gate = _dict(report.get("automation_gate"))
    automation_summary = _dict(report.get("automation_summary"))
    receipt_check = _receipt_check(report)
    receipt_check_outputs = _receipt_check_outputs(report)
    embedded_receipt_check = _embedded_receipt_check(report)
    embedded_receipt_check_outputs = _embedded_receipt_check_outputs(report)
    handoff_assurance = _handoff_assurance(report)
    handoff_assurance_outputs = _handoff_assurance_outputs(report)
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale seed handoff')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Handoff status: `{summary.get('handoff_status')}`",
        f"- Seed status: `{report.get('seed_status')}`",
        f"- Decision status: `{summary.get('decision_status')}`",
        f"- Execute: `{report.get('execute')}`",
        f"- Return code: `{execution.get('returncode')}`",
        f"- Artifacts: `{summary.get('available_artifact_count')}/{summary.get('artifact_count')}`",
        f"- Plan status: `{summary.get('plan_status')}`",
        f"- Seed suite: `{summary.get('seed_suite_path')}`",
        f"- Selected handoff suite: `{summary.get('selected_handoff_suite_consistency')}`",
        f"- Selected handoff mismatches: `{summary.get('selected_handoff_suite_mismatch_count')}`",
        f"- Selected handoff suite path: `{summary.get('selected_handoff_selected_suite_path')}`",
        f"- Selected handoff require clean batch review: `{summary.get('selected_handoff_require_clean_batch_review')}`",
        f"- Selected handoff clean batch review: `{summary.get('selected_handoff_clean_batch_review_status')}`",
        f"- Selected handoff batch CI regressions: `{summary.get('selected_handoff_batch_maturity_ci_regression_count')}`",
        f"- Selected handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('selected_handoff_batch_maturity_ci_regression_names')))}`",
        f"- Selected handoff selected batch CI regressions: `{summary.get('selected_handoff_selected_batch_maturity_ci_regression_count')}`",
        f"- Selected comparison exclusion reasons: `{', '.join(_string_list(summary.get('selected_comparison_exclusion_reasons')))}`",
        f"- Handoff require clean batch review: `{summary.get('handoff_require_clean_batch_review_count')}`",
        f"- Handoff clean batch review: `{summary.get('handoff_clean_batch_review_count')}`",
        f"- Handoff unclean batch review: `{summary.get('handoff_unclean_batch_review_count')}`",
        f"- Handoff batch CI regressions: `{summary.get('handoff_batch_maturity_ci_regression_count')}`",
        f"- Handoff selected batch CI regressions: `{summary.get('handoff_selected_batch_maturity_ci_regression_total')}`",
        f"- Handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('handoff_batch_maturity_ci_regression_names')))}`",
        f"- Comparison exclusion reasons: `{', '.join(_string_list(summary.get('comparison_exclusion_reasons')))}`",
        f"- Comparison-ready clean-required handoffs: `{summary.get('comparison_ready_handoff_require_clean_batch_review_count')}`",
        f"- Comparison-ready clean handoffs: `{summary.get('comparison_ready_handoff_clean_batch_review_count')}`",
        f"- Comparison-ready unclean handoffs: `{summary.get('comparison_ready_handoff_unclean_batch_review_count')}`",
        f"- Comparison-ready handoff batch CI regressions: `{summary.get('comparison_ready_handoff_batch_maturity_ci_regression_count')}`",
        f"- Comparison-ready selected batch CI regressions: `{summary.get('comparison_ready_handoff_selected_batch_maturity_ci_regression_total')}`",
        f"- Comparison-ready handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('comparison_ready_handoff_batch_maturity_ci_regression_names')))}`",
        f"- Selected handoff batch review: `{summary.get('selected_handoff_selected_batch_review_status')}`",
        f"- Selected handoff batch review actions: `{summary.get('selected_handoff_selected_batch_comparison_review_action_count')}`",
        f"- Selected handoff batch blocker actions: `{summary.get('selected_handoff_selected_batch_comparison_blocker_action_count')}`",
        f"- Comparison-ready handoff batch reviews: `{summary.get('comparison_ready_handoff_selected_batch_review_count')}`",
        f"- Comparison-ready handoff batch blockers: `{summary.get('comparison_ready_handoff_selected_batch_blocker_count')}`",
        f"- Comparison-ready handoff batch blocker reasons: `{', '.join(_string_list(summary.get('comparison_ready_handoff_batch_comparison_blocker_reasons')))}`",
        f"- Handoff suite mismatches: `{summary.get('handoff_suite_mismatch_total')}`",
        f"- Plan suite: `{summary.get('plan_suite_path')}`",
        f"- Seed handoff suite alignment: `{summary.get('seed_handoff_suite_alignment_status')}`",
        f"- Seed handoff suite alignment detail: `{summary.get('seed_handoff_suite_alignment_detail')}`",
        f"- Seed handoff clean evidence: `{summary.get('seed_handoff_clean_evidence_status')}`",
        f"- Seed handoff clean evidence ready: `{summary.get('seed_handoff_clean_evidence_ready')}`",
        f"- Seed handoff clean evidence detail: `{summary.get('seed_handoff_clean_evidence_detail')}`",
        f"- Seed handoff clean evidence status domain: `{summary.get('seed_handoff_clean_evidence_status_domain')}`",
        f"- Clean evidence requirement: `{clean_requirement.get('status')}`",
        f"- Clean evidence requirement detail: `{clean_requirement.get('detail')}`",
        f"- Clean evidence requirement status domain: `{clean_requirement.get('status_domain')}`",
        f"- Clean batch-review requirement: `{clean_batch_requirement.get('status')}`",
        f"- Clean batch-review requirement detail: `{clean_batch_requirement.get('detail')}`",
        f"- Clean batch-review requirement selected CI regressions: `{clean_batch_requirement.get('selected_ci_regression_count')}`",
        f"- Clean batch-review requirement status domain: `{clean_batch_requirement.get('status_domain')}`",
        f"- Automation gate: `{automation_gate.get('status')}`",
        f"- Automation gate decision: `{automation_gate.get('decision')}`",
        f"- Automation gate exit code: `{automation_gate.get('exit_code')}`",
        f"- Automation gate required count: `{automation_gate.get('required_requirement_count')}`",
        f"- Automation gate blocking count: `{automation_gate.get('blocking_requirement_count')}`",
        f"- Automation gate detail: `{automation_gate.get('detail')}`",
        f"- Automation gate failed requirements: `{automation_gate.get('failed_requirements')}`",
        f"- Automation gate status domain: `{automation_gate.get('status_domain')}`",
        f"- Automation gate decision domain: `{automation_gate.get('decision_domain')}`",
        f"- Automation summary decision: `{automation_summary.get('decision')}`",
        f"- Automation summary exit code: `{automation_summary.get('exit_code')}`",
        f"- Automation summary blocking source: `{automation_summary.get('blocking_source')}`",
        f"- Automation summary failed requirements: `{automation_summary.get('failed_requirements')}`",
        f"- Automation summary decision domain: `{automation_summary.get('decision_domain')}`",
        f"- Receipt check status: `{receipt_check.get('status')}`",
        f"- Receipt check decision: `{receipt_check.get('decision')}`",
        f"- Receipt check exit code: `{receipt_check.get('exit_code')}`",
        f"- Receipt check checker exit code: `{receipt_check.get('checker_exit_code')}`",
        f"- Receipt check blocking source: `{receipt_check.get('blocking_source')}`",
        f"- Receipt check failed requirements: `{receipt_check.get('failed_requirements')}`",
        f"- Receipt check issue count: `{receipt_check.get('issue_count')}`",
        f"- Receipt check issues: `{receipt_check.get('issues')}`",
        f"- Receipt check receipt path: `{receipt_check.get('receipt_path')}`",
        f"- Receipt check json: `{receipt_check_outputs.get('json')}`",
        f"- Receipt check text: `{receipt_check_outputs.get('text')}`",
        f"- Embedded receipt check status: `{embedded_receipt_check.get('status')}`",
        f"- Embedded receipt check decision: `{embedded_receipt_check.get('decision')}`",
        f"- Embedded receipt check exit code: `{embedded_receipt_check.get('exit_code')}`",
        f"- Embedded receipt check checker exit code: `{embedded_receipt_check.get('checker_exit_code')}`",
        f"- Embedded receipt check sidecar status: `{embedded_receipt_check.get('sidecar_status')}`",
        f"- Embedded receipt check issue count: `{embedded_receipt_check.get('issue_count')}`",
        f"- Embedded receipt check issues: `{embedded_receipt_check.get('issues')}`",
        f"- Embedded receipt check receipt path: `{embedded_receipt_check.get('receipt_path')}`",
        f"- Embedded receipt check receipt path exists: `{embedded_receipt_check.get('receipt_path_exists')}`",
        f"- Embedded receipt check json: `{embedded_receipt_check.get('receipt_check_json')}`",
        f"- Embedded receipt check json exists: `{embedded_receipt_check.get('receipt_check_json_exists')}`",
        f"- Embedded receipt check text: `{embedded_receipt_check.get('receipt_check_text')}`",
        f"- Embedded receipt check text exists: `{embedded_receipt_check.get('receipt_check_text_exists')}`",
        f"- Embedded receipt check output json: `{embedded_receipt_check_outputs.get('json')}`",
        f"- Embedded receipt check output text: `{embedded_receipt_check_outputs.get('text')}`",
        f"- Handoff assurance status: `{handoff_assurance.get('status')}`",
        f"- Handoff assurance decision: `{handoff_assurance.get('decision')}`",
        f"- Handoff assurance exit code: `{handoff_assurance.get('exit_code')}`",
        f"- Handoff assurance checker exit code: `{handoff_assurance.get('checker_exit_code')}`",
        f"- Handoff assurance embedded receipt check status: `{handoff_assurance.get('embedded_receipt_check_status')}`",
        f"- Handoff assurance embedded sidecar status: `{handoff_assurance.get('embedded_receipt_check_sidecar_status')}`",
        f"- Handoff assurance receipt schema version: `{handoff_assurance.get('embedded_receipt_check_receipt_schema_version')}`",
        (
            "- Handoff assurance receipt selected CI regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt CI regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt comparison exclusions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_comparison_exclusion_reasons')}`"
        ),
        f"- Handoff assurance output json exists: `{handoff_assurance.get('embedded_receipt_check_output_json_exists')}`",
        f"- Handoff assurance output text exists: `{handoff_assurance.get('embedded_receipt_check_output_text_exists')}`",
        f"- Handoff assurance issue count: `{handoff_assurance.get('issue_count')}`",
        f"- Handoff assurance issues: `{handoff_assurance.get('issues')}`",
        f"- Handoff assurance json: `{handoff_assurance_outputs.get('json')}`",
        f"- Handoff assurance text: `{handoff_assurance_outputs.get('text')}`",
        f"- Next batch command: `{summary.get('next_batch_command_available')}`",
        "",
        "## Command",
        "",
        "```powershell",
        str(report.get("command_text") or ""),
        "```",
        "",
        "## Execution",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Status | {_md(execution.get('status'))} |",
        f"| Elapsed seconds | {_md(execution.get('elapsed_seconds'))} |",
        f"| Stdout tail | {_md(execution.get('stdout_tail'))} |",
        f"| Stderr tail | {_md(execution.get('stderr_tail'))} |",
        "",
        "## Plan Artifacts",
        "",
        "| Key | Exists | Path |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("artifact_rows")):
        lines.append(f"| {_md(row.get('key'))} | {_md(row.get('exists'))} | {_md(row.get('path'))} |")
    if report.get("next_batch_command"):
        lines.extend(
            ["", "## Next Batch Command", "", "```powershell", str(report.get("next_batch_command_text") or ""), "```"]
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_markdown(report), encoding="utf-8")


def render_promoted_training_scale_seed_handoff_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    clean_requirement = _dict(report.get("clean_evidence_requirement"))
    clean_batch_requirement = _dict(report.get("clean_batch_review_requirement"))
    automation_gate = _dict(report.get("automation_gate"))
    automation_summary = _dict(report.get("automation_summary"))
    receipt_check = _receipt_check(report)
    receipt_check_outputs = _receipt_check_outputs(report)
    embedded_receipt_check = _embedded_receipt_check(report)
    embedded_receipt_check_outputs = _embedded_receipt_check_outputs(report)
    handoff_assurance = _handoff_assurance(report)
    handoff_assurance_outputs = _handoff_assurance_outputs(report)
    clean_evidence_domain = ", ".join(
        str(item) for item in _string_list(summary.get("seed_handoff_clean_evidence_status_domain"))
    )
    clean_requirement_domain = ", ".join(
        str(item) for item in _string_list(clean_requirement.get("status_domain"))
    )
    clean_batch_requirement_domain = ", ".join(
        str(item) for item in _string_list(clean_batch_requirement.get("status_domain"))
    )
    automation_gate_domain = ", ".join(str(item) for item in _string_list(automation_gate.get("status_domain")))
    automation_gate_decision_domain = ", ".join(
        str(item) for item in _string_list(automation_gate.get("decision_domain"))
    )
    automation_summary_decision_domain = ", ".join(
        str(item) for item in _string_list(automation_summary.get("decision_domain"))
    )
    stats = [
        ("Status", summary.get("handoff_status")),
        ("Seed", report.get("seed_status")),
        ("Decision", summary.get("decision_status")),
        ("Execute", report.get("execute")),
        ("Return", execution.get("returncode")),
        ("Artifacts", f"{summary.get('available_artifact_count')}/{summary.get('artifact_count')}"),
        ("Plan", summary.get("plan_status")),
        ("Seed suite", summary.get("seed_suite_path")),
        ("Selected handoff suite", summary.get("selected_handoff_suite_consistency")),
        ("Selected handoff mismatch", summary.get("selected_handoff_suite_mismatch_count")),
        ("Selected clean required", summary.get("selected_handoff_require_clean_batch_review")),
        ("Selected clean batch", summary.get("selected_handoff_clean_batch_review_status")),
        ("Selected CI regressions", summary.get("selected_handoff_batch_maturity_ci_regression_count")),
        (
            "Selected selected CI regressions",
            summary.get("selected_handoff_selected_batch_maturity_ci_regression_count"),
        ),
        ("Handoff clean required", summary.get("handoff_require_clean_batch_review_count")),
        ("Handoff clean", summary.get("handoff_clean_batch_review_count")),
        ("Handoff unclean", summary.get("handoff_unclean_batch_review_count")),
        ("Handoff CI regressions", summary.get("handoff_batch_maturity_ci_regression_count")),
        ("Handoff selected CI regressions", summary.get("handoff_selected_batch_maturity_ci_regression_total")),
        ("Ready clean-required", summary.get("comparison_ready_handoff_require_clean_batch_review_count")),
        ("Ready clean batch", summary.get("comparison_ready_handoff_clean_batch_review_count")),
        ("Ready unclean batch", summary.get("comparison_ready_handoff_unclean_batch_review_count")),
        ("Ready CI regressions", summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")),
        (
            "Ready selected CI regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_total"),
        ),
        ("Selected handoff batch", summary.get("selected_handoff_selected_batch_review_status")),
        ("Selected batch blockers", summary.get("selected_handoff_selected_batch_comparison_blocker_action_count")),
        ("Ready batch reviews", summary.get("comparison_ready_handoff_selected_batch_review_count")),
        ("Ready batch blockers", summary.get("comparison_ready_handoff_selected_batch_blocker_count")),
        ("Handoff suite mismatches", summary.get("handoff_suite_mismatch_total")),
        ("Plan suite", summary.get("plan_suite_path")),
        ("Suite alignment", summary.get("seed_handoff_suite_alignment_status")),
        ("Clean evidence", summary.get("seed_handoff_clean_evidence_status")),
        ("Clean evidence domain", clean_evidence_domain),
        ("Clean evidence gate", clean_requirement.get("status")),
        ("Clean evidence gate domain", clean_requirement_domain),
        ("Clean batch gate", clean_batch_requirement.get("status")),
        ("Clean batch gate selected CI", clean_batch_requirement.get("selected_ci_regression_count")),
        ("Clean batch gate domain", clean_batch_requirement_domain),
        ("Automation gate", automation_gate.get("status")),
        ("Automation decision", automation_gate.get("decision")),
        ("Automation exit", automation_gate.get("exit_code")),
        ("Automation required", automation_gate.get("required_requirement_count")),
        ("Automation blocking", automation_gate.get("blocking_requirement_count")),
        ("Automation gate domain", automation_gate_domain),
        ("Automation decision domain", automation_gate_decision_domain),
        ("Automation summary", automation_summary.get("decision")),
        ("Automation summary exit", automation_summary.get("exit_code")),
        ("Automation blocking source", automation_summary.get("blocking_source")),
        ("Automation summary domain", automation_summary_decision_domain),
        ("Receipt check", receipt_check.get("status")),
        ("Receipt decision", receipt_check.get("decision")),
        ("Receipt exit", receipt_check.get("exit_code")),
        ("Receipt checker exit", receipt_check.get("checker_exit_code")),
        ("Receipt blocking source", receipt_check.get("blocking_source")),
        ("Receipt failed requirements", ", ".join(_string_list(receipt_check.get("failed_requirements")))),
        ("Receipt issue count", receipt_check.get("issue_count")),
        ("Receipt receipt path", receipt_check.get("receipt_path")),
        ("Receipt json", receipt_check_outputs.get("json")),
        ("Receipt text", receipt_check_outputs.get("text")),
        ("Embedded receipt check", embedded_receipt_check.get("status")),
        ("Embedded receipt decision", embedded_receipt_check.get("decision")),
        ("Embedded receipt exit", embedded_receipt_check.get("exit_code")),
        ("Embedded receipt checker exit", embedded_receipt_check.get("checker_exit_code")),
        ("Embedded receipt sidecars", embedded_receipt_check.get("sidecar_status")),
        ("Embedded receipt issue count", embedded_receipt_check.get("issue_count")),
        ("Embedded receipt path exists", embedded_receipt_check.get("receipt_path_exists")),
        ("Embedded receipt json exists", embedded_receipt_check.get("receipt_check_json_exists")),
        ("Embedded receipt text exists", embedded_receipt_check.get("receipt_check_text_exists")),
        ("Embedded receipt output json", embedded_receipt_check_outputs.get("json")),
        ("Embedded receipt output text", embedded_receipt_check_outputs.get("text")),
        ("Handoff assurance", handoff_assurance.get("status")),
        ("Assurance decision", handoff_assurance.get("decision")),
        ("Assurance exit", handoff_assurance.get("exit_code")),
        ("Assurance checker exit", handoff_assurance.get("checker_exit_code")),
        ("Assurance embedded check", handoff_assurance.get("embedded_receipt_check_status")),
        ("Assurance sidecars", handoff_assurance.get("embedded_receipt_check_sidecar_status")),
        ("Assurance receipt schema", handoff_assurance.get("embedded_receipt_check_receipt_schema_version")),
        (
            "Assurance selected CI regressions",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count"
            ),
        ),
        (
            "Assurance CI regressions",
            handoff_assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "Assurance comparison exclusions",
            ", ".join(_string_list(handoff_assurance.get("embedded_receipt_check_receipt_comparison_exclusion_reasons"))),
        ),
        ("Assurance output json exists", handoff_assurance.get("embedded_receipt_check_output_json_exists")),
        ("Assurance output text exists", handoff_assurance.get("embedded_receipt_check_output_text_exists")),
        ("Assurance issue count", handoff_assurance.get("issue_count")),
        ("Assurance json", handoff_assurance_outputs.get("json")),
        ("Assurance text", handoff_assurance_outputs.get("text")),
        ("Batch", summary.get("next_batch_command_available")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale seed handoff'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale seed handoff'))}</h1><p>{_e(report.get('seed_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _command_section(report),
            _execution_section(execution),
            _artifact_section(report),
            _plan_section(report),
            _receipt_check_section(report),
            _embedded_receipt_check_section(report),
            _handoff_assurance_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale seed handoff.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_promoted_training_scale_seed_handoff_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_html(report), encoding="utf-8")


def write_promoted_training_scale_seed_handoff_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_seed_handoff.json",
        "csv": root / "promoted_training_scale_seed_handoff.csv",
        "markdown": root / "promoted_training_scale_seed_handoff.md",
        "html": root / "promoted_training_scale_seed_handoff.html",
        "automation_receipt_json": root / "promoted_training_scale_seed_handoff_automation_receipt.json",
        "automation_receipt_text": root / "promoted_training_scale_seed_handoff_automation_receipt.txt",
    }
    write_promoted_training_scale_seed_handoff_json(report, paths["json"])
    write_promoted_training_scale_seed_handoff_csv(report, paths["csv"])
    write_promoted_training_scale_seed_handoff_markdown(report, paths["markdown"])
    write_promoted_training_scale_seed_handoff_html(report, paths["html"])
    write_promoted_training_scale_seed_handoff_automation_receipt_json(report, paths["automation_receipt_json"])
    write_promoted_training_scale_seed_handoff_automation_receipt_text(report, paths["automation_receipt_text"])
    return {key: str(value) for key, value in paths.items()}


def _plan_section(report: dict[str, Any]) -> str:
    plan = _dict(report.get("plan_report"))
    if not plan:
        return "<section><h2>Plan Report</h2><p>No plan report was loaded.</p></section>"
    dataset = _dict(plan.get("dataset"))
    batch = _dict(plan.get("batch"))
    rows = [
        ("Scale tier", dataset.get("scale_tier")),
        ("Source count", dataset.get("source_count")),
        ("Character count", dataset.get("char_count")),
        ("Quality status", dataset.get("quality_status")),
        ("Warning count", dataset.get("warning_count")),
        ("Variant count", len(_list_of_dicts(plan.get("variants")))),
        ("Batch baseline", batch.get("baseline")),
        ("Suite mode", _dict(plan.get("suite")).get("mode")),
        ("Suite name", _dict(plan.get("suite")).get("name")),
        ("Suite path", _dict(plan.get("suite")).get("path")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    next_batch = _display_command(report.get("next_batch_command"))
    extra = (
        f"<p><strong>Next batch command:</strong></p><pre>{_e(next_batch)}</pre>"
        if next_batch
        else "<p>No next batch command is available yet.</p>"
    )
    return f"<section><h2>Plan Report</h2><table>{body}</table>{extra}</section>"


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


def _command_section(report: dict[str, Any]) -> str:
    return f"<section><h2>Seed Command</h2><pre>{_e(report.get('command_text'))}</pre></section>"


def _execution_section(execution: dict[str, Any]) -> str:
    rows = [
        ("Status", execution.get("status")),
        ("Return code", execution.get("returncode")),
        ("Elapsed seconds", execution.get("elapsed_seconds")),
        ("Blocked reason", execution.get("blocked_reason")),
        ("Stdout tail", execution.get("stdout_tail")),
        ("Stderr tail", execution.get("stderr_tail")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return f"<section><h2>Execution</h2><table>{body}</table></section>"


def _artifact_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("artifact_rows")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('key'))}</td>"
            f"<td>{_e(row.get('exists'))}</td>"
            f"<td>{_e(row.get('count'))}</td>"
            f"<td>{_e(row.get('path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Plan Artifacts</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Key</th><th>Exists</th><th>Count</th><th>Path</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f8f3; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1180px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; width: 180px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


__all__ = [
    "build_promoted_training_scale_seed_handoff_automation_receipt",
    "render_promoted_training_scale_seed_handoff_html",
    "render_promoted_training_scale_seed_handoff_automation_receipt_text",
    "render_promoted_training_scale_seed_handoff_markdown",
    "write_promoted_training_scale_seed_handoff_automation_receipt_json",
    "write_promoted_training_scale_seed_handoff_automation_receipt_text",
    "write_promoted_training_scale_seed_handoff_csv",
    "write_promoted_training_scale_seed_handoff_html",
    "write_promoted_training_scale_seed_handoff_json",
    "write_promoted_training_scale_seed_handoff_markdown",
    "write_promoted_training_scale_seed_handoff_outputs",
]
