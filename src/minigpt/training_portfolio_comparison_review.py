from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict, format_mapping, number_or_none, positive_int_mapping


REVIEW_STATUSES = frozenset({"review", "warn", "fail", "incomplete"})
COVERAGE_REGRESSED_TREND = "coverage-regressed"
CI_REGRESSED_TREND = "ci-regressed"
BENCHMARK_REGRESSED_TREND = "benchmark-regressed"


def build_training_portfolio_recommendations(
    summary: dict[str, Any],
    deltas: list[dict[str, Any]] | None = None,
) -> list[str]:
    recs = []
    ci_reason_detail = _reason_count_detail(summary.get("maturity_ci_regression_reason_counts"))
    best_score_suite_design_regressed = (
        summary.get("best_score_maturity_release_readiness_trend") == BENCHMARK_REGRESSED_TREND
        and (_as_int(summary.get("best_score_maturity_release_readiness_benchmark_suite_design_regression_count")) or 0) > 0
    )
    if summary.get("failed_count"):
        recs.append("Inspect failed portfolio steps before treating downstream benchmark or maturity evidence as comparable.")
    if summary.get("planned_count"):
        recs.append("Run planned portfolios with --execute before using them as model-quality evidence.")
    if summary.get("artifact_regression_count"):
        recs.append("Review artifact coverage regressions; missing scorecards, dataset cards, or manifests weaken the comparison.")
    if summary.get("score_regression_count") or summary.get("loss_regression_count"):
        recs.append("Compare the regressed portfolio's dataset version, training config, and weakest benchmark cases against the baseline.")
    if summary.get("dataset_warning_count"):
        recs.append("Resolve dataset-card warnings before using the best-scoring run as a maturity baseline.")
    if summary.get("maturity_review_count"):
        if is_review_status(summary.get("best_score_maturity_status")):
            if not best_score_suite_design_regressed:
                recs.append("Review the best-scoring portfolio's maturity narrative before promoting it as a clean baseline.")
        else:
            recs.append("Review maturity-narrative findings for non-leading portfolios before archiving the comparison.")
    if summary.get("maturity_coverage_regression_count"):
        if (
            summary.get("best_score_maturity_release_readiness_trend") == COVERAGE_REGRESSED_TREND
            or (_as_int(summary.get("best_score_maturity_release_readiness_test_coverage_regression_count")) or 0) > 0
        ):
            recs.append("Block best-score promotion until release-readiness test coverage regressions are explained or fixed.")
        else:
            recs.append("Review coverage-regressed maturity narratives before using non-leading portfolios as future baselines.")
    if summary.get("maturity_ci_regression_count"):
        if (
            summary.get("best_score_maturity_release_readiness_trend") == CI_REGRESSED_TREND
            or (_as_int(summary.get("best_score_maturity_release_readiness_ci_workflow_regression_count")) or 0) > 0
            or (_as_int(summary.get("best_score_maturity_release_readiness_ci_workflow_order_regression_count")) or 0) > 0
            or (_as_int(summary.get("best_score_maturity_release_readiness_ci_boundary_plan_check_ready_regression_count")) or 0) > 0
            or (_as_int(summary.get("best_score_maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count")) or 0) > 0
        ):
            recs.append(
                "Block best-score promotion until release-readiness CI workflow regressions are explained or fixed"
                + (f" ({ci_reason_detail})." if ci_reason_detail else ".")
            )
        else:
            recs.append(
                "Review CI-regressed maturity narratives before using non-leading portfolios as future baselines"
                + (f" ({ci_reason_detail})." if ci_reason_detail else ".")
            )
    if summary.get("maturity_suite_design_regression_count"):
        if best_score_suite_design_regressed:
            recs.append("Block best-score promotion until release-readiness benchmark suite-design regressions are explained or fixed.")
        else:
            recs.append("Review suite-design-regressed maturity narratives before using non-leading portfolios as future baselines.")
    if not recs:
        recs.append("Use the best-scoring portfolio as the next baseline, then repeat the comparison after larger-corpus training.")
    return recs


def build_training_portfolio_review_actions(
    summary: dict[str, Any],
    portfolios: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    deltas_by_name = {row.get("name"): row for row in deltas}
    actions = []
    best_score_name = _as_str(summary.get("best_score_name"))
    for portfolio in portfolios:
        name = _as_str(portfolio.get("name")) or f"portfolio-{portfolio.get('index') or len(actions) + 1}"
        delta = as_dict(deltas_by_name.get(portfolio.get("name")))
        status = _as_str(portfolio.get("status"))
        if status == "failed":
            actions.append(
                _review_action(
                    actions,
                    name,
                    "execution",
                    "blocker",
                    "portfolio_failed",
                    "Inspect the failed step before comparing benchmark or maturity evidence.",
                    {"failed_step": portfolio.get("failed_step")},
                )
            )
        elif status == "planned":
            actions.append(
                _review_action(
                    actions,
                    name,
                    "execution",
                    "review",
                    "portfolio_not_executed",
                    "Run the planned portfolio with --execute before using it as model-quality evidence.",
                    {"completed_steps": portfolio.get("completed_steps"), "step_count": portfolio.get("step_count")},
                )
            )

        missing_artifacts = [
            str(row.get("key"))
            for row in portfolio.get("core_artifacts", [])
            if isinstance(row, dict) and not row.get("exists") and row.get("key")
        ]
        artifact_delta = _number(delta.get("artifact_coverage_delta"))
        if missing_artifacts or (artifact_delta is not None and float(artifact_delta) < 0):
            actions.append(
                _review_action(
                    actions,
                    name,
                    "artifact",
                    "review",
                    "artifact_coverage_gap",
                    "Restore missing core artifacts before treating the comparison as a complete handoff.",
                    {"missing_artifacts": missing_artifacts, "artifact_coverage_delta": artifact_delta},
                )
            )

        if delta.get("overall_relation") == "regressed" or delta.get("final_val_loss_relation") == "regressed":
            actions.append(
                _review_action(
                    actions,
                    name,
                    "quality",
                    "review",
                    "quality_regression",
                    "Compare dataset version, training config, validation loss, and weakest benchmark cases against the baseline.",
                    {
                        "overall_relation": delta.get("overall_relation"),
                        "final_val_loss_relation": delta.get("final_val_loss_relation"),
                    },
                )
            )

        dataset_status = _as_str(portfolio.get("dataset_readiness_status"))
        dataset_quality = _as_str(portfolio.get("dataset_quality_status"))
        dataset_warning_count = _as_int(portfolio.get("dataset_warning_count")) or 0
        if dataset_warning_count > 0 or is_review_status(dataset_status) or is_review_status(dataset_quality):
            actions.append(
                _review_action(
                    actions,
                    name,
                    "dataset",
                    "review",
                    "dataset_card_review",
                    "Resolve dataset-card warnings before using this portfolio as a maturity baseline.",
                    {
                        "dataset_readiness_status": dataset_status,
                        "dataset_quality_status": dataset_quality,
                        "dataset_warning_count": dataset_warning_count,
                    },
                )
            )

        coverage_regressed = has_maturity_coverage_regression(portfolio)
        if coverage_regressed:
            is_best_score = name == best_score_name
            actions.append(
                _review_action(
                    actions,
                    name,
                    "maturity",
                    "blocker" if is_best_score else "review",
                    "best_score_coverage_regressed" if is_best_score else "portfolio_coverage_regressed",
                    (
                        "Explain or fix release-readiness test coverage regressions before promoting this best-scoring portfolio."
                        if is_best_score
                        else "Review release-readiness test coverage regressions before archiving this portfolio as a future baseline."
                    ),
                    {
                        "maturity_release_readiness_trend": portfolio.get("maturity_release_readiness_trend"),
                        "coverage_regression_count": portfolio.get("maturity_release_readiness_test_coverage_regression_count"),
                        "coverage_status_changed_count": portfolio.get("maturity_release_readiness_test_coverage_status_changed_count"),
                        "max_test_coverage_percent_delta": portfolio.get("maturity_release_readiness_max_test_coverage_percent_delta"),
                        "max_test_coverage_gap_delta": portfolio.get("maturity_release_readiness_max_test_coverage_gap_delta"),
                        "best_score_name": best_score_name,
                    },
                )
            )

        ci_regressed = has_maturity_ci_regression(portfolio)
        if ci_regressed:
            is_best_score = name == best_score_name
            ci_reason_detail = _reason_count_detail(
                portfolio.get("maturity_release_readiness_ci_workflow_regression_reason_counts")
            )
            actions.append(
                _review_action(
                    actions,
                    name,
                    "maturity",
                    "blocker" if is_best_score else "review",
                    "best_score_ci_regressed" if is_best_score else "portfolio_ci_regressed",
                    (
                        "Explain or fix release-readiness CI workflow regressions before promoting this best-scoring portfolio"
                        if is_best_score
                        else "Review release-readiness CI workflow regressions before archiving this portfolio as a future baseline"
                    )
                    + (f" ({ci_reason_detail})." if ci_reason_detail else "."),
                    {
                        "maturity_release_readiness_trend": portfolio.get("maturity_release_readiness_trend"),
                        "ci_workflow_regression_count": portfolio.get("maturity_release_readiness_ci_workflow_regression_count"),
                        "ci_workflow_order_regression_count": portfolio.get("maturity_release_readiness_ci_workflow_order_regression_count"),
                        "ci_workflow_status_changed_count": portfolio.get("maturity_release_readiness_ci_workflow_status_changed_count"),
                        "max_ci_workflow_failed_check_delta": portfolio.get("maturity_release_readiness_max_ci_workflow_failed_check_delta"),
                        "max_ci_workflow_order_violation_delta": portfolio.get("maturity_release_readiness_max_ci_workflow_order_violation_delta"),
                        "ci_workflow_regression_reasons": portfolio.get("maturity_release_readiness_ci_workflow_regression_reasons"),
                        "ci_workflow_regression_reason_counts": portfolio.get("maturity_release_readiness_ci_workflow_regression_reason_counts"),
                        "ci_tiny_plan_digest_gate_ready_regression_count": portfolio.get(
                            "maturity_release_readiness_ci_tiny_plan_digest_gate_ready_regression_count"
                        ),
                        "ci_boundary_gate_check_ready_regression_count": portfolio.get(
                            "maturity_release_readiness_ci_boundary_gate_check_ready_regression_count"
                        ),
                        "ci_boundary_plan_check_ready_regression_count": portfolio.get(
                            "maturity_release_readiness_ci_boundary_plan_check_ready_regression_count"
                        ),
                        "ci_archived_path_portability_check_ready_regression_count": portfolio.get(
                            "maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count"
                        ),
                        "ci_drift_smoke_ready_regression_count": portfolio.get(
                            "maturity_release_readiness_ci_drift_smoke_ready_regression_count"
                        ),
                        "best_score_name": best_score_name,
                    },
                )
            )

        suite_design_regressed = has_maturity_suite_design_regression(portfolio)
        if suite_design_regressed:
            is_best_score = name == best_score_name
            actions.append(
                _review_action(
                    actions,
                    name,
                    "maturity",
                    "blocker" if is_best_score else "review",
                    "best_score_suite_design_regressed" if is_best_score else "portfolio_suite_design_regressed",
                    (
                        "Explain or fix release-readiness benchmark suite-design regressions before promoting this best-scoring portfolio."
                        if is_best_score
                        else "Review release-readiness benchmark suite-design regressions before archiving this portfolio as a future baseline."
                    ),
                    {
                        "maturity_release_readiness_trend": portfolio.get("maturity_release_readiness_trend"),
                        "suite_design_delta_count": portfolio.get("maturity_release_readiness_benchmark_suite_design_delta_count"),
                        "suite_design_regression_count": portfolio.get("maturity_release_readiness_benchmark_suite_design_regression_count"),
                        "design_change_delta_count": portfolio.get("maturity_release_readiness_benchmark_design_change_delta_count"),
                        "max_suite_design_delta": portfolio.get("maturity_release_readiness_max_benchmark_suite_design_delta"),
                        "max_design_change_delta": portfolio.get("maturity_release_readiness_max_benchmark_design_change_delta"),
                        "best_score_name": best_score_name,
                    },
                )
            )

        maturity_status = _as_str(portfolio.get("maturity_portfolio_status"))
        if is_review_status(maturity_status) and not coverage_regressed and not ci_regressed and not suite_design_regressed:
            is_best_score = name == best_score_name
            actions.append(
                _review_action(
                    actions,
                    name,
                    "maturity",
                    "blocker" if is_best_score else "review",
                    "best_score_maturity_review" if is_best_score else "non_leading_maturity_review",
                    (
                        "Review this best-scoring portfolio's maturity narrative before promoting it as a clean baseline."
                        if is_best_score
                        else "Review maturity-narrative findings before archiving this non-leading portfolio."
                    ),
                    {"maturity_portfolio_status": maturity_status, "best_score_name": best_score_name},
                )
            )
    return actions


def is_review_status(value: Any) -> bool:
    text = _as_str(value)
    return text in REVIEW_STATUSES if text is not None else False


def has_maturity_coverage_regression(portfolio: dict[str, Any]) -> bool:
    regression_count = _as_int(portfolio.get("maturity_release_readiness_test_coverage_regression_count")) or 0
    return (
        portfolio.get("maturity_release_readiness_trend") == COVERAGE_REGRESSED_TREND
        or regression_count > 0
    )


def has_maturity_ci_regression(portfolio: dict[str, Any]) -> bool:
    regression_count = _as_int(portfolio.get("maturity_release_readiness_ci_workflow_regression_count")) or 0
    order_regression_count = _as_int(portfolio.get("maturity_release_readiness_ci_workflow_order_regression_count")) or 0
    ready_regression_count = sum(
        _as_int(portfolio.get(key)) or 0
        for key in [
            "maturity_release_readiness_ci_tiny_plan_digest_gate_ready_regression_count",
            "maturity_release_readiness_ci_boundary_gate_check_ready_regression_count",
            "maturity_release_readiness_ci_boundary_plan_check_ready_regression_count",
            "maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count",
            "maturity_release_readiness_ci_drift_smoke_ready_regression_count",
        ]
    )
    return (
        portfolio.get("maturity_release_readiness_trend") == CI_REGRESSED_TREND
        or regression_count > 0
        or order_regression_count > 0
        or ready_regression_count > 0
    )


def has_maturity_suite_design_regression(portfolio: dict[str, Any]) -> bool:
    regression_count = _as_int(portfolio.get("maturity_release_readiness_benchmark_suite_design_regression_count")) or 0
    return (
        portfolio.get("maturity_release_readiness_trend") == BENCHMARK_REGRESSED_TREND
        and regression_count > 0
    )


def _review_action(
    actions: list[dict[str, Any]],
    portfolio: str,
    category: str,
    severity: str,
    reason: str,
    action: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": f"{category}-{len(actions) + 1}",
        "portfolio": portfolio,
        "category": category,
        "severity": severity,
        "reason": reason,
        "action": action,
        "evidence": evidence,
    }


def _number(value: Any) -> float | int | None:
    return number_or_none(value)


def _as_int(value: Any) -> int | None:
    number = number_or_none(value, int)
    return None if number is None else int(number)


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _reason_count_detail(value: Any) -> str:
    detail = format_mapping(positive_int_mapping(value))
    return "" if detail == "none" else detail


__all__ = [
    "CI_REGRESSED_TREND",
    "BENCHMARK_REGRESSED_TREND",
    "COVERAGE_REGRESSED_TREND",
    "REVIEW_STATUSES",
    "build_training_portfolio_recommendations",
    "build_training_portfolio_review_actions",
    "has_maturity_ci_regression",
    "has_maturity_coverage_regression",
    "has_maturity_suite_design_regression",
    "is_review_status",
]
