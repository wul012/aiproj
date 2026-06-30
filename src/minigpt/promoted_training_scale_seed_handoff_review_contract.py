from __future__ import annotations

from typing import Literal, TypedDict


SeedHandoffCleanEvidenceStatus = Literal["ready", "pending-plan", "review", "incomplete"]
SeedHandoffCleanEvidenceRequirementStatus = Literal["not-required", "pass", "fail"]
SeedHandoffCleanBatchReviewRequirementStatus = Literal["not-required", "pass", "fail"]
SeedHandoffAutomationGateStatus = Literal["not-required", "pass", "fail"]
SeedHandoffAutomationGateDecision = Literal["not-requested", "continue", "stop"]
SeedHandoffAutomationSummaryDecision = Literal["continue", "stop"]


class SeedHandoffCleanEvidenceReadiness(TypedDict):
    ready: bool
    status: SeedHandoffCleanEvidenceStatus
    detail: str
    status_domain: list[SeedHandoffCleanEvidenceStatus]


class SeedHandoffCleanEvidenceRequirement(TypedDict):
    required: bool
    status: SeedHandoffCleanEvidenceRequirementStatus
    ready: bool
    readiness_status: SeedHandoffCleanEvidenceStatus | None
    detail: str | None
    status_domain: list[SeedHandoffCleanEvidenceRequirementStatus]


class SeedHandoffCleanBatchReviewRequirement(TypedDict):
    required: bool
    status: SeedHandoffCleanBatchReviewRequirementStatus
    clean: bool
    selected_required: bool
    selected_status: str | None
    selected_ci_regression_count: int
    selected_ci_boundary_plan_check_ready_regression_count: int
    selected_ci_regression_reason_counts: dict[str, int]
    selected_suite_design_regression_count: int
    selected_suite_design_regression_names: list[str]
    detail: str | None
    status_domain: list[SeedHandoffCleanBatchReviewRequirementStatus]


class SeedHandoffAutomationGate(TypedDict):
    required: bool
    status: SeedHandoffAutomationGateStatus
    decision: SeedHandoffAutomationGateDecision
    exit_code: int
    required_requirement_count: int
    passed_requirement_count: int
    failed_requirement_count: int
    blocking_requirement_count: int
    failed_requirements: list[str]
    passed_requirements: list[str]
    detail: str
    status_domain: list[SeedHandoffAutomationGateStatus]
    decision_domain: list[SeedHandoffAutomationGateDecision]


class SeedHandoffAutomationSummary(TypedDict):
    decision: SeedHandoffAutomationSummaryDecision
    exit_code: int
    blocking_source: str | None
    handoff_status: str
    gate_status: SeedHandoffAutomationGateStatus
    gate_decision: SeedHandoffAutomationGateDecision
    gate_required: bool
    gate_blocking_requirement_count: int
    failed_requirements: list[str]
    detail: str
    decision_domain: list[SeedHandoffAutomationSummaryDecision]


SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES: tuple[SeedHandoffCleanEvidenceStatus, ...] = (
    "ready",
    "pending-plan",
    "review",
    "incomplete",
)

SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES: tuple[SeedHandoffCleanEvidenceRequirementStatus, ...] = (
    "not-required",
    "pass",
    "fail",
)

SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES: tuple[SeedHandoffCleanBatchReviewRequirementStatus, ...] = (
    "not-required",
    "pass",
    "fail",
)

SEED_HANDOFF_AUTOMATION_GATE_STATUSES: tuple[SeedHandoffAutomationGateStatus, ...] = (
    "not-required",
    "pass",
    "fail",
)

SEED_HANDOFF_AUTOMATION_GATE_DECISIONS: tuple[SeedHandoffAutomationGateDecision, ...] = (
    "not-requested",
    "continue",
    "stop",
)

SEED_HANDOFF_AUTOMATION_SUMMARY_DECISIONS: tuple[SeedHandoffAutomationSummaryDecision, ...] = (
    "continue",
    "stop",
)


__all__ = [
    "SEED_HANDOFF_AUTOMATION_GATE_DECISIONS",
    "SEED_HANDOFF_AUTOMATION_GATE_STATUSES",
    "SEED_HANDOFF_AUTOMATION_SUMMARY_DECISIONS",
    "SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES",
    "SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES",
    "SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES",
    "SeedHandoffAutomationGate",
    "SeedHandoffAutomationGateDecision",
    "SeedHandoffAutomationGateStatus",
    "SeedHandoffAutomationSummary",
    "SeedHandoffAutomationSummaryDecision",
    "SeedHandoffCleanBatchReviewRequirement",
    "SeedHandoffCleanBatchReviewRequirementStatus",
    "SeedHandoffCleanEvidenceReadiness",
    "SeedHandoffCleanEvidenceRequirement",
    "SeedHandoffCleanEvidenceRequirementStatus",
    "SeedHandoffCleanEvidenceStatus",
]
