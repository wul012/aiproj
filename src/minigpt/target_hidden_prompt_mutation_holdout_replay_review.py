from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review import (
    TASK_HINT_TERMS,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.target_hidden_prompt_mutation_holdout_real_replay import (
    TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.target_hidden_prompt_mutation_holdout_suite import TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.report_check_common import check_entry as _check


TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME = "target_hidden_prompt_mutation_holdout_replay_review.json"
TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_CSV_FILENAME = "target_hidden_prompt_mutation_holdout_replay_review.csv"
TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_TEXT_FILENAME = "target_hidden_prompt_mutation_holdout_replay_review.txt"
TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_MARKDOWN_FILENAME = "target_hidden_prompt_mutation_holdout_replay_review.md"
TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_HTML_FILENAME = "target_hidden_prompt_mutation_holdout_replay_review.html"


def locate_target_hidden_prompt_mutation_holdout_real_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REAL_REPLAY_JSON_FILENAME
    return source


def locate_target_hidden_prompt_mutation_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("target-hidden prompt-mutation holdout replay review input must be a JSON object")
    return dict(payload)


def build_target_hidden_prompt_mutation_holdout_replay_review(
    real_replay_report: dict[str, Any],
    holdout_suite_report: dict[str, Any],
    *,
    real_replay_path: str | Path | None = None,
    holdout_suite_path: str | Path | None = None,
    title: str = "MiniGPT target-hidden prompt-mutation holdout replay review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    suite = as_dict(holdout_suite_report.get("benchmark_suite"))
    cases = list_of_dicts(suite.get("cases"))
    expected_terms = [str(term) for term in as_dict(suite.get("scoring_contract")).get("expected_terms", [])]
    coverage_by_case = {str(row.get("case_id")): row for row in list_of_dicts(holdout_suite_report.get("coverage_rows"))}
    review_rows = _review_rows(cases, expected_terms, coverage_by_case)
    checks = _checks(real_replay_report, holdout_suite_report, cases, review_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, real_replay_report, holdout_suite_report, review_rows, issues)
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
        "source_holdout_suite_summary": as_dict(holdout_suite_report.get("summary")),
        "check_rows": checks,
        "review_rows": review_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_randomized_holdout_approval: bool = False,
    require_promotion_approval: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and report.get("status") != "pass":
        return 1
    if require_randomized_holdout_approval and summary.get("approved_for_randomized_prompt_holdout") is not True:
        return 1
    if require_promotion_approval and summary.get("approved_for_promotion") is not True:
        return 1
    return 0


def _review_rows(
    cases: list[dict[str, Any]],
    expected_terms: list[str],
    coverage_by_case: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        prompt = str(as_dict(case.get("prompt_case")).get("prompt") or "")
        lowered = prompt.lower()
        case_id = str(case.get("case_id"))
        coverage = as_dict(coverage_by_case.get(case_id))
        leaked_terms = [term for term in expected_terms if term.lower() in lowered]
        hint_terms = [term for term in TASK_HINT_TERMS if term in lowered]
        prompt_mutated = coverage.get("prompt_mutated") is True
        rows.append(
            {
                "case_id": case.get("case_id"),
                "source_case_id": case.get("source_case_id"),
                "expected_terms": expected_terms,
                "leaked_terms": leaked_terms,
                "target_leakage": bool(leaked_terms),
                "task_hint_terms": hint_terms,
                "task_hint": bool(hint_terms),
                "prompt_mutated": prompt_mutated,
                "review_status": _row_status(leaked_terms, hint_terms, prompt_mutated),
                "detail": _row_detail(leaked_terms, hint_terms, prompt_mutated),
            }
        )
    return rows


def _row_status(leaked_terms: list[str], hint_terms: list[str], prompt_mutated: bool) -> str:
    if leaked_terms:
        return "block_target_leakage"
    if hint_terms:
        return "block_known_task_hint"
    if not prompt_mutated:
        return "block_unmutated_prompt"
    return "clean_prompt_mutation_target_hidden_prompt"


def _row_detail(leaked_terms: list[str], hint_terms: list[str], prompt_mutated: bool) -> str:
    if leaked_terms:
        return "prompt contains expected terms"
    if hint_terms:
        return "prompt hides expected terms but still uses known pair/target task hints"
    if not prompt_mutated:
        return "prompt does not differ from the source semantic suite"
    return "prompt hides expected terms, avoids known task hints, and differs from source prompts"


def _checks(
    real_replay_report: dict[str, Any],
    suite_report: dict[str, Any],
    cases: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    replay_summary = as_dict(real_replay_report.get("summary"))
    suite_summary = as_dict(suite_report.get("summary"))
    return [
        _check("real_replay_passed", real_replay_report.get("status") == "pass", real_replay_report.get("status"), "prompt-mutation real replay must pass structurally"),
        _check("real_replay_ready", replay_summary.get("target_hidden_prompt_mutation_holdout_real_replay_ready") is True, replay_summary.get("target_hidden_prompt_mutation_holdout_real_replay_ready"), "prompt-mutation real replay summary must be ready"),
        _check("prompt_mutation_model_ready", replay_summary.get("prompt_mutation_holdout_model_quality_ready") is True, replay_summary.get("prompt_mutation_holdout_model_quality_ready"), "prompt-mutation holdout model signal must be ready"),
        _check("suite_passed", suite_report.get("status") == "pass", suite_report.get("status"), "prompt-mutation holdout suite must pass"),
        _check("suite_ready", suite_summary.get("target_hidden_prompt_mutation_holdout_suite_ready") is True, suite_summary.get("target_hidden_prompt_mutation_holdout_suite_ready"), "prompt-mutation holdout suite summary must be ready"),
        _check("mutation_factor_at_least_two", float(suite_summary.get("mutation_factor") or 0.0) >= 2.0, suite_summary.get("mutation_factor"), "prompt-mutation suite should expand source cases"),
        _check("suite_no_task_hints", suite_summary.get("task_hint_case_count") == 0, suite_summary.get("task_hint_case_count"), "prompt-mutation suite should report no known task hints"),
        _check("prompt_mutated_rows_complete", suite_summary.get("prompt_mutated_case_count") == len(cases), suite_summary.get("prompt_mutated_case_count"), "every suite case should be prompt-mutated"),
        _check("target_hidden_cases_present", suite_summary.get("target_hidden_case_count") == len(cases), suite_summary.get("target_hidden_case_count"), "every suite case must remain target-hidden"),
        _check("cases_present", bool(cases), len(cases), "suite cases must be present"),
        _check("review_rows_complete", len(review_rows) == len(cases), len(review_rows), "review must cover every case"),
    ]


def _summary(
    status: str,
    real_replay_report: dict[str, Any],
    suite_report: dict[str, Any],
    rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    replay_summary = as_dict(real_replay_report.get("summary"))
    suite_summary = as_dict(suite_report.get("summary"))
    leakage_count = sum(1 for row in rows if row.get("target_leakage") is True)
    hint_count = sum(1 for row in rows if row.get("task_hint") is True)
    mutated_count = sum(1 for row in rows if row.get("prompt_mutated") is True)
    clean_count = sum(1 for row in rows if row.get("review_status") == "clean_prompt_mutation_target_hidden_prompt")
    source_ready = replay_summary.get("holdout_model_quality_ready") is True
    mutation_ready = replay_summary.get("prompt_mutation_holdout_model_quality_ready") is True
    clean_signal = status == "pass" and source_ready and mutation_ready and leakage_count == 0 and hint_count == 0 and mutated_count == len(rows) and len(rows) >= 10
    return {
        "target_hidden_prompt_mutation_holdout_replay_review_ready": status == "pass",
        "source_holdout_model_quality_ready": source_ready,
        "source_prompt_mutation_holdout_model_quality_ready": mutation_ready,
        "case_count": len(rows),
        "passed_case_count": replay_summary.get("passed_case_count"),
        "pass_rate": replay_summary.get("pass_rate"),
        "source_mutation_factor": suite_summary.get("mutation_factor"),
        "target_leakage_case_count": leakage_count,
        "target_hidden_case_count": len(rows) - leakage_count,
        "task_hint_case_count": hint_count,
        "prompt_mutated_case_count": mutated_count,
        "clean_prompt_mutation_case_count": clean_count,
        "approved_for_randomized_prompt_holdout": clean_signal,
        "approved_for_promotion": False,
        "promotion_ready": False,
        "model_quality_claim": _model_quality_claim(clean_signal, leakage_count, hint_count, mutated_count, len(rows)),
        "next_step": _next_step(clean_signal, leakage_count, hint_count, mutated_count, len(rows)),
        "failed_check_count": len(issues),
    }


def _model_quality_claim(clean_signal: bool, leakage_count: int, hint_count: int, mutated_count: int, case_count: int) -> str:
    if leakage_count:
        return "prompt_mutation_replay_review_blocked_by_target_leakage"
    if hint_count:
        return "prompt_mutation_replay_review_blocked_by_known_task_hint"
    if mutated_count != case_count:
        return "prompt_mutation_replay_review_blocked_by_unmutated_prompt"
    if clean_signal:
        return "prompt_mutation_target_hidden_holdout_clean_signal_reviewed"
    return "prompt_mutation_target_hidden_holdout_replay_review_only"


def _next_step(clean_signal: bool, leakage_count: int, hint_count: int, mutated_count: int, case_count: int) -> str:
    if leakage_count:
        return "repair_prompt_mutation_holdout_prompt_target_leakage"
    if hint_count:
        return "repair_prompt_mutation_holdout_prompt_task_hints"
    if mutated_count != case_count:
        return "repair_prompt_mutation_holdout_unmutated_prompts"
    if clean_signal:
        return "build_randomized_target_hidden_holdout_suite"
    return "diagnose_prompt_mutation_target_hidden_holdout_replay_gap"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_target_hidden_prompt_mutation_holdout_replay_review_inputs"
    if int(summary.get("target_leakage_case_count") or 0) > 0:
        return "target_hidden_prompt_mutation_holdout_replay_review_target_leakage_blocks_promotion"
    if int(summary.get("task_hint_case_count") or 0) > 0:
        return "target_hidden_prompt_mutation_holdout_replay_review_task_hint_blocks_promotion"
    if int(summary.get("prompt_mutated_case_count") or 0) != int(summary.get("case_count") or 0):
        return "target_hidden_prompt_mutation_holdout_replay_review_unmutated_prompt_blocks_promotion"
    if summary.get("approved_for_randomized_prompt_holdout") is True:
        return "target_hidden_prompt_mutation_holdout_replay_review_clean_signal_randomized_holdout_required"
    return "target_hidden_prompt_mutation_holdout_replay_review_blocks_promotion"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Prompt-mutation replay review inputs failed.", "next_action": "repair_prompt_mutation_replay_review_inputs"}
    if summary.get("approved_for_randomized_prompt_holdout") is True:
        return {
            "model_quality_claim": summary.get("model_quality_claim"),
            "reason": "The prompt-mutation target-hidden replay passed clean mutated prompts; build a randomized holdout before promotion.",
            "next_action": summary.get("next_step"),
        }
    return {"model_quality_claim": summary.get("model_quality_claim"), "reason": "The prompt-mutation target-hidden replay review does not support promotion.", "next_action": summary.get("next_step")}


__all__ = [
    "TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_CSV_FILENAME",
    "TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_HTML_FILENAME",
    "TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME",
    "TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_MARKDOWN_FILENAME",
    "TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_TEXT_FILENAME",
    "build_target_hidden_prompt_mutation_holdout_replay_review",
    "locate_target_hidden_prompt_mutation_holdout_real_replay",
    "locate_target_hidden_prompt_mutation_holdout_suite",
    "read_json_report",
    "resolve_exit_code",
]
