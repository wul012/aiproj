from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review.json"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review.csv"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review.txt"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review.md"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review.html"
)


def locate_holdout_real_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REAL_REPLAY_JSON_FILENAME
    return source


def locate_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("tokenizer-covered holdout replay review input must be a JSON object")
    return dict(payload)


def build_tokenizer_coverage_aware_holdout_replay_review(
    real_replay_report: dict[str, Any],
    holdout_suite_report: dict[str, Any],
    *,
    real_replay_path: str | Path | None = None,
    holdout_suite_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory tokenizer-coverage-aware holdout replay review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    suite = as_dict(holdout_suite_report.get("benchmark_suite"))
    cases = list_of_dicts(suite.get("cases"))
    expected_terms = [str(term) for term in as_dict(suite.get("scoring_contract")).get("expected_terms", [])]
    review_rows = _review_rows(cases, expected_terms)
    checks = _checks(real_replay_report, holdout_suite_report, cases, review_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, real_replay_report, review_rows, issues)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_real_replay": str(real_replay_path or ""),
        "source_holdout_suite": str(holdout_suite_path or ""),
        "source_real_replay_summary": as_dict(real_replay_report.get("summary")),
        "check_rows": checks,
        "review_rows": review_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_review_ready: bool, require_approval: bool = False) -> int:
    if require_review_ready and report.get("status") != "pass":
        return 1
    if require_approval and as_dict(report.get("summary")).get("approved_for_promotion") is not True:
        return 1
    return 0


def _review_rows(cases: list[dict[str, Any]], expected_terms: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        prompt = str(as_dict(case.get("prompt_case")).get("prompt") or "")
        leaked_terms = [term for term in expected_terms if term.lower() in prompt.lower()]
        rows.append(
            {
                "case_id": case.get("case_id"),
                "source_case_id": case.get("source_case_id"),
                "expected_terms": expected_terms,
                "leaked_terms": leaked_terms,
                "target_leakage": bool(leaked_terms),
                "review_status": "block_promotion" if leaked_terms else "pass",
                "detail": "prompt contains expected terms" if leaked_terms else "prompt hides expected terms",
            }
        )
    return rows


def _checks(
    real_replay_report: dict[str, Any],
    suite_report: dict[str, Any],
    cases: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    replay_summary = as_dict(real_replay_report.get("summary"))
    suite_summary = as_dict(suite_report.get("summary"))
    return [
        _check("real_replay_passed", real_replay_report.get("status") == "pass", real_replay_report.get("status"), "real replay must pass structurally"),
        _check("real_replay_ready", replay_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay_ready") is True, replay_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay_ready"), "real replay summary must be ready"),
        _check("suite_passed", suite_report.get("status") == "pass", suite_report.get("status"), "holdout suite must pass"),
        _check("suite_ready", suite_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready") is True, suite_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready"), "holdout suite summary must be ready"),
        _check("cases_present", bool(cases), len(cases), "suite cases must be present"),
        _check("review_rows_complete", len(review_rows) == len(cases), len(review_rows), "review must cover every case"),
    ]


def _summary(status: str, real_replay_report: dict[str, Any], rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    replay_summary = as_dict(real_replay_report.get("summary"))
    leakage_count = sum(1 for row in rows if row.get("target_leakage") is True)
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_ready": status == "pass",
        "source_holdout_model_quality_ready": replay_summary.get("holdout_model_quality_ready") is True,
        "case_count": len(rows),
        "target_leakage_case_count": leakage_count,
        "target_hidden_case_count": len(rows) - leakage_count,
        "approved_for_promotion": status == "pass" and replay_summary.get("holdout_model_quality_ready") is True and leakage_count == 0,
        "promotion_ready": False,
        "model_quality_claim": "target_leaked_holdout_pass_review_only" if leakage_count else "target_hidden_holdout_pass_reviewed",
        "next_step": "build_target_hidden_tokenizer_covered_holdout_suite" if leakage_count else "prepare_route_promotion_candidate_review",
        "failed_check_count": len(issues),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_inputs"
    if summary.get("approved_for_promotion") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_approved"
    if int(summary.get("target_leakage_case_count") or 0) > 0:
        return "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_target_leakage_blocks_promotion"
    return "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_blocks_promotion"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Replay review inputs failed.", "next_action": "repair_replay_review_inputs"}
    if summary.get("approved_for_promotion") is True:
        return {"model_quality_claim": summary.get("model_quality_claim"), "reason": "The replay passed and no prompt leaked target terms.", "next_action": summary.get("next_step")}
    return {"model_quality_claim": summary.get("model_quality_claim"), "reason": "The replay passed, but the holdout prompts leak expected terms and cannot approve promotion.", "next_action": summary.get("next_step")}


__all__ = [
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_TEXT_FILENAME",
    "build_tokenizer_coverage_aware_holdout_replay_review",
    "locate_holdout_real_replay",
    "locate_holdout_suite",
    "read_json_report",
    "resolve_exit_code",
]
