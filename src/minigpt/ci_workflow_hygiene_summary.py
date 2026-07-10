from __future__ import annotations

from minigpt.ci_workflow_hygiene_checks import check_passed, forbidden_env_hits, python_version
from minigpt.ci_workflow_hygiene_policy import (
    REQUIRED_ACTIONS,
    REQUIRED_COMMAND_FRAGMENTS,
    REQUIRED_COMMAND_ORDER,
    REQUIRED_PYTHON_VERSION,
)
from minigpt.ci_workflow_hygiene_types import CiWorkflowAction, CiWorkflowCheck, CiWorkflowSummary


def build_summary(
    text: str,
    actions: list[CiWorkflowAction],
    checks: list[CiWorkflowCheck],
) -> CiWorkflowSummary:
    failed_checks = [item for item in checks if item.get("status") != "pass"]
    required_action_repos = set(REQUIRED_ACTIONS)
    found_required_actions = [item for item in actions if item.get("repository") in required_action_repos]
    missing_steps = [
        check for check in checks if check.get("category") == "required_command" and check.get("status") != "pass"
    ]
    order_violations = [
        check for check in checks if check.get("category") == "required_order" and check.get("status") != "pass"
    ]
    execution_policy_checks = [check for check in checks if check.get("category") == "execution_policy"]
    execution_policy_violations = [check for check in execution_policy_checks if check.get("status") != "pass"]
    main_branch_push_scope_ready = check_passed(checks, "execution:main_branch_push_scope")
    tag_push_suppressed = main_branch_push_scope_ready and check_passed(checks, "execution:no_tag_push_trigger")
    pip_dependency_cache_ready = check_passed(checks, "execution:pip_dependency_cache") and check_passed(
        checks, "execution:pip_cache_manifest"
    )
    concurrency_cancel_ready = check_passed(checks, "execution:same_ref_concurrency_group") and check_passed(
        checks, "execution:cancel_superseded_runs"
    )
    plan_digest_gate_present, plan_digest_gate_order_ready, plan_digest_gate_ready = _gate_state(
        checks,
        "command:ci_tiny_scorecard_plan_digest_check",
        "order:ci_tiny_scorecard_plan_check_after_smoke",
        "order:ci_tiny_scorecard_plan_check_before_coverage",
    )
    boundary_gate_check_present, boundary_gate_check_order_ready, boundary_gate_check_ready = _gate_state(
        checks,
        "command:baseline_candidate_threshold_boundary_gate_check",
        "order:baseline_candidate_threshold_boundary_gate_check_after_plan_digest",
        "order:baseline_candidate_threshold_boundary_gate_check_before_coverage",
    )
    boundary_gate_plan_check_present, boundary_gate_plan_check_order_ready, boundary_gate_plan_check_ready = (
        _gate_state(
            checks,
            "command:baseline_candidate_threshold_boundary_gate_plan_check",
            "order:baseline_candidate_threshold_boundary_gate_plan_check_after_gate_check",
            "order:baseline_candidate_threshold_boundary_gate_plan_check_before_coverage",
        )
    )
    (
        archived_path_portability_check_present,
        archived_path_portability_check_order_ready,
        archived_path_portability_check_ready,
    ) = _gate_state(
        checks,
        "command:archived_path_portability_check",
        "order:archived_path_portability_check_before_receipt_smoke",
        "order:archived_path_portability_check_before_coverage",
    )
    receipt_failure_smoke_present, receipt_failure_smoke_order_ready, receipt_failure_smoke_ready = _gate_state(
        checks,
        "command:promoted_seed_receipt_contract_failure_smoke",
        "order:promoted_seed_receipt_contract_failure_smoke_after_assurance",
        "order:promoted_seed_receipt_contract_failure_smoke_before_coverage",
    )
    (
        receipt_failure_smoke_plan_check_present,
        receipt_failure_smoke_plan_check_order_ready,
        receipt_failure_smoke_plan_check_ready,
    ) = _gate_state(
        checks,
        "command:promoted_seed_receipt_contract_failure_smoke_plan_check",
        "order:promoted_seed_receipt_contract_failure_smoke_plan_check_after_smoke",
        "order:promoted_seed_receipt_contract_failure_smoke_plan_check_before_coverage",
    )
    drift_contract_smoke_present, drift_contract_smoke_order_ready, drift_contract_smoke_ready = _gate_state(
        checks,
        "command:release_readiness_drift_contract_smoke",
        "order:release_readiness_drift_contract_smoke_before_coverage",
    )
    project_docs_readability_present, project_docs_readability_order_ready, project_docs_readability_ready = (
        _gate_state(
            checks,
            "command:project_docs_readability_gate",
            "order:project_docs_readability_after_source_encoding",
            "order:project_docs_readability_before_ci_hygiene",
            "order:project_docs_readability_before_coverage",
        )
    )
    static_analysis_present, static_analysis_order_ready, static_analysis_ready = _gate_state(
        checks,
        "command:static_analysis_gate",
        "order:static_analysis_after_ci_hygiene",
        "order:static_analysis_before_coverage",
    )
    type_analysis_present, type_analysis_order_ready, type_analysis_ready = _gate_state(
        checks,
        "command:type_analysis_gate",
        "order:type_analysis_after_static_analysis",
        "order:type_analysis_before_coverage",
    )
    file_size_ratchet_present, file_size_ratchet_order_ready, file_size_ratchet_ready = _gate_state(
        checks,
        "command:file_size_ratchet",
        "order:file_size_ratchet_after_artifact_schema_guard",
        "order:file_size_ratchet_before_coverage",
    )
    aiproj_track_closeout_present, aiproj_track_closeout_order_ready, aiproj_track_closeout_ready = _gate_state(
        checks,
        "command:aiproj_track_closeout",
        "order:aiproj_track_closeout_after_file_size_ratchet",
        "order:aiproj_track_closeout_before_coverage",
    )
    normalization_guard_present, normalization_guard_order_ready, normalization_guard_ready = _gate_state(
        checks,
        "command:normalization_guard",
        "order:normalization_guard_before_coverage",
    )
    return {
        "status": "pass" if not failed_checks else "fail",
        "decision": "continue_with_node24_native_ci" if not failed_checks else "fix_ci_workflow_hygiene",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed_checks),
        "failed_check_count": len(failed_checks),
        "action_count": len(actions),
        "required_action_count": len(REQUIRED_ACTIONS),
        "found_required_action_count": len(found_required_actions),
        "node24_native_action_count": sum(1 for item in found_required_actions if item.get("node24_native")),
        "forbidden_env_count": len(forbidden_env_hits(text)),
        "required_step_count": len(REQUIRED_COMMAND_FRAGMENTS),
        "missing_step_count": len(missing_steps),
        "required_order_count": len(REQUIRED_COMMAND_ORDER),
        "order_violation_count": len(order_violations),
        "execution_policy_check_count": len(execution_policy_checks),
        "execution_policy_violation_count": len(execution_policy_violations),
        "main_branch_push_scope_ready": main_branch_push_scope_ready,
        "tag_push_suppressed": tag_push_suppressed,
        "pip_dependency_cache_ready": pip_dependency_cache_ready,
        "concurrency_cancel_ready": concurrency_cancel_ready,
        "ci_execution_economy_ready": (tag_push_suppressed and pip_dependency_cache_ready and concurrency_cancel_ready),
        "tiny_scorecard_plan_digest_gate_present": plan_digest_gate_present,
        "tiny_scorecard_plan_digest_gate_order_ready": plan_digest_gate_order_ready,
        "tiny_scorecard_plan_digest_gate_ready": plan_digest_gate_ready,
        "baseline_candidate_threshold_boundary_gate_check_present": boundary_gate_check_present,
        "baseline_candidate_threshold_boundary_gate_check_order_ready": boundary_gate_check_order_ready,
        "baseline_candidate_threshold_boundary_gate_check_ready": boundary_gate_check_ready,
        "baseline_candidate_threshold_boundary_gate_plan_check_present": boundary_gate_plan_check_present,
        "baseline_candidate_threshold_boundary_gate_plan_check_order_ready": boundary_gate_plan_check_order_ready,
        "baseline_candidate_threshold_boundary_gate_plan_check_ready": boundary_gate_plan_check_ready,
        "archived_path_portability_check_present": archived_path_portability_check_present,
        "archived_path_portability_check_order_ready": archived_path_portability_check_order_ready,
        "archived_path_portability_check_ready": archived_path_portability_check_ready,
        "promoted_seed_receipt_contract_failure_smoke_present": receipt_failure_smoke_present,
        "promoted_seed_receipt_contract_failure_smoke_order_ready": receipt_failure_smoke_order_ready,
        "promoted_seed_receipt_contract_failure_smoke_ready": receipt_failure_smoke_ready,
        "promoted_seed_receipt_contract_failure_smoke_plan_check_present": receipt_failure_smoke_plan_check_present,
        "promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready": receipt_failure_smoke_plan_check_order_ready,
        "promoted_seed_receipt_contract_failure_smoke_plan_check_ready": receipt_failure_smoke_plan_check_ready,
        "release_readiness_drift_contract_smoke_present": drift_contract_smoke_present,
        "release_readiness_drift_contract_smoke_order_ready": drift_contract_smoke_order_ready,
        "release_readiness_drift_contract_smoke_ready": drift_contract_smoke_ready,
        "project_docs_readability_present": project_docs_readability_present,
        "project_docs_readability_order_ready": project_docs_readability_order_ready,
        "project_docs_readability_ready": project_docs_readability_ready,
        "static_analysis_present": static_analysis_present,
        "static_analysis_order_ready": static_analysis_order_ready,
        "static_analysis_ready": static_analysis_ready,
        "type_analysis_present": type_analysis_present,
        "type_analysis_order_ready": type_analysis_order_ready,
        "type_analysis_ready": type_analysis_ready,
        "file_size_ratchet_present": file_size_ratchet_present,
        "file_size_ratchet_order_ready": file_size_ratchet_order_ready,
        "file_size_ratchet_ready": file_size_ratchet_ready,
        "aiproj_track_closeout_present": aiproj_track_closeout_present,
        "aiproj_track_closeout_order_ready": aiproj_track_closeout_order_ready,
        "aiproj_track_closeout_ready": aiproj_track_closeout_ready,
        "normalization_guard_present": normalization_guard_present,
        "normalization_guard_order_ready": normalization_guard_order_ready,
        "normalization_guard_ready": normalization_guard_ready,
        "python_version": python_version(text),
    }


def build_recommendations(summary: CiWorkflowSummary) -> list[str]:
    if summary.get("status") == "pass":
        return ["Keep CI workflow action versions and quality gates aligned with the Node 24 native policy."]
    recommendations: list[str] = []
    if summary.get("node24_native_action_count", 0) < summary.get("required_action_count", 0):
        recommendations.append("Upgrade required GitHub actions to the expected Node 24 native majors.")
    if summary.get("forbidden_env_count", 0):
        recommendations.append("Remove force-runtime environment variables and rely on native action metadata instead.")
    if summary.get("missing_step_count", 0):
        recommendations.append("Restore required source hygiene and unittest commands in the CI workflow.")
    if summary.get("order_violation_count", 0):
        recommendations.append(
            "Keep assurance and tiny-scorecard evidence checks before coverage so CI fails fast on evidence drift."
        )
    if not summary.get("ci_execution_economy_ready"):
        recommendations.append(
            "Restore main-only push scope, tag suppression, pip caching, and same-ref cancellation to avoid duplicate CI work."
        )
    if not summary.get("project_docs_readability_ready"):
        recommendations.append(
            "Restore the project docs readability gate after source encoding and before CI hygiene and coverage."
        )
    if not summary.get("static_analysis_ready"):
        recommendations.append("Restore the static analysis gate after CI workflow hygiene and before coverage.")
    if not summary.get("type_analysis_ready"):
        recommendations.append("Restore scoped type analysis after static analysis and before coverage.")
    if not summary.get("file_size_ratchet_ready"):
        recommendations.append("Restore the file-size ratchet after artifact schema guard and before coverage.")
    if not summary.get("aiproj_track_closeout_ready"):
        recommendations.append("Restore the aiproj A-track closeout gate after file-size ratchet and before coverage.")
    if not summary.get("promoted_seed_receipt_contract_failure_smoke_ready"):
        recommendations.append("Restore the receipt contract failure smoke after assurance and before coverage.")
    if not summary.get("archived_path_portability_check_ready"):
        recommendations.append("Restore archived path portability before receipt contract smoke and coverage.")
    if not summary.get("promoted_seed_receipt_contract_failure_smoke_plan_check_ready"):
        recommendations.append(
            "Restore the receipt contract failure smoke plan check after the wrapper and before coverage."
        )
    if summary.get("python_version") != REQUIRED_PYTHON_VERSION:
        recommendations.append("Align actions/setup-python with the source compatibility target.")
    if not summary.get("normalization_guard_ready"):
        recommendations.append(
            "Restore the normalization guard before coverage so architecture and public API drift fail fast."
        )
    return recommendations


def _gate_state(
    checks: list[CiWorkflowCheck],
    present_check_id: str,
    *order_check_ids: str,
) -> tuple[bool, bool, bool]:
    present = check_passed(checks, present_check_id)
    order_ready = all(check_passed(checks, check_id) for check_id in order_check_ids)
    return present, order_ready, present and order_ready


__all__ = ["build_recommendations", "build_summary"]
