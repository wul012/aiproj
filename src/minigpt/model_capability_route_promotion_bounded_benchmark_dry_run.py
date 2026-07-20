from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_review import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_JSON_FILENAME = "model_capability_route_promotion_bounded_benchmark_dry_run.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_CSV_FILENAME = "model_capability_route_promotion_bounded_benchmark_dry_run.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_TEXT_FILENAME = "model_capability_route_promotion_bounded_benchmark_dry_run.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_benchmark_dry_run.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_HTML_FILENAME = "model_capability_route_promotion_bounded_benchmark_dry_run.html"


def locate_route_promotion_bounded_benchmark_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME
    return source


def locate_route_promotion_bounded_benchmark_suite_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion bounded benchmark dry-run input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_benchmark_dry_run(
    suite_review: dict[str, Any],
    benchmark_suite_report: dict[str, Any],
    *,
    suite_review_path: str | Path | None = None,
    benchmark_suite_path: str | Path | None = None,
    positive_continuation: str = "fixed loss",
    negative_continuation: str = "fixed only",
    title: str = "MiniGPT model capability route promotion bounded benchmark dry run",
    generated_at: str | None = None,
) -> dict[str, Any]:
    suite = as_dict(benchmark_suite_report.get("benchmark_suite"))
    review_summary = as_dict(suite_review.get("summary"))
    scoring_contract = as_dict(suite.get("scoring_contract"))
    dry_rows = [_score_case(row, positive_continuation) for row in list_of_dicts(suite.get("cases"))]
    negative_control = _score_terms(["fixed", "loss"], negative_continuation)
    checks = _checks(suite_review, benchmark_suite_report, review_summary, scoring_contract, dry_rows, negative_control)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_suite_review": str(suite_review_path or ""),
        "source_benchmark_suite": str(benchmark_suite_path or ""),
        "positive_continuation": positive_continuation,
        "negative_continuation": negative_continuation,
        "dry_run_rows": dry_rows,
        "negative_control": negative_control,
        "check_rows": checks,
        "summary": _summary(status, checks, dry_rows, negative_control, scoring_contract),
        "interpretation": _interpretation(status),
    }


def _score_case(row: dict[str, Any], continuation: str) -> dict[str, Any]:
    expected_terms = [str(term) for term in row.get("expected_terms", [])]
    scores = _score_terms(expected_terms, continuation)
    return {
        "case_id": row.get("case_id"),
        "continuation": continuation,
        "expected_terms": expected_terms,
        "hit_terms": scores["hit_terms"],
        "missed_terms": scores["missed_terms"],
        "case_pass": scores["case_pass"],
    }


def _score_terms(expected_terms: list[str], continuation: str) -> dict[str, Any]:
    lowered = continuation.lower()
    hits = [term for term in expected_terms if term.lower() in lowered]
    missed = [term for term in expected_terms if term not in hits]
    return {"hit_terms": hits, "missed_terms": missed, "case_pass": bool(expected_terms) and not missed}


def _checks(
    suite_review: dict[str, Any],
    benchmark_suite_report: dict[str, Any],
    review_summary: dict[str, Any],
    scoring_contract: dict[str, Any],
    dry_rows: list[dict[str, Any]],
    negative_control: dict[str, Any],
) -> list[dict[str, Any]]:
    passed_rows = [row for row in dry_rows if row.get("case_pass") is True]
    return [
        _check("suite_review_passed", suite_review.get("status") == "pass", suite_review.get("status"), "suite review must pass"),
        _check("suite_review_approved", review_summary.get("approved_for_execution") is True, review_summary.get("approved_for_execution"), "suite review must approve execution"),
        _check("benchmark_suite_passed", benchmark_suite_report.get("status") == "pass", benchmark_suite_report.get("status"), "benchmark suite must pass"),
        _check("expected_terms_fixed_loss", scoring_contract.get("expected_terms") == ["fixed", "loss"], scoring_contract.get("expected_terms"), "scoring contract expected terms must be fixed/loss"),
        _check("dry_rows_present", bool(dry_rows), len(dry_rows), "dry run must score suite cases"),
        _check("positive_rows_pass", len(passed_rows) == len(dry_rows), len(passed_rows), "positive continuation should pass every case"),
        _check("negative_control_fails", negative_control.get("case_pass") is False, negative_control.get("case_pass"), "negative control must fail missing required term"),
    ]


def _summary(
    status: str,
    checks: list[dict[str, Any]],
    dry_rows: list[dict[str, Any]],
    negative_control: dict[str, Any],
    scoring_contract: dict[str, Any],
) -> dict[str, Any]:
    passed_rows = [row for row in dry_rows if row.get("case_pass") is True]
    return {
        "bounded_benchmark_dry_run_ready": status == "pass",
        "case_count": len(dry_rows),
        "passed_case_count": len(passed_rows),
        "failed_case_count": len(dry_rows) - len(passed_rows),
        "expected_terms": scoring_contract.get("expected_terms"),
        "negative_control_passed": negative_control.get("case_pass"),
        "next_step": "run_bounded_route_promotion_real_replay" if status == "pass" else "repair_bounded_benchmark_scoring",
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_benchmark_dry_run_passed"
    return "fix_model_capability_route_promotion_bounded_benchmark_dry_run"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "The dry-run scorer did not validate the scoring contract.", "next_action": "repair scoring contract or suite"}
    return {
        "model_quality_claim": "scorer_validated_only",
        "reason": "The scoring contract correctly passes positive fixed/loss continuations and fails a missing-term negative control.",
        "next_action": "run_bounded_route_promotion_real_replay",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_benchmark_dry_run",
    "locate_route_promotion_bounded_benchmark_suite",
    "locate_route_promotion_bounded_benchmark_suite_review",
    "read_json_report",
    "resolve_exit_code",
]
