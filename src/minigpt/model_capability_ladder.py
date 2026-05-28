from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from minigpt.report_utils import as_dict, list_of_dicts, number_or_none, utc_now


LADDER_JSON_FILENAME = "model_capability_ladder.json"
LADDER_TEXT_FILENAME = "model_capability_ladder.txt"
LADDER_MARKDOWN_FILENAME = "model_capability_ladder.md"
LADDER_HTML_FILENAME = "model_capability_ladder.html"


def parse_max_iters_list(value: str | Iterable[int]) -> list[int]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        values = [int(part) for part in parts if part]
    else:
        values = [int(item) for item in value]
    if not values:
        raise ValueError("at least one max-iters value is required")
    if any(item < 1 for item in values):
        raise ValueError("max-iters values must be at least 1")
    if len(set(values)) != len(values):
        raise ValueError("max-iters values must be unique")
    return sorted(values)


def read_ladder_summary(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def build_model_capability_ladder_report(
    summaries: Iterable[dict[str, Any]],
    *,
    out_dir: str | Path,
    run_config: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [_summary_row(index, summary) for index, summary in enumerate(summaries, start=1)]
    rows.sort(key=lambda row: int(row.get("max_iters") or 0))
    issue_list = _issues(rows)
    status = "pass" if not issue_list else "fail"
    trend = summarize_ladder_trend(rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability ladder",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "capability_ladder_ready" if status == "pass" else "fix_capability_ladder",
        "issue_count": len(issue_list),
        "issues": issue_list,
        "out_dir": str(Path(out_dir)),
        "run_config": dict(run_config),
        "rung_count": len(rows),
        "successful_rung_count": sum(1 for row in rows if row.get("status") == "pass"),
        "max_iters_values": [row.get("max_iters") for row in rows],
        "rows": rows,
        "trend_summary": trend,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": "This ladder uses tiny CPU runs to observe training-signal movement; it is not robust production model quality evidence.",
        },
    }


def summarize_ladder_trend(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("status") == "pass"]
    first = valid[0] if valid else {}
    last = valid[-1] if valid else {}
    best_loss_row = _best_row(valid, "best_val_loss", lower_is_better=True)
    best_score_row = _best_row(valid, "scorecard_overall_score", lower_is_better=False)
    loss_delta = _delta(last.get("best_val_loss"), first.get("best_val_loss"))
    final_loss_delta = _delta(last.get("final_val_loss"), first.get("final_val_loss"))
    score_delta = _delta(last.get("scorecard_overall_score"), first.get("scorecard_overall_score"))
    flag_delta = _delta(last.get("generation_quality_total_flags"), first.get("generation_quality_total_flags"))
    return {
        "status": "pass" if len(valid) >= 2 else "review",
        "decision": _trend_decision(loss_delta, score_delta, flag_delta),
        "first_max_iters": first.get("max_iters"),
        "last_max_iters": last.get("max_iters"),
        "best_loss_max_iters": best_loss_row.get("max_iters") if best_loss_row else None,
        "best_score_max_iters": best_score_row.get("max_iters") if best_score_row else None,
        "best_val_loss_delta_first_to_last": loss_delta,
        "final_val_loss_delta_first_to_last": final_loss_delta,
        "score_delta_first_to_last": score_delta,
        "generation_flags_delta_first_to_last": flag_delta,
        "best_val_loss_monotonic_non_increasing": _is_monotonic(valid, "best_val_loss", reverse=False),
        "score_monotonic_non_decreasing": _is_monotonic(valid, "scorecard_overall_score", reverse=True),
        "generation_flags_monotonic_non_increasing": _is_monotonic(valid, "generation_quality_total_flags", reverse=False),
    }


def _summary_row(index: int, summary: dict[str, Any]) -> dict[str, Any]:
    training = as_dict(summary.get("training"))
    quality = as_dict(summary.get("generation_quality"))
    scorecard = as_dict(summary.get("benchmark_scorecard"))
    eval_suite = as_dict(summary.get("eval_suite"))
    artifacts = as_dict(summary.get("artifacts"))
    commands = list_of_dicts(summary.get("commands"))
    command_failures = [item for item in commands if item.get("status") != "pass"]
    return {
        "index": index,
        "name": f"max-iters-{summary.get('max_iters') or _max_iters_from_summary(summary)}",
        "status": summary.get("status"),
        "decision": summary.get("decision"),
        "summary_path": summary.get("summary_path"),
        "out_dir": summary.get("out_dir"),
        "run_dir": summary.get("run_dir"),
        "max_iters": _max_iters_from_summary(summary),
        "checkpoint_exists": artifacts.get("checkpoint_exists"),
        "eval_suite_case_count": eval_suite.get("case_count"),
        "best_val_loss": number_or_none(training.get("best_val_loss")),
        "final_val_loss": number_or_none(training.get("final_val_loss")),
        "scorecard_overall_status": scorecard.get("overall_status"),
        "scorecard_overall_score": number_or_none(scorecard.get("overall_score")),
        "generation_quality_status": quality.get("overall_status"),
        "generation_quality_total_flags": number_or_none(quality.get("total_flags"), int),
        "pair_same_checkpoint_baseline": as_dict(summary.get("pair_batch")).get("same_checkpoint_baseline"),
        "command_failure_count": len(command_failures),
    }


def _max_iters_from_summary(summary: dict[str, Any]) -> int | None:
    direct = number_or_none(summary.get("max_iters"), int)
    if direct is not None:
        return int(direct)
    config = as_dict(summary.get("run_config"))
    value = config.get("max_iters")
    if value is None:
        value = _train_config_max_iters(summary)
    parsed = number_or_none(value, int)
    return int(parsed) if parsed is not None else None


def _train_config_max_iters(summary: dict[str, Any]) -> int | None:
    run_dir = summary.get("run_dir")
    if not run_dir:
        return None
    config_path = Path(str(run_dir)) / "train_config.json"
    if not config_path.is_file():
        return None
    payload = read_ladder_summary(config_path)
    parsed = number_or_none(payload.get("max_iters"), int)
    return int(parsed) if parsed is not None else None


def _issues(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(rows) < 2:
        issues.append("at least two ladder rungs are required")
    for row in rows:
        if row.get("status") != "pass":
            issues.append(f"{row.get('name')} status is {row.get('status')}")
        if not row.get("checkpoint_exists"):
            issues.append(f"{row.get('name')} checkpoint is missing")
        if row.get("max_iters") is None:
            issues.append(f"{row.get('name')} max_iters is missing")
        if row.get("best_val_loss") is None:
            issues.append(f"{row.get('name')} best_val_loss is missing")
    return issues


def _best_row(rows: list[dict[str, Any]], key: str, *, lower_is_better: bool) -> dict[str, Any] | None:
    values = [row for row in rows if row.get(key) is not None]
    if not values:
        return None
    return min(values, key=lambda row: float(row[key])) if lower_is_better else max(values, key=lambda row: float(row[key]))


def _delta(candidate: Any, baseline: Any) -> float | None:
    left = number_or_none(candidate)
    right = number_or_none(baseline)
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 4)


def _is_monotonic(rows: list[dict[str, Any]], key: str, *, reverse: bool) -> bool | None:
    values = [number_or_none(row.get(key)) for row in rows]
    clean = [float(value) for value in values if value is not None]
    if len(clean) < 2:
        return None
    pairs = zip(clean, clean[1:])
    return all(right >= left for left, right in pairs) if reverse else all(right <= left for left, right in pairs)


def _trend_decision(loss_delta: float | None, score_delta: float | None, flag_delta: float | None) -> str:
    loss_improved = loss_delta is not None and loss_delta < 0
    score_improved = score_delta is not None and score_delta > 0
    flags_improved = flag_delta is not None and flag_delta < 0
    if loss_improved and (score_improved or flags_improved):
        return "training_signal_and_eval_signal_improved"
    if loss_improved:
        return "loss_improved_without_eval_improvement"
    if score_improved or flags_improved:
        return "eval_signal_improved_without_loss_improvement"
    return "no_observed_capability_gain"
