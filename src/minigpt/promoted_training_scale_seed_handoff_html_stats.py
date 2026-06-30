from __future__ import annotations

from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_artifacts import (
    _embedded_receipt_check,
    _embedded_receipt_check_outputs,
    _handoff_assurance,
    _handoff_assurance_outputs,
    _receipt_check,
    _receipt_check_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    string_list as _string_list,
)


def build_promoted_training_scale_seed_handoff_html_stats(report: dict[str, Any]) -> list[tuple[str, Any]]:
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
    return [
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
            "Selected CI boundary plan",
            summary.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Selected CI reasons", _fmt_mapping(summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts"))),
        (
            "Selected suite-design regressions",
            summary.get("selected_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Selected selected CI regressions",
            summary.get("selected_handoff_selected_batch_maturity_ci_regression_count"),
        ),
        (
            "Selected selected CI boundary plan",
            summary.get("selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Selected selected CI reasons",
            _fmt_mapping(summary.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Selected selected suite-design regressions",
            summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_count"),
        ),
        ("Handoff clean required", summary.get("handoff_require_clean_batch_review_count")),
        ("Handoff clean", summary.get("handoff_clean_batch_review_count")),
        ("Handoff unclean", summary.get("handoff_unclean_batch_review_count")),
        ("Handoff CI regressions", summary.get("handoff_batch_maturity_ci_regression_count")),
        (
            "Handoff CI boundary plan",
            summary.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Handoff selected CI regressions", summary.get("handoff_selected_batch_maturity_ci_regression_total")),
        (
            "Handoff selected CI boundary plan",
            summary.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        ("Handoff CI reasons", _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))),
        (
            "Handoff selected CI reasons",
            _fmt_mapping(summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        ("Handoff suite-design regressions", summary.get("handoff_batch_maturity_suite_design_regression_count")),
        (
            "Handoff selected suite-design regressions",
            summary.get("handoff_selected_batch_maturity_suite_design_regression_total"),
        ),
        ("Ready clean-required", summary.get("comparison_ready_handoff_require_clean_batch_review_count")),
        ("Ready clean batch", summary.get("comparison_ready_handoff_clean_batch_review_count")),
        ("Ready unclean batch", summary.get("comparison_ready_handoff_unclean_batch_review_count")),
        ("Ready CI regressions", summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")),
        (
            "Ready CI boundary plan",
            summary.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Ready selected CI regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_total"),
        ),
        (
            "Ready selected CI boundary plan",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "Ready CI reasons",
            _fmt_mapping(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Ready selected CI reasons",
            _fmt_mapping(summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Ready suite-design regressions",
            summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Ready selected suite-design regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"),
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
        (
            "Clean batch gate selected CI boundary plan",
            clean_batch_requirement.get("selected_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Clean batch gate selected CI reasons", _fmt_mapping(clean_batch_requirement.get("selected_ci_regression_reason_counts"))),
        (
            "Clean batch gate selected suite-design",
            clean_batch_requirement.get("selected_suite_design_regression_count"),
        ),
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
            "Assurance selected CI reasons",
            _fmt_mapping(
                handoff_assurance.get(
                    "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts"
                )
            ),
        ),
        (
            "Assurance selected CI boundary plan",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Assurance CI regressions",
            handoff_assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "Assurance CI reasons",
            _fmt_mapping(
                handoff_assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts")
            ),
        ),
        (
            "Assurance CI boundary plan",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Assurance selected suite-design regressions",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count"
            ),
        ),
        (
            "Assurance suite-design regressions",
            handoff_assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Assurance ready suite-design regressions",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"
            ),
        ),
        (
            "Assurance ready CI boundary plan",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Assurance ready CI reasons",
            _fmt_mapping(
                handoff_assurance.get(
                    "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"
                )
            ),
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


__all__ = ["build_promoted_training_scale_seed_handoff_html_stats"]
