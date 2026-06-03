from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_review.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_review.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_review.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_review.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_review.html"


def locate_route_promotion_bounded_real_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion bounded real replay review input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_review(
    real_replay_report: dict[str, Any],
    *,
    real_replay_path: str | Path | None = None,
    minimum_pass_rate_for_repair_review: float = 0.4,
    title: str = "MiniGPT model capability route promotion bounded real replay review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(real_replay_report.get("summary"))
    case_reviews = [_case_review(row) for row in list_of_dicts(real_replay_report.get("replay_rows"))]
    review_summary = _review_summary(case_reviews, replay_summary, minimum_pass_rate_for_repair_review)
    checks = _checks(real_replay_report, replay_summary, case_reviews)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, review_summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_real_replay": str(real_replay_path or ""),
        "source_replay_summary": replay_summary,
        "case_reviews": case_reviews,
        "check_rows": checks,
        "summary": _summary(status, checks, review_summary),
        "interpretation": _interpretation(status, review_summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_review_pass: bool, require_promotion_ready: bool = False) -> int:
    if require_review_pass and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _case_review(row: dict[str, Any]) -> dict[str, Any]:
    expected_terms = [str(term) for term in row.get("expected_terms", [])]
    hit_terms = [str(term) for term in row.get("hit_terms", [])]
    missed_terms = [str(term) for term in row.get("missed_terms", [])]
    continuation = str(row.get("continuation") or "")
    if row.get("case_pass") is True:
        diagnosis = "case_passed"
        severity = "info"
        action = "keep_case_as_replay_anchor"
    elif hit_terms:
        diagnosis = "partial_required_terms_generated"
        severity = "repair"
        action = "target_missing_terms_without_forgetting_hits"
    else:
        diagnosis = "no_required_terms_generated"
        severity = "repair"
        action = "repair_prompt_to_required_term_bridge"
    if "\ufffd" in continuation and row.get("case_pass") is not True:
        diagnosis = f"{diagnosis}_with_unknown_token_surface"
    return {
        "case_id": row.get("case_id"),
        "case_pass": row.get("case_pass") is True,
        "expected_terms": expected_terms,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "continuation_chars": len(continuation),
        "unknown_token_surface": "\ufffd" in continuation,
        "diagnosis": diagnosis,
        "severity": severity,
        "recommended_action": action,
    }


def _review_summary(case_reviews: list[dict[str, Any]], replay_summary: dict[str, Any], minimum_pass_rate: float) -> dict[str, Any]:
    passed = [row for row in case_reviews if row.get("case_pass") is True]
    failed = [row for row in case_reviews if row.get("case_pass") is not True]
    pass_rate = float(replay_summary.get("pass_rate") or 0.0)
    diagnosis_counts: dict[str, int] = {}
    for row in case_reviews:
        key = str(row.get("diagnosis") or "unknown")
        diagnosis_counts[key] = diagnosis_counts.get(key, 0) + 1
    promotion_ready = bool(case_reviews) and not failed and replay_summary.get("model_route_quality_ready") is True
    repair_review_ready = bool(case_reviews) and pass_rate >= minimum_pass_rate
    return {
        "promotion_ready": promotion_ready,
        "repair_review_ready": repair_review_ready,
        "case_count": len(case_reviews),
        "passed_case_count": len(passed),
        "failed_case_count": len(failed),
        "pass_rate": pass_rate,
        "minimum_pass_rate_for_repair_review": minimum_pass_rate,
        "diagnosis_counts": dict(sorted(diagnosis_counts.items())),
        "unknown_token_surface_count": sum(1 for row in case_reviews if row.get("unknown_token_surface") is True),
        "next_step": "promote_bounded_route_replay" if promotion_ready else "build_bounded_real_replay_repair_plan",
    }


def _checks(real_replay_report: dict[str, Any], replay_summary: dict[str, Any], case_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("real_replay_status_passed", real_replay_report.get("status") == "pass", real_replay_report.get("status"), "real replay execution status must pass"),
        _check("real_replay_executed", replay_summary.get("bounded_real_replay_executed") is True, replay_summary.get("bounded_real_replay_executed"), "real replay must have executed"),
        _check("case_reviews_present", bool(case_reviews), len(case_reviews), "review must inspect replay rows"),
        _check("case_count_matches_summary", len(case_reviews) == int(replay_summary.get("case_count") or 0), {"reviews": len(case_reviews), "summary": replay_summary.get("case_count")}, "reviewed cases must match replay summary"),
        _check("no_source_execution_failures", int(real_replay_report.get("failed_count") or 0) == 0, real_replay_report.get("failed_count"), "source replay must have no execution check failures"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, checks: list[dict[str, Any]], review_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_real_replay_review_ready": status == "pass",
        "promotion_ready": review_summary["promotion_ready"] if status == "pass" else False,
        "repair_review_ready": review_summary["repair_review_ready"] if status == "pass" else False,
        "case_count": review_summary["case_count"],
        "passed_case_count": review_summary["passed_case_count"],
        "failed_case_count": review_summary["failed_case_count"],
        "pass_rate": review_summary["pass_rate"],
        "diagnosis_counts": review_summary["diagnosis_counts"],
        "unknown_token_surface_count": review_summary["unknown_token_surface_count"],
        "next_step": review_summary["next_step"] if status == "pass" else "repair_bounded_real_replay_review_inputs",
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, review_summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_review"
    if review_summary["promotion_ready"]:
        return "model_capability_route_promotion_bounded_real_replay_review_accepted"
    return "model_capability_route_promotion_bounded_real_replay_review_needs_repair"


def _interpretation(status: str, review_summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "The replay review could not validate source replay evidence.", "next_action": "repair review inputs"}
    if review_summary["promotion_ready"]:
        return {"model_quality_claim": "bounded_replay_passed", "reason": "All replay cases passed required-term checks.", "next_action": "prepare bounded replay promotion handoff"}
    return {
        "model_quality_claim": "bounded_replay_repair_needed",
        "reason": "Replay ran but missed required terms in one or more cases.",
        "next_action": "build_bounded_real_replay_repair_plan",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REVIEW_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_review",
    "locate_route_promotion_bounded_real_replay",
    "read_json_report",
    "resolve_exit_code",
]
