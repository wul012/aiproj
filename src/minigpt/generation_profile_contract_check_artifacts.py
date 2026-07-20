from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.generation_profile_contract_check import (
    GENERATION_PROFILE_CONTRACT_CHECK_CSV_FILENAME,
    GENERATION_PROFILE_CONTRACT_CHECK_HTML_FILENAME,
    GENERATION_PROFILE_CONTRACT_CHECK_JSON_FILENAME,
    GENERATION_PROFILE_CONTRACT_CHECK_MARKDOWN_FILENAME,
    GENERATION_PROFILE_CONTRACT_CHECK_TEXT_FILENAME,
    checks,
    issues,
    summary,
)
from minigpt.report_utils import csv_cell, html_escape, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_generation_profile_contract_check_text(report: dict[str, Any]) -> str:
    stats = summary(report)
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("endpoint_profile_ids", ",".join(str(item) for item in stats.get("endpoint_profile_ids", []))),
        ("health_profile_ids", ",".join(str(item) for item in stats.get("health_profile_ids", []))),
        ("api_generation_profile", stats.get("api_generation_profile")),
        ("api_blocked_token_count", stats.get("api_blocked_token_count")),
        ("default_output_has_newline", stats.get("default_output_has_newline")),
        ("profile_output_has_newline", stats.get("profile_output_has_newline")),
        ("issues", ",".join(str(issue.get("id")) for issue in issues(report))),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_generation_profile_contract_check_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "category", "target", "expected", "actual", "status", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in checks(report):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_generation_profile_contract_check_markdown(report: dict[str, Any]) -> str:
    stats = summary(report)
    check_rows = [
        "| Check | Category | Status | Target |",
        "| --- | --- | --- | --- |",
    ]
    for row in checks(report):
        check_rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("category")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("target")),
                ]
            )
            + " |"
        )
    issue_lines = ["- none"] if not issues(report) else [f"- `{item.get('id')}`: {item.get('detail')}" for item in issues(report)]
    return "\n".join(
        [
            "# MiniGPT Generation Profile Contract Check",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Failed count: `{report.get('failed_count')}`",
            f"- Endpoint profile ids: `{stats.get('endpoint_profile_ids')}`",
            f"- Health profile ids: `{stats.get('health_profile_ids')}`",
            f"- API generation profile: `{stats.get('api_generation_profile')}`",
            f"- API blocked token count: `{stats.get('api_blocked_token_count')}`",
            "",
            "## Checks",
            "",
            *check_rows,
            "",
            "## Issues",
            "",
            *issue_lines,
            "",
        ]
    )


def render_generation_profile_contract_check_html(report: dict[str, Any]) -> str:
    stats = summary(report)
    cards = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Failed count", report.get("failed_count")),
        ("Endpoint ids", stats.get("endpoint_profile_ids")),
        ("Health ids", stats.get("health_profile_ids")),
        ("API profile", stats.get("api_generation_profile")),
        ("Blocked tokens", stats.get("api_blocked_token_count")),
    ]
    check_rows = "\n".join(_check_row(row) for row in checks(report))
    issue_items = "\n".join(f"<li><strong>{html_escape(item.get('id'))}</strong>: {html_escape(item.get('detail'))}</li>" for item in issues(report)) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT generation profile contract check</title>
{_style()}
</head>
<body>
<main>
<header>
<h1>MiniGPT generation profile contract check</h1>
<p>Verifies the endpoint, health payload, API response, playground HTML, and CLI samples for the generation profile contract.</p>
</header>
<section class="stats">{''.join(_card(label, value) for label, value in cards)}</section>
<section class="panel">
<h2>Checks</h2>
<div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Category</th><th>Status</th><th>Target</th><th>Detail</th></tr></thead>
<tbody>{check_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Issues</h2>
<ul>{issue_items}</ul>
</section>
</main>
</body>
</html>
"""


def write_generation_profile_contract_check_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / GENERATION_PROFILE_CONTRACT_CHECK_JSON_FILENAME,
        "csv": root / GENERATION_PROFILE_CONTRACT_CHECK_CSV_FILENAME,
        "text": root / GENERATION_PROFILE_CONTRACT_CHECK_TEXT_FILENAME,
        "markdown": root / GENERATION_PROFILE_CONTRACT_CHECK_MARKDOWN_FILENAME,
        "html": root / GENERATION_PROFILE_CONTRACT_CHECK_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_generation_profile_contract_check_csv(report, paths["csv"])
    paths["text"].write_text(render_generation_profile_contract_check_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_generation_profile_contract_check_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_generation_profile_contract_check_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _check_row(row: dict[str, Any]) -> str:
    status_class = "pass" if row.get("status") == "pass" else "fail"
    return (
        f"<tr class=\"{status_class}\">"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('category'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('target'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#667085;--line:#d7dee6;--panel:#f7f9fb;--pass:#0f766e;--fail:#b42318}
*{box-sizing:border-box}
body{margin:0;background:#edf1f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;margin:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
tr.pass td:nth-child(3){color:var(--pass);font-weight:700}
tr.fail td:nth-child(3){color:var(--fail);font-weight:700}
li{margin:6px 0}
</style>"""


__all__ = [
    "render_generation_profile_contract_check_html",
    "render_generation_profile_contract_check_markdown",
    "render_generation_profile_contract_check_text",
    "write_generation_profile_contract_check_csv",
    "write_generation_profile_contract_check_outputs",
]
