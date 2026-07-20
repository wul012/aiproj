from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_target_hidden_holdout_suite import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_dry_run_ready as resolve_exit_code


RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME = "randomized_target_hidden_holdout_dry_run.json"
RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_CSV_FILENAME = "randomized_target_hidden_holdout_dry_run.csv"
RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_TEXT_FILENAME = "randomized_target_hidden_holdout_dry_run.txt"
RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_MARKDOWN_FILENAME = "randomized_target_hidden_holdout_dry_run.md"
RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_HTML_FILENAME = "randomized_target_hidden_holdout_dry_run.html"


def locate_randomized_target_hidden_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized target-hidden holdout dry-run input must be a JSON object")
    return dict(payload)


def build_randomized_target_hidden_holdout_dry_run(
    holdout_suite_report: dict[str, Any],
    *,
    positive_continuation: str = " fixed loss",
    negative_continuation: str = " fixed only",
    holdout_suite_path: str | Path | None = None,
    title: str = "MiniGPT randomized target-hidden holdout dry-run",
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
    summary = _summary(status, holdout_suite_report, cases, dry_run_rows, issues)
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
                "random_draw_index": case.get("random_draw_index"),
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
    suite_report: dict[str, Any],
    suite: dict[str, Any],
    cases: list[dict[str, Any]],
    expected_terms: list[str],
    dry_run_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_summary = as_dict(suite_report.get("summary"))
    return [
        _check("holdout_suite_passed", suite_report.get("status") == "pass", suite_report.get("status"), "randomized holdout suite must pass"),
        _check("holdout_suite_ready", source_summary.get("randomized_target_hidden_holdout_suite_ready") is True, source_summary.get("randomized_target_hidden_holdout_suite_ready"), "randomized holdout suite summary must be ready"),
        _check("suite_ready", suite.get("ready") is True, suite.get("ready"), "benchmark suite must be ready"),
        _check("cases_present", bool(cases), len(cases), "randomized holdout suite must include cases"),
        _check("case_count_matches_summary", source_summary.get("candidate_case_count") == len(cases), source_summary.get("candidate_case_count"), "candidate case count must match suite cases"),
        _check("randomized_case_factor_at_least_two", float(source_summary.get("randomized_case_factor") or 0.0) >= 2.0, source_summary.get("randomized_case_factor"), "randomized suite should double the source case count"),
        _check("all_cases_tokenizer_covered", source_summary.get("tokenizer_covered_case_count") == len(cases), source_summary.get("tokenizer_covered_case_count"), "all randomized cases must be tokenizer-covered"),
        _check("all_cases_target_hidden", source_summary.get("target_hidden_case_count") == len(cases), source_summary.get("target_hidden_case_count"), "all randomized cases must hide expected terms"),
        _check("no_task_hints", source_summary.get("task_hint_case_count") == 0, source_summary.get("task_hint_case_count"), "randomized suite should have no known task hints"),
        _check("all_prompts_unique", source_summary.get("unique_prompt_count") == len(cases), source_summary.get("unique_prompt_count"), "randomized suite prompts must be unique"),
        _check("expected_terms_complete", expected_terms == ["fixed", "loss"], expected_terms, "dry-run expects fixed/loss scoring contract"),
        _check("positive_rows_pass", all(row.get("positive_case_pass") is True for row in dry_run_rows), sum(1 for row in dry_run_rows if row.get("positive_case_pass") is True), "positive continuation must pass every case"),
        _check("negative_rows_fail", all(row.get("negative_case_pass") is not True for row in dry_run_rows), sum(1 for row in dry_run_rows if row.get("negative_case_pass") is True), "negative continuation must not pass any case"),
    ]


def _summary(
    status: str,
    suite_report: dict[str, Any],
    cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    source_summary = as_dict(suite_report.get("summary"))
    positive_passed = sum(1 for row in rows if row.get("positive_case_pass") is True)
    negative_passed = sum(1 for row in rows if row.get("negative_case_pass") is True)
    return {
        "randomized_target_hidden_holdout_dry_run_ready": status == "pass",
        "case_count": len(cases),
        "source_random_seed": source_summary.get("random_seed"),
        "source_randomized_case_factor": source_summary.get("randomized_case_factor"),
        "source_unique_prompt_count": source_summary.get("unique_prompt_count"),
        "positive_passed_case_count": positive_passed,
        "negative_passed_case_count": negative_passed,
        "negative_control_passed": negative_passed > 0,
        "promotion_ready": False,
        "model_quality_claim": "dry_run_only",
        "next_step": "run_randomized_target_hidden_holdout_real_replay",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    return "randomized_target_hidden_holdout_dry_run_passed" if status == "pass" else "fix_randomized_target_hidden_holdout_dry_run"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Randomized target-hidden dry-run checks failed.", "next_action": "repair_randomized_target_hidden_holdout_dry_run"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The randomized target-hidden holdout scoring contract passes dry-run checks; real replay is next.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_CSV_FILENAME",
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_HTML_FILENAME",
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME",
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_MARKDOWN_FILENAME",
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_TEXT_FILENAME",
    "build_randomized_target_hidden_holdout_dry_run",
    "locate_randomized_target_hidden_holdout_suite",
    "read_json_report",
    "resolve_exit_code",
]
