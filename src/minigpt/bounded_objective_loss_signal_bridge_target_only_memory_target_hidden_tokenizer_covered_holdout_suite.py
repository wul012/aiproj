from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.eval_suite import PromptCase
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.tokenizer import load_tokenizer
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_suite_ready as resolve_exit_code


TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.json"
)
TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.csv"
)
TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.txt"
)
TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.md"
)
TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.html"
)


def locate_replay_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
    return source


def locate_source_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("target-hidden tokenizer-covered holdout suite input must be a JSON object")
    return dict(payload)


def build_target_hidden_tokenizer_covered_holdout_suite(
    replay_review_report: dict[str, Any],
    source_holdout_suite_report: dict[str, Any],
    *,
    tokenizer_path: str | Path,
    replay_review_path: str | Path | None = None,
    source_holdout_suite_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory target-hidden tokenizer-covered holdout suite",
    generated_at: str | None = None,
) -> dict[str, Any]:
    tokenizer_file = Path(tokenizer_path)
    tokenizer_exists = tokenizer_file.is_file()
    tokenizer = load_tokenizer(tokenizer_file) if tokenizer_exists else None
    source_suite = as_dict(source_holdout_suite_report.get("benchmark_suite"))
    source_cases = list_of_dicts(source_suite.get("cases"))
    expected_terms = [str(term) for term in as_dict(source_suite.get("scoring_contract")).get("expected_terms", [])] or ["fixed", "loss"]
    cases = _candidate_cases(source_cases, expected_terms)
    coverage_rows = _coverage_rows(cases, expected_terms, tokenizer) if tokenizer is not None else []
    checks = _checks(replay_review_report, source_holdout_suite_report, tokenizer_file, source_cases, cases, coverage_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, replay_review_report, source_cases, cases, coverage_rows, issues)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_review": str(replay_review_path or ""),
        "source_holdout_suite": str(source_holdout_suite_path or ""),
        "tokenizer_path": str(tokenizer_file),
        "check_rows": checks,
        "coverage_rows": coverage_rows,
        "benchmark_suite": _suite(status, source_suite, cases, expected_terms),
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def target_hidden_candidate_prompt_seed_text() -> str:
    return "\n".join(prompt for _, prompt, _ in _candidate_prompt_specs())


def _candidate_prompt_specs() -> list[tuple[str, str, str]]:
    return [
        ("answer_learned_pair", "answer with the learned pair\nanswer:", "target-hidden learned pair answer"),
        ("return_target_pair", "return the target pair\noutput:", "target-hidden target pair answer"),
        ("contrast_route_pair", "contrast route pair\nresult:", "target-hidden contrast route answer"),
        ("jsonish_answer_terms", "jsonish answer_terms target pair\nanswer_terms:", "target-hidden structured answer"),
        ("self_check_pair", "self check requires target pair\nfinal answer:", "target-hidden self-check answer"),
    ]


def _candidate_cases(source_cases: list[dict[str, Any]], expected_terms: list[str]) -> list[dict[str, Any]]:
    prompts = _candidate_prompt_specs()
    rows: list[dict[str, Any]] = []
    for index, source_case in enumerate(source_cases, start=1):
        name, prompt, behavior = prompts[(index - 1) % len(prompts)]
        prompt_case = PromptCase(
            name=name,
            prompt=prompt,
            max_new_tokens=24,
            temperature=0.2,
            top_k=10,
            seed=1902 + index,
            task_type="route-promotion-objective-level-contrast-target-hidden",
            difficulty="medium",
            expected_behavior=behavior,
            tags=("route-promotion", "objective-level-contrast", "required-terms", "tokenizer-covered", "target-hidden"),
        ).to_dict()
        rows.append(
            {
                "case_id": f"target-hidden-{name}",
                "source_case_id": source_case.get("case_id"),
                "prompt_case": prompt_case,
                "expected_terms": expected_terms,
                "required_term_count": len(expected_terms),
            }
        )
    return rows


def _coverage_rows(cases: list[dict[str, Any]], expected_terms: list[str], tokenizer: Any) -> list[dict[str, Any]]:
    vocab = set(getattr(tokenizer, "stoi", {}).keys())
    rows: list[dict[str, Any]] = []
    for case in cases:
        prompt = str(as_dict(case.get("prompt_case")).get("prompt") or "")
        unknown = sum(1 for ch in prompt if ch not in vocab)
        leaked = [term for term in expected_terms if term.lower() in prompt.lower()]
        rows.append(
            {
                "case_id": case.get("case_id"),
                "source_case_id": case.get("source_case_id"),
                "prompt_unknown_count": unknown,
                "tokenizer_covered": unknown == 0,
                "leaked_terms": leaked,
                "target_hidden": not leaked,
            }
        )
    return rows


def _checks(review: dict[str, Any], suite_report: dict[str, Any], tokenizer: Path, source_cases: list[dict[str, Any]], cases: list[dict[str, Any]], coverage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    review_summary = as_dict(review.get("summary"))
    return [
        _check("replay_review_passed", review.get("status") == "pass", review.get("status"), "replay review must pass"),
        _check("review_routes_to_target_hidden_suite", review_summary.get("next_step") == "build_target_hidden_tokenizer_covered_holdout_suite", review_summary.get("next_step"), "review must route to target-hidden suite"),
        _check("source_suite_passed", suite_report.get("status") == "pass", suite_report.get("status"), "source suite must pass"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("case_count_preserved", len(cases) == len(source_cases) and bool(cases), len(cases), "target-hidden suite must preserve case count"),
        _check("coverage_rows_complete", len(coverage_rows) == len(cases), len(coverage_rows), "coverage rows must cover every case"),
        _check("all_prompts_tokenizer_covered", all(row.get("tokenizer_covered") is True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("tokenizer_covered") is True), "all prompts must be tokenizer covered"),
        _check("all_prompts_target_hidden", all(row.get("target_hidden") is True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("target_hidden") is True), "all prompts must hide expected terms"),
    ]


def _suite(status: str, source_suite: dict[str, Any], cases: list[dict[str, Any]], expected_terms: list[str]) -> dict[str, Any]:
    return {"ready": status == "pass", "suite_name": "route-promotion-objective-level-contrast-target-hidden-tokenizer-covered-holdout-suite", "suite_version": "v902", "source_suite_name": source_suite.get("suite_name"), "route_id": source_suite.get("route_id"), "consumer_name": "target-hidden-tokenizer-covered-holdout-builder", "allowed_scope": "bounded_model_capability_governance_only" if status == "pass" else "none", "boundary": "target_hidden_ascii_tokenizer_covered_holdout_only", "model_quality_claim": "not_claimed", "cases": cases if status == "pass" else [], "scoring_contract": {"expected_terms": expected_terms, "case_pass_condition": "generated_continuation_contains_both_expected_terms", "suite_pass_condition": "all_cases_pass_without_scope_or_boundary_widening", "minimum_case_count": len(cases)}, "guardrails": ["do not include fixed or loss in prompts", "do not train on these target-hidden holdout prompts before replay", "do not claim promotion before real replay and review"], "proposed_next_artifact": "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run"}


def _summary(status: str, review: dict[str, Any], source_cases: list[dict[str, Any]], cases: list[dict[str, Any]], coverage_rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    review_summary = as_dict(review.get("summary"))
    return {"bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_ready": status == "pass", "source_case_count": len(source_cases), "candidate_case_count": len(cases), "tokenizer_covered_case_count": sum(1 for row in coverage_rows if row.get("tokenizer_covered") is True), "target_hidden_case_count": sum(1 for row in coverage_rows if row.get("target_hidden") is True), "candidate_prompt_unknown_token_count": sum(int(row.get("prompt_unknown_count") or 0) for row in coverage_rows), "source_target_leakage_case_count": review_summary.get("target_leakage_case_count"), "expected_terms": ["fixed", "loss"], "promotion_ready": False, "model_quality_claim": "suite_construction_only", "next_step": "run_target_hidden_tokenizer_covered_holdout_dry_run", "failed_check_count": len(issues)}


def _decision(status: str) -> str:
    return "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_ready" if status == "pass" else "fix_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {"model_quality_claim": summary.get("model_quality_claim") if status == "pass" else "not_claimed", "reason": "Built target-hidden tokenizer-covered holdout prompts." if status == "pass" else "Target-hidden suite inputs failed.", "next_action": summary.get("next_step")}


__all__ = [
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_TEXT_FILENAME",
    "build_target_hidden_tokenizer_covered_holdout_suite",
    "locate_replay_review",
    "locate_source_holdout_suite",
    "read_json_report",
    "resolve_exit_code",
    "target_hidden_candidate_prompt_seed_text",
]
