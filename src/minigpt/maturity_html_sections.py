from __future__ import annotations

import html
from typing import Any


def card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def capability_section(rows: list[dict[str, Any]]) -> str:
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('title'))}</strong><br><span>{_e(row.get('key'))}</span></td>"
            f"<td><span class=\"pill {_e(row.get('status'))}\">{_e(row.get('status'))}</span></td>"
            f"<td>{_e(row.get('maturity_level'))}/{_e(row.get('target_level'))}</td>"
            f"<td>{_e(row.get('score_percent'))}%<br><span>{_e(_version_list(row.get('covered_versions')))}</span></td>"
            f"<td>{_e(row.get('evidence'))}</td>"
            f"<td>{_e(row.get('next_step'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Capability Matrix</h2>'
        '<table><thead><tr><th>Area</th><th>Status</th><th>Level</th><th>Coverage</th><th>Evidence</th><th>Next Step</th></tr></thead><tbody>'
        + "".join(table_rows)
        + "</tbody></table></section>"
    )


def timeline_section(rows: list[dict[str, Any]]) -> str:
    items = []
    for row in rows:
        items.append(
            "<tr>"
            f"<td>{_e(row.get('versions'))}</td>"
            f"<td>{_e(row.get('title'))}</td>"
            f"<td>{_e(row.get('covered_count'))}/{_e(row.get('target_count'))}</td>"
            f"<td>{_e(row.get('status'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Phase Timeline</h2>'
        '<table><thead><tr><th>Versions</th><th>Phase</th><th>Coverage</th><th>Status</th></tr></thead><tbody>'
        + "".join(items)
        + "</tbody></table></section>"
    )


def registry_section(registry: dict[str, Any]) -> str:
    rows = [
        ("Available", registry.get("available")),
        ("Runs", registry.get("run_count")),
        ("Pair reports", _fmt_mapping(registry.get("pair_report_counts"))),
        ("Pair delta cases", registry.get("pair_delta_cases")),
        ("Max generated delta", registry.get("pair_delta_max_generated")),
        ("Quality counts", _fmt_mapping(registry.get("quality_counts"))),
        ("Generation quality", _fmt_mapping(registry.get("generation_quality_counts"))),
    ]
    return '<section class="panel"><h2>Registry Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def release_readiness_section(release_readiness: dict[str, Any]) -> str:
    rows = [
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
        ("CI tiny plan regressions", release_readiness.get("ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count")),
        (
            "CI boundary gate regressions",
            release_readiness.get("ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count"),
        ),
        (
            "CI boundary plan regressions",
            release_readiness.get("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count"),
        ),
        ("CI archived path regressions", release_readiness.get("ci_workflow_archived_path_portability_check_ready_regression_count")),
        ("CI drift smoke regressions", release_readiness.get("ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count")),
        ("Max CI workflow failed-check delta", release_readiness.get("max_abs_ci_workflow_failed_check_delta")),
        ("Max CI workflow order-violation delta", release_readiness.get("max_abs_ci_workflow_order_violation_delta")),
        ("Test coverage regressions", release_readiness.get("test_coverage_regression_count")),
        ("Test coverage status changes", release_readiness.get("test_coverage_status_changed_count")),
        ("Max coverage percent delta", release_readiness.get("max_abs_test_coverage_percent_delta")),
        ("Max coverage gap delta", release_readiness.get("max_abs_test_coverage_gap_delta")),
        ("Benchmark-history regressions", release_readiness.get("benchmark_history_regression_count")),
        ("Benchmark suite-design deltas", release_readiness.get("benchmark_history_suite_design_non_comparison_ready_delta_count")),
        ("Benchmark suite-design regressions", release_readiness.get("benchmark_history_suite_design_non_comparison_ready_regression_count")),
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
        ("Max benchmark generation-flag regression delta", release_readiness.get("max_abs_benchmark_history_generation_flag_regression_delta")),
        (
            "Max benchmark suite-design delta",
            release_readiness.get("max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta"),
        ),
        ("Max benchmark design-change delta", release_readiness.get("max_abs_benchmark_history_design_comparison_changed_entries_delta")),
    ]
    return '<section class="panel"><h2>Release Readiness Trend Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def request_history_section(request_history: dict[str, Any]) -> str:
    rows = [
        ("Available", request_history.get("available")),
        ("Status", request_history.get("status")),
        ("Records", request_history.get("total_log_records")),
        ("Invalid", request_history.get("invalid_record_count")),
        ("OK", request_history.get("ok_count")),
        ("Timeout", request_history.get("timeout_count")),
        ("Bad request", request_history.get("bad_request_count")),
        ("Error", request_history.get("error_count")),
        ("Timeout rate", request_history.get("timeout_rate")),
        ("Error rate", request_history.get("error_rate")),
        ("Checkpoints", request_history.get("unique_checkpoint_count")),
        ("Latest", request_history.get("latest_timestamp")),
    ]
    return '<section class="panel"><h2>Request History Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def recommendation_section(items: list[str]) -> str:
    return '<section class="panel"><h2>Recommendations</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --green:#047857; --amber:#b45309; --red:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:58px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _version_list(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    return ", ".join(f"v{item}" for item in value)


def _fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value))


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


__all__ = [
    "capability_section",
    "card",
    "registry_section",
    "release_readiness_section",
    "recommendation_section",
    "request_history_section",
    "style",
    "timeline_section",
]
