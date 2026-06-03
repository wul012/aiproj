from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite_review.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_CSV_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite_review.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_TEXT_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite_review.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite_review.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_HTML_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite_review.html"


def locate_route_promotion_bounded_benchmark_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion bounded benchmark suite review input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_benchmark_suite_review(
    benchmark_suite_report: dict[str, Any],
    *,
    benchmark_suite_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded benchmark suite review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    suite = as_dict(benchmark_suite_report.get("benchmark_suite"))
    summary = as_dict(benchmark_suite_report.get("summary"))
    case_reviews = [_case_review(row) for row in list_of_dicts(suite.get("cases"))]
    checks = _checks(benchmark_suite_report, suite, summary, case_reviews)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, suite, case_reviews)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_benchmark_suite": str(benchmark_suite_path or ""),
        "source_suite_summary": summary,
        "case_reviews": case_reviews,
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(report: dict[str, Any], *, require_ready_review: bool) -> int:
    return 1 if require_ready_review and report.get("status") != "pass" else 0


def _case_review(row: dict[str, Any]) -> dict[str, Any]:
    prompt_case = as_dict(row.get("prompt_case"))
    expected_terms = [str(term) for term in row.get("expected_terms", [])]
    prompt = str(prompt_case.get("prompt") or "")
    forbidden_surfaces = ["fixed=|loss=", "loss=|fixed=", "fixed -> loss", "loss -> fixed"]
    forbidden_hits = [surface for surface in forbidden_surfaces if surface in prompt]
    return {
        "case_id": row.get("case_id"),
        "prompt_present": bool(prompt),
        "expected_terms": expected_terms,
        "expected_term_count": len(expected_terms),
        "has_fixed_loss": set(expected_terms) == {"fixed", "loss"},
        "forbidden_surface_hits": forbidden_hits,
        "review_status": "pass" if prompt and set(expected_terms) == {"fixed", "loss"} and not forbidden_hits else "fail",
    }


def _checks(
    benchmark_suite_report: dict[str, Any],
    suite: dict[str, Any],
    summary: dict[str, Any],
    case_reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    failed_cases = [row for row in case_reviews if row.get("review_status") != "pass"]
    prompts = [as_dict(row.get("prompt_case")).get("prompt") for row in list_of_dicts(suite.get("cases"))]
    return [
        _check("suite_passed", benchmark_suite_report.get("status") == "pass", benchmark_suite_report.get("status"), "source suite must pass"),
        _check(
            "suite_decision_ready",
            benchmark_suite_report.get("decision") == "model_capability_route_promotion_bounded_benchmark_suite_ready",
            benchmark_suite_report.get("decision"),
            "source suite decision must be ready",
        ),
        _check("suite_ready", summary.get("bounded_benchmark_suite_ready") is True and suite.get("ready") is True, {"summary": summary.get("bounded_benchmark_suite_ready"), "suite": suite.get("ready")}, "suite must be ready"),
        _check("case_count", int(summary.get("case_count") or 0) >= 5, summary.get("case_count"), "suite must include at least five cases"),
        _check("expected_terms", summary.get("expected_terms") == ["fixed", "loss"], summary.get("expected_terms"), "suite expected terms must be fixed/loss"),
        _check("case_reviews_clean", not failed_cases, len(failed_cases), "all case reviews must pass"),
        _check("prompt_uniqueness", len(prompts) == len(set(prompts)), len(prompts) - len(set(prompts)), "suite prompts must be unique"),
        _check("next_artifact_review", suite.get("proposed_next_artifact") == "model_capability_route_promotion_bounded_benchmark_suite_review", suite.get("proposed_next_artifact"), "suite must point at this review artifact"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _review(status: str, suite: dict[str, Any], case_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "approved_for_execution": status == "pass",
        "suite_name": suite.get("suite_name"),
        "route_id": suite.get("route_id"),
        "case_count": len(case_reviews),
        "passed_case_review_count": sum(1 for row in case_reviews if row.get("review_status") == "pass"),
        "next_step": "run_bounded_route_promotion_benchmark_dry_run" if status == "pass" else "repair_bounded_benchmark_suite",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_benchmark_suite_review_ready": status == "pass" and review.get("ready") is True,
        "approved_for_execution": review.get("approved_for_execution"),
        "suite_name": review.get("suite_name"),
        "route_id": review.get("route_id"),
        "case_count": review.get("case_count"),
        "passed_case_review_count": review.get("passed_case_review_count"),
        "next_step": review.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_benchmark_suite_review_ready"
    return "fix_model_capability_route_promotion_bounded_benchmark_suite_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "The bounded benchmark suite is not approved for execution.", "next_action": "repair suite cases or scoring contract"}
    return {
        "model_quality_claim": "suite_review_only",
        "reason": "The bounded suite cases, expected terms, and guardrails are ready for dry-run execution.",
        "next_action": review.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_benchmark_suite_review",
    "locate_route_promotion_bounded_benchmark_suite",
    "read_json_report",
    "resolve_exit_code",
]
