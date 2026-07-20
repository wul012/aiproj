from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_decision_index import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_model_capability_route_promotion_decision_index_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("decision_index_ready", summary.get("decision_index_ready")),
        ("source_decision_count", summary.get("source_decision_count")),
        ("accepted_route_count", summary.get("accepted_route_count")),
        ("route_ids", ",".join(str(item) for item in summary.get("route_ids", []))),
        ("boundary", summary.get("boundary")),
        ("model_quality_claim", summary.get("model_quality_claim")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_decision_index_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["route_id", "entry_status", "source_index", "review_scope", "boundary", "model_quality_claim", "source_decision_path"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("entries")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_decision_index_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion decision index'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('decision_index_ready')}`",
        f"- Accepted routes: `{summary.get('accepted_route_count')}`",
        f"- Route ids: `{', '.join(str(item) for item in summary.get('route_ids', []))}`",
        f"- Boundary: `{summary.get('boundary')}`",
        f"- Claim: `{summary.get('model_quality_claim')}`",
        "",
        "## Route Entries",
        "",
        "| Route | Status | Scope | Boundary | Claim | Source |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("entries")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("route_id")),
                    markdown_cell(row.get("entry_status")),
                    markdown_cell(row.get("review_scope")),
                    markdown_cell(row.get("boundary")),
                    markdown_cell(row.get("model_quality_claim")),
                    markdown_cell(row.get("source_decision_path")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_decision_index_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("decision_index_ready")),
        ("Routes", summary.get("accepted_route_count")),
        ("Boundary", summary.get("boundary")),
        ("Claim", summary.get("model_quality_claim")),
    ]
    entries = "".join(_entry_row(row) for row in list_of_dicts(report.get("entries")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion decision index'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion decision index'))}</h1><p>Indexes accepted bounded route promotion decisions for downstream model capability governance.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Route Entries</h2><div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Status</th><th>Scope</th><th>Boundary</th><th>Claim</th></tr></thead>
<tbody>{entries}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_decision_index_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_decision_index_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_decision_index_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_decision_index_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_decision_index_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _entry_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('route_id'))}</td>"
        f"<td>{html_escape(row.get('entry_status'))}</td>"
        f"<td>{html_escape(row.get('review_scope'))}</td>"
        f"<td>{html_escape(row.get('boundary'))}</td>"
        f"<td>{html_escape(row.get('model_quality_claim'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#15202b;--muted:#64717d;--line:#d8dee4;--panel:#f8fafc;--accent:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:#eef2f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
</style>"""


__all__ = [
    "render_model_capability_route_promotion_decision_index_html",
    "render_model_capability_route_promotion_decision_index_markdown",
    "render_model_capability_route_promotion_decision_index_text",
    "write_model_capability_route_promotion_decision_index_outputs",
]
