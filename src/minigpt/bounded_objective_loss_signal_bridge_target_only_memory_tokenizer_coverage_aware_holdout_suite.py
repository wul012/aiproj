from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.eval_suite import PromptCase
from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.tokenizer import load_tokenizer


TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite.json"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite.csv"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite.txt"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite.md"
)
TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite.html"
)


def locate_holdout_gap_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME
    return source


def locate_source_benchmark_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("tokenizer-coverage-aware holdout suite input must be a JSON object")
    return dict(payload)


def build_tokenizer_coverage_aware_holdout_suite(
    holdout_gap_diagnostic_report: dict[str, Any],
    source_benchmark_suite_report: dict[str, Any],
    *,
    tokenizer_path: str | Path,
    holdout_gap_diagnostic_path: str | Path | None = None,
    source_benchmark_suite_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory tokenizer-coverage-aware holdout suite",
    generated_at: str | None = None,
) -> dict[str, Any]:
    tokenizer_file = Path(tokenizer_path)
    tokenizer_exists = tokenizer_file.is_file()
    tokenizer = load_tokenizer(tokenizer_file) if tokenizer_exists else None
    source_suite = as_dict(source_benchmark_suite_report.get("benchmark_suite"))
    source_cases = list_of_dicts(source_suite.get("cases"))
    expected_terms = _expected_terms(source_suite)
    candidate_cases = _candidate_cases(source_cases, expected_terms)
    coverage_rows = _coverage_rows(candidate_cases, tokenizer) if tokenizer is not None else []
    checks = _checks(holdout_gap_diagnostic_report, source_benchmark_suite_report, tokenizer_file, source_cases, candidate_cases, coverage_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    suite = _suite(status, source_suite, candidate_cases, expected_terms)
    summary = _summary(status, holdout_gap_diagnostic_report, source_cases, candidate_cases, coverage_rows, issues)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_holdout_gap_diagnostic": str(holdout_gap_diagnostic_path or ""),
        "source_benchmark_suite": str(source_benchmark_suite_path or ""),
        "tokenizer_path": str(tokenizer_file),
        "check_rows": checks,
        "coverage_rows": coverage_rows,
        "benchmark_suite": suite,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_suite_ready: bool) -> int:
    return 1 if require_suite_ready and report.get("status") != "pass" else 0


def _expected_terms(source_suite: dict[str, Any]) -> list[str]:
    contract = as_dict(source_suite.get("scoring_contract"))
    terms = [str(term) for term in contract.get("expected_terms", [])]
    return terms or ["fixed", "loss"]


def _candidate_cases(source_cases: list[dict[str, Any]], expected_terms: list[str]) -> list[dict[str, Any]]:
    prompts = [
        ("answer_exact_terms", "answer with exactly two words: fixed loss\nanswer:", "ascii exact objective answer"),
        ("return_target_words", "return the two target words fixed loss\noutput:", "ascii target words answer"),
        ("contrast_route_result", "contrast route result fixed loss\nresult:", "ascii contrast objective answer"),
        ("jsonish_answer_terms", "jsonish answer_terms fixed loss\nanswer_terms:", "ascii structured objective answer"),
        ("self_check_terms", "self check requires fixed and loss\nfinal answer:", "ascii self-check objective answer"),
    ]
    rows: list[dict[str, Any]] = []
    for index, source_case in enumerate(source_cases, start=1):
        name, prompt, behavior = prompts[(index - 1) % len(prompts)]
        prompt_case = PromptCase(
            name=name,
            prompt=prompt,
            max_new_tokens=24,
            temperature=0.2,
            top_k=10,
            seed=1898 + index,
            task_type="route-promotion-objective-level-contrast-tokenizer-covered",
            difficulty="medium",
            expected_behavior=behavior,
            tags=("route-promotion", "objective-level-contrast", "required-terms", "tokenizer-covered"),
        ).to_dict()
        rows.append(
            {
                "case_id": f"tokenizer-covered-{name}",
                "source_case_id": source_case.get("case_id"),
                "prompt_case": prompt_case,
                "expected_terms": expected_terms,
                "required_term_count": len(expected_terms),
            }
        )
    return rows


def _coverage_rows(candidate_cases: list[dict[str, Any]], tokenizer: Any) -> list[dict[str, Any]]:
    vocab = set(getattr(tokenizer, "stoi", {}).keys())
    rows: list[dict[str, Any]] = []
    for row in candidate_cases:
        prompt_case = as_dict(row.get("prompt_case"))
        prompt = str(prompt_case.get("prompt") or "")
        unknown_chars = sorted({ch for ch in prompt if ch not in vocab})
        unknown_count = sum(1 for ch in prompt if ch not in vocab)
        rows.append(
            {
                "case_id": row.get("case_id"),
                "source_case_id": row.get("source_case_id"),
                "prompt_char_count": len(prompt),
                "prompt_unknown_count": unknown_count,
                "prompt_unknown_rate": round(unknown_count / len(prompt), 4) if prompt else 0.0,
                "prompt_unknown_chars": unknown_chars,
                "tokenizer_covered": unknown_count == 0,
            }
        )
    return rows


def _checks(
    diagnostic_report: dict[str, Any],
    source_suite_report: dict[str, Any],
    tokenizer_path: Path,
    source_cases: list[dict[str, Any]],
    candidate_cases: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    diagnostic_summary = as_dict(diagnostic_report.get("summary"))
    return [
        _check("holdout_gap_diagnostic_passed", diagnostic_report.get("status") == "pass", diagnostic_report.get("status"), "holdout gap diagnostic must pass"),
        _check(
            "diagnostic_routes_to_tokenizer_coverage_suite",
            diagnostic_summary.get("next_step") == "build_tokenizer_coverage_aware_holdout_suite_before_more_training",
            diagnostic_summary.get("next_step"),
            "diagnostic must route to tokenizer-coverage-aware holdout suite",
        ),
        _check("source_benchmark_suite_passed", source_suite_report.get("status") == "pass", source_suite_report.get("status"), "source benchmark suite must pass"),
        _check("tokenizer_exists", tokenizer_path.is_file(), str(tokenizer_path), "tokenizer.json must exist"),
        _check("case_count_preserved", len(candidate_cases) == len(source_cases) and bool(candidate_cases), len(candidate_cases), "candidate suite must preserve source case count"),
        _check("coverage_rows_complete", len(coverage_rows) == len(candidate_cases), len(coverage_rows), "coverage report must cover every candidate case"),
        _check("all_candidate_prompts_tokenizer_covered", all(row.get("tokenizer_covered") is True for row in coverage_rows), sum(1 for row in coverage_rows if row.get("tokenizer_covered") is True), "every candidate prompt must be tokenizer covered"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _suite(status: str, source_suite: dict[str, Any], cases: list[dict[str, Any]], expected_terms: list[str]) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "ready": ready,
        "suite_name": "route-promotion-objective-level-contrast-tokenizer-coverage-aware-holdout-suite",
        "suite_version": "v898",
        "source_suite_name": source_suite.get("suite_name"),
        "source_suite_version": source_suite.get("suite_version"),
        "route_id": source_suite.get("route_id"),
        "consumer_name": "tokenizer-coverage-aware-holdout-builder",
        "allowed_scope": "bounded_model_capability_governance_only" if ready else "none",
        "boundary": "ascii_tokenizer_coverage_aware_holdout_only",
        "model_quality_claim": "not_claimed",
        "cases": cases if ready else [],
        "scoring_contract": {
            "expected_terms": expected_terms,
            "case_pass_condition": "generated_continuation_contains_both_expected_terms",
            "suite_pass_condition": "all_cases_pass_without_scope_or_boundary_widening",
            "minimum_case_count": len(cases),
        },
        "guardrails": [
            "do not treat tokenizer-covered suite construction as model capability proof",
            "do not train on these holdout prompts before replay",
            "do not widen expected terms beyond fixed and loss",
        ],
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run",
    }


def _summary(
    status: str,
    diagnostic_report: dict[str, Any],
    source_cases: list[dict[str, Any]],
    candidate_cases: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    diagnostic_summary = as_dict(diagnostic_report.get("summary"))
    covered_count = sum(1 for row in coverage_rows if row.get("tokenizer_covered") is True)
    unknown_count = sum(int(row.get("prompt_unknown_count") or 0) for row in coverage_rows)
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready": status == "pass",
        "source_case_count": len(source_cases),
        "candidate_case_count": len(candidate_cases),
        "tokenizer_covered_case_count": covered_count,
        "candidate_prompt_unknown_token_count": unknown_count,
        "source_prompt_unknown_row_count": diagnostic_summary.get("prompt_unknown_row_count"),
        "source_prompt_unknown_token_count": diagnostic_summary.get("prompt_unknown_token_count"),
        "expected_terms": _expected_terms(as_dict(source_cases[0])) if source_cases else ["fixed", "loss"],
        "promotion_ready": False,
        "model_quality_claim": "suite_construction_only",
        "next_step": "run_tokenizer_coverage_aware_holdout_dry_run",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready"
    return "fix_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Tokenizer-coverage-aware holdout suite inputs failed.",
            "next_action": "repair_tokenizer_coverage_aware_holdout_suite_inputs",
        }
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The holdout suite has been rebuilt with prompts fully covered by the v890 tokenizer while preserving the fixed/loss scoring contract.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_TEXT_FILENAME",
    "build_tokenizer_coverage_aware_holdout_suite",
    "locate_holdout_gap_diagnostic",
    "locate_source_benchmark_suite",
    "read_json_report",
    "resolve_exit_code",
]
