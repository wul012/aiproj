from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.json"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.csv"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.txt"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.md"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.html"
)


def locate_tokenizer_coverage_aware_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("tokenizer-coverage-aware holdout dry-run input must be a JSON object")
    return dict(payload)


def build_tokenizer_coverage_aware_holdout_dry_run(
    holdout_suite_report: dict[str, Any],
    *,
    positive_continuation: str = " fixed loss",
    negative_continuation: str = " fixed only",
    holdout_suite_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory tokenizer-coverage-aware holdout dry-run",
    generated_at: str | None = None,
) -> dict[str, Any]:
    suite = as_dict(holdout_suite_report.get("benchmark_suite"))
    cases = list_of_dicts(suite.get("cases"))
    contract = as_dict(suite.get("scoring_contract"))
    expected_terms = [str(term) for term in contract.get("expected_terms", [])]
    dry_run_rows = _dry_run_rows(cases, expected_terms, positive_continuation, negative_continuation)
    checks = _checks(holdout_suite_report, suite, cases, expected_terms, dry_run_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, cases, dry_run_rows, issues)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_holdout_suite": str(holdout_suite_path or ""),
        "source_holdout_suite_summary": as_dict(holdout_suite_report.get("summary")),
        "positive_continuation": positive_continuation,
        "negative_continuation": negative_continuation,
        "check_rows": checks,
        "dry_run_rows": dry_run_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_dry_run_ready: bool) -> int:
    return 1 if require_dry_run_ready and report.get("status") != "pass" else 0


def _dry_run_rows(
    cases: list[dict[str, Any]],
    expected_terms: list[str],
    positive_continuation: str,
    negative_continuation: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        positive = _score(expected_terms, positive_continuation)
        negative = _score(expected_terms, negative_continuation)
        rows.append(
            {
                "case_id": case.get("case_id"),
                "source_case_id": case.get("source_case_id"),
                "expected_terms": expected_terms,
                "positive_continuation": positive_continuation,
                "positive_case_pass": positive["case_pass"],
                "positive_hit_terms": positive["hit_terms"],
                "positive_missed_terms": positive["missed_terms"],
                "negative_continuation": negative_continuation,
                "negative_case_pass": negative["case_pass"],
                "negative_hit_terms": negative["hit_terms"],
                "negative_missed_terms": negative["missed_terms"],
            }
        )
    return rows


def _score(expected_terms: list[str], continuation: str) -> dict[str, Any]:
    lowered = continuation.lower()
    hit_terms = [term for term in expected_terms if term.lower() in lowered]
    missed_terms = [term for term in expected_terms if term not in hit_terms]
    return {"hit_terms": hit_terms, "missed_terms": missed_terms, "case_pass": bool(expected_terms) and not missed_terms}


def _checks(
    holdout_suite_report: dict[str, Any],
    suite: dict[str, Any],
    cases: list[dict[str, Any]],
    expected_terms: list[str],
    dry_run_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_summary = as_dict(holdout_suite_report.get("summary"))
    return [
        _check("holdout_suite_passed", holdout_suite_report.get("status") == "pass", holdout_suite_report.get("status"), "tokenizer-coverage-aware holdout suite must pass"),
        _check(
            "holdout_suite_ready",
            source_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready") is True,
            source_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready"),
            "holdout suite summary must be ready",
        ),
        _check("suite_ready", suite.get("ready") is True, suite.get("ready"), "benchmark suite must be ready"),
        _check("cases_present", bool(cases), len(cases), "holdout suite must include cases"),
        _check("expected_terms_complete", expected_terms == ["fixed", "loss"], expected_terms, "dry-run expects fixed/loss scoring contract"),
        _check("positive_rows_pass", all(row.get("positive_case_pass") is True for row in dry_run_rows), sum(1 for row in dry_run_rows if row.get("positive_case_pass") is True), "positive continuation must pass every case"),
        _check("negative_rows_fail", all(row.get("negative_case_pass") is not True for row in dry_run_rows), sum(1 for row in dry_run_rows if row.get("negative_case_pass") is True), "negative continuation must not pass any case"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, cases: list[dict[str, Any]], rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    positive_passed = sum(1 for row in rows if row.get("positive_case_pass") is True)
    negative_passed = sum(1 for row in rows if row.get("negative_case_pass") is True)
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_ready": status == "pass",
        "case_count": len(cases),
        "positive_passed_case_count": positive_passed,
        "negative_passed_case_count": negative_passed,
        "negative_control_passed": negative_passed > 0,
        "promotion_ready": False,
        "model_quality_claim": "dry_run_only",
        "next_step": "run_tokenizer_coverage_aware_holdout_real_replay",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_passed"
    return "fix_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Tokenizer-coverage-aware dry-run checks failed.", "next_action": "repair_holdout_dry_run_inputs"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The tokenizer-covered holdout suite scoring contract passes dry-run checks; real replay is now the next evidence step.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_TEXT_FILENAME",
    "build_tokenizer_coverage_aware_holdout_dry_run",
    "locate_tokenizer_coverage_aware_holdout_suite",
    "read_json_report",
    "resolve_exit_code",
]
