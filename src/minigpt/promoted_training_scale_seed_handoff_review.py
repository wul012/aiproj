from __future__ import annotations

from typing import Any, Literal, TypedDict

from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import string_list as _string_list


SeedHandoffCleanEvidenceStatus = Literal["ready", "pending-plan", "review", "incomplete"]
SeedHandoffCleanEvidenceRequirementStatus = Literal["not-required", "pass", "fail"]
SeedHandoffCleanBatchReviewRequirementStatus = Literal["not-required", "pass", "fail"]


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
    detail: str | None
    status_domain: list[SeedHandoffCleanBatchReviewRequirementStatus]


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


def build_seed_handoff_batch_review_summary(baseline: dict[str, Any]) -> dict[str, Any]:
    batch_review = _dict(baseline.get("handoff_batch_review"))
    return {
        "selected_handoff_selected_batch_review_status": batch_review.get(
            "selected_handoff_selected_batch_review_status"
        ),
        "selected_handoff_selected_batch_comparison_review_action_count": batch_review.get(
            "selected_handoff_selected_batch_comparison_review_action_count"
        ),
        "selected_handoff_selected_batch_comparison_blocker_action_count": batch_review.get(
            "selected_handoff_selected_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_selected_batch_maturity_coverage_regression_count": batch_review.get(
            "selected_handoff_selected_batch_maturity_coverage_regression_count"
        ),
        "selected_handoff_batch_comparison_review_action_count": batch_review.get(
            "selected_handoff_batch_comparison_review_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_action_count": batch_review.get(
            "selected_handoff_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_reasons": _string_list(
            batch_review.get("selected_handoff_batch_comparison_blocker_reasons")
        ),
        "comparison_ready_handoff_selected_batch_review_count": batch_review.get(
            "comparison_ready_handoff_selected_batch_review_count"
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": batch_review.get(
            "comparison_ready_handoff_selected_batch_blocker_count"
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": batch_review.get(
            "comparison_ready_handoff_selected_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": batch_review.get(
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_review_action_total": batch_review.get(
            "comparison_ready_handoff_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_action_total": batch_review.get(
            "comparison_ready_handoff_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": _string_list(
            batch_review.get("comparison_ready_handoff_batch_comparison_blocker_reasons")
        ),
    }


def build_seed_handoff_clean_batch_review_summary(baseline: dict[str, Any]) -> dict[str, Any]:
    clean_review = _dict(baseline.get("handoff_clean_batch_review"))
    return {
        "selected_handoff_require_clean_batch_review": clean_review.get(
            "selected_handoff_require_clean_batch_review"
        ),
        "selected_handoff_clean_batch_review_status": clean_review.get(
            "selected_handoff_clean_batch_review_status"
        ),
        "handoff_require_clean_batch_review_count": clean_review.get(
            "handoff_require_clean_batch_review_count"
        ),
        "handoff_clean_batch_review_count": clean_review.get("handoff_clean_batch_review_count"),
        "handoff_unclean_batch_review_count": clean_review.get("handoff_unclean_batch_review_count"),
        "comparison_ready_handoff_require_clean_batch_review_count": clean_review.get(
            "comparison_ready_handoff_require_clean_batch_review_count"
        ),
        "comparison_ready_handoff_clean_batch_review_count": clean_review.get(
            "comparison_ready_handoff_clean_batch_review_count"
        ),
        "comparison_ready_handoff_unclean_batch_review_count": clean_review.get(
            "comparison_ready_handoff_unclean_batch_review_count"
        ),
    }


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
    clean = (not selected_required) or status_text == "clean"
    status: SeedHandoffCleanBatchReviewRequirementStatus = "not-required"
    if required:
        status = "pass" if clean else "fail"
    return {
        "required": bool(required),
        "status": status,
        "clean": clean,
        "selected_required": selected_required,
        "selected_status": status_text,
        "detail": _clean_batch_review_requirement_detail(selected_required, status_text, clean),
        "status_domain": list(SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES),
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


def build_seed_handoff_review_recommendations(
    summary: dict[str, Any],
    clean_evidence_requirement: SeedHandoffCleanEvidenceRequirement | None,
    clean_batch_review_requirement: SeedHandoffCleanBatchReviewRequirement | None = None,
) -> list[str]:
    return (
        _suite_alignment_recommendations(summary)
        + _clean_evidence_requirement_recommendations(clean_evidence_requirement)
        + _clean_batch_review_requirement_recommendations(clean_batch_review_requirement)
        + _handoff_clean_batch_review_recommendations(summary)
        + _handoff_batch_review_recommendations(summary)
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


def _clean_evidence_requirement_recommendations(
    clean_evidence_requirement: SeedHandoffCleanEvidenceRequirement | None,
) -> list[str]:
    requirement = _dict(clean_evidence_requirement)
    if not requirement.get("required"):
        return []
    status = str(requirement.get("status") or "")
    detail = str(requirement.get("detail") or "")
    if status == "pass":
        return ["Clean-evidence requirement passed; this seed handoff can be used as clean comparison evidence."]
    if status == "fail":
        suffix = f": {detail}" if detail else "."
        return [f"Clean-evidence requirement failed; resolve readiness before using this handoff as clean comparison evidence{suffix}"]
    return ["Review clean-evidence requirement status before using this handoff as clean comparison evidence."]


def _clean_batch_review_requirement_detail(selected_required: bool, selected_status: str | None, clean: bool) -> str:
    if clean:
        if selected_required:
            return "selected handoff clean batch-review requirement is clean"
        return "selected handoff does not require clean batch-review evidence"
    return f"selected handoff requires clean batch-review evidence but status is {selected_status or 'missing'}"


def _clean_batch_review_requirement_recommendations(
    clean_batch_review_requirement: SeedHandoffCleanBatchReviewRequirement | None,
) -> list[str]:
    requirement = _dict(clean_batch_review_requirement)
    if not requirement.get("required"):
        return []
    status = str(requirement.get("status") or "")
    detail = str(requirement.get("detail") or "")
    if status == "pass":
        return ["Clean batch-review requirement passed; the selected handoff evidence is clean for seed handoff automation."]
    if status == "fail":
        suffix = f": {detail}" if detail else "."
        return [f"Clean batch-review requirement failed; resolve selected handoff evidence before seed handoff automation{suffix}"]
    return ["Review clean batch-review requirement status before seed handoff automation."]


def _handoff_batch_review_recommendations(summary: dict[str, Any]) -> list[str]:
    selected_status = str(summary.get("selected_handoff_selected_batch_review_status") or "")
    if selected_status == "blocker":
        return [
            "Resolve selected handoff batch blocker actions before treating this seed handoff as clean model-quality evidence."
        ]
    if selected_status == "review":
        return [
            "Review selected handoff batch actions before treating this seed handoff as clean model-quality evidence."
        ]
    if summary.get("comparison_ready_handoff_selected_batch_blocker_count"):
        return [
            "Other comparison-ready promoted inputs carried handoff batch blockers; keep them with this handoff review context."
        ]
    return []


def _handoff_clean_batch_review_recommendations(summary: dict[str, Any]) -> list[str]:
    selected_required = bool(summary.get("selected_handoff_require_clean_batch_review"))
    selected_status = str(summary.get("selected_handoff_clean_batch_review_status") or "")
    if selected_required and selected_status != "clean":
        return [
            "Resolve selected handoff clean batch-review status before treating this seed handoff as clean model-quality evidence."
        ]
    if _int(summary.get("handoff_unclean_batch_review_count")):
        return [
            "Rejected promoted decision inputs include unclean clean-required handoffs; keep them out of the seed handoff baseline."
        ]
    return []


def _suite_alignment_recommendations(summary: dict[str, Any]) -> list[str]:
    status = str(summary.get("seed_handoff_suite_alignment_status") or "")
    detail = str(summary.get("seed_handoff_suite_alignment_detail") or "")
    if status == "pending-plan":
        return ["Suite alignment is pending plan generation; execute the seed handoff before treating the plan suite as confirmed."]
    if status == "consistent":
        return ["Suite alignment is consistent across selected handoff, seed, and generated plan paths."]
    if status == "mismatch":
        return [f"Review suite alignment mismatch before using this handoff as clean model-quality evidence: {detail}"]
    if status == "missing":
        return [f"Record missing suite alignment evidence before treating this handoff as a clean comparison: {detail}"]
    return ["Review suite alignment evidence before continuing the next training-scale cycle."]


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES",
    "SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES",
    "SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES",
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
    "build_seed_handoff_review_recommendations",
    "build_seed_handoff_suite_alignment",
]
