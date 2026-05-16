from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from minigpt.benchmark_scorecard_comparison_artifacts import (
    render_benchmark_scorecard_comparison_html,
    render_benchmark_scorecard_comparison_markdown,
    write_benchmark_scorecard_case_delta_csv,
    write_benchmark_scorecard_comparison_csv,
    write_benchmark_scorecard_comparison_html,
    write_benchmark_scorecard_comparison_json,
    write_benchmark_scorecard_comparison_markdown,
    write_benchmark_scorecard_comparison_outputs,
)
from minigpt.benchmark_scorecard_comparison_deltas import (
    build_benchmark_scorecard_case_deltas,
    build_benchmark_scorecard_group_deltas,
    build_benchmark_scorecard_recommendations,
    build_benchmark_scorecard_run_delta,
    build_benchmark_scorecard_summary,
    select_best_benchmark_scorecard_run,
    summarize_benchmark_scorecard_run,
)


def load_benchmark_scorecard(path: str | Path) -> dict[str, Any]:
    scorecard_path = _resolve_scorecard_path(Path(path))
    payload = json.loads(scorecard_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("benchmark scorecard must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(scorecard_path)
    return payload


def build_benchmark_scorecard_comparison(
    scorecard_paths: list[str | Path],
    *,
    names: list[str] | None = None,
    baseline: str | int | None = None,
    title: str = "MiniGPT benchmark scorecard comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not scorecard_paths:
        raise ValueError("at least one benchmark scorecard is required")
    if names is not None and len(names) != len(scorecard_paths):
        raise ValueError("names length must match scorecard_paths length")

    scorecards = [load_benchmark_scorecard(path) for path in scorecard_paths]
    resolved_names = _resolve_names(scorecards, names)
    runs = [summarize_benchmark_scorecard_run(scorecard, resolved_names[index], index) for index, scorecard in enumerate(scorecards)]
    baseline_run = _select_baseline(runs, baseline)
    deltas = [build_benchmark_scorecard_run_delta(run, baseline_run) for run in runs]
    case_deltas = build_benchmark_scorecard_case_deltas(scorecards, resolved_names, baseline_run)
    task_deltas = build_benchmark_scorecard_group_deltas(scorecards, resolved_names, baseline_run, group_name="task_type")
    difficulty_deltas = build_benchmark_scorecard_group_deltas(scorecards, resolved_names, baseline_run, group_name="difficulty")
    summary = build_benchmark_scorecard_summary(runs, baseline_run, deltas, case_deltas, task_deltas, difficulty_deltas)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or _utc_now(),
        "scorecard_count": len(scorecards),
        "baseline": baseline_run,
        "runs": runs,
        "baseline_deltas": deltas,
        "case_deltas": case_deltas,
        "task_type_deltas": task_deltas,
        "difficulty_deltas": difficulty_deltas,
        "summary": summary,
        "best_by_overall_score": select_best_benchmark_scorecard_run(runs, "overall_score"),
        "best_by_rubric_avg_score": select_best_benchmark_scorecard_run(runs, "rubric_avg_score"),
        "recommendations": build_benchmark_scorecard_recommendations(summary, deltas, case_deltas, task_deltas, difficulty_deltas),
    }


def _resolve_scorecard_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates = [
            path / "benchmark-scorecard" / "benchmark_scorecard.json",
            path / "benchmark_scorecard.json",
        ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"benchmark scorecard not found: {path}")


def _resolve_names(scorecards: list[dict[str, Any]], names: list[str] | None) -> list[str]:
    if names is not None:
        return [str(name) for name in names]
    resolved = []
    for index, scorecard in enumerate(scorecards, start=1):
        run_dir = _as_str(scorecard.get("run_dir"))
        source_path = _as_str(scorecard.get("_source_path"))
        if run_dir:
            resolved.append(Path(run_dir).name or f"scorecard-{index}")
        elif source_path:
            path = Path(source_path)
            resolved.append(path.parent.parent.name if path.parent.name == "benchmark-scorecard" else path.stem)
        else:
            resolved.append(f"scorecard-{index}")
    return resolved


def _select_baseline(runs: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    if baseline is None:
        return runs[0]
    if isinstance(baseline, int):
        if baseline < 0 or baseline >= len(runs):
            raise ValueError(f"baseline index out of range: {baseline}")
        return runs[baseline]
    wanted = baseline.strip()
    if not wanted:
        raise ValueError("baseline cannot be empty")
    if wanted.isdigit():
        index = int(wanted) - 1
        if 0 <= index < len(runs):
            return runs[index]
    for run in runs:
        if wanted in {str(run.get("name")), str(run.get("source_path")), str(run.get("run_dir")), Path(str(run.get("run_dir") or "")).name}:
            return run
    raise ValueError(f"baseline did not match a scorecard name, path, run_dir, or 1-based index: {baseline}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_str(value: Any) -> str | None:
    return None if value is None else str(value)
