from __future__ import annotations

from typing import Any


def build_maturity_narrative_summary(
    maturity: dict[str, Any] | None,
    registry: dict[str, Any] | None,
    request_history: dict[str, Any] | None,
    scorecards: list[dict[str, Any] | None],
    scorecard_decisions: list[dict[str, Any] | None],
    dataset_cards: list[dict[str, Any] | None],
    benchmark_histories: list[dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    maturity_summary = _dict(_pick(maturity, "summary"))
    release = _release_summary(maturity_summary, _dict(_pick(maturity, "release_readiness_context")))
    request = _request_summary(maturity, request_history)
    benchmark_rows = [_scorecard_summary(item) for item in scorecards if isinstance(item, dict)]
    decision_rows = [_scorecard_decision_summary(item) for item in scorecard_decisions if isinstance(item, dict)]
    history_rows = [_benchmark_history_summary(item) for item in (benchmark_histories or []) if isinstance(item, dict)]
    dataset_rows = [_dataset_summary(item) for item in dataset_cards if isinstance(item, dict)]
    benchmark_scores = [row["overall_score"] for row in benchmark_rows if row.get("overall_score") is not None]
    dataset_warnings = sum(int(row.get("warning_count") or 0) for row in dataset_rows)
    decision_non_ready_count = sum(int(row.get("non_comparison_ready_candidate_count") or 0) for row in decision_rows)
    status = _portfolio_status(
        maturity_summary,
        release,
        request,
        benchmark_rows,
        decision_rows,
        history_rows,
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
        "release_readiness_ci_workflow_regression_count": release.get("ci_workflow_regression_count"),
        "release_readiness_ci_workflow_order_regression_count": release.get("ci_workflow_order_regression_count"),
        "release_readiness_ci_workflow_status_changed_count": release.get("ci_workflow_status_changed_count"),
        "release_readiness_max_ci_workflow_failed_check_delta": release.get("max_abs_ci_workflow_failed_check_delta"),
        "release_readiness_max_ci_workflow_order_violation_delta": release.get("max_abs_ci_workflow_order_violation_delta"),
        "release_readiness_test_coverage_regression_count": release.get("test_coverage_regression_count"),
        "release_readiness_test_coverage_status_changed_count": release.get("test_coverage_status_changed_count"),
        "release_readiness_max_test_coverage_percent_delta": release.get("max_abs_test_coverage_percent_delta"),
        "release_readiness_max_test_coverage_gap_delta": release.get("max_abs_test_coverage_gap_delta"),
        "release_readiness_benchmark_history_regression_count": release.get("benchmark_history_regression_count"),
        "release_readiness_benchmark_history_status_changed_count": release.get("benchmark_history_status_changed_count"),
        "release_readiness_benchmark_history_boundary_changed_count": release.get("benchmark_history_boundary_changed_count"),
        "release_readiness_benchmark_requirement_status_changed_count": release.get(
            "benchmark_history_readiness_requirement_status_changed_count"
        ),
        "release_readiness_benchmark_requirement_exit_code_delta_max": release.get(
            "max_abs_benchmark_history_readiness_requirement_exit_code_delta"
        ),
        "release_readiness_benchmark_requirement_failed_reason_added_count": release.get(
            "benchmark_history_readiness_requirement_failed_reason_added_count"
        ),
        "release_readiness_benchmark_requirement_failed_reason_removed_count": release.get(
            "benchmark_history_readiness_requirement_failed_reason_removed_count"
        ),
        "release_readiness_benchmark_requirement_failed_reason_added": release.get(
            "benchmark_history_readiness_requirement_failed_reason_added"
        ),
        "release_readiness_benchmark_requirement_failed_reason_removed": release.get(
            "benchmark_history_readiness_requirement_failed_reason_removed"
        ),
        "release_readiness_benchmark_requirement_failed_reason_recovery_delta_count": release.get(
            "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"
        ),
        "release_readiness_benchmark_requirement_failed_reason_drift_status_counts": release.get(
            "benchmark_history_readiness_requirement_failed_reason_drift_status_counts"
        ),
        "release_readiness_max_benchmark_history_case_regression_delta": release.get("max_abs_benchmark_history_case_regression_delta"),
        "release_readiness_max_benchmark_history_generation_flag_regression_delta": release.get(
            "max_abs_benchmark_history_generation_flag_regression_delta"
        ),
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
        "benchmark_decision_selected_eval_suite_comparison_status": _selected_decision_eval_status(decision_rows),
        "benchmark_decision_non_comparison_ready_candidate_count": decision_non_ready_count,
        "benchmark_decision_non_comparison_ready_candidates": _decision_non_ready_candidates(decision_rows),
        "benchmark_decision_eval_suite_comparison_status_counts": _merge_counts(
            row.get("eval_suite_comparison_status_counts") for row in decision_rows
        ),
        "benchmark_history_count": len(history_rows),
        "benchmark_history_entry_count": sum(int(row.get("entry_count") or 0) for row in history_rows),
        "benchmark_history_ready_count": sum(int(row.get("ready_count") or 0) for row in history_rows),
        "benchmark_history_promote_count": sum(int(row.get("promote_count") or 0) for row in history_rows),
        "benchmark_history_review_count": sum(int(row.get("review_count") or 0) for row in history_rows),
        "benchmark_history_blocked_count": sum(int(row.get("blocked_count") or 0) for row in history_rows),
        "benchmark_history_case_regression_entry_count": sum(int(row.get("case_regression_entry_count") or 0) for row in history_rows),
        "benchmark_history_generation_flag_regression_entry_count": sum(
            int(row.get("generation_quality_flag_regression_entry_count") or 0) for row in history_rows
        ),
        "benchmark_history_readiness_requirement_status_counts": _counts(
            row.get("readiness_requirement_status") or "missing" for row in history_rows
        ),
        "benchmark_history_readiness_requirement_failed_count": sum(
            1 for row in history_rows if row.get("readiness_requirement_status") == "fail"
        ),
        "benchmark_history_readiness_requirement_exit_code_max": _max_int(
            row.get("readiness_requirement_exit_code") for row in history_rows
        ),
        "benchmark_history_readiness_requirement_failed_reasons": _unique_strings(
            reason
            for row in history_rows
            for reason in _string_list(row.get("readiness_requirement_failed_reasons"))
        ),
        "benchmark_history_model_quality_claim_counts": _counts(
            row.get("model_quality_claim") or "missing" for row in history_rows
        ),
        "benchmark_history_boundary_counts": _merge_counts(row.get("boundary_counts") for row in history_rows),
        "benchmark_history_best_candidate": _selected_history_best_candidate(history_rows),
        "benchmark_history_latest_boundary": _latest_history_boundary(history_rows),
        "dataset_card_count": len(dataset_rows),
        "dataset_status_counts": _counts(row.get("quality_status") or "missing" for row in dataset_rows),
        "dataset_warning_count": dataset_warnings,
    }


def build_maturity_narrative_recommendations(summary: dict[str, Any], sections: list[dict[str, Any]]) -> list[str]:
    recommendations = []
    if int(summary.get("benchmark_decision_non_comparison_ready_candidate_count") or 0) > 0:
        recommendations.append(
            "Treat scorecard promotion as review-only until non-comparison-ready eval suites are rerun with comparable benchmark evidence."
        )
    if int(summary.get("benchmark_history_readiness_requirement_failed_count") or 0) > 0:
        recommendations.append(
            "Fix benchmark history readiness requirement failures before using the narrative as repeated model-evaluation evidence."
        )
    if int(summary.get("release_readiness_benchmark_requirement_status_changed_count") or 0) > 0:
        recommendations.append(
            "Review benchmark-history readiness requirement changes before treating the portfolio as release-stable."
        )
    if int(summary.get("release_readiness_benchmark_requirement_failed_reason_added_count") or 0) > 0:
        recommendations.append(
            "Review newly added benchmark-history readiness failed reasons before treating the portfolio as release-stable."
        )
    if int(summary.get("benchmark_history_blocked_count") or 0) > 0:
        recommendations.append("Inspect blocked benchmark history entries before using the portfolio as release-ready evidence.")
    elif int(summary.get("benchmark_history_case_regression_entry_count") or 0) > 0:
        recommendations.append("Review benchmark history entries with case regressions before treating score deltas as model improvement.")
    elif int(summary.get("benchmark_history_generation_flag_regression_entry_count") or 0) > 0:
        recommendations.append("Review benchmark history generation-quality flag regressions before promoting the selected candidate.")
    elif int(summary.get("benchmark_history_review_count") or 0) > 0:
        recommendations.append("Inspect benchmark history entries marked review before treating the portfolio as release-ready.")
    if summary.get("portfolio_status") == "review":
        recommendations.append(
            "Resolve review-level release, request-history, benchmark, or dataset concerns before using this as a release-ready portfolio summary."
        )
        return recommendations
    if summary.get("portfolio_status") == "incomplete":
        return ["Generate missing maturity, request-history, benchmark scorecard, or dataset-card evidence before presenting the narrative."]
    if int(summary.get("benchmark_history_count") or 0) == 0:
        recommendations.append("Add benchmark history ledgers so scorecard comparisons and decisions can be reviewed across repeated runs.")
    if int(summary.get("release_readiness_benchmark_requirement_failed_reason_recovery_delta_count") or 0) > 0:
        recommendations.append(
            "Preserve benchmark readiness failed-reason recovery evidence as a stability signal, but keep it separate from model-quality claims."
        )
    return [
        *recommendations,
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
    decision_rows: list[dict[str, Any]],
    history_rows: list[dict[str, Any]],
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
        or release.get("trend_status") in {"regressed", "ci-regressed", "coverage-regressed", "benchmark-regressed"}
        or int(release.get("regressed_count") or 0) > 0
        or int(release.get("ci_workflow_regression_count") or 0) > 0
        or int(release.get("ci_workflow_order_regression_count") or 0) > 0
        or int(release.get("test_coverage_regression_count") or 0) > 0
        or int(release.get("benchmark_history_regression_count") or 0) > 0
        or int(release.get("benchmark_history_readiness_requirement_status_changed_count") or 0) > 0
        or int(release.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) > 0
        or request.get("status") in {"watch", "warn", "fail"}
        or any(row.get("overall_status") in {"warn", "fail"} for row in benchmark_rows)
        or any(row.get("decision_status") in {"review", "blocked"} for row in decision_rows)
        or any(int(row.get("non_comparison_ready_candidate_count") or 0) > 0 for row in decision_rows)
        or any(int(row.get("blocked_count") or 0) > 0 for row in history_rows)
        or any(int(row.get("review_count") or 0) > 0 for row in history_rows)
        or any(int(row.get("case_regression_entry_count") or 0) > 0 for row in history_rows)
        or any(int(row.get("generation_quality_flag_regression_entry_count") or 0) > 0 for row in history_rows)
        or any(row.get("readiness_requirement_status") == "fail" for row in history_rows)
        or any(row.get("quality_status") in {"warn", "fail"} for row in dataset_rows)
    ):
        return "review"
    return "ready"


def _request_summary(maturity: dict[str, Any] | None, request_history: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(request_history, dict):
        return _dict(request_history.get("summary"))
    return _dict(_pick(maturity, "request_history_context"))


def _release_summary(maturity_summary: dict[str, Any], release_context: dict[str, Any]) -> dict[str, Any]:
    trend_status = _coalesce(release_context.get("trend_status"), maturity_summary.get("release_readiness_trend_status"))
    requirement_status_changed_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_status_changed_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_status_changed_count"),
    )
    requirement_exit_code_delta = _coalesce(
        release_context.get("max_abs_benchmark_history_readiness_requirement_exit_code_delta"),
        maturity_summary.get("release_readiness_benchmark_requirement_exit_code_delta_max"),
    )
    requirement_reason_added_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_added_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_added_count"),
    )
    requirement_reason_removed_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_removed_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_removed_count"),
    )
    requirement_reason_added = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_added"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_added"),
        [],
    )
    requirement_reason_removed = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_removed"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_removed"),
        [],
    )
    requirement_reason_recovery_delta_count = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_recovery_delta_count"),
    )
    requirement_reason_drift_status_counts = _coalesce(
        release_context.get("benchmark_history_readiness_requirement_failed_reason_drift_status_counts"),
        maturity_summary.get("release_readiness_benchmark_requirement_failed_reason_drift_status_counts"),
        {},
    )
    if int(requirement_status_changed_count or 0) > 0 or int(requirement_reason_added_count or 0) > 0:
        trend_status = "benchmark-regressed"
    return {
        **release_context,
        "trend_status": trend_status,
        "regressed_count": _coalesce(release_context.get("regressed_count"), maturity_summary.get("release_readiness_regressed_count")),
        "improved_count": _coalesce(release_context.get("improved_count"), maturity_summary.get("release_readiness_improved_count")),
        "ci_workflow_regression_count": _coalesce(
            release_context.get("ci_workflow_regression_count"),
            maturity_summary.get("release_readiness_ci_workflow_regression_count"),
        ),
        "ci_workflow_order_regression_count": _coalesce(
            release_context.get("ci_workflow_order_regression_count"),
            maturity_summary.get("release_readiness_ci_workflow_order_regression_count"),
        ),
        "ci_workflow_status_changed_count": _coalesce(
            release_context.get("ci_workflow_status_changed_count"),
            maturity_summary.get("release_readiness_ci_workflow_status_changed_count"),
        ),
        "max_abs_ci_workflow_failed_check_delta": _coalesce(
            release_context.get("max_abs_ci_workflow_failed_check_delta"),
            maturity_summary.get("release_readiness_max_ci_workflow_failed_check_delta"),
        ),
        "max_abs_ci_workflow_order_violation_delta": _coalesce(
            release_context.get("max_abs_ci_workflow_order_violation_delta"),
            maturity_summary.get("release_readiness_max_ci_workflow_order_violation_delta"),
        ),
        "test_coverage_regression_count": _coalesce(
            release_context.get("test_coverage_regression_count"),
            maturity_summary.get("release_readiness_test_coverage_regression_count"),
        ),
        "test_coverage_status_changed_count": _coalesce(
            release_context.get("test_coverage_status_changed_count"),
            maturity_summary.get("release_readiness_test_coverage_status_changed_count"),
        ),
        "max_abs_test_coverage_percent_delta": _coalesce(
            release_context.get("max_abs_test_coverage_percent_delta"),
            maturity_summary.get("release_readiness_max_test_coverage_percent_delta"),
        ),
        "max_abs_test_coverage_gap_delta": _coalesce(
            release_context.get("max_abs_test_coverage_gap_delta"),
            maturity_summary.get("release_readiness_max_test_coverage_gap_delta"),
        ),
        "benchmark_history_regression_count": _coalesce(
            release_context.get("benchmark_history_regression_count"),
            maturity_summary.get("release_readiness_benchmark_history_regression_count"),
        ),
        "benchmark_history_status_changed_count": _coalesce(
            release_context.get("benchmark_history_status_changed_count"),
            maturity_summary.get("release_readiness_benchmark_history_status_changed_count"),
        ),
        "benchmark_history_boundary_changed_count": _coalesce(
            release_context.get("benchmark_history_boundary_changed_count"),
            maturity_summary.get("release_readiness_benchmark_history_boundary_changed_count"),
        ),
        "benchmark_history_readiness_requirement_status_changed_count": requirement_status_changed_count,
        "max_abs_benchmark_history_readiness_requirement_exit_code_delta": requirement_exit_code_delta,
        "benchmark_history_readiness_requirement_failed_reason_added_count": requirement_reason_added_count,
        "benchmark_history_readiness_requirement_failed_reason_removed_count": requirement_reason_removed_count,
        "benchmark_history_readiness_requirement_failed_reason_added": _string_list(requirement_reason_added),
        "benchmark_history_readiness_requirement_failed_reason_removed": _string_list(requirement_reason_removed),
        "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": requirement_reason_recovery_delta_count,
        "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": _dict(requirement_reason_drift_status_counts),
        "max_abs_benchmark_history_case_regression_delta": _coalesce(
            release_context.get("max_abs_benchmark_history_case_regression_delta"),
            maturity_summary.get("release_readiness_max_benchmark_history_case_regression_delta"),
        ),
        "max_abs_benchmark_history_generation_flag_regression_delta": _coalesce(
            release_context.get("max_abs_benchmark_history_generation_flag_regression_delta"),
            maturity_summary.get("release_readiness_max_benchmark_history_generation_flag_regression_delta"),
        ),
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
