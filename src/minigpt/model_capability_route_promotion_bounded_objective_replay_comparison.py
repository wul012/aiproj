from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_training_run import (
    BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator


BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_replay_comparison.json"
BOUNDED_OBJECTIVE_REPLAY_COMPARISON_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_replay_comparison.csv"
BOUNDED_OBJECTIVE_REPLAY_COMPARISON_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_replay_comparison.txt"
BOUNDED_OBJECTIVE_REPLAY_COMPARISON_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_replay_comparison.md"
BOUNDED_OBJECTIVE_REPLAY_COMPARISON_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_replay_comparison.html"

GeneratorRunner = Callable[[dict[str, Any], str | Path, str | Path, str], dict[str, Any]]


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def locate_objective_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective replay comparison input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_replay_comparison(
    objective_contract_report: dict[str, Any],
    objective_training_run_report: dict[str, Any],
    *,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    objective_contract_path: str | Path | None = None,
    objective_training_run_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective replay comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    contract_summary = as_dict(objective_contract_report.get("summary"))
    training_summary = as_dict(objective_training_run_report.get("summary"))
    contract = as_dict(objective_contract_report.get("objective_contract"))
    cases = list_of_dicts(objective_contract_report.get("contract_cases"))
    checkpoint = _resolve_checkpoint(objective_training_run_report, checkpoint_path)
    tokenizer = _resolve_tokenizer(objective_training_run_report, tokenizer_path, checkpoint)
    replay_rows, replay_errors = _run_cases(cases, checkpoint, tokenizer, device, generator_runner or _generate_case)
    replay_summary = _replay_summary(replay_rows, cases, contract)
    checks = _checks(objective_contract_report, objective_training_run_report, contract_summary, training_summary, checkpoint, tokenizer, cases, replay_rows, replay_errors)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    comparison = _comparison(status, replay_summary, contract_summary, training_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, comparison),
        "failed_count": len(issues),
        "issues": issues,
        "source_objective_contract": str(objective_contract_path or ""),
        "source_objective_training_run": str(objective_training_run_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "contract_summary": contract_summary,
        "training_summary": training_summary,
        "replay_rows": replay_rows,
        "replay_errors": replay_errors,
        "check_rows": checks,
        "comparison": comparison,
        "summary": _summary(status, checks, comparison),
        "interpretation": _interpretation(status, comparison),
    }


def resolve_exit_code(report: dict[str, Any], *, require_comparison_ready: bool, require_objective_pass: bool = False) -> int:
    if require_comparison_ready and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_objective_pass and summary.get("objective_contract_recovered") is not True:
        return 1
    return 0


def _resolve_checkpoint(training_run: dict[str, Any], override: str | Path | None) -> Path:
    if override is not None:
        return Path(override)
    run_dir = Path(str(training_run.get("run_dir") or ""))
    return run_dir / "checkpoint.pt"


def _resolve_tokenizer(training_run: dict[str, Any], override: str | Path | None, checkpoint: Path) -> Path:
    if override is not None:
        return Path(override)
    return checkpoint.parent / "tokenizer.json"


def _run_cases(
    cases: list[dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    device: str,
    runner: GeneratorRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case.get("case_id") or "")
        expected_terms = [str(term).lower() for term in case.get("required_terms", ["fixed", "loss"])]
        try:
            response = runner(case, checkpoint, tokenizer, device)
            continuation = str(response.get("continuation") or "")
            scores = _score_terms(expected_terms, continuation)
            rows.append(
                {
                    "case_id": case_id,
                    "prompt": response.get("prompt"),
                    "continuation": continuation,
                    "generated": response.get("generated"),
                    "expected_completion": case.get("expected_completion"),
                    "required_terms": expected_terms,
                    "hit_terms": scores["hit_terms"],
                    "missed_terms": scores["missed_terms"],
                    "case_pass": scores["case_pass"],
                    "any_hit": bool(scores["hit_terms"]),
                    "max_new_tokens": response.get("max_new_tokens"),
                    "temperature": response.get("temperature"),
                    "top_k": response.get("top_k"),
                    "seed": response.get("seed"),
                }
            )
        except Exception as exc:  # pragma: no cover - covered through fake runner behavior.
            errors.append({"case_id": case_id, "error": type(exc).__name__, "message": str(exc)})
    return rows, errors


def _generate_case(case: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    request = GenerationRequest(
        prompt=str(case.get("prompt") or ""),
        max_new_tokens=8,
        temperature=0.2,
        top_k=20,
        seed=1839,
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _score_terms(expected_terms: list[str], continuation: str) -> dict[str, Any]:
    lowered = continuation.lower()
    hits = [term for term in expected_terms if term in lowered]
    missed = [term for term in expected_terms if term not in hits]
    return {"hit_terms": hits, "missed_terms": missed, "case_pass": bool(expected_terms) and not missed}


def _replay_summary(rows: list[dict[str, Any]], cases: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    passed = [row for row in rows if row.get("case_pass") is True]
    any_hit = [row for row in rows if row.get("any_hit") is True]
    canonical = [row for row in rows if row.get("case_id") == "canonical_direct_completion"]
    return {
        "case_count": len(cases),
        "executed_case_count": len(rows),
        "passed_case_count": len(passed),
        "failed_case_count": len(rows) - len(passed),
        "any_hit_case_count": len(any_hit),
        "zero_hit_case_count": sum(1 for row in rows if row.get("any_hit") is not True),
        "canonical_case_pass": bool(canonical) and canonical[0].get("case_pass") is True,
        "objective_contract_recovered": bool(cases) and len(passed) == len(cases),
        "pass_rate": round(len(passed) / len(cases), 4) if cases else 0.0,
        "required_exact_completion": contract.get("required_exact_completion"),
    }


def _checks(
    contract_report: dict[str, Any],
    training_report: dict[str, Any],
    contract_summary: dict[str, Any],
    training_summary: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    cases: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    replay_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("contract_passed", contract_report.get("status") == "pass", contract_report.get("status"), "objective contract must pass"),
        _check("contract_ready", contract_summary.get("bounded_objective_contract_ready") is True, contract_summary.get("bounded_objective_contract_ready"), "objective contract must be ready"),
        _check("training_passed", training_report.get("status") == "pass", training_report.get("status"), "objective training evidence must pass"),
        _check("training_ready", training_summary.get("bounded_objective_training_ready") is True, training_summary.get("bounded_objective_training_ready"), "objective training must be ready"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("cases_present", bool(cases), len(cases), "objective contract must provide replay cases"),
        _check("all_cases_executed", len(replay_rows) == len(cases), len(replay_rows), "objective replay should execute every contract case"),
        _check("no_replay_errors", not replay_errors, len(replay_errors), "objective replay should not raise generation errors"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _comparison(status: str, replay_summary: dict[str, Any], contract_summary: dict[str, Any], training_summary: dict[str, Any]) -> dict[str, Any]:
    recovered = replay_summary.get("objective_contract_recovered") is True
    return {
        "ready": status == "pass",
        "case_count": replay_summary.get("case_count"),
        "executed_case_count": replay_summary.get("executed_case_count"),
        "passed_case_count": replay_summary.get("passed_case_count"),
        "failed_case_count": replay_summary.get("failed_case_count"),
        "any_hit_case_count": replay_summary.get("any_hit_case_count"),
        "zero_hit_case_count": replay_summary.get("zero_hit_case_count"),
        "canonical_case_pass": replay_summary.get("canonical_case_pass"),
        "pass_rate": replay_summary.get("pass_rate"),
        "objective_contract_recovered": recovered,
        "unchanged_suite_check_required": contract_summary.get("unchanged_suite_check_required") is True,
        "promotion_ready": False,
        "final_train_loss": training_summary.get("final_train_loss"),
        "final_val_loss": training_summary.get("final_val_loss"),
        "train_loss_delta": training_summary.get("train_loss_delta"),
        "next_step": _next_step(recovered, int(replay_summary.get("any_hit_case_count") or 0)),
    }


def _summary(status: str, checks: list[dict[str, Any]], comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_replay_comparison_ready": status == "pass" and comparison.get("ready") is True,
        "objective_contract_recovered": comparison.get("objective_contract_recovered") if status == "pass" else False,
        "canonical_case_pass": comparison.get("canonical_case_pass") if status == "pass" else False,
        "case_count": comparison.get("case_count"),
        "executed_case_count": comparison.get("executed_case_count"),
        "passed_case_count": comparison.get("passed_case_count"),
        "failed_case_count": comparison.get("failed_case_count"),
        "any_hit_case_count": comparison.get("any_hit_case_count"),
        "zero_hit_case_count": comparison.get("zero_hit_case_count"),
        "pass_rate": comparison.get("pass_rate"),
        "promotion_ready": False,
        "next_step": comparison.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, comparison: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_objective_replay_comparison"
    if comparison.get("objective_contract_recovered") is True:
        return "model_capability_route_promotion_bounded_objective_replay_contract_recovered_holdout_required"
    if int(comparison.get("any_hit_case_count") or 0) > 0:
        return "model_capability_route_promotion_bounded_objective_replay_partial_required_term_hit"
    return "model_capability_route_promotion_bounded_objective_replay_zero_hit"


def _interpretation(status: str, comparison: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Objective replay inputs or execution failed.", "next_action": "repair objective replay inputs"}
    if comparison.get("objective_contract_recovered") is True:
        return {
            "model_quality_claim": "objective_contract_recovered_only",
            "reason": "The checkpoint passed the objective contract cases, but unchanged v803 holdout remains required before route promotion.",
            "next_action": "run_unchanged_bounded_suite_holdout_replay",
        }
    if int(comparison.get("any_hit_case_count") or 0) > 0:
        return {
            "model_quality_claim": "partial_required_term_signal",
            "reason": "At least one objective case hit a required term, but the contract was not recovered.",
            "next_action": comparison.get("next_step"),
        }
    return {
        "model_quality_claim": "not_improved",
        "reason": "The trained checkpoint produced zero required-term hits on the objective contract replay.",
        "next_action": comparison.get("next_step"),
    }


def _next_step(recovered: bool, any_hit_count: int) -> str:
    if recovered:
        return "run_unchanged_bounded_suite_holdout_replay"
    if any_hit_count > 0:
        return "diagnose_bounded_objective_partial_hit_before_more_training"
    return "diagnose_bounded_objective_replay_zero_hit_before_more_training"


__all__ = [
    "BOUNDED_OBJECTIVE_REPLAY_COMPARISON_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_REPLAY_COMPARISON_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_REPLAY_COMPARISON_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_REPLAY_COMPARISON_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_replay_comparison",
    "locate_objective_contract",
    "locate_objective_training_run",
    "read_json_report",
    "resolve_exit_code",
]
