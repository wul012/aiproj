from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import format_mapping as _format_mapping
from minigpt.report_utils import positive_int_mapping as _int_mapping
from minigpt.report_utils import utc_now
from minigpt.training_portfolio_comparison_artifacts import (
    render_training_portfolio_comparison_html,
    render_training_portfolio_comparison_markdown,
    write_training_portfolio_comparison_csv,
    write_training_portfolio_comparison_html,
    write_training_portfolio_comparison_json,
    write_training_portfolio_comparison_markdown,
    write_training_portfolio_comparison_outputs,
)
from minigpt.training_portfolio_comparison_portfolio import build_training_portfolio_summary as _portfolio_summary
from minigpt.training_portfolio_comparison_review import (
    build_training_portfolio_recommendations,
    build_training_portfolio_review_actions,
    has_maturity_ci_regression,
    has_maturity_coverage_regression,
    has_maturity_suite_design_regression,
    is_review_status,
)


def load_training_portfolio(path: str | Path) -> dict[str, Any]:
    portfolio_path = _resolve_portfolio_path(Path(path))
    payload = json.loads(portfolio_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training portfolio must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(portfolio_path)
    return payload


def build_training_portfolio_comparison(
    portfolio_paths: list[str | Path],
    *,
    names: list[str] | None = None,
    baseline: str | int | None = None,
    title: str = "MiniGPT training portfolio comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not portfolio_paths:
        raise ValueError("at least one training portfolio is required")
    if names is not None and len(names) != len(portfolio_paths):
        raise ValueError("names length must match portfolio_paths length")

    reports = [load_training_portfolio(path) for path in portfolio_paths]
    resolved_names = _resolve_names(reports, names)
    portfolios = [
        _portfolio_summary(report, resolved_names[index], index)
        for index, report in enumerate(reports)
    ]
    baseline_portfolio = _select_baseline(portfolios, baseline)
    deltas = [_portfolio_delta(item, baseline_portfolio) for item in portfolios]
    summary = _comparison_summary(portfolios, baseline_portfolio, deltas)
    review_actions = build_training_portfolio_review_actions(summary, portfolios, deltas)
    summary = dict(summary)
    summary["review_action_count"] = len(review_actions)
    summary["blocker_action_count"] = sum(1 for action in review_actions if action.get("severity") == "blocker")
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "portfolio_count": len(portfolios),
        "baseline": baseline_portfolio,
        "portfolios": portfolios,
        "baseline_deltas": deltas,
        "summary": summary,
        "best_by_overall_score": _best_numeric(portfolios, "overall_score", higher_is_better=True),
        "best_by_rubric_avg_score": _best_numeric(portfolios, "rubric_avg_score", higher_is_better=True),
        "best_by_artifact_coverage": _best_numeric(portfolios, "artifact_coverage", higher_is_better=True),
        "best_by_final_val_loss": _best_numeric(portfolios, "final_val_loss", higher_is_better=False),
        "review_actions": review_actions,
        "recommendations": build_training_portfolio_recommendations(summary, deltas),
    }


def _resolve_portfolio_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates = [path / "training_portfolio.json"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"training portfolio not found: {path}")


def _resolve_names(reports: list[dict[str, Any]], names: list[str] | None) -> list[str]:
    if names is not None:
        return [str(name) for name in names]
    resolved = []
    for index, report in enumerate(reports, start=1):
        run_name = _as_str(report.get("run_name"))
        source_path = _as_str(report.get("_source_path"))
        if run_name:
            resolved.append(run_name)
        elif source_path:
            resolved.append(Path(source_path).parent.name or f"portfolio-{index}")
        else:
            resolved.append(f"portfolio-{index}")
    return resolved


def _portfolio_delta(portfolio: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    is_baseline = portfolio.get("name") == baseline.get("name")
    overall_delta = _numeric_delta(portfolio.get("overall_score"), baseline.get("overall_score"))
    rubric_delta = _numeric_delta(portfolio.get("rubric_avg_score"), baseline.get("rubric_avg_score"))
    val_loss_delta = _numeric_delta(portfolio.get("final_val_loss"), baseline.get("final_val_loss"))
    artifact_delta = _numeric_delta(portfolio.get("artifact_coverage"), baseline.get("artifact_coverage"))
    available_artifact_delta = _int_delta(portfolio.get("available_artifact_count"), baseline.get("available_artifact_count"))
    dataset_warning_delta = _int_delta(portfolio.get("dataset_warning_count"), baseline.get("dataset_warning_count"))
    ci_regression_delta = _int_delta(
        portfolio.get("maturity_release_readiness_ci_workflow_regression_count"),
        baseline.get("maturity_release_readiness_ci_workflow_regression_count"),
    )
    ci_order_regression_delta = _int_delta(
        portfolio.get("maturity_release_readiness_ci_workflow_order_regression_count"),
        baseline.get("maturity_release_readiness_ci_workflow_order_regression_count"),
    )
    coverage_regression_delta = _int_delta(
        portfolio.get("maturity_release_readiness_test_coverage_regression_count"),
        baseline.get("maturity_release_readiness_test_coverage_regression_count"),
    )
    suite_design_regression_delta = _int_delta(
        portfolio.get("maturity_release_readiness_benchmark_suite_design_regression_count"),
        baseline.get("maturity_release_readiness_benchmark_suite_design_regression_count"),
    )
    suite_design_delta_count_delta = _int_delta(
        portfolio.get("maturity_release_readiness_benchmark_suite_design_delta_count"),
        baseline.get("maturity_release_readiness_benchmark_suite_design_delta_count"),
    )
    design_change_delta = _int_delta(
        portfolio.get("maturity_release_readiness_benchmark_design_change_delta_count"),
        baseline.get("maturity_release_readiness_benchmark_design_change_delta_count"),
    )
    return {
        "name": portfolio.get("name"),
        "baseline_name": baseline.get("name"),
        "is_baseline": is_baseline,
        "status_changed": portfolio.get("status") != baseline.get("status"),
        "artifact_coverage_delta": artifact_delta,
        "available_artifact_delta": available_artifact_delta,
        "overall_score_delta": overall_delta,
        "rubric_avg_score_delta": rubric_delta,
        "final_val_loss_delta": val_loss_delta,
        "dataset_warning_delta": dataset_warning_delta,
        "maturity_status_changed": portfolio.get("maturity_portfolio_status") != baseline.get("maturity_portfolio_status"),
        "maturity_release_readiness_trend_changed": portfolio.get("maturity_release_readiness_trend") != baseline.get("maturity_release_readiness_trend"),
        "maturity_release_readiness_ci_workflow_regression_delta": ci_regression_delta,
        "maturity_release_readiness_ci_workflow_order_regression_delta": ci_order_regression_delta,
        "maturity_release_readiness_test_coverage_regression_delta": coverage_regression_delta,
        "maturity_release_readiness_benchmark_suite_design_delta_count_delta": suite_design_delta_count_delta,
        "maturity_release_readiness_benchmark_suite_design_regression_delta": suite_design_regression_delta,
        "maturity_release_readiness_benchmark_design_change_delta": design_change_delta,
        "overall_relation": "baseline" if is_baseline else _score_relation(overall_delta),
        "rubric_relation": "baseline" if is_baseline else _score_relation(rubric_delta),
        "artifact_relation": "baseline" if is_baseline else _score_relation(artifact_delta),
        "final_val_loss_relation": "baseline" if is_baseline else _loss_relation(val_loss_delta),
        "explanation": _delta_explanation(portfolio, baseline, overall_delta, artifact_delta, val_loss_delta, is_baseline),
    }


def _comparison_summary(
    portfolios: list[dict[str, Any]],
    baseline: dict[str, Any],
    deltas: list[dict[str, Any]],
) -> dict[str, Any]:
    non_baseline = [row for row in deltas if not row.get("is_baseline")]
    best_score = _best_numeric(portfolios, "overall_score", higher_is_better=True)
    best_artifact = _best_numeric(portfolios, "artifact_coverage", higher_is_better=True)
    lowest_val_loss = _best_numeric(portfolios, "final_val_loss", higher_is_better=False)
    maturity_review_rows = [item for item in portfolios if is_review_status(item.get("maturity_portfolio_status"))]
    maturity_ci_rows = [item for item in portfolios if has_maturity_ci_regression(item)]
    maturity_coverage_rows = [item for item in portfolios if has_maturity_coverage_regression(item)]
    maturity_suite_design_rows = [item for item in portfolios if has_maturity_suite_design_regression(item)]
    return {
        "portfolio_count": len(portfolios),
        "baseline_name": baseline.get("name"),
        "completed_count": sum(1 for item in portfolios if item.get("status") == "completed"),
        "failed_count": sum(1 for item in portfolios if item.get("status") == "failed"),
        "planned_count": sum(1 for item in portfolios if item.get("status") == "planned"),
        "artifact_regression_count": sum(1 for item in non_baseline if _number(item.get("artifact_coverage_delta")) is not None and float(item["artifact_coverage_delta"]) < 0),
        "score_improvement_count": sum(1 for item in non_baseline if _number(item.get("overall_score_delta")) is not None and float(item["overall_score_delta"]) > 0),
        "score_regression_count": sum(1 for item in non_baseline if _number(item.get("overall_score_delta")) is not None and float(item["overall_score_delta"]) < 0),
        "loss_improvement_count": sum(1 for item in non_baseline if item.get("final_val_loss_relation") == "improved"),
        "loss_regression_count": sum(1 for item in non_baseline if item.get("final_val_loss_relation") == "regressed"),
        "dataset_warning_count": sum(int(item.get("dataset_warning_count") or 0) for item in portfolios),
        "maturity_review_count": len(maturity_review_rows),
        "maturity_review_names": [name for item in maturity_review_rows if (name := _as_str(item.get("name")))],
        "maturity_ci_regression_count": len(maturity_ci_rows),
        "maturity_ci_regression_names": [name for item in maturity_ci_rows if (name := _as_str(item.get("name")))],
        "maturity_ci_regression_reason_counts": _merge_reason_counts(maturity_ci_rows),
        "maturity_coverage_regression_count": len(maturity_coverage_rows),
        "maturity_coverage_regression_names": [name for item in maturity_coverage_rows if (name := _as_str(item.get("name")))],
        "maturity_suite_design_regression_count": len(maturity_suite_design_rows),
        "maturity_suite_design_regression_names": [name for item in maturity_suite_design_rows if (name := _as_str(item.get("name")))],
        "best_score_name": _pick(best_score, "name"),
        "best_score_maturity_status": _pick(best_score, "maturity_portfolio_status"),
        "best_score_maturity_release_readiness_trend": _pick(best_score, "maturity_release_readiness_trend"),
        "best_score_maturity_release_readiness_ci_workflow_regression_count": _pick(
            best_score,
            "maturity_release_readiness_ci_workflow_regression_count",
        ),
        "best_score_maturity_release_readiness_ci_workflow_order_regression_count": _pick(
            best_score,
            "maturity_release_readiness_ci_workflow_order_regression_count",
        ),
        "best_score_maturity_release_readiness_ci_workflow_regression_reasons": _pick(
            best_score,
            "maturity_release_readiness_ci_workflow_regression_reasons",
        ),
        "best_score_maturity_release_readiness_ci_workflow_regression_reason_counts": _pick(
            best_score,
            "maturity_release_readiness_ci_workflow_regression_reason_counts",
        ),
        "best_score_maturity_release_readiness_ci_boundary_plan_check_ready_regression_count": _pick(
            best_score,
            "maturity_release_readiness_ci_boundary_plan_check_ready_regression_count",
        ),
        "best_score_maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count": _pick(
            best_score,
            "maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count",
        ),
        "best_score_maturity_release_readiness_test_coverage_regression_count": _pick(
            best_score,
            "maturity_release_readiness_test_coverage_regression_count",
        ),
        "best_score_maturity_release_readiness_benchmark_suite_design_delta_count": _pick(
            best_score,
            "maturity_release_readiness_benchmark_suite_design_delta_count",
        ),
        "best_score_maturity_release_readiness_benchmark_suite_design_regression_count": _pick(
            best_score,
            "maturity_release_readiness_benchmark_suite_design_regression_count",
        ),
        "best_score_maturity_release_readiness_benchmark_design_change_delta_count": _pick(
            best_score,
            "maturity_release_readiness_benchmark_design_change_delta_count",
        ),
        "best_artifact_name": _pick(best_artifact, "name"),
        "lowest_val_loss_name": _pick(lowest_val_loss, "name"),
    }


def _select_baseline(portfolios: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    if baseline is None:
        return portfolios[0]
    if isinstance(baseline, int) or str(baseline).isdigit():
        index = int(baseline) - 1
        if 0 <= index < len(portfolios):
            return portfolios[index]
    needle = str(baseline)
    for portfolio in portfolios:
        if needle in {str(portfolio.get("name")), str(portfolio.get("source_path")), str(portfolio.get("run_name"))}:
            return portfolio
    raise ValueError(f"baseline not found: {baseline}")


def _best_numeric(portfolios: list[dict[str, Any]], key: str, *, higher_is_better: bool) -> dict[str, Any] | None:
    candidates = [item for item in portfolios if _number(item.get(key)) is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item.get(key))) if higher_is_better else min(candidates, key=lambda item: float(item.get(key)))


def _delta_explanation(
    portfolio: dict[str, Any],
    baseline: dict[str, Any],
    overall_delta: float | None,
    artifact_delta: float | None,
    val_loss_delta: float | None,
    is_baseline: bool,
) -> str:
    if is_baseline:
        return "Baseline portfolio."
    parts = []
    if overall_delta is not None:
        parts.append(f"overall {_fmt_signed(overall_delta)}")
    if val_loss_delta is not None:
        parts.append(f"final val loss {_fmt_signed(val_loss_delta)}")
    if artifact_delta is not None and artifact_delta < 0:
        parts.append("artifact coverage regressed")
    if portfolio.get("status") != baseline.get("status"):
        parts.append(f"status changed {baseline.get('status')} -> {portfolio.get('status')}")
    if portfolio.get("maturity_portfolio_status") != baseline.get("maturity_portfolio_status"):
        parts.append("maturity status changed")
    if has_maturity_ci_regression(portfolio):
        reason_detail = _reason_count_detail(
            portfolio.get("maturity_release_readiness_ci_workflow_regression_reason_counts")
        )
        parts.append(
            "release-readiness CI regressed"
            + (f" ({reason_detail})" if reason_detail else "")
        )
    if has_maturity_coverage_regression(portfolio):
        parts.append("release-readiness coverage regressed")
    if has_maturity_suite_design_regression(portfolio):
        parts.append("release-readiness suite-design regressed")
    return "; ".join(parts) if parts else "Comparable to baseline."


def _numeric_delta(value: Any, baseline: Any) -> float | None:
    left = _number(value)
    right = _number(baseline)
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 4)


def _int_delta(value: Any, baseline: Any) -> int | None:
    left = _as_int(value)
    right = _as_int(baseline)
    if left is None or right is None:
        return None
    return left - right


def _score_relation(delta: float | None) -> str:
    if delta is None:
        return "missing"
    if delta > 0:
        return "improved"
    if delta < 0:
        return "regressed"
    return "stable"


def _loss_relation(delta: float | None) -> str:
    if delta is None:
        return "missing"
    if delta < 0:
        return "improved"
    if delta > 0:
        return "regressed"
    return "stable"


def _merge_reason_counts(portfolios: list[dict[str, Any]]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for portfolio in portfolios:
        for reason, count in _int_mapping(
            portfolio.get("maturity_release_readiness_ci_workflow_regression_reason_counts")
        ).items():
            merged[reason] = merged.get(reason, 0) + count
    return dict(sorted(merged.items()))


def _reason_count_detail(value: Any) -> str:
    detail = _format_mapping(_int_mapping(value))
    return "" if detail == "none" else detail


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _pick(mapping: Any, key: str) -> Any:
    return mapping.get(key) if isinstance(mapping, dict) else None


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    number = _number(value)
    return None if number is None else float(number)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _fmt_signed(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "missing"
    return f"{float(number):+.4g}"
