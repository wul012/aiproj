from __future__ import annotations

from typing import Any

from minigpt.maturity_narrative_release import build_maturity_narrative_release_summary as _release_summary
from minigpt.maturity_narrative_summary_helpers import (
    _benchmark_history_summary,
    _coalesce,
    _counts,
    _dataset_summary,
    _decision_non_ready_candidates,
    _dict,
    _latest_history_boundary,
    _max_int,
    _merge_counts,
    _pick,
    _reason_count_detail,
    _request_summary,
    _scorecard_decision_summary,
    _scorecard_summary,
    _selected_decision_eval_status,
    _selected_decision_flag_delta,
    _selected_decision_run,
    _selected_history_best_candidate,
    _string_list,
    _unique_strings,
    _weakest_benchmark_case,
)


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
        "release_readiness_ci_workflow_regression_reasons": release.get("ci_workflow_regression_reasons"),
        "release_readiness_ci_workflow_regression_reason_counts": release.get("ci_workflow_regression_reason_counts"),
        "release_readiness_ci_tiny_plan_digest_gate_ready_regression_count": release.get(
            "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count"
        ),
        "release_readiness_ci_boundary_gate_check_ready_regression_count": release.get(
            "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count"
        ),
        "release_readiness_ci_boundary_plan_check_ready_regression_count": release.get(
            "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count"
        ),
        "release_readiness_ci_archived_path_portability_check_ready_regression_count": release.get(
            "ci_workflow_archived_path_portability_check_ready_regression_count"
        ),
        "release_readiness_ci_drift_smoke_ready_regression_count": release.get(
            "ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count"
        ),
        "release_readiness_max_ci_workflow_failed_check_delta": release.get("max_abs_ci_workflow_failed_check_delta"),
        "release_readiness_max_ci_workflow_order_violation_delta": release.get("max_abs_ci_workflow_order_violation_delta"),
        "release_readiness_test_coverage_regression_count": release.get("test_coverage_regression_count"),
        "release_readiness_test_coverage_status_changed_count": release.get("test_coverage_status_changed_count"),
        "release_readiness_max_test_coverage_percent_delta": release.get("max_abs_test_coverage_percent_delta"),
        "release_readiness_max_test_coverage_gap_delta": release.get("max_abs_test_coverage_gap_delta"),
        "release_readiness_benchmark_history_regression_count": release.get("benchmark_history_regression_count"),
        "release_readiness_benchmark_history_status_changed_count": release.get("benchmark_history_status_changed_count"),
        "release_readiness_benchmark_history_boundary_changed_count": release.get("benchmark_history_boundary_changed_count"),
        "release_readiness_benchmark_suite_design_delta_count": release.get(
            "benchmark_history_suite_design_non_comparison_ready_delta_count"
        ),
        "release_readiness_benchmark_suite_design_regression_count": release.get(
            "benchmark_history_suite_design_non_comparison_ready_regression_count"
        ),
        "release_readiness_benchmark_design_change_delta_count": release.get("benchmark_history_design_comparison_changed_delta_count"),
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
        "release_readiness_benchmark_requirement_failed_reason_mixed_delta_count": release.get(
            "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"
        ),
        "release_readiness_benchmark_requirement_failed_reason_drift_status_counts": release.get(
            "benchmark_history_readiness_requirement_failed_reason_drift_status_counts"
        ),
        "release_readiness_max_benchmark_history_case_regression_delta": release.get("max_abs_benchmark_history_case_regression_delta"),
        "release_readiness_max_benchmark_history_generation_flag_regression_delta": release.get(
            "max_abs_benchmark_history_generation_flag_regression_delta"
        ),
        "release_readiness_max_benchmark_suite_design_delta": release.get(
            "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta"
        ),
        "release_readiness_max_benchmark_design_change_delta": release.get("max_abs_benchmark_history_design_comparison_changed_entries_delta"),
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
        "benchmark_history_suite_design_non_comparison_ready_entry_count": sum(
            int(row.get("suite_design_non_comparison_ready_entry_count") or 0) for row in history_rows
        ),
        "benchmark_history_design_comparison_changed_entry_count": sum(
            int(row.get("design_comparison_changed_entry_count") or 0) for row in history_rows
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
    if int(summary.get("benchmark_history_suite_design_non_comparison_ready_entry_count") or 0) > 0:
        recommendations.append(
            "Fix benchmark history suite-design comparison readiness before treating repeated scorecard evidence as clean benchmark evidence."
        )
    if int(summary.get("benchmark_history_readiness_requirement_failed_count") or 0) > 0:
        recommendations.append(
            "Fix benchmark history readiness requirement failures before using the narrative as repeated model-evaluation evidence."
        )
    if int(summary.get("release_readiness_benchmark_requirement_status_changed_count") or 0) > 0:
        recommendations.append(
            "Review benchmark-history readiness requirement changes before treating the portfolio as release-stable."
        )
    if int(summary.get("release_readiness_benchmark_requirement_failed_reason_mixed_delta_count") or 0) > 0:
        recommendations.append(
            "Review mixed benchmark-history readiness failed-reason drift before treating the portfolio as release-stable; removals do not cancel newly added reasons."
        )
    if int(summary.get("release_readiness_benchmark_requirement_failed_reason_added_count") or 0) > 0:
        recommendations.append(
            "Review newly added benchmark-history readiness failed reasons before treating the portfolio as release-stable."
        )
    if int(summary.get("release_readiness_benchmark_suite_design_regression_count") or 0) > 0:
        recommendations.append(
            "Review release-readiness benchmark suite-design regressions before treating the portfolio as release-stable."
        )
    if int(summary.get("release_readiness_ci_workflow_regression_count") or 0) > 0:
        recommendations.append(
            "Review release readiness CI workflow regression reasons"
            + _reason_count_detail(summary.get("release_readiness_ci_workflow_regression_reason_counts"))
            + " before treating the portfolio as release-stable."
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
        or int(release.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count") or 0) > 0
        or int(release.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) > 0
        or int(release.get("benchmark_history_suite_design_non_comparison_ready_regression_count") or 0) > 0
        or request.get("status") in {"watch", "warn", "fail"}
        or any(row.get("overall_status") in {"warn", "fail"} for row in benchmark_rows)
        or any(row.get("decision_status") in {"review", "blocked"} for row in decision_rows)
        or any(int(row.get("non_comparison_ready_candidate_count") or 0) > 0 for row in decision_rows)
        or any(int(row.get("blocked_count") or 0) > 0 for row in history_rows)
        or any(int(row.get("review_count") or 0) > 0 for row in history_rows)
        or any(int(row.get("case_regression_entry_count") or 0) > 0 for row in history_rows)
        or any(int(row.get("generation_quality_flag_regression_entry_count") or 0) > 0 for row in history_rows)
        or any(int(row.get("suite_design_non_comparison_ready_entry_count") or 0) > 0 for row in history_rows)
        or any(row.get("readiness_requirement_status") == "fail" for row in history_rows)
        or any(row.get("quality_status") in {"warn", "fail"} for row in dataset_rows)
    ):
        return "review"
    return "ready"


__all__ = [
    "build_maturity_narrative_recommendations",
    "build_maturity_narrative_summary",
    "build_maturity_narrative_warnings",
]
