from __future__ import annotations

from typing import Any


def build_maturity_narrative_summary(
    maturity: dict[str, Any] | None,
    registry: dict[str, Any] | None,
    request_history: dict[str, Any] | None,
    scorecards: list[dict[str, Any] | None],
    scorecard_decisions: list[dict[str, Any] | None],
    dataset_cards: list[dict[str, Any] | None],
) -> dict[str, Any]:
    maturity_summary = _dict(_pick(maturity, "summary"))
    release = _release_summary(maturity_summary, _dict(_pick(maturity, "release_readiness_context")))
    request = _request_summary(maturity, request_history)
    benchmark_rows = [_scorecard_summary(item) for item in scorecards if isinstance(item, dict)]
    decision_rows = [_scorecard_decision_summary(item) for item in scorecard_decisions if isinstance(item, dict)]
    dataset_rows = [_dataset_summary(item) for item in dataset_cards if isinstance(item, dict)]
    benchmark_scores = [row["overall_score"] for row in benchmark_rows if row.get("overall_score") is not None]
    dataset_warnings = sum(int(row.get("warning_count") or 0) for row in dataset_rows)
    status = _portfolio_status(
        maturity_summary,
        release,
        request,
        benchmark_rows,
        dataset_rows,
        request_history_available=isinstance(request_history, dict),
    )
    return {
        "portfolio_status": status,
        "current_version": maturity_summary.get("current_version"),
        "maturity_status": maturity_summary.get("overall_status"),
        "average_maturity_level": maturity_summary.get("average_maturity_level"),
        "registry_runs": _coalesce(_pick(registry, "run_count"), maturity_summary.get("registry_runs")),
        "release_readiness_trend_status": release.get("trend_status"),
        "release_readiness_regressed_count": release.get("regressed_count"),
        "release_readiness_improved_count": release.get("improved_count"),
        "request_history_status": request.get("status"),
        "request_history_records": request.get("total_log_records"),
        "request_history_timeout_rate": request.get("timeout_rate"),
        "benchmark_scorecard_count": len(benchmark_rows),
        "benchmark_status_counts": _counts(row.get("overall_status") or "missing" for row in benchmark_rows),
        "benchmark_avg_score": round(sum(float(score) for score in benchmark_scores) / len(benchmark_scores), 2)
        if benchmark_scores
        else None,
        "benchmark_weakest_case": _weakest_benchmark_case(benchmark_rows),
        "benchmark_decision_count": len(decision_rows),
        "benchmark_decision_status_counts": _counts(row.get("decision_status") or "missing" for row in decision_rows),
        "benchmark_decision_selected_run": _selected_decision_run(decision_rows),
        "benchmark_decision_review_item_count": sum(int(row.get("review_item_count") or 0) for row in decision_rows),
        "benchmark_decision_blocker_count": sum(int(row.get("blocker_count") or 0) for row in decision_rows),
        "benchmark_decision_selected_flag_delta": _selected_decision_flag_delta(decision_rows),
        "dataset_card_count": len(dataset_rows),
        "dataset_status_counts": _counts(row.get("quality_status") or "missing" for row in dataset_rows),
        "dataset_warning_count": dataset_warnings,
    }


def build_maturity_narrative_recommendations(summary: dict[str, Any], sections: list[dict[str, Any]]) -> list[str]:
    if summary.get("portfolio_status") == "review":
        return [
            "Resolve review-level release, request-history, benchmark, or dataset concerns before using this as a release-ready portfolio summary."
        ]
    if summary.get("portfolio_status") == "incomplete":
        return ["Generate missing maturity, request-history, benchmark scorecard, or dataset-card evidence before presenting the narrative."]
    return [
        "Use the narrative as the human-facing entry point, then link to maturity, registry, benchmark, dataset, and request-history artifacts for detail.",
        "Keep the next version focused on real model/data capability rather than another display-only report.",
    ]


def build_maturity_narrative_warnings(
    maturity: dict[str, Any] | None,
    registry: dict[str, Any] | None,
    request_history: dict[str, Any] | None,
    scorecards: list[dict[str, Any] | None],
    dataset_cards: list[dict[str, Any] | None],
) -> list[str]:
    warnings = []
    if not isinstance(maturity, dict):
        warnings.append("maturity summary is missing")
    if not isinstance(registry, dict):
        warnings.append("registry is missing")
    if not isinstance(request_history, dict):
        warnings.append("request history summary is missing")
    if not any(isinstance(item, dict) for item in scorecards):
        warnings.append("benchmark scorecards are missing")
    if not any(isinstance(item, dict) for item in dataset_cards):
        warnings.append("dataset cards are missing")
    return warnings


def _portfolio_status(
    maturity: dict[str, Any],
    release: dict[str, Any],
    request: dict[str, Any],
    benchmark_rows: list[dict[str, Any]],
    dataset_rows: list[dict[str, Any]],
    *,
    request_history_available: bool,
) -> str:
    if not maturity or not benchmark_rows or not dataset_rows:
        return "incomplete"
    if not release.get("trend_status") or not request_history_available or not request:
        return "incomplete"
    if (
        maturity.get("overall_status") in {"warn", "fail"}
        or release.get("trend_status") == "regressed"
        or int(release.get("regressed_count") or 0) > 0
        or request.get("status") in {"watch", "warn", "fail"}
        or any(row.get("overall_status") in {"warn", "fail"} for row in benchmark_rows)
        or any(row.get("quality_status") in {"warn", "fail"} for row in dataset_rows)
    ):
        return "review"
    return "ready"


def _request_summary(maturity: dict[str, Any] | None, request_history: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(request_history, dict):
        return _dict(request_history.get("summary"))
    return _dict(_pick(maturity, "request_history_context"))


def _release_summary(maturity_summary: dict[str, Any], release_context: dict[str, Any]) -> dict[str, Any]:
    return {
        **release_context,
        "trend_status": _coalesce(release_context.get("trend_status"), maturity_summary.get("release_readiness_trend_status")),
        "regressed_count": _coalesce(release_context.get("regressed_count"), maturity_summary.get("release_readiness_regressed_count")),
        "improved_count": _coalesce(release_context.get("improved_count"), maturity_summary.get("release_readiness_improved_count")),
    }


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
    return {
        "decision_status": decision.get("decision_status"),
        "recommended_action": decision.get("recommended_action"),
        "selected_run": selected.get("name") or summary.get("selected_name"),
        "selected_relation": selected.get("decision_relation") or summary.get("selected_relation"),
        "selected_rubric_avg_score": selected.get("rubric_avg_score") or summary.get("selected_rubric_avg_score"),
        "selected_generation_quality_total_flags_delta": selected.get("generation_quality_total_flags_delta")
        if selected
        else summary.get("selected_generation_quality_total_flags_delta"),
        "candidate_count": summary.get("candidate_count"),
        "clean_candidate_count": summary.get("clean_candidate_count"),
        "review_candidate_count": summary.get("review_candidate_count"),
        "blocked_candidate_count": summary.get("blocked_candidate_count"),
        "review_item_count": sum(len(_string_list(row.get("review_items"))) for row in evaluations),
        "blocker_count": sum(len(_string_list(row.get("blockers"))) for row in evaluations if not row.get("is_baseline")),
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


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


__all__ = [
    "build_maturity_narrative_recommendations",
    "build_maturity_narrative_summary",
    "build_maturity_narrative_warnings",
]
