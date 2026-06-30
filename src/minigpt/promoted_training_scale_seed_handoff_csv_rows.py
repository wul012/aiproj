from __future__ import annotations

from typing import Any

from minigpt.promoted_training_scale_seed_handoff_csv_fields import handoff_csv_fieldnames
from minigpt.promoted_training_scale_seed_handoff_receipt_artifacts import (
    _embedded_receipt_check_fields,
    _handoff_assurance_fields,
    _receipt_check_fields,
)
from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    string_list as _string_list,
)


def handoff_csv_row(report: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    clean_requirement = _dict(report.get("clean_evidence_requirement"))
    clean_batch_requirement = _dict(report.get("clean_batch_review_requirement"))
    automation_gate = _dict(report.get("automation_gate"))
    automation_summary = _dict(report.get("automation_summary"))
    receipt_check_fields = _receipt_check_fields(report)
    embedded_receipt_check_fields = _embedded_receipt_check_fields(report)
    handoff_assurance_fields = _handoff_assurance_fields(report)
    return {
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
        "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": summary.get(
            "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "selected_handoff_batch_maturity_ci_regression_names": "; ".join(
            _string_list(summary.get("selected_handoff_batch_maturity_ci_regression_names"))
        ),
        "selected_handoff_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts")
        ),
        "selected_handoff_batch_maturity_suite_design_regression_count": summary.get(
            "selected_handoff_batch_maturity_suite_design_regression_count"
        ),
        "selected_handoff_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("selected_handoff_batch_maturity_suite_design_regression_names"))
        ),
        "selected_handoff_selected_batch_maturity_ci_regression_count": summary.get(
            "selected_handoff_selected_batch_maturity_ci_regression_count"
        ),
        "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": summary.get(
            "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "selected_handoff_selected_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")
        ),
        "selected_handoff_selected_batch_maturity_suite_design_regression_count": summary.get(
            "selected_handoff_selected_batch_maturity_suite_design_regression_count"
        ),
        "selected_handoff_selected_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_names"))
        ),
        "selected_comparison_exclusion_reasons": "; ".join(
            _string_list(summary.get("selected_comparison_exclusion_reasons"))
        ),
        "handoff_require_clean_batch_review_count": summary.get("handoff_require_clean_batch_review_count"),
        "handoff_clean_batch_review_count": summary.get("handoff_clean_batch_review_count"),
        "handoff_unclean_batch_review_count": summary.get("handoff_unclean_batch_review_count"),
        "handoff_batch_maturity_ci_regression_count": summary.get("handoff_batch_maturity_ci_regression_count"),
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": summary.get(
            "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "handoff_selected_batch_maturity_ci_regression_total": summary.get(
            "handoff_selected_batch_maturity_ci_regression_total"
        ),
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": summary.get(
            "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
        ),
        "handoff_batch_maturity_ci_regression_names": "; ".join(
            _string_list(summary.get("handoff_batch_maturity_ci_regression_names"))
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("handoff_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_batch_maturity_suite_design_regression_count": summary.get(
            "handoff_batch_maturity_suite_design_regression_count"
        ),
        "handoff_selected_batch_maturity_suite_design_regression_total": summary.get(
            "handoff_selected_batch_maturity_suite_design_regression_total"
        ),
        "handoff_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("handoff_batch_maturity_suite_design_regression_names"))
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("handoff_selected_batch_maturity_suite_design_regression_names"))
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
        "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": summary.get(
            "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": summary.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_total"
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": summary.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_names": "; ".join(
            _string_list(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_names"))
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count": summary.get(
            "comparison_ready_handoff_batch_maturity_suite_design_regression_count"
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total": summary.get(
            "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names"))
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names"))
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
        "clean_batch_review_requirement_selected_ci_boundary_plan_check_ready_regression_count": (
            clean_batch_requirement.get("selected_ci_boundary_plan_check_ready_regression_count")
        ),
        "clean_batch_review_requirement_selected_ci_regression_reason_counts": _fmt_mapping(
            clean_batch_requirement.get("selected_ci_regression_reason_counts")
        ),
        "clean_batch_review_requirement_selected_suite_design_regression_count": clean_batch_requirement.get(
            "selected_suite_design_regression_count"
        ),
        "clean_batch_review_requirement_selected_suite_design_regression_names": "; ".join(
            _string_list(clean_batch_requirement.get("selected_suite_design_regression_names"))
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
    }


__all__ = ["handoff_csv_fieldnames", "handoff_csv_row"]
