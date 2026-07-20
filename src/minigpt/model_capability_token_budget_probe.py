from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from minigpt.report_utils import as_dict, number_or_none, utc_now


TOKEN_BUDGET_JSON_FILENAME = "model_capability_token_budget_probe.json"
TOKEN_BUDGET_TEXT_FILENAME = "model_capability_token_budget_probe.txt"
TOKEN_BUDGET_MARKDOWN_FILENAME = "model_capability_token_budget_probe.md"
TOKEN_BUDGET_HTML_FILENAME = "model_capability_token_budget_probe.html"


def parse_token_caps(value: str | Iterable[int]) -> list[int]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        caps = [int(part) for part in parts if part]
    else:
        caps = [int(item) for item in value]
    if not caps:
        raise ValueError("at least one token cap is required")
    if any(item < 1 for item in caps):
        raise ValueError("token caps must be at least 1")
    if len(set(caps)) != len(caps):
        raise ValueError("token caps must be unique")
    return sorted(caps)


def build_model_capability_token_budget_probe_report(
    diagnostics: Iterable[dict[str, Any]],
    *,
    out_dir: str | Path,
    run_config: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [_diagnostic_row(index, report) for index, report in enumerate(diagnostics, start=1)]
    rows.sort(key=lambda row: int(row.get("case_token_cap") or 0))
    issue_list = _issues(rows)
    status = "pass" if not issue_list else "fail"
    summary = summarize_token_budget_probe(rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability token budget probe",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "token_budget_probe_ready" if status == "pass" else "fix_token_budget_probe",
        "issue_count": len(issue_list),
        "issues": issue_list,
        "out_dir": str(Path(out_dir)),
        "run_config": dict(run_config),
        "token_budget_count": len(rows),
        "rows": rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(summary),
            "next_action": _next_action(summary),
        },
    }


def summarize_token_budget_probe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("status") == "pass"]
    first = valid[0] if valid else {}
    last = valid[-1] if valid else {}
    token_limit_delta = _delta(last.get("token_budget_or_shape_limit_count"), first.get("token_budget_or_shape_limit_count"))
    score_improved_delta = _delta(last.get("score_improved_count"), first.get("score_improved_count"))
    pass_transition_delta = _delta(last.get("pass_transition_count"), first.get("pass_transition_count"))
    persistent_fail_delta = _delta(last.get("persistent_fail_count"), first.get("persistent_fail_count"))
    avg_score_delta_change = _delta(last.get("avg_score_delta"), first.get("avg_score_delta"))
    return {
        "status": "pass" if len(valid) >= 2 else "review",
        "decision": _summary_decision(token_limit_delta, score_improved_delta, pass_transition_delta, persistent_fail_delta),
        "baseline_token_cap": first.get("case_token_cap"),
        "largest_token_cap": last.get("case_token_cap"),
        "token_budget_or_shape_limit_delta": token_limit_delta,
        "score_improved_count_delta": score_improved_delta,
        "pass_transition_count_delta": pass_transition_delta,
        "persistent_fail_count_delta": persistent_fail_delta,
        "avg_score_delta_change": avg_score_delta_change,
        "baseline_token_budget_or_shape_limit_count": first.get("token_budget_or_shape_limit_count"),
        "largest_token_budget_or_shape_limit_count": last.get("token_budget_or_shape_limit_count"),
        "baseline_summary_decision": first.get("summary_decision"),
        "largest_summary_decision": last.get("summary_decision"),
    }


def _diagnostic_row(index: int, report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    run_config = as_dict(report.get("run_config"))
    return {
        "index": index,
        "case_token_cap": number_or_none(report.get("case_token_cap") or run_config.get("case_token_cap"), int),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "source_diagnostic": report.get("source_diagnostic") or report.get("out_dir"),
        "source_ladder_report": report.get("source_ladder_report"),
        "case_count": summary.get("case_count"),
        "score_improved_count": summary.get("score_improved_count"),
        "score_degraded_count": summary.get("score_degraded_count"),
        "score_unchanged_count": summary.get("score_unchanged_count"),
        "persistent_fail_count": summary.get("persistent_fail_count"),
        "pass_transition_count": summary.get("pass_transition_count"),
        "preview_changed_count": summary.get("preview_changed_count"),
        "token_budget_or_shape_limit_count": summary.get("token_budget_or_shape_limit_count"),
        "avg_score_delta": summary.get("avg_score_delta"),
        "summary_decision": summary.get("decision"),
    }


def _issues(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(rows) < 2:
        issues.append("at least two token budgets are required")
    for row in rows:
        label = f"token-cap-{row.get('case_token_cap')}"
        if row.get("case_token_cap") is None:
            issues.append(f"{label} token cap is missing")
        if row.get("status") != "pass":
            issues.append(f"{label} diagnostic status is {row.get('status')}")
        if row.get("token_budget_or_shape_limit_count") is None:
            issues.append(f"{label} token budget stall count is missing")
    return issues


def _summary_decision(
    token_limit_delta: float | None,
    score_improved_delta: float | None,
    pass_transition_delta: float | None,
    persistent_fail_delta: float | None,
) -> str:
    if token_limit_delta is None:
        return "insufficient_token_budget_probe"
    if (
        token_limit_delta < 0
        or (score_improved_delta or 0) > 0
        or (pass_transition_delta or 0) > 0
        or (persistent_fail_delta or 0) < 0
    ):
        return "longer_token_budget_reduces_eval_stall"
    if token_limit_delta == 0:
        return "longer_token_budget_still_blocked"
    return "longer_token_budget_regressed"


def _interpretation_reason(summary: dict[str, Any]) -> str:
    if summary.get("decision") == "longer_token_budget_reduces_eval_stall":
        return "A longer token budget reduced at least one prompt-level stall signal, but this remains tiny smoke evidence."
    if summary.get("decision") == "longer_token_budget_still_blocked":
        return "The longer token budget did not reduce prompt-level stall signals in this tiny probe."
    if summary.get("decision") == "longer_token_budget_regressed":
        return "The longer token budget worsened a stall signal and needs inspection before larger runs."
    return "The token budget probe needs at least two valid token caps before drawing a direction."


def _next_action(summary: dict[str, Any]) -> str:
    if summary.get("decision") == "longer_token_budget_reduces_eval_stall":
        return "repeat the longer-token probe across seeds before increasing model size"
    if summary.get("decision") == "longer_token_budget_still_blocked":
        return "inspect data and rubric requirements before spending more training budget"
    if summary.get("decision") == "longer_token_budget_regressed":
        return "compare generation previews and failure checks for the larger token cap"
    return "run two or more token caps with the same seed and max-iters ladder"


def _delta(candidate: Any, baseline: Any) -> float | None:
    left = number_or_none(candidate)
    right = number_or_none(baseline)
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 4)
