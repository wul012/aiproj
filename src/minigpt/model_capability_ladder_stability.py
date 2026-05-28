from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from minigpt.report_utils import as_dict, number_or_none, utc_now


STABILITY_JSON_FILENAME = "model_capability_ladder_stability.json"
STABILITY_TEXT_FILENAME = "model_capability_ladder_stability.txt"
STABILITY_MARKDOWN_FILENAME = "model_capability_ladder_stability.md"
STABILITY_HTML_FILENAME = "model_capability_ladder_stability.html"


def parse_seed_list(value: str | Iterable[int]) -> list[int]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        seeds = [int(part) for part in parts if part]
    else:
        seeds = [int(item) for item in value]
    if not seeds:
        raise ValueError("at least one seed is required")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seed values must be unique")
    return seeds


def build_model_capability_ladder_stability_report(
    ladder_reports: Iterable[dict[str, Any]],
    *,
    out_dir: str | Path,
    run_config: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [_ladder_row(index, report) for index, report in enumerate(ladder_reports, start=1)]
    issue_list = _issues(rows)
    status = "pass" if not issue_list else "fail"
    stability = summarize_stability(rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability ladder stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "capability_stability_ready" if status == "pass" else "fix_capability_stability",
        "issue_count": len(issue_list),
        "issues": issue_list,
        "out_dir": str(Path(out_dir)),
        "run_config": dict(run_config),
        "seed_count": len(rows),
        "successful_seed_count": sum(1 for row in rows if row.get("status") == "pass"),
        "rows": rows,
        "stability_summary": stability,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": "Multi-seed tiny ladders can replay a training signal, but they still do not prove production model quality.",
        },
    }


def summarize_stability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("status") == "pass"]
    loss_deltas = _numbers(valid, "best_val_loss_delta")
    score_deltas = _numbers(valid, "score_delta")
    flag_deltas = _numbers(valid, "generation_flags_delta")
    loss_improvement_count = sum(1 for value in loss_deltas if value < 0)
    score_improvement_count = sum(1 for value in score_deltas if value > 0)
    flag_improvement_count = sum(1 for value in flag_deltas if value < 0)
    eval_improvement_count = sum(
        1
        for row in valid
        if (number_or_none(row.get("score_delta")) or 0) > 0 or (number_or_none(row.get("generation_flags_delta")) or 0) < 0
    )
    return {
        "status": "pass" if len(valid) >= 2 else "review",
        "decision": _stability_decision(len(valid), loss_improvement_count, eval_improvement_count),
        "seed_count": len(rows),
        "successful_seed_count": len(valid),
        "loss_improvement_seed_count": loss_improvement_count,
        "score_improvement_seed_count": score_improvement_count,
        "generation_flag_improvement_seed_count": flag_improvement_count,
        "eval_improvement_seed_count": eval_improvement_count,
        "all_successful_seeds_loss_improved": bool(valid) and loss_improvement_count == len(valid),
        "any_successful_seed_eval_improved": eval_improvement_count > 0,
        "mean_best_val_loss_delta": _mean(loss_deltas),
        "mean_score_delta": _mean(score_deltas),
        "mean_generation_flags_delta": _mean(flag_deltas),
    }


def _ladder_row(index: int, report: dict[str, Any]) -> dict[str, Any]:
    trend = as_dict(report.get("trend_summary"))
    config = as_dict(report.get("run_config"))
    return {
        "index": index,
        "seed": config.get("seed"),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "report_path": report.get("report_path"),
        "rung_count": report.get("rung_count"),
        "successful_rung_count": report.get("successful_rung_count"),
        "max_iters_values": report.get("max_iters_values"),
        "trend_decision": trend.get("decision"),
        "first_max_iters": trend.get("first_max_iters"),
        "last_max_iters": trend.get("last_max_iters"),
        "best_loss_max_iters": trend.get("best_loss_max_iters"),
        "best_score_max_iters": trend.get("best_score_max_iters"),
        "best_val_loss_delta": number_or_none(trend.get("best_val_loss_delta_first_to_last")),
        "score_delta": number_or_none(trend.get("score_delta_first_to_last")),
        "generation_flags_delta": number_or_none(trend.get("generation_flags_delta_first_to_last")),
    }


def _issues(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(rows) < 2:
        issues.append("at least two seed ladders are required")
    for row in rows:
        label = f"seed-{row.get('seed')}"
        if row.get("status") != "pass":
            issues.append(f"{label} ladder status is {row.get('status')}")
        if row.get("best_val_loss_delta") is None:
            issues.append(f"{label} best_val_loss_delta is missing")
    return issues


def _numbers(rows: list[dict[str, Any]], key: str) -> list[float]:
    values = []
    for row in rows:
        parsed = number_or_none(row.get(key))
        if parsed is not None:
            values.append(float(parsed))
    return values


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _stability_decision(success_count: int, loss_improvement_count: int, eval_improvement_count: int) -> str:
    if success_count < 2:
        return "insufficient_seed_replay"
    if loss_improvement_count == success_count and eval_improvement_count > 0:
        return "repeated_loss_with_some_eval_improvement"
    if loss_improvement_count == success_count:
        return "repeated_loss_improvement_without_eval_improvement"
    if loss_improvement_count > 0:
        return "mixed_loss_improvement"
    return "no_repeated_training_signal"
