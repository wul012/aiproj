from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison.html"


def locate_route_promotion_bounded_real_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def locate_repair_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded real replay repair checkpoint comparison input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison(
    baseline_replay: dict[str, Any],
    repair_replay: dict[str, Any],
    training_run: dict[str, Any] | None = None,
    *,
    baseline_replay_path: str | Path | None = None,
    repair_replay_path: str | Path | None = None,
    training_run_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay repair checkpoint comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    training_run = training_run or {}
    baseline_summary = as_dict(baseline_replay.get("summary"))
    repair_summary = as_dict(repair_replay.get("summary"))
    training_summary = as_dict(training_run.get("summary"))
    case_rows = _case_rows(baseline_replay, repair_replay)
    checks = _checks(baseline_replay, repair_replay, training_run, baseline_summary, repair_summary, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    comparison = _comparison(status, baseline_summary, repair_summary, case_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, comparison),
        "failed_count": len(issues),
        "issues": issues,
        "source_baseline_replay": str(baseline_replay_path or ""),
        "source_repair_replay": str(repair_replay_path or ""),
        "source_training_run": str(training_run_path or ""),
        "baseline_summary": baseline_summary,
        "repair_summary": repair_summary,
        "training_summary": training_summary,
        "case_rows": case_rows,
        "check_rows": checks,
        "comparison": comparison,
        "summary": _summary(status, checks, comparison),
        "interpretation": _interpretation(status, comparison),
    }


def resolve_exit_code(report: dict[str, Any], *, require_comparison_ready: bool, require_improvement: bool = False) -> int:
    if require_comparison_ready and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_improvement and summary.get("repair_checkpoint_improved") is not True:
        return 1
    return 0


def _case_rows(baseline: dict[str, Any], repair: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_rows = {str(row.get("case_id")): row for row in list_of_dicts(baseline.get("replay_rows"))}
    repair_rows = {str(row.get("case_id")): row for row in list_of_dicts(repair.get("replay_rows"))}
    rows = []
    for case_id in sorted(set(baseline_rows) | set(repair_rows)):
        left = as_dict(baseline_rows.get(case_id))
        right = as_dict(repair_rows.get(case_id))
        left_pass = left.get("case_pass") is True
        right_pass = right.get("case_pass") is True
        rows.append(
            {
                "case_id": case_id,
                "baseline_pass": left_pass,
                "repair_pass": right_pass,
                "delta": int(right_pass) - int(left_pass),
                "baseline_hit_terms": left.get("hit_terms", []),
                "baseline_missed_terms": left.get("missed_terms", []),
                "baseline_continuation": left.get("continuation", ""),
                "repair_hit_terms": right.get("hit_terms", []),
                "repair_missed_terms": right.get("missed_terms", []),
                "repair_continuation": right.get("continuation", ""),
            }
        )
    return rows


def _checks(
    baseline: dict[str, Any],
    repair: dict[str, Any],
    training: dict[str, Any],
    baseline_summary: dict[str, Any],
    repair_summary: dict[str, Any],
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    training_summary = as_dict(training.get("summary"))
    training_provided = bool(training)
    return [
        _check("baseline_replay_passed", baseline.get("status") == "pass", baseline.get("status"), "baseline replay execution must pass"),
        _check("repair_replay_passed", repair.get("status") == "pass", repair.get("status"), "repair replay execution must pass"),
        _check(
            "training_run_ready_when_provided",
            (not training_provided) or training_summary.get("bounded_real_replay_repair_training_ready") is True,
            training_summary.get("bounded_real_replay_repair_training_ready") if training_provided else "not_provided",
            "repair training run evidence is optional, but must be ready when provided",
        ),
        _check("case_counts_match", baseline_summary.get("case_count") == repair_summary.get("case_count"), {"baseline": baseline_summary.get("case_count"), "repair": repair_summary.get("case_count")}, "baseline and repair replay should cover the same suite"),
        _check("case_rows_present", bool(case_rows), len(case_rows), "comparison must include case rows"),
    ]


def _comparison(status: str, baseline_summary: dict[str, Any], repair_summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_passed = int(baseline_summary.get("passed_case_count") or 0)
    repair_passed = int(repair_summary.get("passed_case_count") or 0)
    delta = repair_passed - baseline_passed
    baseline_rate = float(baseline_summary.get("pass_rate") or 0.0)
    repair_rate = float(repair_summary.get("pass_rate") or 0.0)
    case_count = len(case_rows)
    repair_ready = bool(repair_summary.get("model_route_quality_ready"))
    return {
        "ready": status == "pass",
        "baseline_passed_case_count": baseline_passed,
        "repair_passed_case_count": repair_passed,
        "passed_case_delta": delta,
        "baseline_pass_rate": baseline_rate,
        "repair_pass_rate": repair_rate,
        "pass_rate_delta": round(repair_rate - baseline_rate, 4),
        "repair_model_route_quality_ready": repair_ready,
        "repair_checkpoint_improved": delta > 0,
        "repair_checkpoint_regressed": delta < 0,
        "promotion_ready": status == "pass" and delta > 0 and repair_ready,
        "case_count": case_count,
        "next_step": _next_step(delta, repair_ready),
    }


def _summary(status: str, checks: list[dict[str, Any]], comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_repair_checkpoint_comparison_ready": status == "pass" and comparison.get("ready") is True,
        "repair_checkpoint_improved": comparison.get("repair_checkpoint_improved"),
        "repair_checkpoint_regressed": comparison.get("repair_checkpoint_regressed"),
        "baseline_passed_case_count": comparison.get("baseline_passed_case_count"),
        "repair_passed_case_count": comparison.get("repair_passed_case_count"),
        "passed_case_delta": comparison.get("passed_case_delta"),
        "baseline_pass_rate": comparison.get("baseline_pass_rate"),
        "repair_pass_rate": comparison.get("repair_pass_rate"),
        "pass_rate_delta": comparison.get("pass_rate_delta"),
        "promotion_ready": comparison.get("promotion_ready"),
        "case_count": comparison.get("case_count"),
        "next_step": comparison.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, comparison: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison"
    if comparison.get("promotion_ready") is True:
        return "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_improved_ready_for_review"
    if comparison.get("repair_checkpoint_improved") is True:
        return "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_partially_improved"
    if comparison.get("repair_checkpoint_regressed") is True:
        return "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_regressed"
    return "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_no_gain"


def _interpretation(status: str, comparison: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Comparison inputs are incomplete.", "next_action": "repair comparison inputs"}
    if comparison.get("repair_checkpoint_improved") is True:
        return {"model_quality_claim": "bounded_replay_improved", "reason": "Repair checkpoint passed more bounded replay cases than baseline.", "next_action": comparison.get("next_step")}
    if comparison.get("repair_checkpoint_regressed") is True:
        return {
            "model_quality_claim": "not_improved",
            "reason": "Repair checkpoint passed fewer bounded replay cases than baseline.",
            "next_action": comparison.get("next_step"),
        }
    return {
        "model_quality_claim": "not_improved",
        "reason": "Repair checkpoint did not beat the baseline bounded replay pass count.",
        "next_action": comparison.get("next_step"),
    }


def _next_step(delta: int, repair_ready: bool) -> str:
    if delta > 0 and repair_ready:
        return "review_repair_checkpoint_before_route_promotion"
    if delta > 0:
        return "continue_bounded_repair_training_before_promotion"
    if delta < 0:
        return "revise_bounded_repair_seed_or_training_strategy_before_replay_promotion"
    return "hold_route_promotion_and_add_stronger_repair_evidence"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison",
    "locate_repair_training_run",
    "locate_route_promotion_bounded_real_replay",
    "read_json_report",
    "resolve_exit_code",
]
