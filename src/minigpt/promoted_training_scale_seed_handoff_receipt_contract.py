from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_assurance import (
    check_promoted_training_scale_seed_handoff_assurance,
)
from minigpt.report_utils import html_escape, string_list


CONTRACT_SUMMARY_JSON_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
CONTRACT_SUMMARY_TEXT_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.txt"
CONTRACT_SUMMARY_MARKDOWN_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.md"
CONTRACT_SUMMARY_HTML_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.html"


def build_promoted_training_scale_seed_handoff_receipt_contract_summary(path: str | Path) -> dict[str, Any]:
    assurance = check_promoted_training_scale_seed_handoff_assurance(path)
    scopes = _suite_design_scopes(assurance)
    boundary_scopes = _ci_boundary_plan_check_scopes(assurance)
    contract_checks = _contract_checks(assurance, scopes, boundary_scopes)
    issues = _contract_issues(assurance, scopes, boundary_scopes)
    status = "pass" if not issues else "fail"
    decision = str(assurance.get("decision") or "")
    receipt_schema_version = _int(assurance.get("embedded_receipt_check_receipt_schema_version"))
    return {
        "contract_summary_version": 1,
        "status": status,
        "decision": decision,
        "checker_exit_code": 0 if status == "pass" and decision == "continue" else 1,
        "handoff_report_path": assurance.get("handoff_report_path"),
        "receipt_schema_version": receipt_schema_version,
        "schema_v3_ready": receipt_schema_version >= 3,
        "schema_v4_ready": receipt_schema_version >= 4,
        "assurance_status": assurance.get("status"),
        "embedded_receipt_check_status": assurance.get("embedded_receipt_check_status"),
        "embedded_receipt_check_sidecar_status": assurance.get("embedded_receipt_check_sidecar_status"),
        "main_embedded_receipt_check_status": assurance.get("main_embedded_receipt_check_status"),
        "receipt_check_output_json_exists": bool(assurance.get("embedded_receipt_check_output_json_exists")),
        "receipt_check_output_text_exists": bool(assurance.get("embedded_receipt_check_output_text_exists")),
        "suite_design_scopes": scopes,
        "ci_boundary_plan_check_scopes": boundary_scopes,
        "contract_checks": contract_checks,
        "contract_check_count": len(contract_checks),
        "failed_contract_check_count": sum(1 for check in contract_checks if check.get("status") != "pass"),
        "issue_count": len(issues),
        "issues": issues,
        "assurance": assurance,
    }


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary: dict[str, Any]) -> str:
    rows = [
        ("receipt_contract_status", summary.get("status")),
        ("receipt_contract_decision", summary.get("decision")),
        ("receipt_contract_checker_exit_code", summary.get("checker_exit_code")),
        ("receipt_contract_schema_version", summary.get("receipt_schema_version")),
        ("receipt_contract_schema_v3_ready", summary.get("schema_v3_ready")),
        ("receipt_contract_schema_v4_ready", summary.get("schema_v4_ready")),
        ("receipt_contract_assurance_status", summary.get("assurance_status")),
        ("receipt_contract_embedded_status", summary.get("embedded_receipt_check_status")),
        ("receipt_contract_sidecar_status", summary.get("embedded_receipt_check_sidecar_status")),
        ("receipt_contract_check_count", summary.get("contract_check_count")),
        ("receipt_contract_failed_check_count", summary.get("failed_contract_check_count")),
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
            "| Check | Scope | Status | Expected | Actual |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for check in _contract_check_rows(summary):
        lines.append(
            f"| {check.get('id')} | {check.get('scope')} | {check.get('status')} | "
            f"{check.get('expected')} | {check.get('actual')} |"
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
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(check.get('id'))}</td>"
        f"<td>{html_escape(check.get('scope'))}</td>"
        f"<td>{html_escape(check.get('status'))}</td>"
        f"<td>{html_escape(check.get('expected'))}</td>"
        f"<td>{html_escape(check.get('actual'))}</td>"
        "</tr>"
        for check in _contract_check_rows(summary)
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
<div class="metric"><span>Assurance</span><strong>{html_escape(summary.get('assurance_status'))}</strong></div>
<div class="metric"><span>Sidecar</span><strong>{html_escape(summary.get('embedded_receipt_check_sidecar_status'))}</strong></div>
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
<h2>Issues</h2>
<ul>
{issue_items}
</ul>
</section>
<section>
<h2>Contract Checks</h2>
<table>
<thead><tr><th>Check</th><th>Scope</th><th>Status</th><th>Expected</th><th>Actual</th></tr></thead>
<tbody>
{check_rows}
</tbody>
</table>
</section>
</main>
</body>
</html>
"""


def write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs(
    summary: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / CONTRACT_SUMMARY_JSON_FILENAME,
        "text": root / CONTRACT_SUMMARY_TEXT_FILENAME,
        "markdown": root / CONTRACT_SUMMARY_MARKDOWN_FILENAME,
        "html": root / CONTRACT_SUMMARY_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(summary),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(summary),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _suite_design_scopes(assurance: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _suite_design_scope(
            "selected",
            assurance.get("embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count"),
            assurance.get("embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_names"),
        ),
        _suite_design_scope(
            "handoff",
            assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count"),
            assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names"),
        ),
        _suite_design_scope(
            "comparison_ready",
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names"
            ),
        ),
    ]


def _suite_design_scope(scope: str, count: Any, names: Any) -> dict[str, Any]:
    resolved_count = _int(count)
    resolved_names = string_list(names)
    return {
        "scope": scope,
        "count": resolved_count,
        "names": resolved_names,
        "name_count": len(resolved_names),
        "count_matches_names": resolved_count == len(resolved_names),
    }


def _ci_boundary_plan_check_scopes(assurance: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _ci_boundary_plan_check_scope(
            "selected",
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        _ci_boundary_plan_check_scope(
            "handoff",
            assurance.get(
                "embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
            ),
        ),
        _ci_boundary_plan_check_scope(
            "comparison_ready",
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
            assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
            ),
        ),
    ]


def _ci_boundary_plan_check_scope(scope: str, handoff_count: Any, selected_count: Any) -> dict[str, Any]:
    resolved_handoff_count = _int(handoff_count)
    resolved_selected_count = _int(selected_count)
    return {
        "scope": scope,
        "handoff_count": resolved_handoff_count,
        "selected_count": resolved_selected_count,
        "selected_within_handoff": 0 <= resolved_selected_count <= resolved_handoff_count,
    }


def _contract_checks(
    assurance: dict[str, Any],
    scopes: list[dict[str, Any]],
    boundary_scopes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    receipt_schema_version = _int(assurance.get("embedded_receipt_check_receipt_schema_version"))
    checks = [
        _contract_check(
            "assurance_status_pass",
            "assurance",
            "pass",
            assurance.get("status"),
            "handoff assurance must pass",
        ),
        _contract_check(
            "schema_v3_ready",
            "receipt",
            True,
            receipt_schema_version >= 3,
            "receipt schema must support suite-design name contract",
        ),
        _contract_check(
            "schema_v4_ready",
            "receipt",
            True,
            receipt_schema_version >= 4,
            "receipt schema must support CI boundary plan-check contract",
        ),
        _contract_check(
            "embedded_receipt_check_sidecar_pass",
            "embedded_receipt_check",
            "pass",
            assurance.get("embedded_receipt_check_sidecar_status"),
            "embedded receipt-check sidecar must pass",
        ),
    ]
    checks.extend(
        _contract_check(
            f"suite_design_{scope.get('scope')}_count_matches_names",
            str(scope.get("scope")),
            True,
            bool(scope.get("count_matches_names")),
            "suite-design regression count must match name count",
        )
        for scope in scopes
    )
    checks.extend(
        _contract_check(
            f"ci_boundary_plan_check_{scope.get('scope')}_selected_within_handoff",
            str(scope.get("scope")),
            True,
            bool(scope.get("selected_within_handoff")),
            "selected CI boundary plan-check count must not exceed handoff count",
        )
        for scope in boundary_scopes
    )
    return checks


def _contract_check(check_id: str, scope: str, expected: Any, actual: Any, detail: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "scope": scope,
        "status": "pass" if actual == expected else "fail",
        "expected": expected,
        "actual": actual,
        "detail": detail,
    }


def _contract_issues(
    assurance: dict[str, Any],
    scopes: list[dict[str, Any]],
    boundary_scopes: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    receipt_schema_version = _int(assurance.get("embedded_receipt_check_receipt_schema_version"))
    if assurance.get("status") != "pass":
        issues.append("handoff assurance must pass")
        issues.extend(f"assurance.{issue}" for issue in string_list(assurance.get("issues")))
    if receipt_schema_version < 3:
        issues.append("receipt schema version must be >= 3 for suite-design name contract")
    if receipt_schema_version < 4:
        issues.append("receipt schema version must be >= 4 for CI boundary plan-check contract")
    if assurance.get("embedded_receipt_check_sidecar_status") != "pass":
        issues.append("embedded receipt-check sidecar status must pass")
    for scope in scopes:
        if not scope.get("count_matches_names"):
            issues.append(
                f"{scope.get('scope')} suite-design regression count {scope.get('count')} "
                f"does not match name count {scope.get('name_count')}"
            )
    for scope in boundary_scopes:
        if not scope.get("selected_within_handoff"):
            issues.append(
                f"{scope.get('scope')} CI boundary plan-check selected count {scope.get('selected_count')} "
                f"exceeds handoff count {scope.get('handoff_count')}"
            )
    return issues


def _scope_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    value = summary.get("suite_design_scopes")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _boundary_scope_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    value = summary.get("ci_boundary_plan_check_scopes")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _contract_check_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    value = summary.get("contract_checks")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "CONTRACT_SUMMARY_HTML_FILENAME",
    "CONTRACT_SUMMARY_JSON_FILENAME",
    "CONTRACT_SUMMARY_MARKDOWN_FILENAME",
    "CONTRACT_SUMMARY_TEXT_FILENAME",
    "build_promoted_training_scale_seed_handoff_receipt_contract_summary",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_html",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_text",
    "write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs",
]
