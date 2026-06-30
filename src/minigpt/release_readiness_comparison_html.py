from __future__ import annotations

from typing import Any

from minigpt.report_utils import html_escape as _e


def stats_section(stats: list[tuple[str, Any]]) -> str:
    return '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>"


def readiness_matrix_section(rows: list[dict[str, Any]]) -> str:
    body = "".join(_html_row(row) for row in rows)
    return (
        '<section class="panel"><h2>Readiness Matrix</h2><table><thead><tr>'
        "<th>Release</th><th>Status</th><th>Decision</th><th>Gate</th><th>Audit</th><th>Score</th>"
        "<th>CI workflow</th><th>CI failed</th><th>CI order violations</th><th>CI plan digest</th>"
        "<th>CI boundary gate</th><th>CI boundary plan</th><th>CI archived paths</th><th>CI receipt plan</th>"
        "<th>CI drift smoke ready</th><th>Request</th><th>Coverage</th><th>Coverage %</th><th>Gap</th>"
        "<th>Benchmark history</th><th>Benchmark ready</th><th>Suite-design not-ready</th><th>Design changes</th>"
        "<th>Benchmark readiness</th><th>Benchmark readiness exit</th><th>Benchmark regressions</th>"
        "<th>Benchmark boundary</th><th>Maturity</th><th>Panels</th>"
        "</tr></thead><tbody>"
        + body
        + "</tbody></table></section>"
    )


def deltas_section(deltas: list[dict[str, Any]]) -> str:
    body = "".join(_html_delta(delta) for delta in deltas)
    return (
        '<section class="panel"><h2>Deltas</h2><table><thead><tr>'
        "<th>Compared</th><th>Status delta</th><th>CI order violation delta</th>"
        "<th>CI plan digest regressed</th><th>CI boundary gate regressed</th><th>CI boundary plan regressed</th>"
        "<th>CI archived paths changed</th><th>CI archived paths regressed</th><th>CI receipt plan changed</th>"
        "<th>CI receipt plan regressed</th><th>CI drift smoke changed</th><th>CI drift smoke regressed</th>"
        "<th>CI regression reasons</th><th>Coverage % delta</th><th>Coverage gap delta</th>"
        "<th>Benchmark status delta</th><th>Suite-design not-ready delta</th><th>Design changes delta</th>"
        "<th>Benchmark readiness changed</th><th>Benchmark readiness exit delta</th><th>Failed reason drift</th>"
        "<th>Failed reasons added</th><th>Failed reasons removed</th><th>Benchmark case regression delta</th>"
        "<th>Benchmark boundary changed</th><th>Panel changes</th><th>Explanation</th>"
        "</tr></thead><tbody>"
        + body
        + "</tbody></table></section>"
    )


def list_section(title: str, values: Any) -> str:
    items = _string_list(values) or ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def style() -> str:
    return """<style>
:root { --ink:#17202a; --muted:#566170; --line:#d5dce6; --page:#f6f7f3; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; --blue:#1f5f74; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(145px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:54px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; background:var(--blue); }
.pill.ready, .pill.improved { background:var(--green); }
.pill.review, .pill.incomplete, .pill.panel-changed { background:var(--amber); }
.pill.blocked, .pill.regressed { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _html_row(row: dict[str, Any]) -> str:
    status = str(row.get("readiness_status") or "missing")
    return (
        "<tr>"
        f"<td>{_e(row.get('release_name') or row.get('readiness_path'))}<br><span>{_e(row.get('readiness_path'))}</span></td>"
        f'<td><span class="pill {status}">{_e(status)}</span></td>'
        f"<td>{_e(row.get('decision'))}</td>"
        f"<td>{_e(row.get('gate_status'))}</td>"
        f"<td>{_e(row.get('audit_status'))}</td>"
        f"<td>{_e(_fmt(row.get('audit_score_percent')))}</td>"
        f"<td>{_e(row.get('ci_workflow_status'))}</td>"
        f"<td>{_e(row.get('ci_workflow_failed_checks'))}</td>"
        f"<td>{_e(row.get('ci_workflow_order_violation_count'))}</td>"
        f"<td>{_e(row.get('ci_workflow_tiny_scorecard_plan_digest_gate_ready'))}</td>"
        f"<td>{_e(row.get('ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready'))}</td>"
        f"<td>{_e(row.get('ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready'))}</td>"
        f"<td>{_e(row.get('ci_workflow_archived_path_portability_check_ready'))}</td>"
        f"<td>{_e(row.get('ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready'))}</td>"
        f"<td>{_e(row.get('ci_workflow_release_readiness_drift_contract_smoke_ready'))}</td>"
        f"<td>{_e(row.get('request_history_status'))}</td>"
        f"<td>{_e(row.get('test_coverage_status'))}</td>"
        f"<td>{_e(_fmt(row.get('test_coverage_percent')))}</td>"
        f"<td>{_e(_fmt(row.get('test_coverage_gap')))}</td>"
        f"<td>{_e(row.get('benchmark_history_status'))}</td>"
        f"<td>{_e(row.get('benchmark_history_ready'))}</td>"
        f"<td>{_e(row.get('benchmark_history_suite_design_non_comparison_ready_entries'))}</td>"
        f"<td>{_e(row.get('benchmark_history_design_comparison_changed_entries'))}</td>"
        f"<td>{_e(row.get('benchmark_history_readiness_requirement_status'))}</td>"
        f"<td>{_e(row.get('benchmark_history_readiness_requirement_exit_code'))}</td>"
        f"<td>{_e(row.get('benchmark_history_case_regressions'))}</td>"
        f"<td>{_e(row.get('benchmark_history_latest_boundary'))}</td>"
        f"<td>{_e(row.get('maturity_status'))}</td>"
        f"<td>{_e(row.get('fail_panel_count'))} fail / {_e(row.get('warn_panel_count'))} warn</td>"
        "</tr>"
    )


def _html_delta(delta: dict[str, Any]) -> str:
    status = str(delta.get("delta_status") or "same")
    return (
        "<tr>"
        f"<td>{_e(delta.get('compared_release') or delta.get('compared_path'))}<br><span>{_e(delta.get('compared_path'))}</span></td>"
        f'<td><span class="pill {status}">{_e(_status_delta_label(delta.get("status_delta")))}</span></td>'
        f"<td>{_e(_fmt(delta.get('ci_workflow_order_violation_delta')))}</td>"
        f"<td>{_e(delta.get('ci_workflow_tiny_scorecard_plan_digest_gate_ready_regressed'))}</td>"
        f"<td>{_e(delta.get('ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regressed'))}</td>"
        f"<td>{_e(delta.get('ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed'))}</td>"
        f"<td>{_e(delta.get('ci_workflow_archived_path_portability_check_ready_changed'))}</td>"
        f"<td>{_e(delta.get('ci_workflow_archived_path_portability_check_ready_regressed'))}</td>"
        f"<td>{_e(delta.get('ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_changed'))}</td>"
        f"<td>{_e(delta.get('ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_regressed'))}</td>"
        f"<td>{_e(delta.get('ci_workflow_release_readiness_drift_contract_smoke_ready_changed'))}</td>"
        f"<td>{_e(delta.get('ci_workflow_release_readiness_drift_contract_smoke_ready_regressed'))}</td>"
        f"<td>{_e(', '.join(_string_list(delta.get('ci_workflow_regression_reasons'))))}</td>"
        f"<td>{_e(_fmt(delta.get('test_coverage_percent_delta')))}</td>"
        f"<td>{_e(_fmt(delta.get('test_coverage_gap_delta')))}</td>"
        f"<td>{_e(_fmt(delta.get('benchmark_history_status_delta')))}</td>"
        f"<td>{_e(_fmt(delta.get('benchmark_history_suite_design_non_comparison_ready_entries_delta')))}</td>"
        f"<td>{_e(_fmt(delta.get('benchmark_history_design_comparison_changed_entries_delta')))}</td>"
        f"<td>{_e(delta.get('benchmark_history_readiness_requirement_status_changed'))}</td>"
        f"<td>{_e(_fmt(delta.get('benchmark_history_readiness_requirement_exit_code_delta')))}</td>"
        f"<td>{_e(delta.get('benchmark_history_readiness_requirement_failed_reason_drift_status'))}</td>"
        f"<td>{_e(', '.join(_string_list(delta.get('benchmark_history_readiness_requirement_failed_reason_added'))))}</td>"
        f"<td>{_e(', '.join(_string_list(delta.get('benchmark_history_readiness_requirement_failed_reason_removed'))))}</td>"
        f"<td>{_e(_fmt(delta.get('benchmark_history_case_regression_delta')))}</td>"
        f"<td>{_e(delta.get('benchmark_history_latest_boundary_changed'))}</td>"
        f"<td>{_e(', '.join(_string_list(delta.get('changed_panels'))))}</td>"
        f"<td>{_e(delta.get('explanation'))}</td>"
        "</tr>"
    )


def _stat(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt(value))}</div>' + "</div>"


def _status_delta_label(value: Any) -> str:
    delta = int(value or 0)
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


__all__ = [
    "deltas_section",
    "list_section",
    "readiness_matrix_section",
    "stats_section",
    "style",
]
