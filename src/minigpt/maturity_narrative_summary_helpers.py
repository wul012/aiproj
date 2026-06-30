from __future__ import annotations

from typing import Any


def _request_summary(maturity: dict[str, Any] | None, request_history: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(request_history, dict):
        return _dict(request_history.get("summary"))
    return _dict(_pick(maturity, "request_history_context"))


def _scorecard_summary(scorecard: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(scorecard.get("summary"))
    return {
        "overall_status": summary.get("overall_status"),
        "overall_score": summary.get("overall_score"),
        "rubric_status": summary.get("rubric_status"),
        "rubric_avg_score": summary.get("rubric_avg_score"),
        "weakest_rubric_case": summary.get("weakest_rubric_case"),
        "weakest_rubric_score": summary.get("weakest_rubric_score"),
    }


def _scorecard_decision_summary(decision: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(decision.get("summary"))
    selected = _dict(decision.get("selected_run"))
    evaluations = _list_of_dicts(decision.get("candidate_evaluations"))
    non_ready_candidates = _decision_row_non_ready_candidates(evaluations, summary)
    return {
        "decision_status": decision.get("decision_status"),
        "recommended_action": decision.get("recommended_action"),
        "selected_run": selected.get("name") or summary.get("selected_name"),
        "selected_relation": selected.get("decision_relation") or summary.get("selected_relation"),
        "selected_rubric_avg_score": selected.get("rubric_avg_score") or summary.get("selected_rubric_avg_score"),
        "selected_generation_quality_total_flags_delta": selected.get("generation_quality_total_flags_delta")
        if selected
        else summary.get("selected_generation_quality_total_flags_delta"),
        "selected_eval_suite_comparison_status": selected.get("eval_suite_comparison_status")
        or summary.get("selected_eval_suite_comparison_status"),
        "candidate_count": summary.get("candidate_count"),
        "clean_candidate_count": summary.get("clean_candidate_count"),
        "review_candidate_count": summary.get("review_candidate_count"),
        "blocked_candidate_count": summary.get("blocked_candidate_count"),
        "non_comparison_ready_candidate_count": _coalesce(
            summary.get("non_comparison_ready_candidate_count"),
            len(non_ready_candidates),
        ),
        "non_comparison_ready_candidates": non_ready_candidates,
        "eval_suite_comparison_status_counts": _counts(
            row.get("eval_suite_comparison_status") or "missing" for row in evaluations if not row.get("is_baseline")
        ),
        "review_item_count": sum(len(_string_list(row.get("review_items"))) for row in evaluations),
        "blocker_count": sum(len(_string_list(row.get("blockers"))) for row in evaluations if not row.get("is_baseline")),
    }


def _benchmark_history_summary(history: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(history.get("summary"))
    readiness = _dict(history.get("readiness_requirement"))
    entries = _list_of_dicts(history.get("entries"))
    return {
        "entry_count": summary.get("entry_count") if summary else len(entries),
        "promote_count": summary.get("promote_count"),
        "review_count": summary.get("review_count"),
        "blocked_count": summary.get("blocked_count"),
        "ready_count": summary.get("ready_count"),
        "case_regression_entry_count": summary.get("case_regression_entry_count"),
        "generation_quality_flag_regression_entry_count": summary.get("generation_quality_flag_regression_entry_count"),
        "suite_design_non_comparison_ready_entry_count": summary.get("suite_design_non_comparison_ready_entry_count"),
        "design_comparison_changed_entry_count": summary.get("design_comparison_changed_entry_count"),
        "best_candidate_name": summary.get("best_candidate_name"),
        "model_quality_claim": summary.get("model_quality_claim"),
        "readiness_requirement_status": readiness.get("status"),
        "readiness_requirement_decision": readiness.get("decision"),
        "readiness_requirement_exit_code": readiness.get("exit_code"),
        "readiness_requirement_min_ready_entries": readiness.get("min_ready_entries"),
        "readiness_requirement_ready_count": readiness.get("ready_count"),
        "readiness_requirement_failed_reasons": _string_list(readiness.get("failed_reasons")),
        "boundary_counts": _counts(row.get("boundary") or "missing" for row in entries),
        "latest_boundary": entries[-1].get("boundary") if entries else None,
    }


def _dataset_summary(card: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(card.get("summary"))
    quality = _dict(card.get("quality"))
    return {
        "readiness_status": summary.get("readiness_status"),
        "quality_status": summary.get("quality_status") or quality.get("status"),
        "warning_count": summary.get("warning_count") or quality.get("warning_count"),
        "short_fingerprint": summary.get("short_fingerprint"),
    }


def _weakest_benchmark_case(rows: list[dict[str, Any]]) -> str | None:
    candidates = [row for row in rows if row.get("weakest_rubric_score") is not None]
    if not candidates:
        return None
    weakest = min(candidates, key=lambda item: float(item.get("weakest_rubric_score") or 0.0))
    return weakest.get("weakest_rubric_case")


def _selected_decision_run(rows: list[dict[str, Any]]) -> str | None:
    selected = [row for row in rows if row.get("selected_run")]
    if not selected:
        return None
    return str(selected[-1].get("selected_run"))


def _selected_decision_flag_delta(rows: list[dict[str, Any]]) -> Any:
    selected = [row for row in rows if row.get("selected_run")]
    if not selected:
        return None
    return selected[-1].get("selected_generation_quality_total_flags_delta")


def _selected_decision_eval_status(rows: list[dict[str, Any]]) -> str | None:
    selected = [row for row in rows if row.get("selected_run")]
    if not selected:
        return None
    value = selected[-1].get("selected_eval_suite_comparison_status")
    return None if value is None else str(value)


def _decision_non_ready_candidates(rows: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for row in rows:
        for name in _string_list(row.get("non_comparison_ready_candidates")):
            if name not in names:
                names.append(name)
    return names


def _selected_history_best_candidate(rows: list[dict[str, Any]]) -> str | None:
    selected = [row for row in rows if row.get("best_candidate_name")]
    if not selected:
        return None
    return str(selected[-1].get("best_candidate_name"))


def _latest_history_boundary(rows: list[dict[str, Any]]) -> str | None:
    selected = [row for row in rows if row.get("latest_boundary")]
    if not selected:
        return None
    return str(selected[-1].get("latest_boundary"))


def _max_int(values: Any) -> int | None:
    parsed: list[int] = []
    for value in values:
        if value is None:
            continue
        try:
            parsed.append(int(value))
        except (TypeError, ValueError):
            continue
    return max(parsed) if parsed else None


def _unique_strings(values: Any) -> list[str]:
    items: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in items:
            items.append(text)
    return items


def _decision_row_non_ready_candidates(evaluations: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    from_summary = _string_list(summary.get("non_comparison_ready_candidates"))
    if from_summary:
        return from_summary
    return [
        str(row.get("name"))
        for row in evaluations
        if not row.get("is_baseline") and row.get("eval_suite_comparison_status") not in {None, "pass"} and row.get("name")
    ]


def _merge_counts(rows: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key, value in row.items():
            counts[str(key)] = counts.get(str(key), 0) + int(value or 0)
    return counts


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _reason_count_detail(value: Any) -> str:
    counts = _dict(value)
    if not counts:
        return ""
    return " (" + ", ".join(f"{key}:{counts[key]}" for key in sorted(counts)) + ")"


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts
