from __future__ import annotations

from typing import Any

from minigpt.promoted_training_scale_seed_review import (
    append_seed_handoff_batch_review_recommendation,
    append_seed_handoff_clean_batch_recommendation,
    build_seed_handoff_batch_review_summary,
    build_seed_handoff_clean_batch_review_summary,
)
from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
)


def build_promoted_training_scale_seed_summary(
    seed_status: str,
    decision: dict[str, Any],
    seed: dict[str, Any],
    plan: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    sources = _list_of_dicts(plan.get("sources"))
    summary = {
        "seed_status": seed_status,
        "decision_status": decision.get("decision_status"),
        "selected_name": seed.get("selected_name"),
        "selected_gate_status": seed.get("gate_status"),
        "selected_batch_status": seed.get("batch_status"),
        "selected_readiness_score": seed.get("readiness_score"),
        "selected_run_exists": seed.get("training_scale_run_exists"),
        "source_count": len(sources),
        "missing_source_count": sum(1 for row in sources if not row.get("exists")),
        "command_available": plan.get("command_available"),
        "execution_ready": plan.get("execution_ready"),
        "baseline_suite_path": _dict(seed.get("suite")).get("path"),
        "selected_handoff_require_suite_consistency": _dict(seed.get("handoff_suite_guard")).get("selected_handoff_require_suite_consistency"),
        "selected_handoff_suite_consistency": _dict(seed.get("handoff_suite_guard")).get("selected_handoff_suite_consistency"),
        "selected_handoff_suite_mismatch_count": _dict(seed.get("handoff_suite_guard")).get("selected_handoff_suite_mismatch_count"),
        "selected_handoff_selected_suite_path": _dict(seed.get("handoff_suite_guard")).get("selected_handoff_selected_suite_path"),
        "handoff_suite_consistent_count": _dict(seed.get("handoff_suite_guard")).get("handoff_suite_consistent_count"),
        "handoff_suite_mismatch_total": _dict(seed.get("handoff_suite_guard")).get("handoff_suite_mismatch_total"),
        "next_suite_path": _dict(plan.get("suite")).get("path"),
        "next_suite_source": plan.get("suite_source"),
        "blocker_count": len(blockers),
    }
    summary.update(build_seed_handoff_clean_batch_review_summary(seed))
    summary.update(build_seed_handoff_batch_review_summary(seed))
    return summary


def build_promoted_training_scale_seed_recommendations(
    seed_status: str,
    seed: dict[str, Any],
    plan: dict[str, Any],
    blockers: list[str],
) -> list[str]:
    if seed_status == "ready":
        recommendations = [
            "Run the generated plan command on the next corpus, then pass its outputs through the v70-v80 training scale chain.",
            "Keep the selected promoted baseline path in the seed report so the next cycle can explain where it came from.",
        ]
        append_seed_handoff_clean_batch_recommendation(recommendations, seed)
        append_seed_handoff_batch_review_recommendation(recommendations, seed)
        return recommendations
    if seed_status == "review":
        recommendations = [
            "Review the promoted baseline decision before running the next plan command.",
            "If the review is accepted, reuse the generated command and keep this seed as the cycle handoff artifact.",
        ]
        append_seed_handoff_clean_batch_recommendation(recommendations, seed)
        append_seed_handoff_batch_review_recommendation(recommendations, seed)
        return recommendations
    if blockers:
        return ["Fix the seed blockers before starting the next training scale planning cycle."]
    return ["Inspect the promoted baseline decision before building a next-cycle plan."]


__all__ = [
    "build_promoted_training_scale_seed_recommendations",
    "build_promoted_training_scale_seed_summary",
]
