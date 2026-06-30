from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any

from minigpt.maturity_html_sections import (
    capability_section,
    card,
    registry_section,
    release_readiness_section,
    recommendation_section,
    request_history_section,
    style,
    timeline_section,
)


def write_maturity_summary_json(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def write_maturity_summary_csv(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "key",
        "title",
        "status",
        "maturity_level",
        "target_level",
        "score_percent",
        "covered_count",
        "target_count",
        "covered_versions",
        "missing_versions",
        "next_step",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(summary.get("capabilities")):
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_maturity_summary_markdown(summary: dict[str, Any]) -> str:
    overview = _dict(summary.get("summary"))
    lines = [
        f"# {summary.get('title', 'MiniGPT project maturity summary')}",
        "",
        f"- Generated: `{summary.get('generated_at')}`",
        f"- Project root: `{summary.get('project_root')}`",
        "",
        "## Overview",
        "",
        *_markdown_table(
            [
                ("Current version", overview.get("current_version")),
                ("Published versions", overview.get("published_version_count")),
                ("Archive versions", overview.get("archive_version_count")),
                ("Explanation versions", overview.get("explanation_version_count")),
                ("Average maturity level", overview.get("average_maturity_level")),
                ("Overall status", overview.get("overall_status")),
                ("Registry runs", overview.get("registry_runs")),
                ("Release readiness trend", overview.get("release_readiness_trend_status")),
                ("Release readiness deltas", overview.get("release_readiness_delta_count")),
                ("Release readiness regressions", overview.get("release_readiness_regressed_count")),
                ("Release readiness CI workflow regressions", overview.get("release_readiness_ci_workflow_regression_count")),
                ("Release readiness CI order regressions", overview.get("release_readiness_ci_workflow_order_regression_count")),
                ("Release readiness CI regression reasons", _fmt_mapping(overview.get("release_readiness_ci_workflow_regression_reason_counts"))),
                (
                    "Release readiness CI tiny plan regressions",
                    overview.get("release_readiness_ci_tiny_plan_digest_gate_ready_regression_count"),
                ),
                (
                    "Release readiness CI boundary gate regressions",
                    overview.get("release_readiness_ci_boundary_gate_check_ready_regression_count"),
                ),
                (
                    "Release readiness CI boundary plan regressions",
                    overview.get("release_readiness_ci_boundary_plan_check_ready_regression_count"),
                ),
                (
                    "Release readiness CI archived path regressions",
                    overview.get("release_readiness_ci_archived_path_portability_check_ready_regression_count"),
                ),
                ("Release readiness CI drift smoke regressions", overview.get("release_readiness_ci_drift_smoke_ready_regression_count")),
                ("Release readiness test coverage regressions", overview.get("release_readiness_test_coverage_regression_count")),
                ("Release readiness benchmark-history regressions", overview.get("release_readiness_benchmark_history_regression_count")),
                (
                    "Release readiness benchmark suite-design deltas",
                    overview.get("release_readiness_benchmark_suite_design_delta_count"),
                ),
                (
                    "Release readiness benchmark suite-design regressions",
                    overview.get("release_readiness_benchmark_suite_design_regression_count"),
                ),
                (
                    "Release readiness benchmark design changes",
                    overview.get("release_readiness_benchmark_design_change_delta_count"),
                ),
                ("Release readiness benchmark requirement changes", overview.get("release_readiness_benchmark_requirement_status_changed_count")),
                ("Release readiness benchmark requirement exit delta", overview.get("release_readiness_max_benchmark_requirement_exit_code_delta")),
                (
                    "Release readiness benchmark failed reasons added",
                    overview.get("release_readiness_benchmark_requirement_failed_reason_added_count"),
                ),
                (
                    "Release readiness benchmark failed reasons removed",
                    overview.get("release_readiness_benchmark_requirement_failed_reason_removed_count"),
                ),
                (
                    "Release readiness benchmark failed reason removals",
                    ", ".join(_string_list(overview.get("release_readiness_benchmark_requirement_failed_reason_removed"))) or "none",
                ),
                (
                    "Release readiness benchmark failed reason recovery deltas",
                    overview.get("release_readiness_benchmark_requirement_failed_reason_recovery_delta_count"),
                ),
                (
                    "Release readiness benchmark failed reason mixed deltas",
                    overview.get("release_readiness_benchmark_requirement_failed_reason_mixed_delta_count"),
                ),
                (
                    "Release readiness benchmark failed reason drift",
                    _fmt_mapping(overview.get("release_readiness_benchmark_requirement_failed_reason_drift_status_counts")),
                ),
                ("Release readiness max benchmark suite-design delta", overview.get("release_readiness_max_benchmark_suite_design_delta")),
                ("Release readiness max benchmark design-change delta", overview.get("release_readiness_max_benchmark_design_change_delta")),
                ("Request history status", overview.get("request_history_status")),
                ("Request history records", overview.get("request_history_records")),
            ]
        ),
        "",
        "## Capability Matrix",
        "",
        "| Area | Status | Level | Score | Evidence | Next step |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in _list_of_dicts(summary.get("capabilities")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("title")),
                    _md(row.get("status")),
                    _md(f"{row.get('maturity_level')}/{row.get('target_level')}"),
                    _md(f"{row.get('score_percent')}%"),
                    _md(row.get("evidence")),
                    _md(row.get("next_step")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Phase Timeline", "", "| Versions | Phase | Status |", "| --- | --- | --- |"])
    for phase in _list_of_dicts(summary.get("phase_timeline")):
        lines.append(f"| {_md(phase.get('versions'))} | {_md(phase.get('title'))} | {_md(phase.get('status'))} |")
    request_history = _dict(summary.get("request_history_context"))
    lines.extend(
        [
            "",
            "## Request History Context",
            "",
            *_markdown_table(
                [
                    ("Available", request_history.get("available")),
                    ("Status", request_history.get("status")),
                    ("Records", request_history.get("total_log_records")),
                    ("Invalid", request_history.get("invalid_record_count")),
                    ("Timeout rate", request_history.get("timeout_rate")),
                    ("Bad request rate", request_history.get("bad_request_rate")),
                    ("Error rate", request_history.get("error_rate")),
                    ("Checkpoints", request_history.get("unique_checkpoint_count")),
                    ("Latest", request_history.get("latest_timestamp")),
                ]
            ),
        ]
    )
    release_readiness = _dict(summary.get("release_readiness_context"))
    lines.extend(
        [
            "",
            "## Release Readiness Trend Context",
            "",
            *_markdown_table(
                [
                    ("Available", release_readiness.get("available")),
                    ("Trend status", release_readiness.get("trend_status")),
                    ("Comparison counts", _fmt_mapping(release_readiness.get("comparison_counts"))),
                    ("Delta count", release_readiness.get("delta_count")),
                    ("Runs with deltas", release_readiness.get("run_count")),
                    ("Regressed", release_readiness.get("regressed_count")),
                    ("Improved", release_readiness.get("improved_count")),
                    ("Panel changed", release_readiness.get("panel_changed_count")),
                    ("Changed panels", release_readiness.get("changed_panel_delta_count")),
                    ("Max status delta", release_readiness.get("max_abs_status_delta")),
                    ("CI workflow regressions", release_readiness.get("ci_workflow_regression_count")),
                    ("CI workflow order regressions", release_readiness.get("ci_workflow_order_regression_count")),
                    ("CI workflow status changes", release_readiness.get("ci_workflow_status_changed_count")),
                    ("CI workflow regression reasons", _fmt_mapping(release_readiness.get("ci_workflow_regression_reason_counts"))),
                    (
                        "CI tiny plan regressions",
                        release_readiness.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count"),
                    ),
                    (
                        "CI boundary gate regressions",
                        release_readiness.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count"),
                    ),
                    (
                        "CI boundary plan regressions",
                        release_readiness.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count"),
                    ),
                    (
                        "CI archived path regressions",
                        release_readiness.get("ci_workflow_archived_path_portability_check_ready_regression_count"),
                    ),
                    (
                        "CI drift smoke regressions",
                        release_readiness.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count"),
                    ),
                    ("Max CI workflow failed-check delta", release_readiness.get("max_abs_ci_workflow_failed_check_delta")),
                    ("Max CI workflow order-violation delta", release_readiness.get("max_abs_ci_workflow_order_violation_delta")),
                    ("Test coverage regressions", release_readiness.get("test_coverage_regression_count")),
                    ("Test coverage status changes", release_readiness.get("test_coverage_status_changed_count")),
                    ("Max coverage percent delta", release_readiness.get("max_abs_test_coverage_percent_delta")),
                    ("Max coverage gap delta", release_readiness.get("max_abs_test_coverage_gap_delta")),
                    ("Benchmark-history regressions", release_readiness.get("benchmark_history_regression_count")),
                    (
                        "Benchmark suite-design deltas",
                        release_readiness.get("benchmark_history_suite_design_non_comparison_ready_delta_count"),
                    ),
                    (
                        "Benchmark suite-design regressions",
                        release_readiness.get("benchmark_history_suite_design_non_comparison_ready_regression_count"),
                    ),
                    ("Benchmark design changes", release_readiness.get("benchmark_history_design_comparison_changed_delta_count")),
                    ("Benchmark-history status changes", release_readiness.get("benchmark_history_status_changed_count")),
                    ("Benchmark-history boundary changes", release_readiness.get("benchmark_history_boundary_changed_count")),
                    ("Benchmark requirement changes", release_readiness.get("benchmark_history_readiness_requirement_status_changed_count")),
                    ("Benchmark requirement exit delta", release_readiness.get("max_abs_benchmark_history_readiness_requirement_exit_code_delta")),
                    ("Benchmark failed reasons added", release_readiness.get("benchmark_history_readiness_requirement_failed_reason_added_count")),
                    ("Benchmark failed reasons removed", release_readiness.get("benchmark_history_readiness_requirement_failed_reason_removed_count")),
                    (
                        "Benchmark failed reason removals",
                        ", ".join(_string_list(release_readiness.get("benchmark_history_readiness_requirement_failed_reason_removed"))) or "none",
                    ),
                    (
                        "Benchmark failed reason recovery deltas",
                        release_readiness.get("benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"),
                    ),
                    (
                        "Benchmark failed reason mixed deltas",
                        release_readiness.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"),
                    ),
                    (
                        "Benchmark failed reason drift",
                        _fmt_mapping(release_readiness.get("benchmark_history_readiness_requirement_failed_reason_drift_status_counts")),
                    ),
                    ("Max benchmark case-regression delta", release_readiness.get("max_abs_benchmark_history_case_regression_delta")),
                    (
                        "Max benchmark generation-flag regression delta",
                        release_readiness.get("max_abs_benchmark_history_generation_flag_regression_delta"),
                    ),
                    (
                        "Max benchmark suite-design delta",
                        release_readiness.get("max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta"),
                    ),
                    (
                        "Max benchmark design-change delta",
                        release_readiness.get("max_abs_benchmark_history_design_comparison_changed_entries_delta"),
                    ),
                ]
            ),
        ]
    )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(summary.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_maturity_summary_markdown(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_summary_markdown(summary), encoding="utf-8")


def render_maturity_summary_html(summary: dict[str, Any]) -> str:
    overview = _dict(summary.get("summary"))
    registry = _dict(summary.get("registry_context"))
    release_readiness = _dict(summary.get("release_readiness_context"))
    request_history = _dict(summary.get("request_history_context"))
    stats = [
        ("Current", overview.get("current_version")),
        ("Versions", overview.get("published_version_count")),
        ("Archives", overview.get("archive_version_count")),
        ("Explanations", overview.get("explanation_version_count")),
        ("Maturity", overview.get("average_maturity_level")),
        ("Status", overview.get("overall_status")),
        ("Runs", overview.get("registry_runs")),
        ("Pair deltas", registry.get("pair_delta_cases")),
        ("Release trend", release_readiness.get("trend_status")),
        ("Readiness deltas", release_readiness.get("delta_count")),
        ("CI regressions", release_readiness.get("ci_workflow_regression_count")),
        ("CI order regressions", release_readiness.get("ci_workflow_order_regression_count")),
        ("CI reasons", _fmt_mapping(release_readiness.get("ci_workflow_regression_reason_counts"))),
        ("CI boundary plan", release_readiness.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count")),
        ("CI archived paths", release_readiness.get("ci_workflow_archived_path_portability_check_ready_regression_count")),
        ("Coverage regressions", release_readiness.get("test_coverage_regression_count")),
        ("Benchmark regressions", release_readiness.get("benchmark_history_regression_count")),
        ("Benchmark suite deltas", release_readiness.get("benchmark_history_suite_design_non_comparison_ready_delta_count")),
        ("Benchmark suite regressions", release_readiness.get("benchmark_history_suite_design_non_comparison_ready_regression_count")),
        ("Benchmark design changes", release_readiness.get("benchmark_history_design_comparison_changed_delta_count")),
        ("Benchmark req changes", release_readiness.get("benchmark_history_readiness_requirement_status_changed_count")),
        ("Benchmark req exit", release_readiness.get("max_abs_benchmark_history_readiness_requirement_exit_code_delta")),
        ("Benchmark reasons added", release_readiness.get("benchmark_history_readiness_requirement_failed_reason_added_count")),
        ("Benchmark reasons removed", release_readiness.get("benchmark_history_readiness_requirement_failed_reason_removed_count")),
        ("Benchmark recoveries", release_readiness.get("benchmark_history_readiness_requirement_failed_reason_recovery_delta_count")),
        ("Benchmark mixed", release_readiness.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count")),
        ("Benchmark suite max", release_readiness.get("max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta")),
        ("Benchmark design max", release_readiness.get("max_abs_benchmark_history_design_comparison_changed_entries_delta")),
        ("Requests", request_history.get("total_log_records")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(summary.get('title', 'MiniGPT project maturity summary'))}</title>",
            style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(summary.get('title', 'MiniGPT project maturity summary'))}</h1><p>{_e(summary.get('project_root'))}</p></header>",
            '<section class="stats">' + "".join(card(label, value) for label, value in stats) + "</section>",
            capability_section(_list_of_dicts(summary.get("capabilities"))),
            timeline_section(_list_of_dicts(summary.get("phase_timeline"))),
            registry_section(registry),
            release_readiness_section(release_readiness),
            request_history_section(request_history),
            recommendation_section(_string_list(summary.get("recommendations"))),
            "<footer>Generated by MiniGPT maturity summary exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_maturity_summary_html(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_summary_html(summary), encoding="utf-8")


def write_maturity_summary_outputs(summary: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "maturity_summary.json",
        "csv": root / "maturity_summary.csv",
        "markdown": root / "maturity_summary.md",
        "html": root / "maturity_summary.html",
    }
    write_maturity_summary_json(summary, paths["json"])
    write_maturity_summary_csv(summary, paths["csv"])
    write_maturity_summary_markdown(summary, paths["markdown"])
    write_maturity_summary_html(summary, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value))


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return value


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


__all__ = [
    "render_maturity_summary_html",
    "render_maturity_summary_markdown",
    "write_maturity_summary_csv",
    "write_maturity_summary_html",
    "write_maturity_summary_json",
    "write_maturity_summary_markdown",
    "write_maturity_summary_outputs",
]
