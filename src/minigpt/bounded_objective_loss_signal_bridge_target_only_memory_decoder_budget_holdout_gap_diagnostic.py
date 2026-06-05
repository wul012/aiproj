from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.tokenizer import load_tokenizer


TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic.json"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic.csv"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic.txt"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic.md"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic.html"
)


def locate_decoder_budget_holdout_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder-budget holdout gap diagnostic input must be a JSON object")
    return dict(payload)


def build_decoder_budget_holdout_gap_diagnostic(
    holdout_replay_report: dict[str, Any],
    *,
    tokenizer_path: str | Path,
    training_corpus_path: str | Path,
    holdout_replay_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory decoder-budget holdout gap diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    tokenizer_file = Path(tokenizer_path)
    corpus_file = Path(training_corpus_path)
    tokenizer_exists = tokenizer_file.is_file()
    corpus_exists = corpus_file.is_file()
    tokenizer = load_tokenizer(tokenizer_file) if tokenizer_exists else None
    corpus = corpus_file.read_text(encoding="utf-8-sig") if corpus_exists else ""
    replay_rows = list_of_dicts(holdout_replay_report.get("replay_rows"))
    diagnostic_rows = _diagnostic_rows(replay_rows, tokenizer, corpus) if tokenizer is not None else []
    checks = _checks(holdout_replay_report, tokenizer_file, corpus_file, replay_rows, diagnostic_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, holdout_replay_report, diagnostic_rows, issues)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_holdout_replay": str(holdout_replay_path or ""),
        "source_holdout_replay_summary": as_dict(holdout_replay_report.get("summary")),
        "tokenizer_path": str(tokenizer_file),
        "training_corpus_path": str(corpus_file),
        "check_rows": checks,
        "diagnostic_rows": diagnostic_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_diagnostic_ready: bool) -> int:
    return 1 if require_diagnostic_ready and report.get("status") != "pass" else 0


def _diagnostic_rows(replay_rows: list[dict[str, Any]], tokenizer: Any, corpus: str) -> list[dict[str, Any]]:
    vocab = set(getattr(tokenizer, "stoi", {}).keys())
    rows: list[dict[str, Any]] = []
    for row in replay_rows:
        prompt = str(row.get("prompt") or "")
        continuation = str(row.get("continuation") or "")
        unknown_chars = sorted({ch for ch in prompt if ch not in vocab})
        unknown_count = sum(1 for ch in prompt if ch not in vocab)
        prompt_char_count = len(prompt)
        prompt_exact_in_corpus = prompt in corpus
        expected_terms = [str(term) for term in row.get("expected_terms", [])]
        missing_terms_from_corpus = [term for term in expected_terms if term not in corpus]
        failure_class = _failure_class(row, unknown_count, prompt_exact_in_corpus, missing_terms_from_corpus)
        rows.append(
            {
                "case_id": row.get("case_id"),
                "case_pass": row.get("case_pass") is True,
                "prompt_char_count": prompt_char_count,
                "prompt_unknown_count": unknown_count,
                "prompt_unknown_rate": round(unknown_count / prompt_char_count, 4) if prompt_char_count else 0.0,
                "prompt_unknown_chars": unknown_chars,
                "prompt_exact_in_corpus": prompt_exact_in_corpus,
                "expected_terms": expected_terms,
                "expected_terms_missing_from_corpus": missing_terms_from_corpus,
                "continuation_replacement_count": continuation.count("�"),
                "hit_terms": [str(term) for term in row.get("hit_terms", [])],
                "missed_terms": [str(term) for term in row.get("missed_terms", [])],
                "failure_class": failure_class,
            }
        )
    return rows


def _failure_class(
    replay_row: dict[str, Any],
    unknown_count: int,
    prompt_exact_in_corpus: bool,
    missing_terms_from_corpus: list[str],
) -> str:
    if replay_row.get("case_pass") is True:
        return "passed"
    if unknown_count > 0:
        return "tokenizer_prompt_coverage_gap"
    if not prompt_exact_in_corpus:
        return "holdout_prompt_unseen_surface_gap"
    if missing_terms_from_corpus:
        return "training_corpus_required_term_gap"
    return "required_term_generation_gap"


def _checks(
    holdout_replay_report: dict[str, Any],
    tokenizer_path: Path,
    corpus_path: Path,
    replay_rows: list[dict[str, Any]],
    diagnostic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("holdout_replay_passed", holdout_replay_report.get("status") == "pass", holdout_replay_report.get("status"), "holdout replay must pass structurally"),
        _check("tokenizer_exists", tokenizer_path.is_file(), str(tokenizer_path), "tokenizer.json must exist"),
        _check("training_corpus_exists", corpus_path.is_file(), str(corpus_path), "prepared training corpus must exist"),
        _check("replay_rows_present", bool(replay_rows), len(replay_rows), "holdout replay must include replay rows"),
        _check("diagnostic_rows_complete", len(diagnostic_rows) == len(replay_rows), len(diagnostic_rows), "diagnostic should cover every replay row"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(
    status: str,
    holdout_replay_report: dict[str, Any],
    diagnostic_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    holdout_summary = as_dict(holdout_replay_report.get("summary"))
    tokenizer_gap_count = sum(1 for row in diagnostic_rows if row.get("failure_class") == "tokenizer_prompt_coverage_gap")
    unseen_surface_count = sum(1 for row in diagnostic_rows if row.get("failure_class") == "holdout_prompt_unseen_surface_gap")
    generation_gap_count = sum(1 for row in diagnostic_rows if row.get("failure_class") == "required_term_generation_gap")
    passed_count = sum(1 for row in diagnostic_rows if row.get("failure_class") == "passed")
    replacement_rows = sum(1 for row in diagnostic_rows if int(row.get("continuation_replacement_count") or 0) > 0)
    prompt_unknown_rows = sum(1 for row in diagnostic_rows if int(row.get("prompt_unknown_count") or 0) > 0)
    total_unknown = sum(int(row.get("prompt_unknown_count") or 0) for row in diagnostic_rows)
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic_ready": status == "pass",
        "source_promotion_ready": holdout_summary.get("promotion_ready") is True,
        "source_holdout_pass_rate": holdout_summary.get("pass_rate"),
        "case_count": len(diagnostic_rows),
        "passed_case_count": passed_count,
        "tokenizer_prompt_coverage_gap_count": tokenizer_gap_count,
        "holdout_prompt_unseen_surface_gap_count": unseen_surface_count,
        "required_term_generation_gap_count": generation_gap_count,
        "continuation_replacement_row_count": replacement_rows,
        "prompt_unknown_row_count": prompt_unknown_rows,
        "prompt_unknown_token_count": total_unknown,
        "dominant_gap": _dominant_gap(tokenizer_gap_count, unseen_surface_count, generation_gap_count),
        "promotion_ready": False,
        "model_quality_claim": "holdout_gap_diagnostic_only",
        "next_step": _next_step(tokenizer_gap_count, unseen_surface_count),
        "failed_check_count": len(issues),
    }


def _dominant_gap(tokenizer_gap_count: int, unseen_surface_count: int, generation_gap_count: int) -> str:
    if tokenizer_gap_count > 0:
        return "tokenizer_prompt_coverage_gap"
    if unseen_surface_count > 0:
        return "holdout_prompt_unseen_surface_gap"
    if generation_gap_count > 0:
        return "required_term_generation_gap"
    return "no_holdout_gap_detected"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic_inputs"
    dominant = summary.get("dominant_gap")
    if dominant == "tokenizer_prompt_coverage_gap":
        return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_tokenizer_coverage_blocks_promotion"
    if dominant == "holdout_prompt_unseen_surface_gap":
        return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_unseen_prompt_surface_blocks_promotion"
    if dominant == "required_term_generation_gap":
        return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_required_term_generation_blocks_promotion"
    return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_not_detected_review_required"


def _next_step(tokenizer_gap_count: int, unseen_surface_count: int) -> str:
    if tokenizer_gap_count > 0:
        return "build_tokenizer_coverage_aware_holdout_suite_before_more_training"
    if unseen_surface_count > 0:
        return "build_prompt_surface_coverage_patch_before_more_training"
    return "inspect_required_term_generation_gap_before_more_training"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Holdout gap diagnostic inputs are incomplete.",
            "next_action": summary.get("next_step"),
        }
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": f"The dominant v896 holdout gap is {summary.get('dominant_gap')}; this is diagnostic evidence only and does not promote the model.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_TEXT_FILENAME",
    "build_decoder_budget_holdout_gap_diagnostic",
    "locate_decoder_budget_holdout_replay",
    "read_json_report",
    "resolve_exit_code",
]
