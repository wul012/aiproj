from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (
    CONTRACT_SUMMARY_JSON_FILENAME,
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check_rows import (
    check_rows,
    check_summary_sidecars,
    contract_profile_checks as build_contract_profile_checks,
    contract_profile_issues,
    failed_check_count,
    json_text,
    missing_sidecars,
    summary_check_failed_targets,
    summary_check_family_summary,
    summary_field_checks as build_summary_field_checks,
    summary_field_issues,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check_render_sections import (
    check_family_html_sections,
    check_family_markdown_lines,
    check_family_text_rows,
)
from minigpt.report_utils import html_escape, string_list


CONTRACT_SUMMARY_CHECK_JSON_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.json"
CONTRACT_SUMMARY_CHECK_TEXT_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.txt"
CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.md"
CONTRACT_SUMMARY_CHECK_HTML_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.html"

SUMMARY_COMPARE_KEYS = (
    "contract_summary_version",
    "status",
    "decision",
    "checker_exit_code",
    "handoff_report_path",
    "receipt_schema_version",
    "schema_v3_ready",
    "schema_v4_ready",
    "assurance_status",
    "embedded_receipt_check_status",
    "embedded_receipt_check_sidecar_status",
    "main_embedded_receipt_check_status",
    "receipt_check_output_json_exists",
    "receipt_check_output_text_exists",
    "suite_design_scopes",
    "ci_boundary_plan_check_scopes",
    "contract_checks",
    "contract_check_count",
    "failed_contract_check_count",
    "contract_check_status_counts",
    "contract_check_type_summary",
    "issue_count",
    "issues",
)


def check_promoted_training_scale_seed_handoff_receipt_contract_summary(
    summary_path: str | Path,
    *,
    handoff_path: str | Path | None = None,
) -> dict[str, Any]:
    resolved_summary_path = resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(summary_path)
    actual = load_promoted_training_scale_seed_handoff_receipt_contract_summary(resolved_summary_path)
    source_path = Path(handoff_path) if handoff_path is not None else _handoff_path_from_summary(actual)
    issues: list[str] = []
    expected: dict[str, Any] = {}
    summary_field_checks: list[dict[str, Any]] = []
    contract_profile_checks = build_contract_profile_checks(actual)
    issues.extend(contract_profile_issues(contract_profile_checks))
    if source_path is None:
        issues.append("handoff report path is required for receipt contract summary check")
    else:
        try:
            expected = build_promoted_training_scale_seed_handoff_receipt_contract_summary(source_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"could not rebuild receipt contract summary from handoff path: {exc}")
    if expected:
        summary_field_checks = build_summary_field_checks(expected, actual, SUMMARY_COMPARE_KEYS)
        issues.extend(summary_field_issues(summary_field_checks))
        sidecars = check_summary_sidecars(resolved_summary_path.parent, expected)
    else:
        sidecars = missing_sidecars(resolved_summary_path.parent)
    sidecar_checks = check_rows(sidecars.get("checks"))
    issues.extend(string_list(sidecars.get("issues")))
    family_summary = summary_check_family_summary(summary_field_checks, contract_profile_checks, sidecar_checks)
    failed_targets = summary_check_failed_targets(summary_field_checks, contract_profile_checks, sidecar_checks)
    status = "pass" if not issues else "fail"
    decision = str((expected or actual).get("decision") or "")
    return {
        "summary_check_version": 1,
        "status": status,
        "decision": decision,
        "checker_exit_code": 0 if status == "pass" and decision == "continue" else 1,
        "summary_path": str(resolved_summary_path),
        "handoff_path": str(source_path) if source_path is not None else None,
        "actual_summary_status": actual.get("status"),
        "expected_summary_status": expected.get("status") if expected else None,
        "actual_schema_version": actual.get("receipt_schema_version"),
        "expected_schema_version": expected.get("receipt_schema_version") if expected else None,
        "summary_field_check_count": len(summary_field_checks),
        "failed_summary_field_check_count": failed_check_count(summary_field_checks),
        "summary_field_checks": summary_field_checks,
        "contract_profile_status": "pass" if failed_check_count(contract_profile_checks) == 0 else "fail",
        "contract_profile_check_count": len(contract_profile_checks),
        "failed_contract_profile_check_count": failed_check_count(contract_profile_checks),
        "contract_profile_checks": contract_profile_checks,
        "sidecar_status": sidecars.get("status"),
        "sidecar_check_count": len(sidecar_checks),
        "failed_sidecar_check_count": failed_check_count(sidecar_checks),
        "sidecar_checks": sidecar_checks,
        "check_family_summary": family_summary,
        "failed_check_target_count": len(failed_targets),
        "failed_check_targets": failed_targets,
        "sidecar_issue_count": sidecars.get("issue_count"),
        "sidecar_issues": sidecars.get("issues"),
        "text_path": sidecars.get("text_path"),
        "text_exists": sidecars.get("text_exists"),
        "markdown_path": sidecars.get("markdown_path"),
        "markdown_exists": sidecars.get("markdown_exists"),
        "html_path": sidecars.get("html_path"),
        "html_exists": sidecars.get("html_exists"),
        "issue_count": len(issues),
        "issues": issues,
        "actual_summary": actual,
        "expected_summary": expected,
    }


def load_promoted_training_scale_seed_handoff_receipt_contract_summary(path: str | Path) -> dict[str, Any]:
    payload = json.loads(
        resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(path).read_text(
            encoding="utf-8-sig"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("receipt contract summary must be a JSON object")
    return dict(payload)


def resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / CONTRACT_SUMMARY_JSON_FILENAME
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text(check: dict[str, Any]) -> str:
    rows = [
        ("receipt_contract_summary_check_status", check.get("status")),
        ("receipt_contract_summary_check_decision", check.get("decision")),
        ("receipt_contract_summary_check_checker_exit_code", check.get("checker_exit_code")),
        ("receipt_contract_summary_check_actual_status", check.get("actual_summary_status")),
        ("receipt_contract_summary_check_expected_status", check.get("expected_summary_status")),
        ("receipt_contract_summary_check_actual_schema_version", check.get("actual_schema_version")),
        ("receipt_contract_summary_check_expected_schema_version", check.get("expected_schema_version")),
        ("receipt_contract_summary_check_summary_field_check_count", check.get("summary_field_check_count")),
        (
            "receipt_contract_summary_check_failed_summary_field_check_count",
            check.get("failed_summary_field_check_count"),
        ),
        ("receipt_contract_summary_check_contract_profile_status", check.get("contract_profile_status")),
        ("receipt_contract_summary_check_contract_profile_check_count", check.get("contract_profile_check_count")),
        (
            "receipt_contract_summary_check_failed_contract_profile_check_count",
            check.get("failed_contract_profile_check_count"),
        ),
        *check_family_text_rows(check),
        ("receipt_contract_summary_check_sidecar_status", check.get("sidecar_status")),
        ("receipt_contract_summary_check_sidecar_check_count", check.get("sidecar_check_count")),
        ("receipt_contract_summary_check_failed_sidecar_check_count", check.get("failed_sidecar_check_count")),
        ("receipt_contract_summary_check_issue_count", check.get("issue_count")),
        ("receipt_contract_summary_check_issues", json.dumps(check.get("issues"), ensure_ascii=False)),
        (
            "receipt_contract_summary_check_summary_field_checks",
            json.dumps(check.get("summary_field_checks"), ensure_ascii=False),
        ),
        (
            "receipt_contract_summary_check_contract_profile_checks",
            json.dumps(check.get("contract_profile_checks"), ensure_ascii=False),
        ),
        (
            "receipt_contract_summary_check_sidecar_checks",
            json.dumps(check.get("sidecar_checks"), ensure_ascii=False),
        ),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown(check: dict[str, Any]) -> str:
    lines = [
        "# Promoted Seed Handoff Receipt Contract Summary Check",
        "",
        f"- Status: `{check.get('status')}`",
        f"- Decision: `{check.get('decision')}`",
        f"- Actual summary status: `{check.get('actual_summary_status')}`",
        f"- Expected summary status: `{check.get('expected_summary_status')}`",
        f"- Sidecar status: `{check.get('sidecar_status')}`",
        f"- Failed summary field checks: `{check.get('failed_summary_field_check_count')}`",
            f"- Failed contract profile checks: `{check.get('failed_contract_profile_check_count')}`",
            f"- Failed check targets: `{check.get('failed_check_target_count')}`",
            f"- Failed sidecar checks: `{check.get('failed_sidecar_check_count')}`",
            f"- Issue count: `{check.get('issue_count')}`",
            "",
        "## Summary Field Checks",
        "",
        "| Field | Type | Target | Status |",
        "| --- | --- | --- | --- |",
    ]
    for row in check_rows(check.get("summary_field_checks")):
        lines.append(
            f"| {row.get('key')} | {row.get('check_type')} | "
            f"{row.get('target')} | {row.get('status')} |"
        )
    lines.extend(check_family_markdown_lines(check))
    lines.extend(
        [
            "",
            "## Contract Profile Checks",
            "",
            "| Field | Type | Target | Status |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in check_rows(check.get("contract_profile_checks")):
        lines.append(
            f"| {row.get('key')} | {row.get('check_type')} | "
            f"{row.get('target')} | {row.get('status')} |"
        )
    lines.extend(
        [
            "",
            "## Sidecar Checks",
            "",
            "| Sidecar | Type | Target | Status | Exists |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in check_rows(check.get("sidecar_checks")):
        lines.append(
            f"| {row.get('id')} | {row.get('check_type')} | {row.get('target')} | "
            f"{row.get('status')} | {row.get('exists')} |"
        )
    lines.extend(
        [
            "",
            "## Sidecars",
            "",
            f"- Text exists: `{check.get('text_exists')}`",
            f"- Markdown exists: `{check.get('markdown_exists')}`",
            f"- HTML exists: `{check.get('html_exists')}`",
            "",
            "## Issues",
            "",
        ]
    )
    issues = string_list(check.get("issues"))
    if not issues:
        lines.append("- none")
    else:
        lines.extend(f"- {issue}" for issue in issues)
    return "\n".join(lines) + "\n"


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html(check: dict[str, Any]) -> str:
    issues = string_list(check.get("issues"))
    issue_items = "\n".join(f"<li>{html_escape(issue)}</li>" for issue in issues) or "<li>none</li>"
    summary_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('key'))}</td>"
        f"<td>{html_escape(row.get('check_type'))}</td>"
        f"<td>{html_escape(row.get('target'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(json_text(row.get('expected')))}</td>"
        f"<td>{html_escape(json_text(row.get('actual')))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
        for row in check_rows(check.get("summary_field_checks"))
    )
    contract_profile_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('key'))}</td>"
        f"<td>{html_escape(row.get('check_type'))}</td>"
        f"<td>{html_escape(row.get('target'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(json_text(row.get('expected')))}</td>"
        f"<td>{html_escape(json_text(row.get('actual')))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
        for row in check_rows(check.get("contract_profile_checks"))
    )
    sidecar_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('check_type'))}</td>"
        f"<td>{html_escape(row.get('target'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('exists'))}</td>"
        f"<td>{html_escape(row.get('expected_sha256'))}</td>"
        f"<td>{html_escape(row.get('actual_sha256'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
        for row in check_rows(check.get("sidecar_checks"))
    )
    family_sections = check_family_html_sections(check)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT receipt contract summary check</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f5f7f8; color: #172029; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d7dee3; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d7dee3; border-radius: 8px; padding: 10px; background: #fbfcfd; }}
.metric span {{ display: block; color: #5a6871; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: anywhere; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid #d7dee3; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef3f6; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT receipt contract summary check</h1>
<section>
<h2>Check</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(check.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(check.get('decision'))}</strong></div>
<div class="metric"><span>Actual</span><strong>{html_escape(check.get('actual_summary_status'))}</strong></div>
<div class="metric"><span>Expected</span><strong>{html_escape(check.get('expected_summary_status'))}</strong></div>
<div class="metric"><span>Profile</span><strong>{html_escape(check.get('contract_profile_status'))}</strong></div>
<div class="metric"><span>Failed Targets</span><strong>{html_escape(check.get('failed_check_target_count'))}</strong></div>
<div class="metric"><span>Sidecar</span><strong>{html_escape(check.get('sidecar_status'))}</strong></div>
<div class="metric"><span>Issues</span><strong>{html_escape(check.get('issue_count'))}</strong></div>
</div>
</section>
{family_sections}
<section>
<h2>Summary Field Checks</h2>
<table>
<thead>
<tr><th>Field</th><th>Type</th><th>Target</th><th>Status</th><th>Expected</th><th>Actual</th><th>Detail</th></tr>
</thead>
<tbody>
{summary_rows}
</tbody>
</table>
</section>
<section>
<h2>Contract Profile Checks</h2>
<table>
<thead>
<tr><th>Field</th><th>Type</th><th>Target</th><th>Status</th><th>Expected</th><th>Actual</th><th>Detail</th></tr>
</thead>
<tbody>
{contract_profile_rows}
</tbody>
</table>
</section>
<section>
<h2>Sidecar Checks</h2>
<table>
<thead>
<tr>
<th>Sidecar</th><th>Type</th><th>Target</th><th>Status</th><th>Exists</th>
<th>Expected SHA-256</th><th>Actual SHA-256</th><th>Detail</th>
</tr>
</thead>
<tbody>
{sidecar_rows}
</tbody>
</table>
</section>
<section>
<h2>Sidecars</h2>
<ul>
<li>Text exists: {html_escape(check.get('text_exists'))}</li>
<li>Markdown exists: {html_escape(check.get('markdown_exists'))}</li>
<li>HTML exists: {html_escape(check.get('html_exists'))}</li>
</ul>
</section>
<section>
<h2>Issues</h2>
<ul>
{issue_items}
</ul>
</section>
</main>
</body>
</html>
"""


def write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs(
    check: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / CONTRACT_SUMMARY_CHECK_JSON_FILENAME,
        "text": root / CONTRACT_SUMMARY_CHECK_TEXT_FILENAME,
        "markdown": root / CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME,
        "html": root / CONTRACT_SUMMARY_CHECK_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text(check),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown(check),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html(check),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _handoff_path_from_summary(summary: dict[str, Any]) -> Path | None:
    value = summary.get("handoff_report_path")
    return Path(str(value)) if value else None


__all__ = [
    "CONTRACT_SUMMARY_CHECK_HTML_FILENAME",
    "CONTRACT_SUMMARY_CHECK_JSON_FILENAME",
    "CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME",
    "CONTRACT_SUMMARY_CHECK_TEXT_FILENAME",
    "check_promoted_training_scale_seed_handoff_receipt_contract_summary",
    "load_promoted_training_scale_seed_handoff_receipt_contract_summary",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text",
    "resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path",
    "write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs",
]
