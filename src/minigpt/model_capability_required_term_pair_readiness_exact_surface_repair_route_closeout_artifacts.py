from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout import (
    PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_CSV_FILENAME,
    PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_HTML_FILENAME,
    PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_JSON_FILENAME,
    PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_MARKDOWN_FILENAME,
    PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_exact_surface_repair_route_closeout_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    closeout = as_dict(report.get("closeout"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("closeout_ready", summary.get("closeout_ready")),
        ("closed_route", summary.get("closed_route")),
        ("recommended_next_route", summary.get("recommended_next_route")),
        ("candidate_route_count", summary.get("candidate_route_count")),
        ("closed_reason", closeout.get("closed_reason")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_exact_surface_repair_route_closeout_markdown(report: dict[str, Any]) -> str:
    closeout = as_dict(report.get("closeout"))
    routes = ["| Route | Why | Risk |", "| --- | --- | --- |"]
    for row in list_of_dicts(closeout.get("candidate_routes")):
        routes.append("| " + " | ".join([markdown_cell(row.get("route")), markdown_cell(row.get("why")), markdown_cell(row.get("risk"))]) + " |")
    return "\n".join(
        [
            "# MiniGPT Exact-Surface Repair Route Closeout",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Closed route: `{closeout.get('closed_route')}`",
            f"- Recommended next route: `{closeout.get('recommended_next_route')}`",
            "",
            "## Candidate Routes",
            "",
            *routes,
            "",
        ]
    )


def render_exact_surface_repair_route_closeout_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    closeout = as_dict(report.get("closeout"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("closeout_ready")),
        ("Closed route", summary.get("closed_route")),
        ("Next route", summary.get("recommended_next_route")),
        ("Candidates", summary.get("candidate_route_count")),
    ]
    do_not = "".join(f"<li>{html_escape(item)}</li>" for item in closeout.get("do_not_continue", []))
    routes = "".join(_route_html(row) for row in list_of_dicts(closeout.get("candidate_routes")))
    checks = "".join(_check_html(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT exact-surface repair route closeout</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT exact-surface repair route closeout</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Do Not Continue</h2><ul>{do_not}</ul></section>
<section class="panel"><h2>Candidate Routes</h2><div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Why</th><th>Risk</th></tr></thead>
<tbody>{routes}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_exact_surface_repair_route_closeout_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["route", "why", "risk"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(as_dict(report.get("closeout")).get("candidate_routes")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_exact_surface_repair_route_closeout_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_JSON_FILENAME,
        "csv": root / PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_CSV_FILENAME,
        "text": root / PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_EXACT_SURFACE_REPAIR_ROUTE_CLOSEOUT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_exact_surface_repair_route_closeout_csv(report, paths["csv"])
    paths["text"].write_text(render_exact_surface_repair_route_closeout_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_exact_surface_repair_route_closeout_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_exact_surface_repair_route_closeout_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _route_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('route'))}</td>"
        f"<td>{html_escape(row.get('why'))}</td>"
        f"<td>{html_escape(row.get('risk'))}</td>"
        "</tr>"
    )


def _check_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('actual'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p,li{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
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
    "render_exact_surface_repair_route_closeout_html",
    "render_exact_surface_repair_route_closeout_markdown",
    "render_exact_surface_repair_route_closeout_text",
    "write_exact_surface_repair_route_closeout_outputs",
]
