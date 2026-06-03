from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_route_promotion_bounded_benchmark_dry_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_review import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay.html"

GeneratorRunner = Callable[[dict[str, Any], str | Path, str | Path, str], dict[str, Any]]


def locate_route_promotion_bounded_benchmark_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME
    return source


def locate_route_promotion_bounded_benchmark_suite_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME
    return source


def locate_route_promotion_bounded_benchmark_dry_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion bounded real replay input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay(
    suite_review: dict[str, Any],
    benchmark_suite_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    suite_review_path: str | Path | None = None,
    benchmark_suite_path: str | Path | None = None,
    dry_run_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay",
    generated_at: str | None = None,
) -> dict[str, Any]:
    checkpoint = Path(checkpoint_path)
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else checkpoint.parent / "tokenizer.json"
    suite = as_dict(benchmark_suite_report.get("benchmark_suite"))
    cases = list_of_dicts(suite.get("cases"))
    replay_rows, replay_errors = _run_cases(cases, checkpoint, tokenizer, device, generator_runner or _generate_case)
    checks = _checks(suite_review, benchmark_suite_report, dry_run_report, checkpoint, tokenizer, cases, replay_rows, replay_errors)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    model_summary = _model_summary(replay_rows, cases)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, model_summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_suite_review": str(suite_review_path or ""),
        "source_benchmark_suite": str(benchmark_suite_path or ""),
        "source_dry_run": str(dry_run_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "replay_rows": replay_rows,
        "replay_errors": replay_errors,
        "check_rows": checks,
        "summary": _summary(status, checks, model_summary),
        "interpretation": _interpretation(status, model_summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_execution_pass: bool, require_model_pass: bool = False) -> int:
    if require_execution_pass and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_model_pass and summary.get("model_route_quality_ready") is not True:
        return 1
    return 0


def _run_cases(
    cases: list[dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    device: str,
    runner: GeneratorRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row in cases:
        case_id = str(row.get("case_id") or "")
        expected_terms = [str(term) for term in row.get("expected_terms", [])]
        try:
            response = runner(row, checkpoint, tokenizer, device)
            continuation = str(response.get("continuation") or "")
            scores = _score_terms(expected_terms, continuation)
            rows.append(
                {
                    "case_id": case_id,
                    "prompt": response.get("prompt"),
                    "continuation": continuation,
                    "generated": response.get("generated"),
                    "expected_terms": expected_terms,
                    "hit_terms": scores["hit_terms"],
                    "missed_terms": scores["missed_terms"],
                    "case_pass": scores["case_pass"],
                    "seed": response.get("seed"),
                    "max_new_tokens": response.get("max_new_tokens"),
                    "temperature": response.get("temperature"),
                    "top_k": response.get("top_k"),
                }
            )
        except Exception as exc:  # pragma: no cover - exercised through fake runner tests.
            errors.append({"case_id": case_id, "error": type(exc).__name__, "message": str(exc)})
    return rows, errors


def _generate_case(row: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    prompt_case = as_dict(row.get("prompt_case"))
    request = GenerationRequest(
        prompt=str(prompt_case.get("prompt") or ""),
        max_new_tokens=int(prompt_case.get("max_new_tokens") or 24),
        temperature=float(prompt_case.get("temperature") or 0.2),
        top_k=None if prompt_case.get("top_k") in {None, "", 0, "0"} else int(prompt_case.get("top_k")),
        seed=None if prompt_case.get("seed") in {None, ""} else int(prompt_case.get("seed")),
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _score_terms(expected_terms: list[str], continuation: str) -> dict[str, Any]:
    lowered = continuation.lower()
    hits = [term for term in expected_terms if term.lower() in lowered]
    missed = [term for term in expected_terms if term not in hits]
    return {"hit_terms": hits, "missed_terms": missed, "case_pass": bool(expected_terms) and not missed}


def _checks(
    suite_review: dict[str, Any],
    benchmark_suite_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    cases: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    replay_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    dry_summary = as_dict(dry_run_report.get("summary"))
    review_summary = as_dict(suite_review.get("summary"))
    return [
        _check("suite_review_passed", suite_review.get("status") == "pass", suite_review.get("status"), "suite review must pass before real replay"),
        _check("suite_review_approved", review_summary.get("approved_for_execution") is True, review_summary.get("approved_for_execution"), "suite review must approve real replay"),
        _check("benchmark_suite_passed", benchmark_suite_report.get("status") == "pass", benchmark_suite_report.get("status"), "benchmark suite must pass"),
        _check("dry_run_passed", dry_run_report.get("status") == "pass", dry_run_report.get("status"), "dry-run scorer must pass before real replay"),
        _check("dry_run_ready", dry_summary.get("bounded_benchmark_dry_run_ready") is True, dry_summary.get("bounded_benchmark_dry_run_ready"), "dry-run summary must be ready"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("cases_present", bool(cases), len(cases), "benchmark suite must provide replay cases"),
        _check("all_cases_executed", len(replay_rows) == len(cases), len(replay_rows), "real replay should execute every case"),
        _check("no_replay_errors", not replay_errors, len(replay_errors), "real replay should not raise generation errors"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _model_summary(replay_rows: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    passed_rows = [row for row in replay_rows if row.get("case_pass") is True]
    return {
        "case_count": len(cases),
        "executed_case_count": len(replay_rows),
        "passed_case_count": len(passed_rows),
        "failed_case_count": len(replay_rows) - len(passed_rows),
        "model_route_quality_ready": bool(cases) and len(passed_rows) == len(cases),
        "pass_rate": round(len(passed_rows) / len(cases), 4) if cases else 0.0,
    }


def _summary(status: str, checks: list[dict[str, Any]], model_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_real_replay_executed": status == "pass",
        "model_route_quality_ready": model_summary["model_route_quality_ready"] if status == "pass" else False,
        "case_count": model_summary["case_count"],
        "executed_case_count": model_summary["executed_case_count"],
        "passed_case_count": model_summary["passed_case_count"],
        "failed_case_count": model_summary["failed_case_count"],
        "pass_rate": model_summary["pass_rate"],
        "next_step": "review_bounded_route_promotion_real_replay" if status == "pass" else "repair_real_replay_inputs",
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, model_summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_inputs"
    if model_summary["model_route_quality_ready"]:
        return "model_capability_route_promotion_bounded_real_replay_passed"
    return "model_capability_route_promotion_bounded_real_replay_completed_with_model_gaps"


def _interpretation(status: str, model_summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Real replay inputs or execution failed.", "next_action": "repair replay inputs"}
    if model_summary["model_route_quality_ready"]:
        return {"model_quality_claim": "bounded_suite_passed", "reason": "Every bounded replay case generated both required terms.", "next_action": "review replay evidence before any stronger claim"}
    return {
        "model_quality_claim": "bounded_replay_partial_only",
        "reason": "Replay executed, but at least one case missed a required term.",
        "next_action": "review missed cases before promoting model capability",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay",
    "locate_route_promotion_bounded_benchmark_dry_run",
    "locate_route_promotion_bounded_benchmark_suite",
    "locate_route_promotion_bounded_benchmark_suite_review",
    "read_json_report",
    "resolve_exit_code",
]
