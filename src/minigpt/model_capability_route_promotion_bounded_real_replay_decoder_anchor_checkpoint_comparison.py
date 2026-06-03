from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison.html"


def locate_route_promotion_bounded_real_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def locate_decoder_anchor_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded real replay decoder anchor checkpoint comparison input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison(
    baseline_replay: dict[str, Any],
    prompt_aligned_replay: dict[str, Any],
    decoder_anchor_replay: dict[str, Any],
    decoder_anchor_training_run: dict[str, Any] | None = None,
    *,
    baseline_replay_path: str | Path | None = None,
    prompt_aligned_replay_path: str | Path | None = None,
    decoder_anchor_replay_path: str | Path | None = None,
    training_run_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor checkpoint comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    training_run = decoder_anchor_training_run or {}
    baseline_summary = as_dict(baseline_replay.get("summary"))
    prompt_summary = as_dict(prompt_aligned_replay.get("summary"))
    decoder_summary = as_dict(decoder_anchor_replay.get("summary"))
    training_summary = as_dict(training_run.get("summary"))
    case_rows = _case_rows(baseline_replay, prompt_aligned_replay, decoder_anchor_replay)
    checks = _checks(baseline_replay, prompt_aligned_replay, decoder_anchor_replay, training_run, baseline_summary, prompt_summary, decoder_summary, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    comparison = _comparison(status, baseline_summary, prompt_summary, decoder_summary, case_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, comparison),
        "failed_count": len(issues),
        "issues": issues,
        "source_baseline_replay": str(baseline_replay_path or ""),
        "source_prompt_aligned_replay": str(prompt_aligned_replay_path or ""),
        "source_decoder_anchor_replay": str(decoder_anchor_replay_path or ""),
        "source_training_run": str(training_run_path or ""),
        "baseline_summary": baseline_summary,
        "prompt_aligned_summary": prompt_summary,
        "decoder_anchor_summary": decoder_summary,
        "training_summary": training_summary,
        "case_rows": case_rows,
        "check_rows": checks,
        "comparison": comparison,
        "summary": _summary(status, checks, comparison),
        "interpretation": _interpretation(status, comparison),
    }


def resolve_exit_code(report: dict[str, Any], *, require_comparison_ready: bool, require_improvement: bool = False, require_recovery: bool = False) -> int:
    if require_comparison_ready and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_improvement and summary.get("decoder_anchor_checkpoint_improved_over_baseline") is not True:
        return 1
    if require_recovery and summary.get("decoder_anchor_checkpoint_recovered_over_prompt") is not True:
        return 1
    return 0


def _case_rows(baseline: dict[str, Any], prompt_aligned: dict[str, Any], decoder_anchor: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_rows = {str(row.get("case_id")): row for row in list_of_dicts(baseline.get("replay_rows"))}
    prompt_rows = {str(row.get("case_id")): row for row in list_of_dicts(prompt_aligned.get("replay_rows"))}
    decoder_rows = {str(row.get("case_id")): row for row in list_of_dicts(decoder_anchor.get("replay_rows"))}
    rows = []
    for case_id in sorted(set(baseline_rows) | set(prompt_rows) | set(decoder_rows)):
        baseline_row = as_dict(baseline_rows.get(case_id))
        prompt_row = as_dict(prompt_rows.get(case_id))
        decoder_row = as_dict(decoder_rows.get(case_id))
        baseline_pass = baseline_row.get("case_pass") is True
        prompt_pass = prompt_row.get("case_pass") is True
        decoder_pass = decoder_row.get("case_pass") is True
        rows.append(
            {
                "case_id": case_id,
                "baseline_pass": baseline_pass,
                "prompt_aligned_pass": prompt_pass,
                "decoder_anchor_pass": decoder_pass,
                "decoder_vs_baseline_delta": int(decoder_pass) - int(baseline_pass),
                "decoder_vs_prompt_delta": int(decoder_pass) - int(prompt_pass),
                "baseline_hit_terms": baseline_row.get("hit_terms", []),
                "baseline_missed_terms": baseline_row.get("missed_terms", []),
                "baseline_continuation": baseline_row.get("continuation", ""),
                "prompt_aligned_hit_terms": prompt_row.get("hit_terms", []),
                "prompt_aligned_missed_terms": prompt_row.get("missed_terms", []),
                "prompt_aligned_continuation": prompt_row.get("continuation", ""),
                "decoder_anchor_hit_terms": decoder_row.get("hit_terms", []),
                "decoder_anchor_missed_terms": decoder_row.get("missed_terms", []),
                "decoder_anchor_continuation": decoder_row.get("continuation", ""),
            }
        )
    return rows


def _checks(
    baseline: dict[str, Any],
    prompt_aligned: dict[str, Any],
    decoder_anchor: dict[str, Any],
    training: dict[str, Any],
    baseline_summary: dict[str, Any],
    prompt_summary: dict[str, Any],
    decoder_summary: dict[str, Any],
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    training_summary = as_dict(training.get("summary"))
    training_provided = bool(training)
    case_counts = {
        "baseline": baseline_summary.get("case_count"),
        "prompt_aligned": prompt_summary.get("case_count"),
        "decoder_anchor": decoder_summary.get("case_count"),
    }
    return [
        _check("baseline_replay_passed", baseline.get("status") == "pass", baseline.get("status"), "baseline replay execution must pass"),
        _check("prompt_aligned_replay_passed", prompt_aligned.get("status") == "pass", prompt_aligned.get("status"), "prompt-aligned replay execution must pass"),
        _check("decoder_anchor_replay_passed", decoder_anchor.get("status") == "pass", decoder_anchor.get("status"), "decoder anchor replay execution must pass"),
        _check(
            "decoder_anchor_training_ready_when_provided",
            (not training_provided) or training_summary.get("decoder_anchor_training_ready") is True,
            training_summary.get("decoder_anchor_training_ready") if training_provided else "not_provided",
            "decoder anchor training evidence is optional, but must be ready when provided",
        ),
        _check("case_counts_match", len(set(case_counts.values())) == 1, case_counts, "baseline, prompt-aligned, and decoder-anchor replay should cover the same suite"),
        _check("case_rows_present", bool(case_rows), len(case_rows), "comparison must include case rows"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _comparison(status: str, baseline_summary: dict[str, Any], prompt_summary: dict[str, Any], decoder_summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_passed = int(baseline_summary.get("passed_case_count") or 0)
    prompt_passed = int(prompt_summary.get("passed_case_count") or 0)
    decoder_passed = int(decoder_summary.get("passed_case_count") or 0)
    baseline_rate = float(baseline_summary.get("pass_rate") or 0.0)
    prompt_rate = float(prompt_summary.get("pass_rate") or 0.0)
    decoder_rate = float(decoder_summary.get("pass_rate") or 0.0)
    decoder_ready = bool(decoder_summary.get("model_route_quality_ready"))
    baseline_delta = decoder_passed - baseline_passed
    prompt_delta = decoder_passed - prompt_passed
    return {
        "ready": status == "pass",
        "baseline_passed_case_count": baseline_passed,
        "prompt_aligned_passed_case_count": prompt_passed,
        "decoder_anchor_passed_case_count": decoder_passed,
        "decoder_vs_baseline_passed_case_delta": baseline_delta,
        "decoder_vs_prompt_passed_case_delta": prompt_delta,
        "baseline_pass_rate": baseline_rate,
        "prompt_aligned_pass_rate": prompt_rate,
        "decoder_anchor_pass_rate": decoder_rate,
        "decoder_vs_baseline_pass_rate_delta": round(decoder_rate - baseline_rate, 4),
        "decoder_vs_prompt_pass_rate_delta": round(decoder_rate - prompt_rate, 4),
        "decoder_anchor_model_route_quality_ready": decoder_ready,
        "decoder_anchor_checkpoint_improved_over_baseline": baseline_delta > 0,
        "decoder_anchor_checkpoint_recovered_over_prompt": prompt_delta > 0,
        "decoder_anchor_checkpoint_regressed_from_baseline": baseline_delta < 0,
        "promotion_ready": status == "pass" and baseline_delta > 0 and decoder_ready,
        "case_count": len(case_rows),
        "next_step": _next_step(baseline_delta, prompt_delta, decoder_ready),
    }


def _summary(status: str, checks: list[dict[str, Any]], comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_decoder_anchor_checkpoint_comparison_ready": status == "pass" and comparison.get("ready") is True,
        "decoder_anchor_checkpoint_improved_over_baseline": comparison.get("decoder_anchor_checkpoint_improved_over_baseline"),
        "decoder_anchor_checkpoint_recovered_over_prompt": comparison.get("decoder_anchor_checkpoint_recovered_over_prompt"),
        "decoder_anchor_checkpoint_regressed_from_baseline": comparison.get("decoder_anchor_checkpoint_regressed_from_baseline"),
        "baseline_passed_case_count": comparison.get("baseline_passed_case_count"),
        "prompt_aligned_passed_case_count": comparison.get("prompt_aligned_passed_case_count"),
        "decoder_anchor_passed_case_count": comparison.get("decoder_anchor_passed_case_count"),
        "decoder_vs_baseline_passed_case_delta": comparison.get("decoder_vs_baseline_passed_case_delta"),
        "decoder_vs_prompt_passed_case_delta": comparison.get("decoder_vs_prompt_passed_case_delta"),
        "baseline_pass_rate": comparison.get("baseline_pass_rate"),
        "prompt_aligned_pass_rate": comparison.get("prompt_aligned_pass_rate"),
        "decoder_anchor_pass_rate": comparison.get("decoder_anchor_pass_rate"),
        "decoder_vs_baseline_pass_rate_delta": comparison.get("decoder_vs_baseline_pass_rate_delta"),
        "decoder_vs_prompt_pass_rate_delta": comparison.get("decoder_vs_prompt_pass_rate_delta"),
        "promotion_ready": comparison.get("promotion_ready"),
        "case_count": comparison.get("case_count"),
        "next_step": comparison.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, comparison: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison"
    if comparison.get("promotion_ready") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_improved_ready_for_review"
    if comparison.get("decoder_anchor_checkpoint_recovered_over_prompt") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_partially_recovered"
    if comparison.get("decoder_anchor_checkpoint_regressed_from_baseline") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_regressed_from_baseline"
    return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_no_gain"


def _interpretation(status: str, comparison: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Comparison inputs are incomplete.", "next_action": "repair decoder anchor comparison inputs"}
    if comparison.get("decoder_anchor_checkpoint_improved_over_baseline") is True:
        return {"model_quality_claim": "bounded_replay_improved", "reason": "Decoder-anchor checkpoint passed more bounded replay cases than baseline.", "next_action": comparison.get("next_step")}
    if comparison.get("decoder_anchor_checkpoint_recovered_over_prompt") is True:
        return {"model_quality_claim": "partial_recovery", "reason": "Decoder-anchor checkpoint recovered cases versus prompt-aligned checkpoint but did not beat baseline.", "next_action": comparison.get("next_step")}
    if comparison.get("decoder_anchor_checkpoint_regressed_from_baseline") is True:
        return {"model_quality_claim": "not_improved", "reason": "Decoder-anchor checkpoint did not recover the baseline bounded replay pass count.", "next_action": comparison.get("next_step")}
    return {"model_quality_claim": "not_improved", "reason": "Decoder-anchor checkpoint did not improve over prompt-aligned replay.", "next_action": comparison.get("next_step")}


def _next_step(baseline_delta: int, prompt_delta: int, decoder_ready: bool) -> str:
    if baseline_delta > 0 and decoder_ready:
        return "review_decoder_anchor_checkpoint_before_route_promotion"
    if prompt_delta > 0:
        return "continue_decoder_anchor_training_before_promotion"
    if baseline_delta < 0:
        return "diagnose_decoder_anchor_checkpoint_replay_failure_before_more_training"
    return "hold_route_promotion_and_revise_decoder_anchor_training_strategy"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_CHECKPOINT_COMPARISON_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison",
    "locate_decoder_anchor_training_run",
    "locate_route_promotion_bounded_real_replay",
    "read_json_report",
    "resolve_exit_code",
]
