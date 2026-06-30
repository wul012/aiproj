from __future__ import annotations

import json
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_contract_context import row_list
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_rows import contract_check_rows
from minigpt.report_utils import html_escape, string_list


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary: dict[str, Any]) -> str:
    rows = [
        ("receipt_contract_status", summary.get("status")),
        ("receipt_contract_decision", summary.get("decision")),
        ("receipt_contract_checker_exit_code", summary.get("checker_exit_code")),
        ("receipt_contract_schema_version", summary.get("receipt_schema_version")),
        ("receipt_contract_schema_v3_ready", summary.get("schema_v3_ready")),
        ("receipt_contract_schema_v4_ready", summary.get("schema_v4_ready")),
        ("receipt_contract_schema_v5_ready", summary.get("schema_v5_ready")),
        ("receipt_contract_assurance_status", summary.get("assurance_status")),
        ("receipt_contract_embedded_status", summary.get("embedded_receipt_check_status")),
        ("receipt_contract_sidecar_status", summary.get("embedded_receipt_check_sidecar_status")),
        ("receipt_contract_check_count", summary.get("contract_check_count")),
        ("receipt_contract_failed_check_count", summary.get("failed_contract_check_count")),
        (
            "receipt_contract_check_status_counts",
            json.dumps(summary.get("contract_check_status_counts"), ensure_ascii=False),
        ),
        (
            "receipt_contract_check_type_summary",
            json.dumps(summary.get("contract_check_type_summary"), ensure_ascii=False),
        ),
        ("receipt_contract_issue_count", summary.get("issue_count")),
        ("receipt_contract_issues", json.dumps(summary.get("issues"), ensure_ascii=False)),
        ("receipt_contract_checks", json.dumps(summary.get("contract_checks"), ensure_ascii=False)),
    ]
    for scope in _scope_rows(summary):
        name = scope["scope"]
        rows.extend(
            [
                (f"receipt_contract_{name}_suite_design_count", scope.get("count")),
                (
                    f"receipt_contract_{name}_suite_design_names",
                    json.dumps(scope.get("names"), ensure_ascii=False),
                ),
                (f"receipt_contract_{name}_suite_design_count_matches_names", scope.get("count_matches_names")),
            ]
        )
    for scope in _boundary_scope_rows(summary):
        name = scope["scope"]
        rows.extend(
            [
                (
                    f"receipt_contract_{name}_ci_boundary_plan_check_handoff_count",
                    scope.get("handoff_count"),
                ),
                (
                    f"receipt_contract_{name}_ci_boundary_plan_check_selected_count",
                    scope.get("selected_count"),
                ),
                (
                    f"receipt_contract_{name}_ci_boundary_plan_check_selected_within_handoff",
                    scope.get("selected_within_handoff"),
                ),
            ]
        )
    for scope in _reason_scope_rows(summary):
        name = scope["scope"]
        rows.extend(
            [
                (
                    f"receipt_contract_{name}_ci_reason_handoff_counts",
                    json.dumps(scope.get("handoff_reason_counts"), ensure_ascii=False, sort_keys=True),
                ),
                (
                    f"receipt_contract_{name}_ci_reason_selected_counts",
                    json.dumps(scope.get("selected_reason_counts"), ensure_ascii=False, sort_keys=True),
                ),
                (
                    f"receipt_contract_{name}_ci_reason_selected_within_handoff",
                    scope.get("selected_reasons_within_handoff"),
                ),
                (
                    f"receipt_contract_{name}_ci_reason_missing_reasons",
                    json.dumps(scope.get("missing_reasons"), ensure_ascii=False),
                ),
            ]
        )
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Promoted Seed Handoff Receipt Contract Summary",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        f"- Receipt schema version: `{summary.get('receipt_schema_version')}`",
        f"- Schema v3 ready: `{summary.get('schema_v3_ready')}`",
        f"- Schema v4 ready: `{summary.get('schema_v4_ready')}`",
        f"- Schema v5 ready: `{summary.get('schema_v5_ready')}`",
        f"- Assurance status: `{summary.get('assurance_status')}`",
        f"- Embedded sidecar status: `{summary.get('embedded_receipt_check_sidecar_status')}`",
        "",
        "## Suite-Design Scopes",
        "",
        "| Scope | Count | Names | Count matches names |",
        "| --- | ---: | --- | --- |",
    ]
    for scope in _scope_rows(summary):
        names = ", ".join(string_list(scope.get("names"))) or "none"
        lines.append(
            f"| {scope.get('scope')} | {scope.get('count')} | {names} | {scope.get('count_matches_names')} |"
        )
    lines.extend(
        [
            "",
            "## CI Boundary Plan-Check Scopes",
            "",
            "| Scope | Handoff count | Selected count | Selected within handoff |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for scope in _boundary_scope_rows(summary):
        lines.append(
            f"| {scope.get('scope')} | {scope.get('handoff_count')} | "
            f"{scope.get('selected_count')} | {scope.get('selected_within_handoff')} |"
        )
    lines.extend(
        [
            "",
            "## CI Reason-Count Scopes",
            "",
            "| Scope | Handoff reasons | Selected reasons | Selected within handoff | Missing reasons |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for scope in _reason_scope_rows(summary):
        handoff_counts = json.dumps(scope.get("handoff_reason_counts"), ensure_ascii=False, sort_keys=True)
        selected_counts = json.dumps(scope.get("selected_reason_counts"), ensure_ascii=False, sort_keys=True)
        missing = ", ".join(string_list(scope.get("missing_reasons"))) or "none"
        lines.append(
            f"| {scope.get('scope')} | {handoff_counts} | {selected_counts} | "
            f"{scope.get('selected_reasons_within_handoff')} | {missing} |"
        )
    lines.extend(["", "## Issues", ""])
    issues = string_list(summary.get("issues"))
    if not issues:
        lines.append("- none")
    else:
        lines.extend(f"- {issue}" for issue in issues)
    lines.extend(
        [
            "",
            "## Contract Checks",
            "",
            "| Check | Type | Target | Scope | Status | Expected | Actual |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for check in contract_check_rows(summary):
        lines.append(
            f"| {check.get('id')} | {check.get('check_type')} | {check.get('target')} | "
            f"{check.get('scope')} | {check.get('status')} | {check.get('expected')} | {check.get('actual')} |"
        )
    lines.extend(
        [
            "",
            "## Contract Check Type Summary",
            "",
            "| Type | Status | Count | Passed | Failed | Required | Targets |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in _contract_check_type_summary_rows(summary):
        targets = ", ".join(string_list(row.get("targets"))) or "none"
        lines.append(
            f"| {row.get('check_type')} | {row.get('status')} | {row.get('count')} | "
            f"{row.get('passed_count')} | {row.get('failed_count')} | {row.get('required_count')} | {targets} |"
        )
    return "\n".join(lines) + "\n"


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(summary: dict[str, Any]) -> str:
    suite_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(scope.get('scope'))}</td>"
        f"<td>{html_escape(scope.get('count'))}</td>"
        f"<td>{html_escape(', '.join(string_list(scope.get('names'))) or 'none')}</td>"
        f"<td>{html_escape(scope.get('count_matches_names'))}</td>"
        "</tr>"
        for scope in _scope_rows(summary)
    )
    boundary_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(scope.get('scope'))}</td>"
        f"<td>{html_escape(scope.get('handoff_count'))}</td>"
        f"<td>{html_escape(scope.get('selected_count'))}</td>"
        f"<td>{html_escape(scope.get('selected_within_handoff'))}</td>"
        "</tr>"
        for scope in _boundary_scope_rows(summary)
    )
    reason_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(scope.get('scope'))}</td>"
        f"<td>{html_escape(json.dumps(scope.get('handoff_reason_counts'), ensure_ascii=False, sort_keys=True))}</td>"
        f"<td>{html_escape(json.dumps(scope.get('selected_reason_counts'), ensure_ascii=False, sort_keys=True))}</td>"
        f"<td>{html_escape(scope.get('selected_reasons_within_handoff'))}</td>"
        f"<td>{html_escape(', '.join(string_list(scope.get('missing_reasons'))) or 'none')}</td>"
        "</tr>"
        for scope in _reason_scope_rows(summary)
    )
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(check.get('id'))}</td>"
        f"<td>{html_escape(check.get('check_type'))}</td>"
        f"<td>{html_escape(check.get('target'))}</td>"
        f"<td>{html_escape(check.get('scope'))}</td>"
        f"<td>{html_escape(check.get('status'))}</td>"
        f"<td>{html_escape(check.get('expected'))}</td>"
        f"<td>{html_escape(check.get('actual'))}</td>"
        f"<td>{html_escape(check.get('detail'))}</td>"
        "</tr>"
        for check in contract_check_rows(summary)
    )
    type_summary_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('check_type'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('count'))}</td>"
        f"<td>{html_escape(row.get('passed_count'))}</td>"
        f"<td>{html_escape(row.get('failed_count'))}</td>"
        f"<td>{html_escape(row.get('required_count'))}</td>"
        f"<td>{html_escape(', '.join(string_list(row.get('targets'))) or 'none')}</td>"
        "</tr>"
        for row in _contract_check_type_summary_rows(summary)
    )
    issues = string_list(summary.get("issues"))
    issue_items = "\n".join(f"<li>{html_escape(issue)}</li>" for issue in issues) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT promoted seed handoff receipt contract summary</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f6f8f7; color: #17211d; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d7dfdb; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d7dfdb; border-radius: 8px; padding: 10px; background: #fbfcfb; }}
.metric span {{ display: block; color: #5c6c65; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: anywhere; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid #d7dfdb; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef3f1; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT promoted seed handoff receipt contract summary</h1>
<section>
<h2>Contract</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(summary.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(summary.get('decision'))}</strong></div>
<div class="metric"><span>Schema</span><strong>{html_escape(summary.get('receipt_schema_version'))}</strong></div>
<div class="metric"><span>Schema v5</span><strong>{html_escape(summary.get('schema_v5_ready'))}</strong></div>
<div class="metric"><span>Assurance</span><strong>{html_escape(summary.get('assurance_status'))}</strong></div>
<div class="metric"><span>Sidecar</span>
<strong>{html_escape(summary.get('embedded_receipt_check_sidecar_status'))}</strong></div>
<div class="metric"><span>Issues</span><strong>{html_escape(summary.get('issue_count'))}</strong></div>
</div>
</section>
<section>
<h2>Suite-Design Scopes</h2>
<table>
<thead><tr><th>Scope</th><th>Count</th><th>Names</th><th>Count matches names</th></tr></thead>
<tbody>
{suite_rows}
</tbody>
</table>
</section>
<section>
<h2>CI Boundary Plan-Check Scopes</h2>
<table>
<thead><tr><th>Scope</th><th>Handoff count</th><th>Selected count</th><th>Selected within handoff</th></tr></thead>
<tbody>
{boundary_rows}
</tbody>
</table>
</section>
<section>
<h2>CI Reason-Count Scopes</h2>
<table>
<thead>
<tr><th>Scope</th><th>Handoff reasons</th><th>Selected reasons</th><th>Selected within handoff</th><th>Missing reasons</th></tr>
</thead>
<tbody>
{reason_rows}
</tbody>
</table>
</section>
<section>
<h2>Issues</h2>
<ul>
{issue_items}
</ul>
</section>
<section>
<h2>Contract Checks</h2>
<table>
<thead>
<tr>
<th>Check</th><th>Type</th><th>Target</th><th>Scope</th><th>Status</th>
<th>Expected</th><th>Actual</th><th>Detail</th>
</tr>
</thead>
<tbody>
{check_rows}
</tbody>
</table>
</section>
<section>
<h2>Contract Check Type Summary</h2>
<table>
<thead>
<tr>
<th>Type</th><th>Status</th><th>Count</th><th>Passed</th><th>Failed</th><th>Required</th><th>Targets</th>
</tr>
</thead>
<tbody>
{type_summary_rows}
</tbody>
</table>
</section>
</main>
</body>
</html>
"""


def _scope_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return row_list(summary.get("suite_design_scopes"))


def _boundary_scope_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return row_list(summary.get("ci_boundary_plan_check_scopes"))


def _reason_scope_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return row_list(summary.get("ci_reason_count_scopes"))


def _contract_check_type_summary_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return row_list(summary.get("contract_check_type_summary"))


__all__ = [
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_html",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_text",
]
