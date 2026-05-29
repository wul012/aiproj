from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from minigpt.report_utils import as_dict, first_present, number_or_none, utc_now


TOKEN_BUDGET_STABILITY_JSON_FILENAME = "model_capability_token_budget_stability.json"
TOKEN_BUDGET_STABILITY_TEXT_FILENAME = "model_capability_token_budget_stability.txt"
TOKEN_BUDGET_STABILITY_MARKDOWN_FILENAME = "model_capability_token_budget_stability.md"
TOKEN_BUDGET_STABILITY_HTML_FILENAME = "model_capability_token_budget_stability.html"

_REQUIRED_DELTA_FIELDS = [
    "token_budget_or_shape_limit_delta",
    "persistent_fail_count_delta",
    "score_improved_count_delta",
    "pass_transition_count_delta",
]


def build_model_capability_token_budget_stability_report(
    probe_reports: Iterable[dict[str, Any]],
    *,
    out_dir: str | Path,
    run_config: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [_probe_row(index, report) for index, report in enumerate(probe_reports, start=1)]
    issue_list = _issues(rows, run_config)
    status = "pass" if not issue_list else "fail"
    stability = summarize_token_budget_stability(rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability token budget stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "token_budget_stability_ready" if status == "pass" else "fix_token_budget_stability",
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
            "reason": _interpretation_reason(stability),
            "next_action": _next_action(stability),
        },
    }


def summarize_token_budget_stability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("status") == "pass"]
    token_deltas = _numbers(valid, "token_budget_or_shape_limit_delta")
    persistent_fail_deltas = _numbers(valid, "persistent_fail_count_delta")
    score_improved_deltas = _numbers(valid, "score_improved_count_delta")
    pass_transition_deltas = _numbers(valid, "pass_transition_count_delta")
    avg_score_deltas = _numbers(valid, "avg_score_delta_change")
    token_relief_count = sum(1 for value in token_deltas if value < 0)
    persistent_relief_count = sum(1 for value in persistent_fail_deltas if value < 0)
    score_improvement_count = sum(1 for value in score_improved_deltas if value > 0)
    pass_transition_count = sum(1 for value in pass_transition_deltas if value > 0)
    score_or_pass_progress_count = sum(
        1
        for row in valid
        if (number_or_none(row.get("score_improved_count_delta")) or 0) > 0
        or (number_or_none(row.get("pass_transition_count_delta")) or 0) > 0
    )
    return {
        "status": "pass" if len(valid) >= 2 else "review",
        "decision": _stability_decision(len(valid), token_relief_count, score_or_pass_progress_count),
        "seed_count": len(rows),
        "successful_seed_count": len(valid),
        "token_relief_seed_count": token_relief_count,
        "persistent_fail_relief_seed_count": persistent_relief_count,
        "score_improvement_seed_count": score_improvement_count,
        "pass_transition_seed_count": pass_transition_count,
        "score_or_pass_progress_seed_count": score_or_pass_progress_count,
        "all_successful_seeds_token_relief": bool(valid) and token_relief_count == len(valid),
        "any_successful_seed_score_or_pass_progress": score_or_pass_progress_count > 0,
        "mean_token_budget_or_shape_limit_delta": _mean(token_deltas),
        "mean_persistent_fail_count_delta": _mean(persistent_fail_deltas),
        "mean_score_improved_count_delta": _mean(score_improved_deltas),
        "mean_pass_transition_count_delta": _mean(pass_transition_deltas),
        "mean_avg_score_delta_change": _mean(avg_score_deltas),
    }


def _probe_row(index: int, report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    config = as_dict(report.get("run_config"))
    return {
        "index": index,
        "seed": number_or_none(first_present(report.get("seed"), config.get("seed")), int),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "report_path": report.get("report_path"),
        "token_budget_count": number_or_none(report.get("token_budget_count"), int),
        "baseline_token_cap": summary.get("baseline_token_cap"),
        "largest_token_cap": summary.get("largest_token_cap"),
        "token_budget_or_shape_limit_delta": number_or_none(summary.get("token_budget_or_shape_limit_delta")),
        "persistent_fail_count_delta": number_or_none(summary.get("persistent_fail_count_delta")),
        "score_improved_count_delta": number_or_none(summary.get("score_improved_count_delta")),
        "pass_transition_count_delta": number_or_none(summary.get("pass_transition_count_delta")),
        "avg_score_delta_change": number_or_none(summary.get("avg_score_delta_change")),
        "summary_decision": summary.get("decision"),
    }


def _issues(rows: list[dict[str, Any]], run_config: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if len(rows) < 2:
        issues.append("at least two token budget probe seeds are required")
    if (number_or_none(run_config.get("command_failure_count"), int) or 0) > 0:
        issues.append("one or more token budget probe commands failed")
    seed_values = [row.get("seed") for row in rows if row.get("seed") is not None]
    if len(seed_values) != len(set(seed_values)):
        issues.append("seed values must be unique")
    for row in rows:
        label = f"seed-{row.get('seed')}"
        if row.get("seed") is None:
            issues.append("seed value is missing")
        if row.get("status") != "pass":
            issues.append(f"{label} token budget probe status is {row.get('status')}")
        if (number_or_none(row.get("token_budget_count"), int) or 0) < 2:
            issues.append(f"{label} token_budget_count must be at least 2")
        for field in _REQUIRED_DELTA_FIELDS:
            if row.get(field) is None:
                issues.append(f"{label} {field} is missing")
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


def _stability_decision(success_count: int, token_relief_count: int, score_or_pass_progress_count: int) -> str:
    if success_count < 2:
        return "insufficient_seed_probe"
    if token_relief_count == success_count and score_or_pass_progress_count > 0:
        return "repeated_token_budget_relief_with_some_score_progress"
    if token_relief_count == success_count:
        return "repeated_token_budget_relief_without_score_progress"
    if token_relief_count > 0:
        return "mixed_token_budget_relief"
    return "no_repeated_token_budget_relief"


def _interpretation_reason(stability: dict[str, Any]) -> str:
    decision = stability.get("decision")
    if decision == "repeated_token_budget_relief_with_some_score_progress":
        return "Longer token budgets repeatedly reduced stall signals, with limited score or pass-transition progress in at least one seed."
    if decision == "repeated_token_budget_relief_without_score_progress":
        return "Longer token budgets repeatedly reduced token/shape stalls, but did not improve score or pass-transition evidence."
    if decision == "mixed_token_budget_relief":
        return "The longer token budget helped only part of the seed set, so the next change should inspect unstable prompts before scaling."
    if decision == "no_repeated_token_budget_relief":
        return "The longer token budget did not repeat the stall-relief signal across successful seeds."
    return "At least two successful seed probes are required before calling token-budget relief stable."


def _next_action(stability: dict[str, Any]) -> str:
    decision = stability.get("decision")
    if decision == "repeated_token_budget_relief_without_score_progress":
        return "keep cap 12 as the evaluation budget and probe data/rubric changes before increasing model size"
    if decision == "repeated_token_budget_relief_with_some_score_progress":
        return "promote cap 12 for the next tiny baseline/candidate run and keep score progress under review"
    if decision == "mixed_token_budget_relief":
        return "compare per-seed diagnostic rows before spending a larger training budget"
    if decision == "no_repeated_token_budget_relief":
        return "return to prompt length and checker requirements before changing training scale"
    return "rerun the token-budget probe with at least two seeds"
