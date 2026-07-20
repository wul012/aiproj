from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review import (
    TASK_HINT_TERMS,
)
from minigpt.eval_suite import PromptCase
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.target_hidden_prompt_mutation_holdout_replay_review import TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
from minigpt.target_hidden_prompt_mutation_holdout_suite import TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.tokenizer import load_tokenizer
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_suite_ready as resolve_exit_code


RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME = "randomized_target_hidden_holdout_suite.json"
RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_CSV_FILENAME = "randomized_target_hidden_holdout_suite.csv"
RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_TEXT_FILENAME = "randomized_target_hidden_holdout_suite.txt"
RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_MARKDOWN_FILENAME = "randomized_target_hidden_holdout_suite.md"
RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_HTML_FILENAME = "randomized_target_hidden_holdout_suite.html"


def locate_replay_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
    return source


def locate_source_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized target-hidden holdout suite input must be a JSON object")
    return dict(payload)


def build_randomized_target_hidden_holdout_suite(
    replay_review_report: dict[str, Any],
    source_holdout_suite_report: dict[str, Any],
    *,
    tokenizer_path: str | Path,
    seed: int = 914,
    candidate_count: int = 20,
    replay_review_path: str | Path | None = None,
    source_holdout_suite_path: str | Path | None = None,
    title: str = "MiniGPT randomized target-hidden tokenizer-covered holdout suite",
    generated_at: str | None = None,
) -> dict[str, Any]:
    tokenizer_file = Path(tokenizer_path)
    tokenizer_exists = tokenizer_file.is_file()
    tokenizer = load_tokenizer(tokenizer_file) if tokenizer_exists else None
    source_suite = as_dict(source_holdout_suite_report.get("benchmark_suite"))
    source_cases = list_of_dicts(source_suite.get("cases"))
    expected_terms = [str(term) for term in as_dict(source_suite.get("scoring_contract")).get("expected_terms", [])] or ["fixed", "loss"]
    cases = _candidate_cases(source_cases, expected_terms, seed=seed, candidate_count=candidate_count)
    source_prompts = [str(as_dict(case.get("prompt_case")).get("prompt") or "") for case in source_cases]
    coverage_rows = _coverage_rows(cases, expected_terms, tokenizer, source_prompts) if tokenizer is not None else []
    checks = _checks(replay_review_report, source_holdout_suite_report, tokenizer_file, seed, source_cases, cases, coverage_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, replay_review_report, source_cases, cases, coverage_rows, seed, issues)
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
        "random_seed": seed,
        "check_rows": checks,
        "coverage_rows": coverage_rows,
        "benchmark_suite": _suite(status, source_suite, cases, expected_terms, seed),
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def randomized_target_hidden_candidate_prompt_seed_text() -> str:
    return " ".join(_prompt_pool_words()) + "\n" + "\n".join(f"{tail}:" for tail in _tail_pool())


def _candidate_cases(source_cases: list[dict[str, Any]], expected_terms: list[str], *, seed: int, candidate_count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    source_count = max(len(source_cases), 1)
    attempts = 0
    while len(rows) < candidate_count and attempts < candidate_count * 20:
        attempts += 1
        words = rng.sample(_prompt_pool_words(), 3)
        tail = rng.choice(_tail_pool())
        prompt = f"{words[0]} {words[1]} {words[2]}\n{tail}:"
        if prompt in seen:
            continue
        seen.add(prompt)
        index = len(rows) + 1
        source_case = source_cases[(index - 1) % source_count] if source_cases else {}
        prompt_case = PromptCase(
            name=f"randomized_hidden_{index:02d}",
            prompt=prompt,
            max_new_tokens=24,
            temperature=0.2,
            top_k=10,
            seed=4010 + index,
            task_type="route-promotion-objective-level-contrast-randomized-target-hidden",
            difficulty="hard",
            expected_behavior="randomized target-hidden prompt should recover required terms from learned route",
            tags=("route-promotion", "objective-level-contrast", "required-terms", "tokenizer-covered", "target-hidden", "randomized"),
        ).to_dict()
        rows.append(
            {
                "case_id": f"randomized-target-hidden-{index:02d}",
                "source_case_id": source_case.get("case_id"),
                "prompt_case": prompt_case,
                "expected_terms": expected_terms,
                "required_term_count": len(expected_terms),
                "random_seed": seed,
                "random_draw_index": index,
                "source_case_index": (index - 1) % source_count,
            }
        )
    return rows


def _coverage_rows(cases: list[dict[str, Any]], expected_terms: list[str], tokenizer: Any, source_prompts: list[str]) -> list[dict[str, Any]]:
    vocab = set(getattr(tokenizer, "stoi", {}).keys())
    source_prompt_set = set(source_prompts)
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
                "random_draw_index": case.get("random_draw_index"),
                "prompt_unknown_count": unknown,
                "tokenizer_covered": unknown == 0,
                "leaked_terms": leaked,
                "target_hidden": not leaked,
                "task_hint_terms": task_hints,
                "task_hint": bool(task_hints),
                "unique_prompt": prompt not in source_prompt_set,
                "randomized_prompt": True,
            }
        )
    return rows


def _checks(
    review: dict[str, Any],
    source_suite_report: dict[str, Any],
    tokenizer: Path,
    seed: int,
    source_cases: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    review_summary = as_dict(review.get("summary"))
    source_summary = as_dict(source_suite_report.get("summary"))
    prompt_count = _unique_prompt_count(cases)
    return [
        _check("replay_review_passed", review.get("status") == "pass", review.get("status"), "v913 replay review must pass"),
        _check("review_approves_randomized_holdout", review_summary.get("approved_for_randomized_prompt_holdout") is True, review_summary.get("approved_for_randomized_prompt_holdout"), "review must approve randomized holdout"),
        _check("review_routes_to_randomized_suite", review_summary.get("next_step") == "build_randomized_target_hidden_holdout_suite", review_summary.get("next_step"), "review must route to randomized holdout suite"),
        _check("source_suite_passed", source_suite_report.get("status") == "pass", source_suite_report.get("status"), "source prompt-mutation suite must pass"),
        _check("source_suite_ready", source_summary.get("target_hidden_prompt_mutation_holdout_suite_ready") is True, source_summary.get("target_hidden_prompt_mutation_holdout_suite_ready"), "source prompt-mutation suite summary must be ready"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("seed_positive", seed > 0, seed, "random seed must be positive and reproducible"),
        _check("candidate_expands_source", len(cases) >= len(source_cases) * 2 and bool(source_cases), len(cases), "randomized suite should double the source prompt-mutation case count"),
        _check("coverage_rows_complete", len(coverage_rows) == len(cases), len(coverage_rows), "coverage rows must cover every case"),
        _check("all_prompts_tokenizer_covered", all(row.get("tokenizer_covered") is True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("tokenizer_covered") is True), "all randomized prompts must be tokenizer covered"),
        _check("all_prompts_target_hidden", all(row.get("target_hidden") is True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("target_hidden") is True), "all randomized prompts must hide expected terms"),
        _check("no_prompt_task_hints", all(row.get("task_hint") is not True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("task_hint") is True), "randomized prompts should avoid known task-hint terms"),
        _check("all_prompts_unique", prompt_count == len(cases), prompt_count, "randomized prompts must be unique"),
        _check("all_prompts_new_vs_source", all(row.get("unique_prompt") is True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("unique_prompt") is True), "randomized prompts should differ from source prompts"),
    ]


def _suite(status: str, source_suite: dict[str, Any], cases: list[dict[str, Any]], expected_terms: list[str], seed: int) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "suite_name": "route-promotion-objective-level-contrast-randomized-target-hidden-holdout-suite",
        "suite_version": "v914",
        "source_suite_name": source_suite.get("suite_name"),
        "route_id": source_suite.get("route_id"),
        "consumer_name": "randomized-target-hidden-holdout-builder",
        "allowed_scope": "bounded_model_capability_governance_only" if status == "pass" else "none",
        "boundary": "seeded_randomized_target_hidden_ascii_tokenizer_covered_holdout_only",
        "model_quality_claim": "not_claimed",
        "random_seed": seed,
        "cases": cases if status == "pass" else [],
        "scoring_contract": {
            "expected_terms": expected_terms,
            "case_pass_condition": "generated_continuation_contains_both_expected_terms",
            "suite_pass_condition": "all_cases_pass_without_scope_or_boundary_widening",
            "minimum_case_count": len(cases),
        },
        "guardrails": ["do not include fixed or loss in prompts", "do not use known pair/target task-hint terms", "do not claim promotion before dry-run, replay, and review"],
        "proposed_next_artifact": "randomized_target_hidden_holdout_dry_run",
    }


def _summary(
    status: str,
    review: dict[str, Any],
    source_cases: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    seed: int,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    review_summary = as_dict(review.get("summary"))
    return {
        "randomized_target_hidden_holdout_suite_ready": status == "pass",
        "source_case_count": len(source_cases),
        "candidate_case_count": len(cases),
        "random_seed": seed,
        "randomized_case_factor": round(len(cases) / len(source_cases), 2) if source_cases else 0.0,
        "tokenizer_covered_case_count": sum(1 for row in coverage_rows if row.get("tokenizer_covered") is True),
        "target_hidden_case_count": sum(1 for row in coverage_rows if row.get("target_hidden") is True),
        "task_hint_case_count": sum(1 for row in coverage_rows if row.get("task_hint") is True),
        "unique_prompt_count": _unique_prompt_count(cases),
        "new_vs_source_prompt_count": sum(1 for row in coverage_rows if row.get("unique_prompt") is True),
        "candidate_prompt_unknown_token_count": sum(int(row.get("prompt_unknown_count") or 0) for row in coverage_rows),
        "source_prompt_mutation_clean_case_count": review_summary.get("clean_prompt_mutation_case_count"),
        "source_pass_rate": review_summary.get("pass_rate"),
        "expected_terms": ["fixed", "loss"],
        "promotion_ready": False,
        "model_quality_claim": "suite_construction_only",
        "next_step": "dry_run_randomized_target_hidden_holdout",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    return "randomized_target_hidden_holdout_suite_ready" if status == "pass" else "fix_randomized_target_hidden_holdout_suite"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Randomized target-hidden suite inputs failed.", "next_action": "repair_randomized_target_hidden_holdout_suite"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "Built a seeded randomized target-hidden suite that remains tokenizer-covered and avoids known target hints.",
        "next_action": summary.get("next_step"),
    }


def _prompt_pool_words() -> list[str]:
    return ["memory", "answer", "stored", "route", "final", "result", "output", "complete", "learned", "write", "self", "check", "words"]


def _tail_pool() -> list[str]:
    return ["answer", "output", "result", "final"]


def _unique_prompt_count(cases: list[dict[str, Any]]) -> int:
    return len({str(as_dict(case.get("prompt_case")).get("prompt") or "") for case in cases})


__all__ = [
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_CSV_FILENAME",
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_HTML_FILENAME",
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME",
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_MARKDOWN_FILENAME",
    "RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_TEXT_FILENAME",
    "build_randomized_target_hidden_holdout_suite",
    "locate_replay_review",
    "locate_source_holdout_suite",
    "randomized_target_hidden_candidate_prompt_seed_text",
    "read_json_report",
    "resolve_exit_code",
]
