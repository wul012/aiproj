from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    write_json_payload,
)
from minigpt.release_readiness_comparison_html import (
    deltas_section,
    list_section,
    readiness_matrix_section,
    stats_section,
    style,
)


def write_release_readiness_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_release_readiness_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = _list_of_dicts(report.get("rows"))
    fieldnames = [
        "readiness_path",
        "release_name",
        "readiness_status",
        "decision",
        "readiness_score",
        "gate_status",
        "audit_status",
        "audit_score_percent",
        "ci_workflow_status",
        "ci_workflow_failed_checks",
        "ci_workflow_required_order_count",
        "ci_workflow_order_violation_count",
        "ci_workflow_tiny_scorecard_plan_digest_gate_ready",
        "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready",
        "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready",
        "ci_workflow_archived_path_portability_check_ready",
        "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready",
        "ci_workflow_release_readiness_drift_contract_smoke_ready",
        "request_history_status",
        "test_coverage_status",
        "test_coverage_percent",
        "test_coverage_fail_under",
        "test_coverage_gap",
        "benchmark_history_status",
        "benchmark_history_entries",
        "benchmark_history_ready",
        "benchmark_history_review",
        "benchmark_history_blocked",
        "benchmark_history_case_regressions",
        "benchmark_history_generation_flag_regressions",
        "benchmark_history_suite_design_non_comparison_ready_entries",
        "benchmark_history_design_comparison_changed_entries",
        "benchmark_history_readiness_requirement_status",
        "benchmark_history_readiness_requirement_exit_code",
        "benchmark_history_readiness_requirement_failed_reasons",
        "benchmark_history_model_quality_claim",
        "benchmark_history_latest_boundary",
        "maturity_status",
        "ready_runs",
        "missing_artifacts",
        "fail_panel_count",
        "warn_panel_count",
        "action_count",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def write_release_readiness_delta_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = _list_of_dicts(report.get("deltas"))
    fieldnames = [
        "baseline_path",
        "compared_path",
        "baseline_release",
        "compared_release",
        "baseline_status",
        "compared_status",
        "status_delta",
        "delta_status",
        "audit_score_delta",
        "ci_workflow_failed_check_delta",
        "ci_workflow_required_order_delta",
        "ci_workflow_order_violation_delta",
        "ci_workflow_status_changed",
        "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regressed",
        "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regressed",
        "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed",
        "baseline_ci_workflow_archived_path_portability_check_ready",
        "compared_ci_workflow_archived_path_portability_check_ready",
        "ci_workflow_archived_path_portability_check_ready_changed",
        "ci_workflow_archived_path_portability_check_ready_regressed",
        "baseline_ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready",
        "compared_ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready",
        "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_changed",
        "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_regressed",
        "baseline_ci_workflow_release_readiness_drift_contract_smoke_ready",
        "compared_ci_workflow_release_readiness_drift_contract_smoke_ready",
        "ci_workflow_release_readiness_drift_contract_smoke_ready_changed",
        "ci_workflow_release_readiness_drift_contract_smoke_ready_regressed",
        "ci_workflow_regression_reasons",
        "test_coverage_percent_delta",
        "test_coverage_gap_delta",
        "test_coverage_status_changed",
        "benchmark_history_status_delta",
        "benchmark_history_status_changed",
        "benchmark_history_ready_delta",
        "benchmark_history_review_delta",
        "benchmark_history_blocked_delta",
        "benchmark_history_case_regression_delta",
        "benchmark_history_generation_flag_regression_delta",
        "benchmark_history_suite_design_non_comparison_ready_entries_delta",
        "benchmark_history_design_comparison_changed_entries_delta",
        "benchmark_history_readiness_requirement_status_changed",
        "benchmark_history_readiness_requirement_exit_code_delta",
        "compared_benchmark_history_readiness_requirement_failed_reasons",
        "benchmark_history_readiness_requirement_failed_reason_added_count",
        "benchmark_history_readiness_requirement_failed_reason_removed_count",
        "benchmark_history_readiness_requirement_failed_reason_added",
        "benchmark_history_readiness_requirement_failed_reason_removed",
        "benchmark_history_readiness_requirement_failed_reason_drift_status",
        "benchmark_history_model_quality_claim_changed",
        "benchmark_history_latest_boundary_changed",
        "missing_artifact_delta",
        "fail_panel_delta",
        "warn_panel_delta",
        "changed_panels",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for delta in deltas:
            writer.writerow({key: _csv_value(delta.get(key)) for key in fieldnames})


def render_release_readiness_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT release readiness comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Baseline: `{report.get('baseline_path')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Readiness reports", summary.get("readiness_count")),
                ("Baseline status", summary.get("baseline_status")),
                ("Ready count", summary.get("ready_count")),
                ("Blocked count", summary.get("blocked_count")),
                ("Improved count", summary.get("improved_count")),
                ("Regressed count", summary.get("regressed_count")),
                ("Changed panel deltas", summary.get("changed_panel_delta_count")),
                ("CI workflow regressions", summary.get("ci_workflow_regression_count")),
                ("CI order regressions", summary.get("ci_workflow_order_regression_count")),
                (
                    "CI drift-contract smoke ready changes",
                    summary.get("ci_workflow_release_readiness_drift_contract_smoke_ready_changed_count"),
                ),
                (
                    "CI drift-contract smoke ready regressions",
                    summary.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count"),
                ),
                (
                    "CI tiny plan digest regressions",
                    summary.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count"),
                ),
                (
                    "CI boundary gate check regressions",
                    summary.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count"),
                ),
                (
                    "CI boundary plan check regressions",
                    summary.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count"),
                ),
                (
                    "CI archived path portability changes",
                    summary.get("ci_workflow_archived_path_portability_check_ready_changed_count"),
                ),
                (
                    "CI archived path portability regressions",
                    summary.get("ci_workflow_archived_path_portability_check_ready_regression_count"),
                ),
                (
                    "CI receipt plan-check changes",
                    summary.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_changed_count"),
                ),
                (
                    "CI receipt plan-check regressions",
                    summary.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_regression_count"),
                ),
                ("CI workflow regression reasons", _fmt_mapping(summary.get("ci_workflow_regression_reason_counts"))),
                ("Max CI order violation delta", summary.get("max_abs_ci_workflow_order_violation_delta")),
                ("Test coverage regressions", summary.get("test_coverage_regression_count")),
                ("Benchmark history deltas", summary.get("benchmark_history_delta_count")),
                ("Benchmark history regressions", summary.get("benchmark_history_regression_count")),
                (
                    "Benchmark suite-design not-ready deltas",
                    summary.get("benchmark_history_suite_design_non_comparison_ready_delta_count"),
                ),
                (
                    "Benchmark suite-design not-ready regressions",
                    summary.get("benchmark_history_suite_design_non_comparison_ready_regression_count"),
                ),
                (
                    "Benchmark design-comparison change deltas",
                    summary.get("benchmark_history_design_comparison_changed_delta_count"),
                ),
                (
                    "Benchmark readiness failed reasons added",
                    summary.get("benchmark_history_readiness_requirement_failed_reason_added_count"),
                ),
                (
                    "Benchmark readiness failed reasons removed",
                    summary.get("benchmark_history_readiness_requirement_failed_reason_removed_count"),
                ),
                (
                    "Benchmark readiness failed reason removals",
                    ", ".join(_string_list(summary.get("benchmark_history_readiness_requirement_failed_reason_removed"))) or "none",
                ),
                (
                    "Benchmark readiness failed reason recovery deltas",
                    summary.get("benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"),
                ),
                (
                    "Benchmark readiness failed reason mixed deltas",
                    summary.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"),
                ),
                (
                    "Benchmark readiness failed reason drift",
                    _fmt_mapping(summary.get("benchmark_history_readiness_requirement_failed_reason_drift_status_counts")),
                ),
            ]
        ),
        "",
        "## Readiness Matrix",
        "",
        "| Release | Status | Decision | Gate | Audit | Score | CI workflow | CI failed | CI order violations | CI plan digest | CI boundary gate | CI boundary plan | CI archived paths | CI receipt plan | CI drift smoke ready | Request history | Coverage | Coverage % | Coverage gap | Benchmark history | Benchmark ready | Suite-design not-ready | Design changes | Benchmark readiness | Benchmark readiness exit | Benchmark regressions | Benchmark boundary | Maturity | Fail panels | Warn panels |",
        "| --- | --- | --- | --- | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | --- | --- | ---: | ---: |",
    ]
    for row in _list_of_dicts(report.get("rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("release_name") or row.get("readiness_path")),
                    _md(row.get("readiness_status")),
                    _md(row.get("decision")),
                    _md(row.get("gate_status")),
                    _md(row.get("audit_status")),
                    _md(row.get("audit_score_percent")),
                    _md(row.get("ci_workflow_status")),
                    _md(row.get("ci_workflow_failed_checks")),
                    _md(row.get("ci_workflow_order_violation_count")),
                    _md(row.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready")),
                    _md(row.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready")),
                    _md(row.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready")),
                    _md(row.get("ci_workflow_archived_path_portability_check_ready")),
                    _md(row.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready")),
                    _md(row.get("ci_workflow_release_readiness_drift_contract_smoke_ready")),
                    _md(row.get("request_history_status")),
                    _md(row.get("test_coverage_status")),
                    _md(row.get("test_coverage_percent")),
                    _md(row.get("test_coverage_gap")),
                    _md(row.get("benchmark_history_status")),
                    _md(row.get("benchmark_history_ready")),
                    _md(row.get("benchmark_history_suite_design_non_comparison_ready_entries")),
                    _md(row.get("benchmark_history_design_comparison_changed_entries")),
                    _md(row.get("benchmark_history_readiness_requirement_status")),
                    _md(row.get("benchmark_history_readiness_requirement_exit_code")),
                    _md(row.get("benchmark_history_case_regressions")),
                    _md(row.get("benchmark_history_latest_boundary")),
                    _md(row.get("maturity_status")),
                    _md(row.get("fail_panel_count")),
                    _md(row.get("warn_panel_count")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Deltas",
            "",
            "| Compared | Status delta | CI order violation delta | CI plan digest regressed | CI boundary gate regressed | CI boundary plan regressed | CI archived paths changed | CI archived paths regressed | CI receipt plan changed | CI receipt plan regressed | CI drift smoke changed | CI drift smoke regressed | CI regression reasons | Coverage % delta | Coverage gap delta | Benchmark status delta | Suite-design not-ready delta | Design changes delta | Benchmark readiness changed | Benchmark readiness exit delta | Failed reason drift | Failed reasons added | Failed reasons removed | Benchmark case regression delta | Benchmark boundary changed | Panel changes | Explanation |",
            "| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for delta in _list_of_dicts(report.get("deltas")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(delta.get("compared_release") or delta.get("compared_path")),
                    _md(delta.get("status_delta")),
                    _md(delta.get("ci_workflow_order_violation_delta")),
                    _md(delta.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready_regressed")),
                    _md(delta.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regressed")),
                    _md(delta.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed")),
                    _md(delta.get("ci_workflow_archived_path_portability_check_ready_changed")),
                    _md(delta.get("ci_workflow_archived_path_portability_check_ready_regressed")),
                    _md(delta.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_changed")),
                    _md(delta.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_regressed")),
                    _md(delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_changed")),
                    _md(delta.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regressed")),
                    _md(", ".join(_string_list(delta.get("ci_workflow_regression_reasons")))),
                    _md(delta.get("test_coverage_percent_delta")),
                    _md(delta.get("test_coverage_gap_delta")),
                    _md(delta.get("benchmark_history_status_delta")),
                    _md(delta.get("benchmark_history_suite_design_non_comparison_ready_entries_delta")),
                    _md(delta.get("benchmark_history_design_comparison_changed_entries_delta")),
                    _md(delta.get("benchmark_history_readiness_requirement_status_changed")),
                    _md(delta.get("benchmark_history_readiness_requirement_exit_code_delta")),
                    _md(delta.get("benchmark_history_readiness_requirement_failed_reason_drift_status")),
                    _md(", ".join(_string_list(delta.get("benchmark_history_readiness_requirement_failed_reason_added")))),
                    _md(", ".join(_string_list(delta.get("benchmark_history_readiness_requirement_failed_reason_removed")))),
                    _md(delta.get("benchmark_history_case_regression_delta")),
                    _md(delta.get("benchmark_history_latest_boundary_changed")),
                    _md(", ".join(_string_list(delta.get("changed_panels")))),
                    _md(delta.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_release_readiness_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_readiness_comparison_markdown(report), encoding="utf-8")


def render_release_readiness_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Reports", summary.get("readiness_count")),
        ("Baseline", summary.get("baseline_status")),
        ("Ready", summary.get("ready_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Improved", summary.get("improved_count")),
        ("Regressed", summary.get("regressed_count")),
        ("Panel deltas", summary.get("changed_panel_delta_count")),
        ("CI regressions", summary.get("ci_workflow_regression_count")),
        ("CI order regressions", summary.get("ci_workflow_order_regression_count")),
        ("CI drift smoke changes", summary.get("ci_workflow_release_readiness_drift_contract_smoke_ready_changed_count")),
        ("CI drift smoke regressions", summary.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count")),
        ("CI tiny plan regressions", summary.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count")),
        ("CI boundary gate regressions", summary.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count")),
        ("CI boundary plan regressions", summary.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count")),
        ("CI archived path changes", summary.get("ci_workflow_archived_path_portability_check_ready_changed_count")),
        ("CI archived path regressions", summary.get("ci_workflow_archived_path_portability_check_ready_regression_count")),
        ("CI receipt plan changes", summary.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_changed_count")),
        ("CI receipt plan regressions", summary.get("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_regression_count")),
        ("CI regression reasons", _fmt_mapping(summary.get("ci_workflow_regression_reason_counts"))),
        ("Coverage regressions", summary.get("test_coverage_regression_count")),
        ("Benchmark deltas", summary.get("benchmark_history_delta_count")),
        ("Benchmark regressions", summary.get("benchmark_history_regression_count")),
        ("Bench design deltas", summary.get("benchmark_history_suite_design_non_comparison_ready_delta_count")),
        ("Bench design regressions", summary.get("benchmark_history_suite_design_non_comparison_ready_regression_count")),
        ("Bench design changes", summary.get("benchmark_history_design_comparison_changed_delta_count")),
        ("Benchmark reason additions", summary.get("benchmark_history_readiness_requirement_failed_reason_added_count")),
        ("Benchmark reason removals", summary.get("benchmark_history_readiness_requirement_failed_reason_removed_count")),
        ("Benchmark reason recoveries", summary.get("benchmark_history_readiness_requirement_failed_reason_recovery_delta_count")),
        ("Benchmark reason mixed", summary.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count")),
        ("Generated", report.get("generated_at")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT release readiness comparison'))}</title>",
            style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT release readiness comparison'))}</h1><p>baseline: {_e(report.get('baseline_path'))}</p></header>",
            stats_section(stats),
            readiness_matrix_section(_list_of_dicts(report.get("rows"))),
            deltas_section(_list_of_dicts(report.get("deltas"))),
            list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT release readiness comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_release_readiness_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_readiness_comparison_html(report), encoding="utf-8")


def write_release_readiness_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "release_readiness_comparison.json",
        "csv": root / "release_readiness_comparison.csv",
        "delta_csv": root / "release_readiness_deltas.csv",
        "markdown": root / "release_readiness_comparison.md",
        "html": root / "release_readiness_comparison.html",
    }
    write_release_readiness_comparison_json(report, paths["json"])
    write_release_readiness_comparison_csv(report, paths["csv"])
    write_release_readiness_delta_csv(report, paths["delta_csv"])
    write_release_readiness_comparison_markdown(report, paths["markdown"])
    write_release_readiness_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _csv_value(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(_string_list(value))
    return str(csv_cell(value))


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value))


def _md(value: Any) -> str:
    return _fmt(value).replace("|", "\\|").replace("\n", " ")


__all__ = [
    "render_release_readiness_comparison_html",
    "render_release_readiness_comparison_markdown",
    "write_release_readiness_comparison_csv",
    "write_release_readiness_comparison_html",
    "write_release_readiness_comparison_json",
    "write_release_readiness_comparison_markdown",
    "write_release_readiness_comparison_outputs",
    "write_release_readiness_delta_csv",
]
