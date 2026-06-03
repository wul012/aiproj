from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_review import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_plan.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_plan.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_plan.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_plan.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_plan.html"


def locate_route_promotion_bounded_real_replay_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion bounded real replay repair plan input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_repair_plan(
    real_replay_review: dict[str, Any],
    *,
    real_replay_review_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay repair plan",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(real_replay_review.get("summary"))
    case_reviews = list_of_dicts(real_replay_review.get("case_reviews"))
    repair_tasks = [_repair_task(row) for row in case_reviews if row.get("case_pass") is not True]
    checks = _checks(real_replay_review, review_summary, case_reviews, repair_tasks)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    plan = _plan(status, repair_tasks, review_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, plan),
        "failed_count": len(issues),
        "issues": issues,
        "source_real_replay_review": str(real_replay_review_path or ""),
        "source_review_summary": review_summary,
        "repair_tasks": repair_tasks,
        "check_rows": checks,
        "repair_plan": plan,
        "summary": _summary(status, checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def resolve_exit_code(report: dict[str, Any], *, require_plan_ready: bool) -> int:
    return 1 if require_plan_ready and report.get("status") != "pass" else 0


def _repair_task(row: dict[str, Any]) -> dict[str, Any]:
    case_id = str(row.get("case_id") or "unknown-case")
    missed_terms = [str(term) for term in row.get("missed_terms", [])]
    hit_terms = [str(term) for term in row.get("hit_terms", [])]
    diagnosis = str(row.get("diagnosis") or "unknown")
    if diagnosis.startswith("partial_required_terms_generated"):
        repair_type = "missing_term_retention_repair"
        training_focus = "preserve observed hit terms while adding missed required terms"
    elif diagnosis.startswith("no_required_terms_generated"):
        repair_type = "prompt_to_required_terms_bridge_repair"
        training_focus = "teach the prompt surface to emit both required terms directly"
    else:
        repair_type = "general_required_terms_repair"
        training_focus = "rebuild the fixed/loss answer bridge for this case"
    surface_probe = "unknown_token_surface_probe" if row.get("unknown_token_surface") is True else "standard_surface_probe"
    return {
        "task_id": f"repair-{case_id}",
        "case_id": case_id,
        "repair_type": repair_type,
        "diagnosis": diagnosis,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "surface_probe": surface_probe,
        "training_focus": training_focus,
        "required_success_condition": "continuation_contains_fixed_and_loss",
        "recommended_action": row.get("recommended_action"),
    }


def _checks(
    review: dict[str, Any],
    review_summary: dict[str, Any],
    case_reviews: list[dict[str, Any]],
    repair_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("review_status_passed", review.get("status") == "pass", review.get("status"), "source replay review must pass"),
        _check("review_needs_repair", review_summary.get("promotion_ready") is False, review_summary.get("promotion_ready"), "repair plan is only needed when promotion is not ready"),
        _check("repair_review_ready", review_summary.get("repair_review_ready") is True, review_summary.get("repair_review_ready"), "source review must be ready for repair planning"),
        _check("case_reviews_present", bool(case_reviews), len(case_reviews), "repair plan must inspect case reviews"),
        _check("repair_tasks_present", bool(repair_tasks), len(repair_tasks), "repair plan must include failed-case tasks"),
        _check("repair_task_count_matches_failed_cases", len(repair_tasks) == int(review_summary.get("failed_case_count") or 0), {"tasks": len(repair_tasks), "failed_cases": review_summary.get("failed_case_count")}, "repair tasks must match failed replay cases"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(status: str, repair_tasks: list[dict[str, Any]], review_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "task_count": len(repair_tasks),
        "source_pass_rate": review_summary.get("pass_rate"),
        "target_pass_rate": 1.0,
        "required_terms": ["fixed", "loss"],
        "non_goals": [
            "do_not_claim_general_llm_quality",
            "do_not_expand_beyond_bounded_fixed_loss_route",
            "do_not_promote_until_real_replay_passes_all_cases",
        ],
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_repair_seed",
        "next_step": "build_bounded_real_replay_repair_seed" if status == "pass" else "repair_bounded_real_replay_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_real_replay_repair_plan_ready": status == "pass" and plan.get("ready") is True,
        "task_count": plan.get("task_count"),
        "source_pass_rate": plan.get("source_pass_rate"),
        "target_pass_rate": plan.get("target_pass_rate"),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "next_step": plan.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, plan: dict[str, Any]) -> str:
    if status == "pass" and plan.get("ready") is True:
        return "model_capability_route_promotion_bounded_real_replay_repair_plan_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_repair_plan"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Repair plan inputs are not ready.", "next_action": "repair replay review evidence"}
    return {
        "model_quality_claim": "repair_plan_only",
        "reason": "The plan translates missed bounded replay cases into targeted repair tasks; it does not prove model improvement.",
        "next_action": plan.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_repair_plan",
    "locate_route_promotion_bounded_real_replay_review",
    "read_json_report",
    "resolve_exit_code",
]
