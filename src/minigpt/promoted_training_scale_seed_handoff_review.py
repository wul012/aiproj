from __future__ import annotations

from typing import Any, Literal, TypedDict

from minigpt.promoted_training_scale_seed_handoff_review_recommendations import (
    build_seed_handoff_review_recommendations,
)
from minigpt.promoted_training_scale_seed_handoff_review_recommendations import (
    clean_batch_review_requirement_detail as _clean_batch_review_requirement_detail,
)
from minigpt.promoted_training_scale_seed_handoff_review_summary import (
    build_seed_handoff_batch_review_summary,
    build_seed_handoff_clean_batch_review_summary,
)
from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import ci_boundary_plan_check_ready_regression_count
from minigpt.report_utils import positive_int_mapping as _int_mapping
from minigpt.report_utils import string_list as _string_list


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


def build_seed_handoff_clean_evidence_requirement(
    summary: dict[str, Any],
    *,
    required: bool = False,
) -> SeedHandoffCleanEvidenceRequirement:
    ready = bool(summary.get("seed_handoff_clean_evidence_ready"))
    status: SeedHandoffCleanEvidenceRequirementStatus = "not-required"
    if required:
        status = "pass" if ready else "fail"
    readiness_status = summary.get("seed_handoff_clean_evidence_status")
    if readiness_status not in SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES:
        readiness_status = None
    detail = summary.get("seed_handoff_clean_evidence_detail")
    return {
        "required": bool(required),
        "status": status,
        "ready": ready,
        "readiness_status": readiness_status,
        "detail": str(detail) if detail is not None else None,
        "status_domain": list(SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES),
    }


def build_seed_handoff_clean_batch_review_requirement(
    summary: dict[str, Any],
    *,
    required: bool = False,
) -> SeedHandoffCleanBatchReviewRequirement:
    selected_required = bool(summary.get("selected_handoff_require_clean_batch_review"))
    selected_status = summary.get("selected_handoff_clean_batch_review_status")
    status_text = str(selected_status) if selected_status is not None else None
    selected_ci_regressions = _int(summary.get("selected_handoff_batch_maturity_ci_regression_count"))
    selected_ci_regression_reasons = _int_mapping(
        summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts")
    )
    selected_boundary_plan_regressions = ci_boundary_plan_check_ready_regression_count(
        summary.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        selected_ci_regression_reasons,
    )
    selected_suite_design_regressions = _int(
        summary.get("selected_handoff_batch_maturity_suite_design_regression_count")
    )
    selected_suite_design_names = _string_list(
        summary.get("selected_handoff_batch_maturity_suite_design_regression_names")
    )
    clean = (not selected_required) or (
        status_text == "clean"
        and selected_ci_regressions == 0
        and selected_boundary_plan_regressions == 0
        and selected_suite_design_regressions == 0
    )
    status: SeedHandoffCleanBatchReviewRequirementStatus = "not-required"
    if required:
        status = "pass" if clean else "fail"
    return {
        "required": bool(required),
        "status": status,
        "clean": clean,
        "selected_required": selected_required,
        "selected_status": status_text,
        "selected_ci_regression_count": selected_ci_regressions,
        "selected_ci_boundary_plan_check_ready_regression_count": selected_boundary_plan_regressions,
        "selected_ci_regression_reason_counts": selected_ci_regression_reasons,
        "selected_suite_design_regression_count": selected_suite_design_regressions,
        "selected_suite_design_regression_names": selected_suite_design_names,
        "detail": _clean_batch_review_requirement_detail(
            selected_required,
            status_text,
            selected_ci_regressions,
            selected_boundary_plan_regressions,
            selected_suite_design_regressions,
            clean,
        ),
        "status_domain": list(SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES),
    }


def build_seed_handoff_automation_gate(
    clean_evidence_requirement: SeedHandoffCleanEvidenceRequirement,
    clean_batch_review_requirement: SeedHandoffCleanBatchReviewRequirement,
) -> SeedHandoffAutomationGate:
    requirements = {
        "clean_evidence": _dict(clean_evidence_requirement),
        "clean_batch_review": _dict(clean_batch_review_requirement),
    }
    required_names = [name for name, requirement in requirements.items() if requirement.get("required")]
    failed = [name for name in required_names if requirements[name].get("status") == "fail"]
    passed = [name for name in required_names if requirements[name].get("status") == "pass"]
    if not required_names:
        status: SeedHandoffAutomationGateStatus = "not-required"
        decision: SeedHandoffAutomationGateDecision = "not-requested"
        exit_code = 0
        detail = "no seed handoff automation requirements were requested"
    elif failed:
        status = "fail"
        decision = "stop"
        exit_code = 1
        detail = "failed automation requirement(s): " + ", ".join(failed)
    else:
        status = "pass"
        decision = "continue"
        exit_code = 0
        detail = "all requested seed handoff automation requirements passed"
    return {
        "required": bool(required_names),
        "status": status,
        "decision": decision,
        "exit_code": exit_code,
        "required_requirement_count": len(required_names),
        "passed_requirement_count": len(passed),
        "failed_requirement_count": len(failed),
        "blocking_requirement_count": len(failed),
        "failed_requirements": failed,
        "passed_requirements": passed,
        "detail": detail,
        "status_domain": list(SEED_HANDOFF_AUTOMATION_GATE_STATUSES),
        "decision_domain": list(SEED_HANDOFF_AUTOMATION_GATE_DECISIONS),
    }


def build_seed_handoff_automation_summary(
    summary: dict[str, Any],
    automation_gate: SeedHandoffAutomationGate,
) -> SeedHandoffAutomationSummary:
    gate = _dict(automation_gate)
    handoff_status = str(summary.get("handoff_status") or "")
    failed_requirements = _string_list(gate.get("failed_requirements"))
    gate_decision = str(gate.get("decision") or "")
    gate_status = str(gate.get("status") or "")
    gate_blocking_count = _int(gate.get("blocking_requirement_count"))
    execution_blocking_statuses = {"blocked", "failed", "timeout"}
    if gate_decision == "stop":
        decision: SeedHandoffAutomationSummaryDecision = "stop"
        exit_code = _int(gate.get("exit_code")) or 1
        blocking_source = "automation_gate"
        detail = str(gate.get("detail") or "automation gate requested stop")
    elif handoff_status in execution_blocking_statuses:
        decision = "stop"
        exit_code = 1
        blocking_source = "handoff_execution"
        detail = f"seed handoff status is {handoff_status}"
    else:
        decision = "continue"
        exit_code = 0
        blocking_source = None
        detail = "seed handoff automation can continue"
    return {
        "decision": decision,
        "exit_code": exit_code,
        "blocking_source": blocking_source,
        "handoff_status": handoff_status,
        "gate_status": gate_status if gate_status in SEED_HANDOFF_AUTOMATION_GATE_STATUSES else "not-required",
        "gate_decision": (
            gate_decision
            if gate_decision in SEED_HANDOFF_AUTOMATION_GATE_DECISIONS
            else "not-requested"
        ),
        "gate_required": bool(gate.get("required")),
        "gate_blocking_requirement_count": gate_blocking_count,
        "failed_requirements": failed_requirements,
        "detail": detail,
        "decision_domain": list(SEED_HANDOFF_AUTOMATION_SUMMARY_DECISIONS),
    }


def build_seed_handoff_clean_evidence_readiness(
    handoff_status: Any,
    suite_alignment: dict[str, Any],
) -> SeedHandoffCleanEvidenceReadiness:
    alignment_status = str(suite_alignment.get("status") or "")
    detail = str(suite_alignment.get("detail") or "")
    if alignment_status == "consistent" and handoff_status == "completed":
        return _clean_evidence_payload(
            ready=True,
            status="ready",
            detail="completed handoff has consistent suite alignment and can be used as clean comparison evidence",
        )
    if alignment_status == "pending-plan":
        return _clean_evidence_payload(
            ready=False,
            status="pending-plan",
            detail="execute the seed handoff before treating clean comparison evidence as ready",
        )
    if alignment_status == "missing":
        return _clean_evidence_payload(
            ready=False,
            status="incomplete",
            detail=f"missing suite alignment evidence: {detail}",
        )
    if alignment_status == "mismatch":
        return _clean_evidence_payload(
            ready=False,
            status="review",
            detail=f"review suite alignment mismatch before using this as clean comparison evidence: {detail}",
        )
    return _clean_evidence_payload(
        ready=False,
        status="review",
        detail="review seed handoff suite alignment before treating this as clean comparison evidence",
    )


def build_seed_handoff_suite_alignment(selected_handoff_path: Any, seed_path: Any, plan_path: Any) -> dict[str, Any]:
    selected = None if selected_handoff_path is None else str(selected_handoff_path)
    seed = None if seed_path is None else str(seed_path)
    plan = None if plan_path is None else str(plan_path)
    missing = [name for name, value in (("selected_handoff", selected), ("seed", seed)) if not value]
    mismatches = []
    if selected and seed and selected != seed:
        mismatches.append(f"selected_handoff={selected} differs from seed={seed}")
    if plan:
        if seed and plan != seed:
            mismatches.append(f"plan={plan} differs from seed={seed}")
        if selected and plan != selected:
            mismatches.append(f"plan={plan} differs from selected_handoff={selected}")
    if missing:
        status = "missing"
        detail = "missing required suite path(s): " + ", ".join(missing)
    elif mismatches:
        status = "mismatch"
        detail = "; ".join(mismatches)
    elif plan:
        status = "consistent"
        detail = f"selected_handoff, seed, and plan suite paths align at {plan}"
    else:
        status = "pending-plan"
        detail = f"selected_handoff and seed suite paths align at {seed}; plan suite is not available yet"
    return {
        "status": status,
        "detail": detail,
        "mismatch_count": len(mismatches),
        "missing_count": len(missing),
    }


def _clean_evidence_payload(
    *,
    ready: bool,
    status: SeedHandoffCleanEvidenceStatus,
    detail: str,
) -> SeedHandoffCleanEvidenceReadiness:
    return {
        "ready": ready,
        "status": status,
        "detail": detail,
        "status_domain": list(SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES),
    }


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES",
    "SEED_HANDOFF_AUTOMATION_GATE_STATUSES",
    "SEED_HANDOFF_AUTOMATION_GATE_DECISIONS",
    "SEED_HANDOFF_AUTOMATION_SUMMARY_DECISIONS",
    "SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES",
    "SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES",
    "SeedHandoffAutomationGate",
    "SeedHandoffAutomationGateDecision",
    "SeedHandoffAutomationGateStatus",
    "SeedHandoffAutomationSummary",
    "SeedHandoffAutomationSummaryDecision",
    "SeedHandoffCleanBatchReviewRequirement",
    "SeedHandoffCleanBatchReviewRequirementStatus",
    "SeedHandoffCleanEvidenceRequirement",
    "SeedHandoffCleanEvidenceRequirementStatus",
    "SeedHandoffCleanEvidenceReadiness",
    "SeedHandoffCleanEvidenceStatus",
    "build_seed_handoff_batch_review_summary",
    "build_seed_handoff_clean_batch_review_summary",
    "build_seed_handoff_clean_batch_review_requirement",
    "build_seed_handoff_clean_evidence_readiness",
    "build_seed_handoff_clean_evidence_requirement",
    "build_seed_handoff_automation_gate",
    "build_seed_handoff_automation_summary",
    "build_seed_handoff_review_recommendations",
    "build_seed_handoff_suite_alignment",
]
