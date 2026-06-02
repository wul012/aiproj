from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import ci_boundary_plan_check_ready_regression_count
from minigpt.report_utils import format_mapping as _fmt_mapping
from minigpt.report_utils import string_list as _string_list


def build_seed_handoff_review_recommendations(
    summary: dict[str, Any],
    clean_evidence_requirement: dict[str, Any] | None,
    clean_batch_review_requirement: dict[str, Any] | None = None,
) -> list[str]:
    return (
        _suite_alignment_recommendations(summary)
        + _clean_evidence_requirement_recommendations(clean_evidence_requirement)
        + _clean_batch_review_requirement_recommendations(clean_batch_review_requirement)
        + _handoff_clean_batch_review_recommendations(summary)
        + _handoff_batch_review_recommendations(summary)
    )


def clean_batch_review_requirement_detail(
    selected_required: bool,
    selected_status: str | None,
    selected_ci_regressions: int,
    selected_boundary_plan_regressions: int,
    selected_suite_design_regressions: int,
    clean: bool,
) -> str:
    if clean:
        if selected_required:
            return "selected handoff clean batch-review requirement is clean"
        return "selected handoff does not require clean batch-review evidence"
    if selected_required and selected_boundary_plan_regressions:
        return (
            "selected handoff requires clean batch-review evidence but carries "
            f"{selected_boundary_plan_regressions} CI boundary plan-check regression(s)"
        )
    if selected_required and selected_ci_regressions:
        return (
            "selected handoff requires clean batch-review evidence but carries "
            f"{selected_ci_regressions} batch CI regression(s)"
        )
    if selected_required and selected_suite_design_regressions:
        return (
            "selected handoff requires clean batch-review evidence but carries "
            f"{selected_suite_design_regressions} batch suite-design regression(s)"
        )
    return f"selected handoff requires clean batch-review evidence but status is {selected_status or 'missing'}"


def _clean_evidence_requirement_recommendations(clean_evidence_requirement: dict[str, Any] | None) -> list[str]:
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


def _clean_batch_review_requirement_recommendations(
    clean_batch_review_requirement: dict[str, Any] | None,
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
    selected_ci_regressions = _int(summary.get("selected_handoff_batch_maturity_ci_regression_count"))
    selected_boundary_plan_regressions = ci_boundary_plan_check_ready_regression_count(
        summary.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts"),
    )
    selected_suite_design_regressions = _int(
        summary.get("selected_handoff_batch_maturity_suite_design_regression_count")
    )
    if selected_required and selected_status != "clean":
        return [
            "Resolve selected handoff clean batch-review status before treating this seed handoff as clean model-quality evidence."
        ]
    if selected_required and selected_boundary_plan_regressions:
        return [
            "Resolve selected handoff batch CI regressions caused by boundary plan-check readiness before treating "
            "this seed handoff as clean model-quality evidence. "
            f"Boundary plan regressions: {selected_boundary_plan_regressions}."
        ]
    if selected_required and selected_ci_regressions:
        reasons = _fmt_mapping(summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts"))
        return [
            "Resolve selected handoff batch CI regressions before treating this seed handoff as clean model-quality "
            f"evidence; observed reasons: {reasons}."
        ]
    if selected_required and selected_suite_design_regressions:
        names = ", ".join(_string_list(summary.get("selected_handoff_batch_maturity_suite_design_regression_names")))
        suffix = f" Observed names: {names}." if names else ""
        return [
            "Resolve selected handoff batch suite-design regressions before treating this seed handoff as clean "
            f"model-quality evidence.{suffix}"
        ]
    handoff_boundary_plan_regressions = ci_boundary_plan_check_ready_regression_count(
        summary.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        summary.get("handoff_batch_maturity_ci_regression_reason_counts"),
    )
    if _int(summary.get("handoff_batch_maturity_ci_regression_count")):
        if handoff_boundary_plan_regressions:
            return [
                "Rejected promoted decision inputs include handoff batch CI regressions caused by boundary "
                "plan-check readiness; keep them out of the seed handoff baseline. "
                f"Boundary plan regressions: {handoff_boundary_plan_regressions}."
            ]
        reasons = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        return [
            "Rejected promoted decision inputs include handoff batch CI regressions; keep them out of the seed handoff "
            f"baseline. Observed reasons: {reasons}."
        ]
    if _int(summary.get("handoff_batch_maturity_suite_design_regression_count")):
        names = ", ".join(_string_list(summary.get("handoff_batch_maturity_suite_design_regression_names")))
        suffix = f" Observed names: {names}." if names else ""
        return [
            "Rejected promoted decision inputs include handoff batch suite-design regressions; keep them out of the "
            f"seed handoff baseline.{suffix}"
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
    "build_seed_handoff_review_recommendations",
    "clean_batch_review_requirement_detail",
]
