from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def best_registered_run(runs: list[Any], field: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if getattr(run, field) is not None]
    if not candidates:
        return None
    best = min(candidates, key=lambda run: getattr(run, field))
    return {"name": best.name, "path": best.path, field: getattr(best, field)}


def annotate_loss_leaderboard(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for run in runs:
        run["best_val_loss_rank"] = None
        run["best_val_loss_delta"] = None
        run["is_best_val_loss"] = False
    candidates = [
        run
        for run in runs
        if _as_optional_float(run.get("best_val_loss")) is not None
    ]
    candidates.sort(key=lambda run: (_as_optional_float(run.get("best_val_loss")) or float("inf"), str(run.get("name") or "")))
    if not candidates:
        return []
    best_loss = _as_optional_float(candidates[0].get("best_val_loss")) or 0.0
    leaderboard = []
    for rank, run in enumerate(candidates, start=1):
        loss = _as_optional_float(run.get("best_val_loss")) or 0.0
        delta = loss - best_loss
        run["best_val_loss_rank"] = rank
        run["best_val_loss_delta"] = delta
        run["is_best_val_loss"] = rank == 1
        leaderboard.append(
            {
                "rank": rank,
                "name": run.get("name"),
                "path": run.get("path"),
                "best_val_loss": loss,
                "best_val_loss_delta": delta,
                "dataset_quality": run.get("dataset_quality"),
                "eval_suite_cases": run.get("eval_suite_cases"),
                "generation_quality_status": run.get("generation_quality_status"),
                "benchmark_rubric_avg_score": run.get("benchmark_rubric_avg_score"),
                "benchmark_rubric_status": run.get("benchmark_rubric_status"),
                "tags": list(run.get("tags") or []),
                "note": run.get("note"),
            }
        )
    return leaderboard


def annotate_rubric_leaderboard(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for run in runs:
        run["benchmark_rubric_rank"] = None
        run["benchmark_rubric_delta_from_best"] = None
        run["is_best_benchmark_rubric"] = False
    candidates = [
        run
        for run in runs
        if _as_optional_float(run.get("benchmark_rubric_avg_score")) is not None
    ]
    candidates.sort(key=lambda run: (-(_as_optional_float(run.get("benchmark_rubric_avg_score")) or 0.0), str(run.get("name") or "")))
    if not candidates:
        return []
    best_score = _as_optional_float(candidates[0].get("benchmark_rubric_avg_score")) or 0.0
    leaderboard = []
    for rank, run in enumerate(candidates, start=1):
        score = _as_optional_float(run.get("benchmark_rubric_avg_score")) or 0.0
        delta = score - best_score
        run["benchmark_rubric_rank"] = rank
        run["benchmark_rubric_delta_from_best"] = delta
        run["is_best_benchmark_rubric"] = rank == 1
        leaderboard.append(
            {
                "rank": rank,
                "name": run.get("name"),
                "path": run.get("path"),
                "benchmark_rubric_avg_score": score,
                "benchmark_rubric_delta_from_best": delta,
                "benchmark_rubric_status": run.get("benchmark_rubric_status"),
                "benchmark_weakest_rubric_case": run.get("benchmark_weakest_rubric_case"),
                "benchmark_weakest_rubric_score": run.get("benchmark_weakest_rubric_score"),
                "best_val_loss": run.get("best_val_loss"),
                "generation_quality_status": run.get("generation_quality_status"),
                "tags": list(run.get("tags") or []),
                "note": run.get("note"),
            }
        )
    return leaderboard


def benchmark_rubric_summary(leaderboard: list[dict[str, Any]]) -> dict[str, Any]:
    if not leaderboard:
        return {
            "available": False,
            "run_count": 0,
            "regression_count": 0,
        }
    regressions = [item for item in leaderboard if (_as_optional_float(item.get("benchmark_rubric_delta_from_best")) or 0.0) < 0]
    weakest = leaderboard[-1]
    largest_regression = min(
        regressions,
        key=lambda item: _as_optional_float(item.get("benchmark_rubric_delta_from_best")) or 0.0,
        default=None,
    )
    best = leaderboard[0]
    return {
        "available": True,
        "run_count": len(leaderboard),
        "best_run": best.get("name"),
        "best_score": best.get("benchmark_rubric_avg_score"),
        "weakest_run": weakest.get("name"),
        "weakest_score": weakest.get("benchmark_rubric_avg_score"),
        "regression_count": len(regressions),
        "largest_regression_run": _pick(largest_regression, "name"),
        "largest_regression_delta": _pick(largest_regression, "benchmark_rubric_delta_from_best"),
    }


def counts(values: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        key = str(value)
        result[key] = result.get(key, 0) + 1
    return result


def collect_pair_delta_rows(run_dirs: list[str | Path], names: list[str] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, run_dir in enumerate(run_dirs):
        root = Path(run_dir)
        run_name = str(names[index]) if names is not None else root.name
        report_path = root / "pair_batch" / "pair_generation_batch.json"
        report = _read_json(report_path)
        if not isinstance(report, dict):
            continue
        suite = _pick_dict(report, "suite")
        left = _pick_dict(report, "left")
        right = _pick_dict(report, "right")
        for result in report.get("results", []):
            if not isinstance(result, dict):
                continue
            comparison = _pick_dict(result, "comparison")
            generated_delta = _as_optional_float(_pick(comparison, "generated_char_delta"))
            continuation_delta = _as_optional_float(_pick(comparison, "continuation_char_delta"))
            if generated_delta is None and continuation_delta is None:
                continue
            rows.append(
                {
                    "run_name": run_name,
                    "run_path": str(root),
                    "case": _as_str(_pick(result, "name")) or "unknown",
                    "task_type": _as_str(_pick(result, "task_type")),
                    "difficulty": _as_str(_pick(result, "difficulty")),
                    "generated_equal": _pick(comparison, "generated_equal"),
                    "continuation_equal": _pick(comparison, "continuation_equal"),
                    "generated_char_delta": _int_if_whole(generated_delta),
                    "continuation_char_delta": _int_if_whole(continuation_delta),
                    "abs_generated_char_delta": _int_if_whole(abs(generated_delta)) if generated_delta is not None else None,
                    "abs_continuation_char_delta": _int_if_whole(abs(continuation_delta)) if continuation_delta is not None else None,
                    "suite_name": _as_str(_pick(suite, "name")),
                    "suite_version": _as_str(_pick(suite, "version")),
                    "left_checkpoint_id": _as_str(_pick(left, "checkpoint_id")),
                    "right_checkpoint_id": _as_str(_pick(right, "checkpoint_id")),
                    "report_path": str(report_path),
                }
            )
    return rows


def pair_delta_leaderboard(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda item: (
            _as_optional_float(item.get("abs_generated_char_delta")) or -1.0,
            _as_optional_float(item.get("abs_continuation_char_delta")) or -1.0,
            str(item.get("run_name") or ""),
            str(item.get("case") or ""),
        ),
        reverse=True,
    )
    return ordered[:limit]


def pair_delta_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    run_names = {str(row.get("run_name")) for row in rows if row.get("run_name")}
    generated_values = [_as_optional_float(row.get("abs_generated_char_delta")) for row in rows]
    continuation_values = [_as_optional_float(row.get("abs_continuation_char_delta")) for row in rows]
    generated_values = [value for value in generated_values if value is not None]
    continuation_values = [value for value in continuation_values if value is not None]
    return {
        "case_count": len(rows),
        "run_count": len(run_names),
        "max_abs_generated_char_delta": _int_if_whole(max(generated_values)) if generated_values else None,
        "max_abs_continuation_char_delta": _int_if_whole(max(continuation_values)) if continuation_values else None,
    }


def collect_release_readiness_delta_rows(run_dirs: list[str | Path], names: list[str] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, run_dir in enumerate(run_dirs):
        root = Path(run_dir)
        run_name = str(names[index]) if names is not None else root.name
        report = _read_release_readiness_comparison(root)
        if not isinstance(report, dict):
            continue
        report_path = _as_str(report.get("release_readiness_comparison_path"))
        for delta in report.get("deltas", []):
            if not isinstance(delta, dict):
                continue
            changed_panels = _as_str_list(delta.get("changed_panels"))
            rows.append(
                {
                    "run_name": run_name,
                    "run_path": str(root),
                    "baseline_release": _as_str(delta.get("baseline_release")),
                    "compared_release": _as_str(delta.get("compared_release")),
                    "baseline_status": _as_str(delta.get("baseline_status")),
                    "compared_status": _as_str(delta.get("compared_status")),
                    "status_delta": _int_if_whole(_as_optional_float(delta.get("status_delta"))),
                    "delta_status": _as_str(delta.get("delta_status")) or "same",
                    "baseline_ci_workflow_status": _as_str(delta.get("baseline_ci_workflow_status")),
                    "compared_ci_workflow_status": _as_str(delta.get("compared_ci_workflow_status")),
                    "ci_workflow_failed_check_delta": _int_if_whole(_as_optional_float(delta.get("ci_workflow_failed_check_delta"))),
                    "ci_workflow_status_changed": bool(delta.get("ci_workflow_status_changed")),
                    "audit_score_delta": _int_if_whole(_as_optional_float(delta.get("audit_score_delta"))),
                    "missing_artifact_delta": _int_if_whole(_as_optional_float(delta.get("missing_artifact_delta"))),
                    "fail_panel_delta": _int_if_whole(_as_optional_float(delta.get("fail_panel_delta"))),
                    "warn_panel_delta": _int_if_whole(_as_optional_float(delta.get("warn_panel_delta"))),
                    "changed_panel_count": len(changed_panels),
                    "changed_panels": changed_panels,
                    "explanation": _as_str(delta.get("explanation")),
                    "report_path": report_path,
                }
            )
    return rows


def release_readiness_delta_leaderboard(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    status_priority = {"regressed": 0, "improved": 1, "panel-changed": 2, "same": 3}
    ordered = sorted(
        rows,
        key=lambda item: (
            status_priority.get(str(item.get("delta_status") or ""), 4),
            -int(bool(item.get("ci_workflow_status_changed"))),
            -abs(_as_optional_float(item.get("ci_workflow_failed_check_delta")) or 0.0),
            -abs(_as_optional_float(item.get("status_delta")) or 0.0),
            -int(item.get("changed_panel_count") or 0),
            str(item.get("run_name") or ""),
            str(item.get("compared_release") or ""),
        ),
    )
    return ordered[:limit]


def release_readiness_delta_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    run_names = {str(row.get("run_name")) for row in rows if row.get("run_name")}
    result_counts = counts(row.get("delta_status") or "missing" for row in rows)
    status_deltas = [abs(value) for value in (_as_optional_float(row.get("status_delta")) for row in rows) if value is not None]
    ci_failed_deltas = [
        abs(value)
        for value in (_as_optional_float(row.get("ci_workflow_failed_check_delta")) for row in rows)
        if value is not None
    ]
    return {
        "delta_count": len(rows),
        "run_count": len(run_names),
        "regressed_count": result_counts.get("regressed", 0),
        "improved_count": result_counts.get("improved", 0),
        "panel_changed_count": result_counts.get("panel-changed", 0),
        "same_count": result_counts.get("same", 0),
        "changed_panel_delta_count": sum(1 for row in rows if int(row.get("changed_panel_count") or 0) > 0),
        "ci_workflow_regression_count": sum(1 for row in rows if _is_ci_workflow_regression_row(row)),
        "ci_workflow_status_changed_count": sum(1 for row in rows if bool(row.get("ci_workflow_status_changed"))),
        "max_abs_ci_workflow_failed_check_delta": _int_if_whole(max(ci_failed_deltas)) if ci_failed_deltas else None,
        "max_abs_status_delta": _int_if_whole(max(status_deltas)) if status_deltas else None,
    }


def _is_ci_workflow_regression_row(row: dict[str, Any]) -> bool:
    failed_delta = _as_optional_float(row.get("ci_workflow_failed_check_delta"))
    if failed_delta is not None and failed_delta > 0:
        return True
    if not row.get("ci_workflow_status_changed"):
        return False
    return _ci_status_score(row.get("compared_ci_workflow_status")) < _ci_status_score(row.get("baseline_ci_workflow_status"))


def _ci_status_score(value: Any) -> int:
    order = {"missing": 0, "fail": 0, "warn": 1, "review": 1, "pass": 2}
    return order.get(str(value or "missing"), 0)


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_release_readiness_comparison(root: Path) -> dict[str, Any]:
    candidates = [
        root / "release-readiness-comparison" / "release_readiness_comparison.json",
        root / "release_readiness_comparison.json",
    ]
    for path in candidates:
        payload = _read_json(path)
        if isinstance(payload, dict):
            payload["release_readiness_comparison_path"] = str(path)
            return payload
    return {}


def _pick(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    nested = _pick(payload, key)
    return nested if isinstance(nested, dict) else {}


def _as_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_if_whole(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []
