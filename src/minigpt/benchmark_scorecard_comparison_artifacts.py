from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.benchmark_scorecard_comparison_sections import (
    render_benchmark_scorecard_comparison_html,
    render_benchmark_scorecard_comparison_markdown,
)


def write_benchmark_scorecard_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_benchmark_scorecard_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "source_path",
        "run_dir",
        "overall_status",
        "overall_score",
        "rubric_status",
        "rubric_avg_score",
        "rubric_pass_count",
        "rubric_warn_count",
        "rubric_fail_count",
        "generation_quality_total_flags",
        "generation_quality_dominant_flag",
        "generation_quality_worst_case",
        "generation_quality_worst_case_status",
        "weakest_rubric_case",
        "weakest_rubric_score",
        "case_count",
        "component_count",
        "task_type_count",
        "difficulty_count",
        "baseline_name",
        "is_baseline",
        "overall_score_delta",
        "rubric_avg_score_delta",
        "rubric_pass_count_delta",
        "rubric_warn_count_delta",
        "rubric_fail_count_delta",
        "generation_quality_total_flags_delta",
        "generation_quality_flag_relation",
        "generation_quality_dominant_flag_changed",
        "generation_quality_worst_case_changed",
        "weakest_case_changed",
        "overall_relation",
        "rubric_relation",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for run in _list_of_dicts(report.get("runs")):
            row = dict(run)
            row.update(deltas.get(run.get("name"), {}))
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def write_benchmark_scorecard_case_delta_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case",
        "run_name",
        "baseline_name",
        "task_type",
        "difficulty",
        "baseline_rubric_score",
        "rubric_score",
        "rubric_score_delta",
        "baseline_rubric_status",
        "rubric_status",
        "relation",
        "status_changed",
        "added_missing_terms",
        "removed_missing_terms",
        "added_failed_checks",
        "removed_failed_checks",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("case_deltas")):
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def write_benchmark_scorecard_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_comparison_markdown(report), encoding="utf-8")


def write_benchmark_scorecard_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_comparison_html(report), encoding="utf-8")


def write_benchmark_scorecard_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "benchmark_scorecard_comparison.json",
        "csv": root / "benchmark_scorecard_comparison.csv",
        "case_delta_csv": root / "benchmark_scorecard_case_deltas.csv",
        "markdown": root / "benchmark_scorecard_comparison.md",
        "html": root / "benchmark_scorecard_comparison.html",
    }
    write_benchmark_scorecard_comparison_json(report, paths["json"])
    write_benchmark_scorecard_comparison_csv(report, paths["csv"])
    write_benchmark_scorecard_case_delta_csv(report, paths["case_delta_csv"])
    write_benchmark_scorecard_comparison_markdown(report, paths["markdown"])
    write_benchmark_scorecard_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


__all__ = [
    "render_benchmark_scorecard_comparison_html",
    "render_benchmark_scorecard_comparison_markdown",
    "write_benchmark_scorecard_case_delta_csv",
    "write_benchmark_scorecard_comparison_csv",
    "write_benchmark_scorecard_comparison_html",
    "write_benchmark_scorecard_comparison_json",
    "write_benchmark_scorecard_comparison_markdown",
    "write_benchmark_scorecard_comparison_outputs",
]
