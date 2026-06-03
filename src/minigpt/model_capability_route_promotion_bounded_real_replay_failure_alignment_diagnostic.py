from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_TRAINING_RUN_REVISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic.html"


def locate_benchmark_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME
    return source


def locate_checkpoint_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_JSON_FILENAME
    return source


def locate_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_JSON_FILENAME
    return source


def locate_training_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_TRAINING_RUN_REVISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded real replay failure alignment diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic(
    benchmark_suite_report: dict[str, Any],
    comparison_report: dict[str, Any],
    seed_revision_report: dict[str, Any],
    training_revision_report: dict[str, Any],
    *,
    corpus_path: str | Path,
    benchmark_suite_path: str | Path | None = None,
    comparison_path: str | Path | None = None,
    seed_revision_path: str | Path | None = None,
    training_revision_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay failure alignment diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    corpus = Path(corpus_path).read_text(encoding="utf-8-sig") if Path(corpus_path).is_file() else ""
    suite = as_dict(benchmark_suite_report.get("benchmark_suite"))
    cases = list_of_dicts(suite.get("cases"))
    comparison_summary = as_dict(comparison_report.get("summary"))
    seed_summary = as_dict(seed_revision_report.get("summary"))
    training_summary = as_dict(training_revision_report.get("summary"))
    case_rows = {str(row.get("case_id")): row for row in list_of_dicts(comparison_report.get("case_rows"))}
    diagnostics = [_case_diagnostic(case, as_dict(case_rows.get(str(case.get("case_id")))), corpus) for case in cases]
    root_causes = _root_causes(diagnostics, comparison_summary, training_summary)
    checks = _checks(benchmark_suite_report, comparison_report, seed_revision_report, training_revision_report, corpus, diagnostics)
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
        "source_benchmark_suite": str(benchmark_suite_path or ""),
        "source_comparison": str(comparison_path or ""),
        "source_seed_revision": str(seed_revision_path or ""),
        "source_training_revision": str(training_revision_path or ""),
        "source_corpus": str(corpus_path),
        "source_summaries": {"comparison": comparison_summary, "seed_revision": seed_summary, "training_revision": training_summary},
        "case_diagnostics": diagnostics,
        "root_causes": root_causes,
        "check_rows": checks,
        "summary": _summary(status, checks, diagnostics, root_causes),
        "interpretation": _interpretation(status, root_causes),
    }


def resolve_exit_code(report: dict[str, Any], *, require_diagnostic_ready: bool) -> int:
    return 1 if require_diagnostic_ready and report.get("status") != "pass" else 0


def _case_diagnostic(case: dict[str, Any], row: dict[str, Any], corpus: str) -> dict[str, Any]:
    prompt_case = as_dict(case.get("prompt_case"))
    prompt = str(prompt_case.get("prompt") or "")
    continuation = str(row.get("repair_continuation") or "")
    expected_terms = [str(term) for term in case.get("expected_terms", [])]
    missed_terms = [term for term in expected_terms if term.lower() not in continuation.lower()]
    prompt_in_corpus = bool(prompt and prompt in corpus)
    return {
        "case_id": str(case.get("case_id") or ""),
        "prompt_in_corpus": prompt_in_corpus,
        "expected_terms": expected_terms,
        "repair_pass": row.get("repair_pass") is True,
        "repair_continuation": continuation,
        "missed_terms": missed_terms,
        "corpus_fixed_count": corpus.lower().count("fixed"),
        "corpus_loss_count": corpus.lower().count("loss"),
        "diagnosis": _diagnosis(prompt_in_corpus, missed_terms, corpus),
        "recommended_action": _recommended_action(prompt_in_corpus, missed_terms),
    }


def _diagnosis(prompt_in_corpus: bool, missed_terms: list[str], corpus: str) -> str:
    if not missed_terms:
        return "case_aligned"
    if not prompt_in_corpus:
        return "benchmark_prompt_not_represented_in_training_corpus"
    if "fixed" in corpus.lower() and "loss" in corpus.lower():
        return "required_terms_present_but_generation_not_anchored"
    return "required_terms_underrepresented_in_corpus"


def _recommended_action(prompt_in_corpus: bool, missed_terms: list[str]) -> str:
    if not missed_terms:
        return "keep_case_as_regression_guard"
    if not prompt_in_corpus:
        return "add_exact_benchmark_prompt_completion_examples"
    return "add_decoder_anchoring_examples_or_adjust_decoding"


def _root_causes(diagnostics: list[dict[str, Any]], comparison_summary: dict[str, Any], training_summary: dict[str, Any]) -> list[dict[str, Any]]:
    causes = []
    prompt_gap_count = sum(1 for row in diagnostics if row.get("prompt_in_corpus") is not True)
    failed_count = sum(1 for row in diagnostics if row.get("repair_pass") is not True)
    if prompt_gap_count:
        causes.append({"cause_id": "benchmark_prompt_training_corpus_gap", "severity": "high", "evidence": prompt_gap_count, "detail": "Benchmark prompts are not exactly represented in the revised training corpus."})
    if failed_count and comparison_summary.get("repair_checkpoint_regressed") is True:
        causes.append({"cause_id": "repair_training_not_replay_aligned", "severity": "high", "evidence": comparison_summary.get("pass_rate_delta"), "detail": "Training produced a checkpoint, but bounded replay still regressed against baseline."})
    if training_summary.get("final_val_loss") is not None and failed_count:
        causes.append({"cause_id": "loss_improvement_not_sufficient_for_exact_terms", "severity": "medium", "evidence": training_summary.get("final_val_loss"), "detail": "Loss evidence is not enough for fixed/loss exact-term generation."})
    return causes


def _checks(
    suite: dict[str, Any],
    comparison: dict[str, Any],
    seed_revision: dict[str, Any],
    training_revision: dict[str, Any],
    corpus: str,
    diagnostics: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("benchmark_suite_passed", suite.get("status") == "pass", suite.get("status"), "benchmark suite must pass"),
        _check("comparison_passed", comparison.get("status") == "pass", comparison.get("status"), "comparison must pass"),
        _check("promotion_blocked", as_dict(comparison.get("summary")).get("promotion_ready") is False, as_dict(comparison.get("summary")).get("promotion_ready"), "diagnostic is for blocked promotion"),
        _check("seed_revision_passed", seed_revision.get("status") == "pass", seed_revision.get("status"), "seed revision must pass"),
        _check("training_revision_passed", training_revision.get("status") == "pass", training_revision.get("status"), "training revision must pass"),
        _check("corpus_present", bool(corpus.strip()), len(corpus), "corpus must be readable"),
        _check("case_diagnostics_present", bool(diagnostics), len(diagnostics), "diagnostic must inspect benchmark cases"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, checks: list[dict[str, Any]], diagnostics: list[dict[str, Any]], root_causes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "bounded_real_replay_failure_alignment_diagnostic_ready": status == "pass",
        "case_count": len(diagnostics),
        "failed_case_count": sum(1 for row in diagnostics if row.get("repair_pass") is not True),
        "prompt_gap_count": sum(1 for row in diagnostics if row.get("prompt_in_corpus") is not True),
        "root_cause_count": len(root_causes),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision",
        "next_step": "build_prompt_aligned_seed_revision" if status == "pass" else "repair_failure_alignment_diagnostic_inputs",
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic"


def _interpretation(status: str, root_causes: list[dict[str, Any]]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Diagnostic inputs are incomplete.", "next_action": "repair diagnostic inputs"}
    return {
        "model_quality_claim": "not_improved",
        "reason": "Replay remains failed; diagnostic points to prompt/corpus alignment and exact-term anchoring gaps.",
        "next_action": "build_prompt_aligned_seed_revision" if root_causes else "review_diagnostic_manually",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic",
    "locate_benchmark_suite",
    "locate_checkpoint_comparison",
    "locate_seed_revision",
    "locate_training_revision",
    "read_json_report",
    "resolve_exit_code",
]
