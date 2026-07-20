from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_DRY_RUN_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_execution_model as resolve_exit_code


TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay.json"
)
TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay.csv"
)
TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay.txt"
)
TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay.md"
)
TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay.html"
)

GeneratorRunner = Callable[[dict[str, Any], str | Path, str | Path, str], dict[str, Any]]


def locate_target_hidden_tokenizer_covered_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME
    return source


def locate_target_hidden_tokenizer_covered_holdout_dry_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_DRY_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("target-hidden tokenizer-covered holdout real replay input must be a JSON object")
    return dict(payload)


def build_target_hidden_tokenizer_covered_holdout_real_replay(
    holdout_suite_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    holdout_suite_path: str | Path | None = None,
    dry_run_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory target-hidden tokenizer-covered holdout real replay",
    generated_at: str | None = None,
) -> dict[str, Any]:
    checkpoint = Path(checkpoint_path)
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else checkpoint.parent / "tokenizer.json"
    suite = as_dict(holdout_suite_report.get("benchmark_suite"))
    cases = list_of_dicts(suite.get("cases"))
    expected_terms = [str(term) for term in as_dict(suite.get("scoring_contract")).get("expected_terms", [])]
    replay_rows, replay_errors = _run_cases(cases, expected_terms, checkpoint, tokenizer, device, generator_runner or _generate_case)
    checks = _checks(holdout_suite_report, dry_run_report, checkpoint, tokenizer, cases, replay_rows, replay_errors, expected_terms)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, cases, replay_rows, issues)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_holdout_suite": str(holdout_suite_path or ""),
        "source_dry_run": str(dry_run_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "check_rows": checks,
        "replay_rows": replay_rows,
        "replay_errors": replay_errors,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _run_cases(
    cases: list[dict[str, Any]],
    expected_terms: list[str],
    checkpoint: Path,
    tokenizer: Path,
    device: str,
    runner: GeneratorRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for case in cases:
        try:
            response = runner(case, checkpoint, tokenizer, device)
            continuation = str(response.get("continuation") or "")
            score = _score(expected_terms, continuation)
            rows.append(
                {
                    "case_id": case.get("case_id"),
                    "source_case_id": case.get("source_case_id"),
                    "prompt": response.get("prompt"),
                    "continuation": continuation,
                    "generated": response.get("generated"),
                    "expected_terms": expected_terms,
                    "hit_terms": score["hit_terms"],
                    "missed_terms": score["missed_terms"],
                    "case_pass": score["case_pass"],
                    "seed": response.get("seed"),
                    "max_new_tokens": response.get("max_new_tokens"),
                    "temperature": response.get("temperature"),
                    "top_k": response.get("top_k"),
                }
            )
        except Exception as exc:  # pragma: no cover - covered by fake runner tests.
            errors.append({"case_id": case.get("case_id"), "error": type(exc).__name__, "message": str(exc)})
    return rows, errors


def _generate_case(case: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    prompt_case = as_dict(case.get("prompt_case"))
    request = GenerationRequest(
        prompt=str(prompt_case.get("prompt") or ""),
        max_new_tokens=int(prompt_case.get("max_new_tokens") or 24),
        temperature=float(prompt_case.get("temperature") or 0.2),
        top_k=None if prompt_case.get("top_k") in {None, "", 0, "0"} else int(prompt_case.get("top_k")),
        seed=None if prompt_case.get("seed") in {None, ""} else int(prompt_case.get("seed")),
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _score(expected_terms: list[str], continuation: str) -> dict[str, Any]:
    lowered = continuation.lower()
    hit_terms = [term for term in expected_terms if term.lower() in lowered]
    missed_terms = [term for term in expected_terms if term not in hit_terms]
    return {"hit_terms": hit_terms, "missed_terms": missed_terms, "case_pass": bool(expected_terms) and not missed_terms}


def _checks(
    suite_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    cases: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    replay_errors: list[dict[str, Any]],
    expected_terms: list[str],
) -> list[dict[str, Any]]:
    dry_summary = as_dict(dry_run_report.get("summary"))
    suite_summary = as_dict(suite_report.get("summary"))
    suite_ready_key = "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_ready"
    dry_ready_key = "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run_ready"
    return [
        _check("holdout_suite_passed", suite_report.get("status") == "pass", suite_report.get("status"), "target-hidden holdout suite must pass"),
        _check("holdout_suite_ready", suite_summary.get(suite_ready_key) is True, suite_summary.get(suite_ready_key), "holdout suite summary must be ready"),
        _check("target_hidden_cases_present", suite_summary.get("target_hidden_case_count") == len(cases), suite_summary.get("target_hidden_case_count"), "every suite case must remain target-hidden"),
        _check("dry_run_passed", dry_run_report.get("status") == "pass", dry_run_report.get("status"), "dry-run must pass before real replay"),
        _check("dry_run_ready", dry_summary.get(dry_ready_key) is True, dry_summary.get(dry_ready_key), "dry-run summary must be ready"),
        _check("expected_terms_complete", expected_terms == ["fixed", "loss"], expected_terms, "real replay expects fixed/loss contract"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("cases_present", bool(cases), len(cases), "target-hidden holdout suite must include cases"),
        _check("all_cases_executed", len(replay_rows) == len(cases), len(replay_rows), "real replay should execute every case"),
        _check("no_replay_errors", not replay_errors, len(replay_errors), "real replay should not raise generation errors"),
    ]


def _summary(status: str, cases: list[dict[str, Any]], rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for row in rows if row.get("case_pass") is True)
    any_hit = sum(1 for row in rows if row.get("hit_terms"))
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_ready": status == "pass",
        "case_count": len(cases),
        "executed_case_count": len(rows),
        "passed_case_count": passed,
        "failed_case_count": len(rows) - passed,
        "any_hit_case_count": any_hit,
        "zero_hit_case_count": len(rows) - any_hit,
        "pass_rate": round(passed / len(cases), 4) if cases else 0.0,
        "holdout_model_quality_ready": status == "pass" and bool(cases) and passed == len(cases),
        "promotion_ready": False,
        "model_quality_claim": "target_hidden_holdout_replay_only",
        "next_step": "review_target_hidden_tokenizer_covered_holdout_replay_result",
        "failed_check_count": len(issues),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_inputs"
    if summary.get("holdout_model_quality_ready") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_passed_review_required"
    if int(summary.get("any_hit_case_count") or 0) > 0:
        return "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_partial_model_gap"
    return "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_zero_hit_model_gap"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Target-hidden real replay inputs failed.", "next_action": "repair_target_hidden_real_replay_inputs"}
    if summary.get("holdout_model_quality_ready") is True:
        return {"model_quality_claim": summary.get("model_quality_claim"), "reason": "The checkpoint passed every target-hidden holdout case; review remains required before promotion.", "next_action": summary.get("next_step")}
    return {"model_quality_claim": summary.get("model_quality_claim"), "reason": "The target-hidden holdout suite executed, but the checkpoint did not pass every case.", "next_action": summary.get("next_step")}


__all__ = [
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_TEXT_FILENAME",
    "build_target_hidden_tokenizer_covered_holdout_real_replay",
    "locate_target_hidden_tokenizer_covered_holdout_dry_run",
    "locate_target_hidden_tokenizer_covered_holdout_suite",
    "read_json_report",
    "resolve_exit_code",
]
