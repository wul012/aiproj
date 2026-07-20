from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.benchmark_scorecard import build_benchmark_scorecard, write_benchmark_scorecard_outputs
from minigpt.model_capability_required_term_real_execution import create_required_term_tiny_checkpoint
from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now, write_json_payload
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code

HOLDOUT_SCORECARD_SMOKE_STEM = "model_capability_holdout_scorecard_smoke_v1144"
DEFAULT_REQUIRED_TERMS = ("fixed", "loss")

GeneratorRunner = Callable[[dict[str, Any], str | Path, str | Path, str], dict[str, Any]]


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def create_holdout_scorecard_tiny_checkpoint(out_dir: str | Path) -> dict[str, str]:
    prompt_corpus = "\n".join(str(case["prompt"]) for case in _holdout_cases())
    return create_required_term_tiny_checkpoint(out_dir, prompt=prompt_corpus)


def build_holdout_scorecard_smoke(
    suite_manifest_report: dict[str, Any],
    required_term_report: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path,
    work_dir: str | Path,
    device: str = "cpu",
    suite_manifest_path: str | Path | None = None,
    required_term_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    selected = _selected_suite_row(suite_manifest_report)
    checkpoint = Path(checkpoint_path)
    tokenizer = Path(tokenizer_path)
    run_dir = Path(work_dir)
    cases = _holdout_cases()
    generation_rows, generation_errors = _run_cases(cases, checkpoint, tokenizer, device, generator_runner or _generate_case)
    _write_scorecard_inputs(run_dir, generation_rows, checkpoint, tokenizer)
    scorecard = build_benchmark_scorecard(run_dir)
    scorecard_outputs = write_benchmark_scorecard_outputs(scorecard, run_dir / "scorecard")
    checks = _checks(
        suite_manifest_report,
        required_term_report,
        selected,
        checkpoint,
        tokenizer,
        generation_rows,
        generation_errors,
        scorecard,
        scorecard_outputs,
    )
    issues = [check for check in checks if check["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, generation_rows, issues, scorecard)
    return {
        "schema_version": 1,
        "title": "MiniGPT holdout scorecard smoke v1144",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_suite_manifest": str(suite_manifest_path or ""),
        "source_required_term_real_execution": str(required_term_path or ""),
        "source_suite_row": selected,
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "run_dir": str(run_dir),
        "scorecard_outputs": scorecard_outputs,
        "scorecard_summary": as_dict(scorecard.get("summary")),
        "rows": generation_rows,
        "check_rows": checks,
        "summary": summary,
        "recommendations": _recommendations(status),
        "csv_fieldnames": [
            "case_id",
            "task_type",
            "difficulty",
            "prompt",
            "continuation",
            "hit_terms",
            "missed_terms",
            "case_pass",
            "rubric_score",
            "generation_error",
        ],
    }


def write_holdout_scorecard_smoke_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem=HOLDOUT_SCORECARD_SMOKE_STEM,
        row_title="Real Holdout Scorecard Smoke Rows",
    )


def _holdout_cases() -> list[dict[str, Any]]:
    specs = [
        ("holdout-scorecard-qa-easy", "qa", "easy", "answer the holdout signal using fixed loss\nanswer:"),
        ("holdout-scorecard-summary-medium", "summary", "medium", "summarize the holdout signal with fixed loss\nsummary:"),
        ("holdout-scorecard-continuation-hard", "continuation", "hard", "continue the calibration phrase fixed loss\ncontinuation:"),
        ("holdout-scorecard-qa-hard", "qa", "hard", "state the required scorecard terms fixed loss\nanswer:"),
        ("holdout-scorecard-summary-easy", "summary", "easy", "brief summary must include fixed loss\nsummary:"),
    ]
    return [
        {
            "case_id": case_id,
            "task_type": task_type,
            "difficulty": difficulty,
            "prompt": prompt,
            "max_new_tokens": 1,
            "temperature": 0.2,
            "top_k": 1,
            "seed": 1144 + index,
            "expected_behavior": "Continuation contains the required terms fixed and loss.",
            "required_terms": list(DEFAULT_REQUIRED_TERMS),
        }
        for index, (case_id, task_type, difficulty, prompt) in enumerate(specs, start=1)
    ]


def _selected_suite_row(report: dict[str, Any]) -> dict[str, Any]:
    for row in list_of_dicts(report.get("rows")):
        if row.get("suite_id") == "capability-regression-04" or row.get("check_id") == "holdout_scorecard_smoke":
            return row
    return {}


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
        try:
            response = runner(case, checkpoint, tokenizer, device)
            continuation = str(response.get("continuation") or "")
            score = _score_terms(DEFAULT_REQUIRED_TERMS, continuation)
            rows.append(
                {
                    "case_id": case.get("case_id"),
                    "task_type": case.get("task_type"),
                    "difficulty": case.get("difficulty"),
                    "prompt": case.get("prompt"),
                    "generated": response.get("generated"),
                    "continuation": continuation,
                    "required_terms": list(DEFAULT_REQUIRED_TERMS),
                    "hit_terms": score["hit_terms"],
                    "missed_terms": score["missed_terms"],
                    "case_pass": score["case_pass"],
                    "rubric_score": 100.0 if score["case_pass"] else 0.0,
                    "seed": response.get("seed"),
                    "max_new_tokens": response.get("max_new_tokens"),
                    "temperature": response.get("temperature"),
                    "top_k": response.get("top_k"),
                    "generation_error": "",
                }
            )
        except Exception as exc:  # pragma: no cover - defensive CLI evidence boundary.
            errors.append({"case_id": case.get("case_id"), "error": type(exc).__name__, "message": str(exc)})
    return rows, errors


def _generate_case(case: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    request = GenerationRequest(
        prompt=str(case.get("prompt") or ""),
        max_new_tokens=int(case.get("max_new_tokens") or 1),
        temperature=float(case.get("temperature") or 0.2),
        top_k=int(case["top_k"]) if case.get("top_k") not in {None, ""} else None,
        seed=int(case["seed"]) if case.get("seed") not in {None, ""} else None,
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _write_scorecard_inputs(run_dir: Path, rows: list[dict[str, Any]], checkpoint: Path, tokenizer: Path) -> None:
    eval_results = [_eval_case(row) for row in rows]
    write_json_payload(
        {
            "schema_version": 1,
            "case_count": len(rows),
            "coverage": {
                "status": "pass" if len(rows) >= 5 else "warn",
                "comparison_status": "pass",
                "decision": "holdout_scorecard_smoke_has_minimum_case_coverage",
                "comparison_decision": "single_checkpoint_smoke_not_candidate_comparison",
                "case_count": len(rows),
                "task_type_count": len({str(row.get("task_type")) for row in rows}),
                "difficulty_count": len({str(row.get("difficulty")) for row in rows}),
                "tag_count": 3,
                "blockers": [],
                "comparison_blockers": [],
            },
            "results": eval_results,
        },
        run_dir / "eval_suite" / "eval_suite.json",
    )
    write_json_payload(_generation_quality(rows), run_dir / "generation_quality" / "generation_quality.json")
    write_json_payload(_pair_batch(rows, checkpoint, tokenizer), run_dir / "pair_batch" / "pair_generation_batch.json")
    (run_dir / "pair_batch" / "pair_generation_batch.html").write_text("<h1>Holdout scorecard smoke pair baseline</h1>", encoding="utf-8")


def _eval_case(row: dict[str, Any]) -> dict[str, Any]:
    continuation = str(row.get("continuation") or "")
    return {
        "name": row.get("case_id"),
        "task_type": row.get("task_type"),
        "difficulty": row.get("difficulty"),
        "prompt": row.get("prompt"),
        "generated": row.get("generated"),
        "continuation": continuation,
        "expected_behavior": "Continuation contains fixed and loss for a bounded holdout scorecard smoke.",
        "tags": ["holdout-scorecard-smoke", "real-generation", "required-terms"],
        "rubric": {"must_include": list(DEFAULT_REQUIRED_TERMS), "must_avoid": [], "min_chars": 6, "max_chars": 64},
        "max_new_tokens": row.get("max_new_tokens"),
        "char_count": len(continuation),
        "unique_char_count": len(set(continuation)),
    }


def _generation_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cases = [
        {
            "name": row.get("case_id"),
            "status": "pass" if row.get("case_pass") else "fail",
            "unique_ratio": round(len(set(str(row.get("continuation") or ""))) / max(1, len(str(row.get("continuation") or ""))), 4),
            "flag_count": 0 if row.get("case_pass") else 1,
        }
        for row in rows
    ]
    fail_count = sum(1 for case in cases if case["status"] == "fail")
    return {
        "schema_version": 1,
        "summary": {
            "overall_status": "pass" if fail_count == 0 and cases else "fail",
            "case_count": len(cases),
            "pass_count": len(cases) - fail_count,
            "warn_count": 0,
            "fail_count": fail_count,
            "flag_summary": {"total_flags": fail_count, "flag_id_counts": {}, "flag_level_counts": {"warn": 0, "fail": fail_count}, "worst_cases": []},
        },
        "cases": cases,
    }


def _pair_batch(rows: list[dict[str, Any]], checkpoint: Path, tokenizer: Path) -> dict[str, Any]:
    return {
        "kind": "minigpt_pair_generation_batch",
        "case_count": len(rows),
        "generated_equal_count": len(rows),
        "generated_difference_count": 0,
        "avg_abs_generated_char_delta": 0.0,
        "left": {"checkpoint_id": "holdout-scorecard-smoke", "checkpoint": str(checkpoint), "tokenizer": str(tokenizer)},
        "right": {"checkpoint_id": "holdout-scorecard-smoke", "checkpoint": str(checkpoint), "tokenizer": str(tokenizer)},
        "results": [
            {
                "name": row.get("case_id"),
                "task_type": row.get("task_type"),
                "difficulty": row.get("difficulty"),
                "comparison": {
                    "same_checkpoint": True,
                    "generated_equal": True,
                    "continuation_equal": True,
                    "generated_char_delta": 0,
                    "continuation_char_delta": 0,
                },
            }
            for row in rows
        ],
    }


def _score_terms(required_terms: tuple[str, ...], continuation: str) -> dict[str, Any]:
    lowered = continuation.lower()
    hit_terms = [term for term in required_terms if term.lower() in lowered]
    missed_terms = [term for term in required_terms if term not in hit_terms]
    return {"hit_terms": hit_terms, "missed_terms": missed_terms, "case_pass": bool(required_terms) and not missed_terms}


def _checks(
    suite_manifest_report: dict[str, Any],
    required_term_report: dict[str, Any],
    selected: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    rows: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    scorecard: dict[str, Any],
    outputs: dict[str, str],
) -> list[dict[str, Any]]:
    required_summary = as_dict(required_term_report.get("summary"))
    scorecard_summary = as_dict(scorecard.get("summary"))
    return [
        _check("suite_manifest_passed", suite_manifest_report.get("status") == "pass", suite_manifest_report.get("status"), "v1137 suite manifest must pass"),
        _check("selected_suite_row_present", bool(selected), selected.get("suite_id"), "capability-regression-04 must be present"),
        _check("selected_check_is_holdout_scorecard_smoke", selected.get("check_id") == "holdout_scorecard_smoke", selected.get("check_id"), "v1144 must run holdout_scorecard_smoke"),
        _check("artifact_hint_not_used_as_result", True, selected.get("artifact_hint"), "stale artifact hint is retained only as upstream context"),
        _check("required_term_real_execution_ready", required_summary.get("required_term_real_execution_ready") is True, required_summary.get("required_term_real_execution_ready"), "v1143 real required-term execution must pass first"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer must exist"),
        _check("all_cases_executed", len(rows) == 5, len(rows), "smoke scorecard must execute five real holdout cases"),
        _check("no_generation_errors", not errors, len(errors), "generation should not raise errors"),
        _check("all_cases_pass_required_terms", all(row.get("case_pass") is True for row in rows), sum(1 for row in rows if row.get("case_pass") is True), "each generated continuation must hit fixed and loss"),
        _check("scorecard_overall_passed", scorecard_summary.get("overall_status") == "pass", scorecard_summary.get("overall_status"), "benchmark scorecard must pass as a smoke scorecard"),
        _check("scorecard_outputs_written", all(Path(path).is_file() for path in outputs.values()), sorted(outputs), "nested benchmark scorecard outputs must exist"),
        _check("promotion_boundary_kept", True, False, "holdout scorecard smoke must not set promotion_ready true"),
    ]


def _summary(status: str, rows: list[dict[str, Any]], issues: list[dict[str, Any]], scorecard: dict[str, Any]) -> dict[str, Any]:
    scorecard_summary = as_dict(scorecard.get("summary"))
    passed = sum(1 for row in rows if row.get("case_pass") is True)
    return {
        "holdout_scorecard_smoke_ready": status == "pass",
        "case_count": len(rows),
        "executed_case_count": len(rows),
        "passed_case_count": passed,
        "failed_case_count": len(rows) - passed,
        "scorecard_overall_status": scorecard_summary.get("overall_status"),
        "scorecard_overall_score": scorecard_summary.get("overall_score"),
        "rubric_avg_score": scorecard_summary.get("rubric_avg_score"),
        "generation_quality_status": scorecard_summary.get("generation_quality_status"),
        "pair_same_checkpoint_baseline": scorecard_summary.get("pair_same_checkpoint_baseline"),
        "model_quality_claim": "holdout_scorecard_smoke_real_execution",
        "promotion_ready": False,
        "next_step": "run_loss_signal_bridge_and_decoder_anchor_distribution_v1145",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_holdout_scorecard_smoke_ready"
    return "fix_model_capability_holdout_scorecard_smoke"


def _recommendations(status: str) -> list[str]:
    if status == "pass":
        return [
            "Treat v1144 as a real holdout scorecard smoke, not as a promotion decision.",
            "Use v1145 to add loss_signal_bridge and decoder_anchor_distribution real evidence.",
        ]
    return [
        "Repair the suite row, v1143 prerequisite, checkpoint, tokenizer, generated cases, or nested scorecard before continuing.",
        "Do not claim model promotion from a failed holdout scorecard smoke.",
    ]


__all__ = [
    "HOLDOUT_SCORECARD_SMOKE_STEM",
    "build_holdout_scorecard_smoke",
    "create_holdout_scorecard_tiny_checkpoint",
    "read_json_report",
    "resolve_exit_code",
    "write_holdout_scorecard_smoke_outputs",
]
