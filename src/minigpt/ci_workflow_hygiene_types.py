from __future__ import annotations

from typing import Any, Literal, TypedDict


CheckStatus = Literal["pass", "fail"]


class CiWorkflowCheck(TypedDict):
    id: str
    category: str
    target: str
    expected: str
    actual: str
    status: CheckStatus
    detail: str


class CiWorkflowAction(TypedDict):
    repository: str
    version: str
    raw: str
    line: int
    node24_native: bool


class CiWorkflowSummary(TypedDict):
    status: CheckStatus
    decision: str
    check_count: int
    passed_check_count: int
    failed_check_count: int
    action_count: int
    required_action_count: int
    found_required_action_count: int
    node24_native_action_count: int
    forbidden_env_count: int
    required_step_count: int
    missing_step_count: int
    required_order_count: int
    order_violation_count: int
    execution_policy_check_count: int
    execution_policy_violation_count: int
    main_branch_push_scope_ready: bool
    tag_push_suppressed: bool
    pip_dependency_cache_ready: bool
    concurrency_cancel_ready: bool
    ci_execution_economy_ready: bool
    tiny_scorecard_plan_digest_gate_present: bool
    tiny_scorecard_plan_digest_gate_order_ready: bool
    tiny_scorecard_plan_digest_gate_ready: bool
    baseline_candidate_threshold_boundary_gate_check_present: bool
    baseline_candidate_threshold_boundary_gate_check_order_ready: bool
    baseline_candidate_threshold_boundary_gate_check_ready: bool
    baseline_candidate_threshold_boundary_gate_plan_check_present: bool
    baseline_candidate_threshold_boundary_gate_plan_check_order_ready: bool
    baseline_candidate_threshold_boundary_gate_plan_check_ready: bool
    archived_path_portability_check_present: bool
    archived_path_portability_check_order_ready: bool
    archived_path_portability_check_ready: bool
    promoted_seed_receipt_contract_failure_smoke_present: bool
    promoted_seed_receipt_contract_failure_smoke_order_ready: bool
    promoted_seed_receipt_contract_failure_smoke_ready: bool
    promoted_seed_receipt_contract_failure_smoke_plan_check_present: bool
    promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready: bool
    promoted_seed_receipt_contract_failure_smoke_plan_check_ready: bool
    release_readiness_drift_contract_smoke_present: bool
    release_readiness_drift_contract_smoke_order_ready: bool
    release_readiness_drift_contract_smoke_ready: bool
    project_docs_readability_present: bool
    project_docs_readability_order_ready: bool
    project_docs_readability_ready: bool
    static_analysis_present: bool
    static_analysis_order_ready: bool
    static_analysis_ready: bool
    type_analysis_present: bool
    type_analysis_order_ready: bool
    type_analysis_ready: bool
    file_size_ratchet_present: bool
    file_size_ratchet_order_ready: bool
    file_size_ratchet_ready: bool
    aiproj_track_closeout_present: bool
    aiproj_track_closeout_order_ready: bool
    aiproj_track_closeout_ready: bool
    normalization_guard_present: bool
    normalization_guard_order_ready: bool
    normalization_guard_ready: bool
    python_version: str


class CiWorkflowReport(TypedDict):
    schema_version: int
    title: str
    generated_at: str
    workflow_path: str
    policy: dict[str, Any]
    summary: CiWorkflowSummary
    actions: list[CiWorkflowAction]
    checks: list[CiWorkflowCheck]
    recommendations: list[str]


__all__ = [
    "CheckStatus",
    "CiWorkflowAction",
    "CiWorkflowCheck",
    "CiWorkflowReport",
    "CiWorkflowSummary",
]
