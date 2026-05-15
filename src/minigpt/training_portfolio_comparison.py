from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from minigpt.training_portfolio_comparison_artifacts import (
    render_training_portfolio_comparison_html,
    render_training_portfolio_comparison_markdown,
    write_training_portfolio_comparison_csv,
    write_training_portfolio_comparison_html,
    write_training_portfolio_comparison_json,
    write_training_portfolio_comparison_markdown,
    write_training_portfolio_comparison_outputs,
)


CORE_ARTIFACT_KEYS = [
    "run_manifest",
    "eval_suite",
    "generation_quality",
    "benchmark_scorecard",
    "dataset_card",
    "registry",
    "maturity_summary",
    "maturity_narrative",
]


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
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or _utc_now(),
        "portfolio_count": len(portfolios),
        "baseline": baseline_portfolio,
        "portfolios": portfolios,
        "baseline_deltas": deltas,
        "summary": summary,
        "best_by_overall_score": _best_numeric(portfolios, "overall_score", higher_is_better=True),
        "best_by_rubric_avg_score": _best_numeric(portfolios, "rubric_avg_score", higher_is_better=True),
        "best_by_artifact_coverage": _best_numeric(portfolios, "artifact_coverage", higher_is_better=True),
        "best_by_final_val_loss": _best_numeric(portfolios, "final_val_loss", higher_is_better=False),
        "recommendations": _recommendations(summary, deltas),
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


def _portfolio_summary(report: dict[str, Any], name: str, index: int) -> dict[str, Any]:
    source_path = Path(str(report.get("_source_path") or "training_portfolio.json"))
    project_root = Path(str(report.get("project_root") or source_path.parent))
    execution = _dict(report.get("execution"))
    artifacts = _dict(report.get("artifacts"))
    rows = _artifact_rows(artifacts, project_root, source_path)
    row_by_key = {row["key"]: row for row in rows}

    scorecard = _read_artifact_json(row_by_key, "benchmark_scorecard")
    dataset_card = _read_artifact_json(row_by_key, "dataset_card")
    maturity_narrative = _read_artifact_json(row_by_key, "maturity_narrative")
    manifest = _read_artifact_json(row_by_key, "run_manifest")
    eval_suite = _read_artifact_json(row_by_key, "eval_suite")
    generation_quality = _read_artifact_json(row_by_key, "generation_quality")

    scorecard_summary = _dict(_pick(scorecard, "summary"))
    dataset_summary = _dict(_pick(dataset_card, "summary"))
    dataset = _dict(_pick(dataset_card, "dataset"))
    maturity_summary = _dict(_pick(maturity_narrative, "summary"))
    manifest_data = _dict(_pick(manifest, "data"))
    manifest_model = _dict(_pick(manifest, "model"))
    manifest_results = _dict(_pick(manifest, "results"))
    manifest_history = _dict(_pick(manifest_results, "history_summary"))
    generation_summary = _dict(_pick(generation_quality, "summary"))

    artifact_count = _as_int(execution.get("artifact_count")) or len(rows)
    available_artifact_count = sum(1 for row in rows if row["exists"])
    artifact_coverage = 0.0 if artifact_count == 0 else round(available_artifact_count / artifact_count, 4)

    dataset_label = _dataset_label(report, dataset)
    return {
        "name": name,
        "index": index + 1,
        "source_path": str(source_path),
        "project_root": str(project_root),
        "run_name": report.get("run_name"),
        "dataset_name": report.get("dataset_name") or dataset.get("name"),
        "dataset_version": report.get("dataset_version") or dataset.get("version"),
        "dataset": dataset_label,
        "status": execution.get("status") or "unknown",
        "execute": execution.get("execute"),
        "step_count": execution.get("step_count"),
        "completed_steps": execution.get("completed_steps"),
        "failed_step": execution.get("failed_step"),
        "artifact_count": artifact_count,
        "available_artifact_count": available_artifact_count,
        "artifact_coverage": artifact_coverage,
        "core_artifacts": [row_by_key.get(key, _missing_artifact(key)) for key in CORE_ARTIFACT_KEYS],
        "overall_status": scorecard_summary.get("overall_status"),
        "overall_score": _as_float(scorecard_summary.get("overall_score")),
        "rubric_status": scorecard_summary.get("rubric_status"),
        "rubric_avg_score": _as_float(scorecard_summary.get("rubric_avg_score")),
        "weakest_rubric_case": scorecard_summary.get("weakest_rubric_case"),
        "weakest_rubric_score": _as_float(scorecard_summary.get("weakest_rubric_score")),
        "best_val_loss": _as_float(
            manifest_history.get("best_val_loss")
            or _pick(manifest_results, "best_val_loss")
        ),
        "final_val_loss": _as_float(
            manifest_history.get("last_val_loss")
            or manifest_history.get("final_val_loss")
            or _pick(manifest_results, "last_val_loss")
            or _pick(manifest_results, "final_val_loss")
        ),
        "last_loss": _as_float(_pick(manifest_results, "last_loss")),
        "parameter_count": _as_int(_pick(manifest_model, "parameter_count")),
        "token_count": _as_int(_pick(manifest_data, "token_count")),
        "train_token_count": _as_int(_pick(manifest_data, "train_token_count")),
        "val_token_count": _as_int(_pick(manifest_data, "val_token_count")),
        "eval_suite_name": _pick(eval_suite, "suite_name") or _pick(_dict(_pick(eval_suite, "suite")), "name"),
        "eval_suite_version": _pick(eval_suite, "suite_version") or _pick(_dict(_pick(eval_suite, "suite")), "version"),
        "eval_case_count": _as_int(_pick(eval_suite, "case_count")),
        "generation_quality_status": generation_summary.get("overall_status"),
        "generation_quality_cases": _as_int(generation_summary.get("case_count")),
        "generation_quality_warn_count": _as_int(generation_summary.get("warn_count")),
        "generation_quality_fail_count": _as_int(generation_summary.get("fail_count")),
        "generation_quality_avg_unique_ratio": _as_float(generation_summary.get("avg_unique_ratio")),
        "dataset_readiness_status": dataset_summary.get("readiness_status"),
        "dataset_quality_status": dataset_summary.get("quality_status"),
        "dataset_warning_count": _as_int(dataset_summary.get("warning_count")) or 0,
        "maturity_portfolio_status": maturity_summary.get("portfolio_status"),
        "maturity_release_readiness_trend": maturity_summary.get("release_readiness_trend_status"),
        "maturity_request_history_status": maturity_summary.get("request_history_status"),
    }


def _artifact_rows(artifacts: dict[str, Any], project_root: Path, source_path: Path) -> list[dict[str, Any]]:
    rows = []
    for key, raw_path in sorted(artifacts.items()):
        path = _resolve_artifact_path(raw_path, project_root, source_path)
        rows.append({"key": key, "path": str(path), "exists": path.exists()})
    return rows


def _resolve_artifact_path(raw_path: Any, project_root: Path, source_path: Path) -> Path:
    path = Path(str(raw_path))
    if path.is_absolute():
        return path
    candidates = [
        project_root / path,
        source_path.parent / path,
        Path.cwd() / path,
        path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return project_root / path


def _read_artifact_json(row_by_key: dict[str, dict[str, Any]], key: str) -> dict[str, Any] | None:
    row = row_by_key.get(key)
    if not row or not row.get("exists"):
        return None
    try:
        payload = json.loads(Path(str(row.get("path"))).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _portfolio_delta(portfolio: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    is_baseline = portfolio.get("name") == baseline.get("name")
    overall_delta = _numeric_delta(portfolio.get("overall_score"), baseline.get("overall_score"))
    rubric_delta = _numeric_delta(portfolio.get("rubric_avg_score"), baseline.get("rubric_avg_score"))
    val_loss_delta = _numeric_delta(portfolio.get("final_val_loss"), baseline.get("final_val_loss"))
    artifact_delta = _numeric_delta(portfolio.get("artifact_coverage"), baseline.get("artifact_coverage"))
    available_artifact_delta = _int_delta(portfolio.get("available_artifact_count"), baseline.get("available_artifact_count"))
    dataset_warning_delta = _int_delta(portfolio.get("dataset_warning_count"), baseline.get("dataset_warning_count"))
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
        "maturity_review_count": sum(1 for item in portfolios if item.get("maturity_portfolio_status") in {"review", "warn", "fail", "incomplete"}),
        "best_score_name": _pick(_best_numeric(portfolios, "overall_score", higher_is_better=True), "name"),
        "best_artifact_name": _pick(_best_numeric(portfolios, "artifact_coverage", higher_is_better=True), "name"),
        "lowest_val_loss_name": _pick(_best_numeric(portfolios, "final_val_loss", higher_is_better=False), "name"),
    }


def _recommendations(summary: dict[str, Any], deltas: list[dict[str, Any]]) -> list[str]:
    recs = []
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
    if not recs:
        recs.append("Use the best-scoring portfolio as the next baseline, then repeat the comparison after larger-corpus training.")
    return recs


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
    return "; ".join(parts) if parts else "Comparable to baseline."


def _dataset_label(report: dict[str, Any], dataset: dict[str, Any]) -> str:
    name = report.get("dataset_name") or dataset.get("name") or dataset.get("id")
    version = report.get("dataset_version") or dataset.get("version")
    if name and version:
        return f"{name}@{version}"
    return str(name or version or "missing")


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


def _missing_artifact(key: str) -> dict[str, Any]:
    return {"key": key, "path": None, "exists": False}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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
