from __future__ import annotations

from pathlib import Path

DEFAULT_WORKFLOW_PATH = Path(".github") / "workflows" / "ci.yml"
REQUIRED_ACTIONS = {"actions/checkout": "v6", "actions/setup-python": "v6"}
FORBIDDEN_ENV_VARS = ("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24",)
COVERAGE_FAIL_UNDER_FLOOR = 88.98
REQUIRED_COMMAND_FRAGMENTS = {
    "source_encoding_gate": "scripts/check_source_encoding.py",
    "project_docs_readability_gate": "scripts/check_project_docs_readability.py",
    "ci_workflow_hygiene_gate": "scripts/check_ci_workflow_hygiene.py",
    "static_analysis_gate": "scripts/check_static_analysis.py",
    "type_analysis_gate": "scripts/check_type_analysis.py",
    "archived_path_portability_check": "scripts/check_archived_path_portability.py",
    "promoted_seed_handoff_assurance_smoke": "scripts/check_promoted_seed_handoff_assurance_smoke.py",
    "promoted_seed_receipt_contract_failure_smoke": "scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py",
    "promoted_seed_receipt_contract_failure_smoke_plan_check": "scripts/check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py",
    "tiny_scorecard_comparison_inline_check_smoke": "scripts/run_ci_tiny_scorecard_comparison_smoke.py",
    "tiny_scorecard_summary_check_sidecar": "--summary-check-out-dir",
    "ci_tiny_scorecard_plan_digest_check": "scripts/check_ci_tiny_scorecard_plan.py",
    "baseline_candidate_threshold_boundary_gate_check": "scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py",
    "baseline_candidate_threshold_boundary_gate_plan_check": "scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py",
    "release_readiness_drift_contract_smoke": "scripts/check_release_readiness_drift_contract_smoke.py",
    "normalization_guard": "scripts/check_normalization_guard.py",
    "test_coverage_report": "scripts/run_test_coverage.py",
    "coverage_fail_under_gate": f"--fail-under {COVERAGE_FAIL_UNDER_FLOOR}",
}
REQUIRED_COMMAND_ORDER = {
    "project_docs_readability_after_source_encoding": (
        "scripts/check_source_encoding.py",
        "scripts/check_project_docs_readability.py",
    ),
    "project_docs_readability_before_ci_hygiene": (
        "scripts/check_project_docs_readability.py",
        "scripts/check_ci_workflow_hygiene.py",
    ),
    "project_docs_readability_before_coverage": (
        "scripts/check_project_docs_readability.py",
        "scripts/run_test_coverage.py",
    ),
    "static_analysis_after_ci_hygiene": (
        "scripts/check_ci_workflow_hygiene.py",
        "scripts/check_static_analysis.py",
    ),
    "static_analysis_before_coverage": (
        "scripts/check_static_analysis.py",
        "scripts/run_test_coverage.py",
    ),
    "type_analysis_after_static_analysis": (
        "scripts/check_static_analysis.py",
        "scripts/check_type_analysis.py",
    ),
    "type_analysis_before_coverage": (
        "scripts/check_type_analysis.py",
        "scripts/run_test_coverage.py",
    ),
    "promoted_seed_handoff_assurance_smoke_before_coverage": (
        "scripts/check_promoted_seed_handoff_assurance_smoke.py",
        "scripts/run_test_coverage.py",
    ),
    "tiny_scorecard_inline_check_smoke_before_coverage": (
        "scripts/run_ci_tiny_scorecard_comparison_smoke.py",
        "scripts/run_test_coverage.py",
    ),
    "archived_path_portability_check_before_receipt_smoke": (
        "scripts/check_archived_path_portability.py",
        "scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py",
    ),
    "archived_path_portability_check_before_coverage": (
        "scripts/check_archived_path_portability.py",
        "scripts/run_test_coverage.py",
    ),
    "promoted_seed_receipt_contract_failure_smoke_after_assurance": (
        "scripts/check_promoted_seed_handoff_assurance_smoke.py",
        "scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py",
    ),
    "promoted_seed_receipt_contract_failure_smoke_before_coverage": (
        "scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py",
        "scripts/run_test_coverage.py",
    ),
    "promoted_seed_receipt_contract_failure_smoke_plan_check_after_smoke": (
        "scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py",
        "scripts/check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py",
    ),
    "promoted_seed_receipt_contract_failure_smoke_plan_check_before_coverage": (
        "scripts/check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py",
        "scripts/run_test_coverage.py",
    ),
    "ci_tiny_scorecard_plan_check_after_smoke": (
        "scripts/run_ci_tiny_scorecard_comparison_smoke.py",
        "scripts/check_ci_tiny_scorecard_plan.py",
    ),
    "ci_tiny_scorecard_plan_check_before_coverage": (
        "scripts/check_ci_tiny_scorecard_plan.py",
        "scripts/run_test_coverage.py",
    ),
    "baseline_candidate_threshold_boundary_gate_check_after_plan_digest": (
        "scripts/check_ci_tiny_scorecard_plan.py",
        "scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py",
    ),
    "baseline_candidate_threshold_boundary_gate_check_before_coverage": (
        "scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py",
        "scripts/run_test_coverage.py",
    ),
    "baseline_candidate_threshold_boundary_gate_plan_check_after_gate_check": (
        "scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py",
        "scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py",
    ),
    "baseline_candidate_threshold_boundary_gate_plan_check_before_coverage": (
        "scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py",
        "scripts/run_test_coverage.py",
    ),
    "release_readiness_drift_contract_smoke_before_coverage": (
        "scripts/check_release_readiness_drift_contract_smoke.py",
        "scripts/run_test_coverage.py",
    ),
    "normalization_guard_before_coverage": (
        "scripts/check_normalization_guard.py",
        "scripts/run_test_coverage.py",
    ),
}
REQUIRED_PYTHON_VERSION = "3.11"


__all__ = [
    "DEFAULT_WORKFLOW_PATH",
    "FORBIDDEN_ENV_VARS",
    "COVERAGE_FAIL_UNDER_FLOOR",
    "REQUIRED_ACTIONS",
    "REQUIRED_COMMAND_FRAGMENTS",
    "REQUIRED_COMMAND_ORDER",
    "REQUIRED_PYTHON_VERSION",
]
