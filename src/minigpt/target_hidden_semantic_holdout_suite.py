from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
    TASK_HINT_TERMS,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.eval_suite import PromptCase
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.tokenizer import load_tokenizer


TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME = "target_hidden_semantic_holdout_suite.json"
TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_CSV_FILENAME = "target_hidden_semantic_holdout_suite.csv"
TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_TEXT_FILENAME = "target_hidden_semantic_holdout_suite.txt"
TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_MARKDOWN_FILENAME = "target_hidden_semantic_holdout_suite.md"
TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_HTML_FILENAME = "target_hidden_semantic_holdout_suite.html"


def locate_replay_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
    return source


def locate_source_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("target-hidden semantic holdout suite input must be a JSON object")
    return dict(payload)


def build_target_hidden_semantic_holdout_suite(
    replay_review_report: dict[str, Any],
    source_holdout_suite_report: dict[str, Any],
    *,
    tokenizer_path: str | Path,
    replay_review_path: str | Path | None = None,
    source_holdout_suite_path: str | Path | None = None,
    title: str = "MiniGPT target-hidden semantic paraphrase tokenizer-covered holdout suite",
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


def resolve_exit_code(report: dict[str, Any], *, require_suite_ready: bool) -> int:
    return 1 if require_suite_ready and report.get("status") != "pass" else 0


def semantic_candidate_prompt_seed_text() -> str:
    return "\n".join(prompt for _, prompt, _ in _candidate_prompt_specs())


def _candidate_prompt_specs() -> list[tuple[str, str, str]]:
    return [
        ("memory_answer", "answer from memory\nanswer:", "semantic hidden memory answer"),
        ("stored_result", "write stored result\noutput:", "semantic hidden stored result"),
        ("learned_route", "complete learned route\nresult:", "semantic hidden route completion"),
        ("final_words", "return final words\nanswer:", "semantic hidden final words"),
        ("memory_self_check", "self check memory result\nfinal:", "semantic hidden self-check"),
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
            seed=2006 + index,
            task_type="route-promotion-objective-level-contrast-semantic-target-hidden",
            difficulty="medium",
            expected_behavior=behavior,
            tags=("route-promotion", "objective-level-contrast", "required-terms", "tokenizer-covered", "target-hidden", "semantic-paraphrase"),
        ).to_dict()
        rows.append(
            {
                "case_id": f"semantic-hidden-{name}",
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
        lowered = prompt.lower()
        unknown = sum(1 for ch in prompt if ch not in vocab)
        leaked = [term for term in expected_terms if term.lower() in lowered]
        task_hints = [term for term in TASK_HINT_TERMS if term in lowered]
        rows.append(
            {
                "case_id": case.get("case_id"),
                "source_case_id": case.get("source_case_id"),
                "prompt_unknown_count": unknown,
                "tokenizer_covered": unknown == 0,
                "leaked_terms": leaked,
                "target_hidden": not leaked,
                "task_hint_terms": task_hints,
                "task_hint": bool(task_hints),
            }
        )
    return rows


def _checks(
    review: dict[str, Any],
    suite_report: dict[str, Any],
    tokenizer: Path,
    source_cases: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    review_summary = as_dict(review.get("summary"))
    return [
        _check("replay_review_passed", review.get("status") == "pass", review.get("status"), "v905 replay review must pass"),
        _check("review_approves_wider_holdout", review_summary.get("approved_for_wider_holdout") is True, review_summary.get("approved_for_wider_holdout"), "review must approve wider holdout"),
        _check("review_routes_to_semantic_suite", review_summary.get("next_step") == "build_semantic_paraphrase_target_hidden_holdout_suite", review_summary.get("next_step"), "review must route to semantic suite"),
        _check("source_suite_passed", suite_report.get("status") == "pass", suite_report.get("status"), "source target-hidden suite must pass"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("case_count_preserved", len(cases) == len(source_cases) and bool(cases), len(cases), "semantic suite must preserve case count"),
        _check("coverage_rows_complete", len(coverage_rows) == len(cases), len(coverage_rows), "coverage rows must cover every case"),
        _check("all_prompts_tokenizer_covered", all(row.get("tokenizer_covered") is True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("tokenizer_covered") is True), "all prompts must be tokenizer covered"),
        _check("all_prompts_target_hidden", all(row.get("target_hidden") is True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("target_hidden") is True), "all prompts must hide expected terms"),
        _check("no_prompt_task_hints", all(row.get("task_hint") is not True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("task_hint") is True), "semantic suite should avoid known task-hint terms"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _suite(status: str, source_suite: dict[str, Any], cases: list[dict[str, Any]], expected_terms: list[str]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "suite_name": "route-promotion-objective-level-contrast-semantic-paraphrase-target-hidden-holdout-suite",
        "suite_version": "v906",
        "source_suite_name": source_suite.get("suite_name"),
        "route_id": source_suite.get("route_id"),
        "consumer_name": "target-hidden-semantic-holdout-builder",
        "allowed_scope": "bounded_model_capability_governance_only" if status == "pass" else "none",
        "boundary": "semantic_paraphrase_target_hidden_ascii_tokenizer_covered_holdout_only",
        "model_quality_claim": "not_claimed",
        "cases": cases if status == "pass" else [],
        "scoring_contract": {
            "expected_terms": expected_terms,
            "case_pass_condition": "generated_continuation_contains_both_expected_terms",
            "suite_pass_condition": "all_cases_pass_without_scope_or_boundary_widening",
            "minimum_case_count": len(cases),
        },
        "guardrails": ["do not include fixed or loss in prompts", "do not use known pair/target task-hint terms", "do not claim promotion before dry-run, replay, and review"],
        "proposed_next_artifact": "target_hidden_semantic_holdout_dry_run",
    }


def _summary(
    status: str,
    review: dict[str, Any],
    source_cases: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    review_summary = as_dict(review.get("summary"))
    task_hint_count = sum(1 for row in coverage_rows if row.get("task_hint") is True)
    return {
        "target_hidden_semantic_holdout_suite_ready": status == "pass",
        "source_case_count": len(source_cases),
        "candidate_case_count": len(cases),
        "tokenizer_covered_case_count": sum(1 for row in coverage_rows if row.get("tokenizer_covered") is True),
        "target_hidden_case_count": sum(1 for row in coverage_rows if row.get("target_hidden") is True),
        "task_hint_case_count": task_hint_count,
        "candidate_prompt_unknown_token_count": sum(int(row.get("prompt_unknown_count") or 0) for row in coverage_rows),
        "source_task_hint_case_count": review_summary.get("task_hint_case_count"),
        "expected_terms": ["fixed", "loss"],
        "promotion_ready": False,
        "model_quality_claim": "suite_construction_only",
        "next_step": "run_target_hidden_semantic_holdout_dry_run",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    return "target_hidden_semantic_holdout_suite_ready" if status == "pass" else "fix_target_hidden_semantic_holdout_suite"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Semantic target-hidden suite inputs failed.", "next_action": "repair_target_hidden_semantic_holdout_suite"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "Built tokenizer-covered target-hidden prompts without known pair/target task-hint terms.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_CSV_FILENAME",
    "TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_HTML_FILENAME",
    "TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME",
    "TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_MARKDOWN_FILENAME",
    "TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_TEXT_FILENAME",
    "build_target_hidden_semantic_holdout_suite",
    "locate_replay_review",
    "locate_source_holdout_suite",
    "read_json_report",
    "resolve_exit_code",
    "semantic_candidate_prompt_seed_text",
]
