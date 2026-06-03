from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay import MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison.html"


def locate_route_promotion_bounded_real_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def locate_rebalanced_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("rebalanced checkpoint comparison input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison(
    baseline_replay: dict[str, Any],
    prompt_aligned_replay: dict[str, Any],
    decoder_anchor_replay: dict[str, Any],
    rebalanced_replay: dict[str, Any],
    rebalanced_training: dict[str, Any] | None = None,
    *,
    baseline_replay_path: str | Path | None = None,
    prompt_aligned_replay_path: str | Path | None = None,
    decoder_anchor_replay_path: str | Path | None = None,
    rebalanced_replay_path: str | Path | None = None,
    rebalanced_training_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced checkpoint comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    route_rows = [
        _route("baseline", baseline_replay),
        _route("prompt_aligned", prompt_aligned_replay),
        _route("decoder_anchor", decoder_anchor_replay),
        _route("rebalanced", rebalanced_replay),
    ]
    training_summary = as_dict((rebalanced_training or {}).get("summary"))
    checks = _checks(route_rows, rebalanced_training)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    comparison = _comparison(status, route_rows, training_summary)
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
        "source_rebalanced_replay": str(rebalanced_replay_path or ""),
        "source_rebalanced_training": str(rebalanced_training_path or ""),
        "route_rows": route_rows,
        "training_summary": training_summary,
        "check_rows": checks,
        "checkpoint_comparison": comparison,
        "summary": _summary(status, checks, comparison),
        "interpretation": _interpretation(status, comparison),
    }


def resolve_exit_code(report: dict[str, Any], *, require_comparison_ready: bool, require_improvement: bool) -> int:
    summary = as_dict(report.get("summary"))
    if require_comparison_ready and report.get("status") != "pass":
        return 1
    if require_improvement and summary.get("rebalanced_checkpoint_improved_over_baseline") is not True:
        return 1
    return 0


def _route(label: str, replay: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    return {
        "label": label,
        "status": replay.get("status"),
        "executed": summary.get("bounded_real_replay_executed"),
        "case_count": int(summary.get("case_count") or 0),
        "passed_case_count": int(summary.get("passed_case_count") or 0),
        "failed_case_count": int(summary.get("failed_case_count") or 0),
        "pass_rate": float(summary.get("pass_rate") or 0.0),
        "model_route_quality_ready": summary.get("model_route_quality_ready"),
    }


def _checks(route_rows: list[dict[str, Any]], training: dict[str, Any] | None) -> list[dict[str, Any]]:
    training_summary = as_dict((training or {}).get("summary"))
    return [
        *[_check(f"{row['label']}_replay_passed", row.get("status") == "pass", row.get("status"), f"{row['label']} replay must pass") for row in route_rows],
        *[_check(f"{row['label']}_replay_executed", row.get("executed") is True, row.get("executed"), f"{row['label']} replay must execute") for row in route_rows],
        _check("rebalanced_training_ready", training is None or training_summary.get("decoder_anchor_rebalanced_training_ready") is True, training_summary.get("decoder_anchor_rebalanced_training_ready"), "optional rebalanced training evidence must be ready"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _comparison(status: str, route_rows: list[dict[str, Any]], training_summary: dict[str, Any]) -> dict[str, Any]:
    by_label = {str(row.get("label")): row for row in route_rows}
    baseline = by_label["baseline"]
    prompt = by_label["prompt_aligned"]
    decoder = by_label["decoder_anchor"]
    rebalanced = by_label["rebalanced"]
    return {
        "ready": status == "pass",
        "baseline_passed_case_count": baseline.get("passed_case_count"),
        "prompt_aligned_passed_case_count": prompt.get("passed_case_count"),
        "decoder_anchor_passed_case_count": decoder.get("passed_case_count"),
        "rebalanced_passed_case_count": rebalanced.get("passed_case_count"),
        "rebalanced_vs_baseline_pass_rate_delta": round(float(rebalanced.get("pass_rate") or 0.0) - float(baseline.get("pass_rate") or 0.0), 4),
        "rebalanced_vs_prompt_pass_rate_delta": round(float(rebalanced.get("pass_rate") or 0.0) - float(prompt.get("pass_rate") or 0.0), 4),
        "rebalanced_vs_decoder_anchor_pass_rate_delta": round(float(rebalanced.get("pass_rate") or 0.0) - float(decoder.get("pass_rate") or 0.0), 4),
        "rebalanced_checkpoint_improved_over_baseline": float(rebalanced.get("pass_rate") or 0.0) > float(baseline.get("pass_rate") or 0.0),
        "rebalanced_checkpoint_recovered_over_prompt": float(rebalanced.get("pass_rate") or 0.0) > float(prompt.get("pass_rate") or 0.0),
        "rebalanced_checkpoint_recovered_over_decoder_anchor": float(rebalanced.get("pass_rate") or 0.0) > float(decoder.get("pass_rate") or 0.0),
        "promotion_ready": rebalanced.get("model_route_quality_ready") is True,
        "final_val_loss": training_summary.get("final_val_loss"),
        "next_step": "diagnose_rebalanced_checkpoint_replay_failure_before_more_training" if status == "pass" else "repair_rebalanced_checkpoint_comparison_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "rebalanced_checkpoint_comparison_ready": status == "pass" and comparison.get("ready") is True,
        "baseline_passed_case_count": comparison.get("baseline_passed_case_count"),
        "prompt_aligned_passed_case_count": comparison.get("prompt_aligned_passed_case_count"),
        "decoder_anchor_passed_case_count": comparison.get("decoder_anchor_passed_case_count"),
        "rebalanced_passed_case_count": comparison.get("rebalanced_passed_case_count"),
        "rebalanced_vs_baseline_pass_rate_delta": comparison.get("rebalanced_vs_baseline_pass_rate_delta"),
        "rebalanced_vs_prompt_pass_rate_delta": comparison.get("rebalanced_vs_prompt_pass_rate_delta"),
        "rebalanced_vs_decoder_anchor_pass_rate_delta": comparison.get("rebalanced_vs_decoder_anchor_pass_rate_delta"),
        "rebalanced_checkpoint_improved_over_baseline": comparison.get("rebalanced_checkpoint_improved_over_baseline"),
        "rebalanced_checkpoint_recovered_over_prompt": comparison.get("rebalanced_checkpoint_recovered_over_prompt"),
        "rebalanced_checkpoint_recovered_over_decoder_anchor": comparison.get("rebalanced_checkpoint_recovered_over_decoder_anchor"),
        "promotion_ready": comparison.get("promotion_ready"),
        "next_step": comparison.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, comparison: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison"
    if comparison.get("rebalanced_checkpoint_improved_over_baseline") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_improved_over_baseline"
    if comparison.get("rebalanced_checkpoint_recovered_over_decoder_anchor") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_partial_recovery"
    return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_still_regressed_from_baseline"


def _interpretation(status: str, comparison: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Rebalanced checkpoint comparison inputs are incomplete.", "next_action": "repair comparison inputs"}
    if comparison.get("rebalanced_checkpoint_improved_over_baseline") is True:
        return {"model_quality_claim": "candidate_improved", "reason": "Rebalanced replay exceeds the baseline pass rate.", "next_action": comparison.get("next_step")}
    return {"model_quality_claim": "not_improved", "reason": "Rebalanced replay does not exceed the baseline pass rate.", "next_action": comparison.get("next_step")}


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison",
    "locate_rebalanced_training_run",
    "locate_route_promotion_bounded_real_replay",
    "read_json_report",
    "resolve_exit_code",
]
