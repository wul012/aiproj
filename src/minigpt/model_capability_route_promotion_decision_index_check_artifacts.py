from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_decision_index_check import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_route_promotion_decision_index_check_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("contract_check_ready", summary.get("contract_check_ready")),
        ("source_decision_count", summary.get("source_decision_count")),
        ("original_accepted_route_count", summary.get("original_accepted_route_count")),
        ("rebuilt_accepted_route_count", summary.get("rebuilt_accepted_route_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_decision_index_check_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "actual", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_decision_index_check_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion decision index contract check'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('contract_check_ready')}`",
        f"- Source decisions: `{summary.get('source_decision_count')}`",
        f"- Original routes: `{summary.get('original_route_ids')}`",
        f"- Rebuilt routes: `{summary.get('rebuilt_route_ids')}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Actual | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_decision_index_check_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("contract_check_ready")),
        ("Sources", summary.get("source_decision_count")),
        ("Original routes", summary.get("original_accepted_route_count")),
        ("Rebuilt routes", summary.get("rebuilt_accepted_route_count")),
    ]
    rows = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion decision index contract check'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion decision index contract check'))}</h1><p>Rebuilds the decision index from source decisions and compares contract fields.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_decision_index_check_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_decision_index_check_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_decision_index_check_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_decision_index_check_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_decision_index_check_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _check_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('actual'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#64717d;--line:#d8dee4;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef1f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_model_capability_route_promotion_decision_index_check_html",
    "render_model_capability_route_promotion_decision_index_check_markdown",
    "render_model_capability_route_promotion_decision_index_check_text",
    "write_model_capability_route_promotion_decision_index_check_outputs",
]
