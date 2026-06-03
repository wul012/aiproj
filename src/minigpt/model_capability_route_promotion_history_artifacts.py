from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_history import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, string_list, write_json_payload


def render_model_capability_route_promotion_history_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    requirement = as_dict(report.get("readiness_requirement"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("entry_count", summary.get("entry_count")),
        ("ready_count", summary.get("ready_count")),
        ("blocked_count", summary.get("blocked_count")),
        ("boundary_mismatch_count", summary.get("boundary_mismatch_count")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("readiness_requirement_status", requirement.get("status")),
        ("readiness_requirement_failed_reasons", ",".join(string_list(requirement.get("failed_reasons")))),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_history_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "index",
        "name",
        "route_id",
        "route_status",
        "promotion_readiness",
        "history_entry_status",
        "boundary",
        "boundary_matches",
        "model_quality_claim",
        "seed_count",
        "min_pair_full_count",
        "pair_full_strength_spread",
        "source_manifest_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("entries")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_history_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    requirement = as_dict(report.get("readiness_requirement"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion history'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Entries: `{summary.get('entry_count')}`",
        f"- Ready: `{summary.get('ready_count')}`",
        f"- Boundary mismatches: `{summary.get('boundary_mismatch_count')}`",
        f"- Model quality claim: `{summary.get('model_quality_claim')}`",
        f"- Readiness requirement: `{requirement.get('status')}`",
        "",
        "## Ledger",
        "",
        "| Name | Route | Status | Ready | Boundary | Claim | Seeds | Pair Full Min | Spread |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("entries")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("name")),
                    markdown_cell(row.get("route_id")),
                    markdown_cell(row.get("route_status")),
                    markdown_cell(row.get("promotion_readiness")),
                    markdown_cell(row.get("boundary")),
                    markdown_cell(row.get("model_quality_claim")),
                    markdown_cell(row.get("seed_count")),
                    markdown_cell(row.get("min_pair_full_count")),
                    markdown_cell(row.get("pair_full_strength_spread")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {markdown_cell(item)}" for item in string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_history_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    requirement = as_dict(report.get("readiness_requirement"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Entries", summary.get("entry_count")),
        ("Ready", summary.get("ready_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Boundary mismatches", summary.get("boundary_mismatch_count")),
        ("Claim", summary.get("model_quality_claim")),
        ("Readiness", requirement.get("status")),
    ]
    entries = "".join(_entry_row(row) for row in list_of_dicts(report.get("entries")))
    recommendations = "".join(f"<li>{html_escape(item)}</li>" for item in string_list(report.get("recommendations")))
    failed = ", ".join(string_list(requirement.get("failed_reasons"))) or "none"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion history'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion history'))}</h1><p>Tracks route promotion manifests as bounded model capability history without broad production claims.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Readiness Requirement</h2><p>Status: <strong>{html_escape(requirement.get('status'))}</strong>; failed reasons: <strong>{html_escape(failed)}</strong></p></section>
<section class="panel"><h2>Ledger</h2><div class="table-wrap"><table>
<thead><tr><th>Name</th><th>Route</th><th>Status</th><th>Ready</th><th>Boundary</th><th>Claim</th><th>Seeds</th><th>Pair Full Min</th><th>Spread</th><th>Source</th></tr></thead>
<tbody>{entries}</tbody>
</table></div></section>
<section class="panel"><h2>Recommendations</h2><ul>{recommendations}</ul></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_history_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_history_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_history_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_history_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_history_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _entry_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('name'))}</td>"
        f"<td>{html_escape(row.get('route_id'))}</td>"
        f"<td>{html_escape(row.get('route_status'))}</td>"
        f"<td>{html_escape(row.get('promotion_readiness'))}</td>"
        f"<td>{html_escape(row.get('boundary'))}</td>"
        f"<td>{html_escape(row.get('model_quality_claim'))}</td>"
        f"<td>{html_escape(row.get('seed_count'))}</td>"
        f"<td>{html_escape(row.get('min_pair_full_count'))}</td>"
        f"<td>{html_escape(row.get('pair_full_strength_spread'))}</td>"
        f"<td>{html_escape(row.get('source_manifest_path'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#62707d;--line:#d8dee4;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#edf2f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
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
ul{margin:0;padding-left:20px}
li{margin:6px 0}
</style>"""


__all__ = [
    "render_model_capability_route_promotion_history_html",
    "render_model_capability_route_promotion_history_markdown",
    "render_model_capability_route_promotion_history_text",
    "write_model_capability_route_promotion_history_outputs",
]
