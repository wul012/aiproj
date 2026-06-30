from __future__ import annotations

from typing import Any

from minigpt.promoted_training_scale_seed_handoff_review import (
    SeedHandoffCleanBatchReviewRequirement,
    SeedHandoffCleanEvidenceRequirement,
    build_seed_handoff_batch_review_summary,
    build_seed_handoff_clean_batch_review_summary,
    build_seed_handoff_clean_evidence_readiness,
    build_seed_handoff_review_recommendations,
    build_seed_handoff_suite_alignment,
)
from minigpt.report_utils import (
    as_dict as _dict,
    count_available_artifacts,
    list_of_dicts as _list_of_dicts,
)


def build_promoted_training_scale_seed_handoff_summary(
    seed: dict[str, Any],
    next_plan: dict[str, Any],
    plan_report: dict[str, Any],
    execution: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    next_batch_command: list[str],
) -> dict[str, Any]:
    baseline = _dict(seed.get("baseline_seed"))
    plan_summary = _dict(plan_report.get("summary"))
    plan_suite = _dict(plan_report.get("suite"))
    plan_dataset = _dict(plan_report.get("dataset"))
    handoff_guard = _dict(baseline.get("handoff_suite_guard"))
    seed_suite_path = _dict(next_plan.get("suite")).get("path")
    selected_handoff_suite_path = handoff_guard.get("selected_handoff_selected_suite_path")
    plan_suite_path = plan_suite.get("path") or plan_summary.get("suite_path")
    suite_alignment = build_seed_handoff_suite_alignment(selected_handoff_suite_path, seed_suite_path, plan_suite_path)
    clean_evidence_readiness = build_seed_handoff_clean_evidence_readiness(execution.get("status"), suite_alignment)
    summary = {
        "handoff_status": execution.get("status"),
        "seed_status": seed.get("seed_status"),
        "decision_status": baseline.get("decision_status"),
        "selected_name": baseline.get("selected_name"),
        "selected_gate_status": baseline.get("gate_status"),
        "selected_batch_status": baseline.get("batch_status"),
        "selected_readiness_score": baseline.get("readiness_score"),
        "source_count": len(_list_of_dicts(next_plan.get("sources"))),
        "missing_source_count": sum(1 for row in _list_of_dicts(next_plan.get("sources")) if not row.get("exists")),
        "artifact_count": len(artifact_rows),
        "available_artifact_count": count_available_artifacts(artifact_rows),
        "plan_status": "available" if plan_report else "missing",
        "seed_suite_path": seed_suite_path,
        "seed_suite_source": next_plan.get("suite_source"),
        "selected_handoff_require_suite_consistency": handoff_guard.get("selected_handoff_require_suite_consistency"),
        "selected_handoff_suite_consistency": handoff_guard.get("selected_handoff_suite_consistency"),
        "selected_handoff_suite_mismatch_count": handoff_guard.get("selected_handoff_suite_mismatch_count"),
        "selected_handoff_selected_suite_path": selected_handoff_suite_path,
        "handoff_suite_consistent_count": handoff_guard.get("handoff_suite_consistent_count"),
        "handoff_suite_mismatch_total": handoff_guard.get("handoff_suite_mismatch_total"),
        "comparison_ready_handoff_suite_mismatch_total": handoff_guard.get("comparison_ready_handoff_suite_mismatch_total"),
        "plan_suite_mode": plan_suite.get("mode") or plan_summary.get("suite_mode"),
        "plan_suite_name": plan_suite.get("name") or plan_summary.get("suite_name"),
        "plan_suite_path": plan_suite_path,
        "seed_handoff_suite_alignment_status": suite_alignment["status"],
        "seed_handoff_suite_alignment_detail": suite_alignment["detail"],
        "seed_handoff_suite_alignment_mismatch_count": suite_alignment["mismatch_count"],
        "seed_handoff_suite_alignment_missing_count": suite_alignment["missing_count"],
        "seed_handoff_clean_evidence_ready": clean_evidence_readiness["ready"],
        "seed_handoff_clean_evidence_status": clean_evidence_readiness["status"],
        "seed_handoff_clean_evidence_detail": clean_evidence_readiness["detail"],
        "seed_handoff_clean_evidence_status_domain": clean_evidence_readiness["status_domain"],
        "plan_scale_tier": plan_dataset.get("scale_tier"),
        "plan_variant_count": len(_list_of_dicts(plan_report.get("variants"))),
        "plan_source_count": plan_dataset.get("source_count"),
        "plan_quality_status": plan_dataset.get("quality_status"),
        "next_batch_command_available": bool(next_batch_command),
        "execution_returncode": execution.get("returncode"),
        "execution_elapsed_seconds": execution.get("elapsed_seconds"),
    }
    summary.update(build_seed_handoff_clean_batch_review_summary(baseline))
    summary.update(build_seed_handoff_batch_review_summary(baseline))
    return summary


def build_promoted_training_scale_seed_handoff_recommendations(
    summary: dict[str, Any],
    plan_report: dict[str, Any],
    execution: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    next_batch_command: list[str],
    clean_evidence_requirement: SeedHandoffCleanEvidenceRequirement | None = None,
    clean_batch_review_requirement: SeedHandoffCleanBatchReviewRequirement | None = None,
) -> list[str]:
    status = str(summary.get("handoff_status") or "")
    review_recommendations = build_seed_handoff_review_recommendations(
        summary,
        clean_evidence_requirement,
        clean_batch_review_requirement,
    )
    if status == "planned":
        return (
            review_recommendations
            + ["Review the generated seed command, then rerun with --execute to materialize the next training scale plan."]
        )
    if status == "blocked":
        return (
            review_recommendations
            + ["Fix the seed or plan blockers before trying to produce the next training scale plan."]
        )
    if status == "timeout":
        return (
            review_recommendations
            + ["Inspect the partial plan output tree and rerun with a larger timeout if the plan command is still valid."]
        )
    if status == "failed":
        return (
            review_recommendations
            + ["Inspect stdout/stderr tails and the seed command before retrying the next plan handoff."]
        )
    recommendations = review_recommendations + [
        "Use the generated plan report and batch command as the next input to the training-scale workflow.",
    ]
    if plan_report:
        recommendations.append("Keep the generated plan JSON and variants JSON as the evidence for the next cycle.")
    if artifact_rows and summary.get("available_artifact_count") != summary.get("artifact_count"):
        recommendations.append("Some expected plan artifacts are missing; inspect the plan output directory before moving on.")
    if next_batch_command:
        recommendations.append("The next batch command is ready, but it should be reviewed before executing training.")
    if execution.get("returncode") not in {None, 0}:
        recommendations.append("The plan command returned a non-zero exit code, so treat the seed handoff as failed.")
    return recommendations


__all__ = [
    "build_promoted_training_scale_seed_handoff_recommendations",
    "build_promoted_training_scale_seed_handoff_summary",
]
