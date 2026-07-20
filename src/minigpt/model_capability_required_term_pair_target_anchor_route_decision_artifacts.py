from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_target_anchor_route_decision import (
    PAIR_TARGET_ANCHOR_ROUTE_DECISION_CSV_FILENAME,
    PAIR_TARGET_ANCHOR_ROUTE_DECISION_HTML_FILENAME,
    PAIR_TARGET_ANCHOR_ROUTE_DECISION_JSON_FILENAME,
    PAIR_TARGET_ANCHOR_ROUTE_DECISION_MARKDOWN_FILENAME,
    PAIR_TARGET_ANCHOR_ROUTE_DECISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_target_anchor_route_decision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("target_anchor_route_count", summary.get("target_anchor_route_count")),
        ("target_anchor_visible_hit_route_count", summary.get("target_anchor_visible_hit_route_count")),
        ("residual_signal_routes", ",".join(str(value) for value in summary.get("residual_signal_routes", []))),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_model_capability_required_term_pair_target_anchor_route_decision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Target-Anchor Route Decision",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Target-anchor routes: `{summary.get('target_anchor_route_count')}`",
            f"- Target-anchor visible hits: `{summary.get('target_anchor_visible_hit_route_count')}`",
            f"- Residual routes: `{','.join(str(value) for value in summary.get('residual_signal_routes', []))}`",
            "",
            "## Route Rows",
            "",
            *_route_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_target_anchor_route_decision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Target routes", summary.get("target_anchor_route_count")),
        ("Target visible", summary.get("target_anchor_visible_hit_route_count")),
        ("Residual", ",".join(str(value) for value in summary.get("residual_signal_routes", []))),
    ]
    rows = "\n".join(_route_html(row) for row in list_of_dicts(report.get("route_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT target-anchor route decision</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT target-anchor route decision</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Route Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Type</th><th>Pair-full</th><th>Hit terms</th><th>Reasons</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_target_anchor_route_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_TARGET_ANCHOR_ROUTE_DECISION_JSON_FILENAME,
        "csv": root / PAIR_TARGET_ANCHOR_ROUTE_DECISION_CSV_FILENAME,
        "text": root / PAIR_TARGET_ANCHOR_ROUTE_DECISION_TEXT_FILENAME,
        "markdown": root / PAIR_TARGET_ANCHOR_ROUTE_DECISION_MARKDOWN_FILENAME,
        "html": root / PAIR_TARGET_ANCHOR_ROUTE_DECISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_target_anchor_route_decision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_target_anchor_route_decision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_target_anchor_route_decision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["source_label", "route_type", "pair_full_seed_count", "seed_count", "hit_terms", "rejection_reasons"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("route_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _route_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Route | Type | Pair-full | Hit terms | Reasons |", "| --- | --- | ---: | --- | --- |"]
    for row in list_of_dicts(report.get("route_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_label")),
                    markdown_cell(row.get("route_type")),
                    markdown_cell(f"{row.get('pair_full_seed_count')}/{row.get('seed_count')}"),
                    markdown_cell(",".join(str(term) for term in row.get("hit_terms", []))),
                    markdown_cell(",".join(str(reason) for reason in row.get("rejection_reasons", []))),
                ]
            )
            + " |"
        )
    return rows


def _route_html(row: dict[str, Any]) -> str:
    pair_full = f"{row.get('pair_full_seed_count')}/{row.get('seed_count')}"
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('route_type'))}</td>"
        f"<td>{html_escape(pair_full)}</td>"
        f"<td>{html_escape(','.join(str(term) for term in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(reason) for reason in row.get('rejection_reasons', [])))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#18212b;--muted:#607080;--line:#d7dee6;--panel:#f6f8fb;--accent:#4f5420}
*{box-sizing:border-box}
body{margin:0;background:#f2f4f0;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_required_term_pair_target_anchor_route_decision_html",
    "render_model_capability_required_term_pair_target_anchor_route_decision_markdown",
    "render_model_capability_required_term_pair_target_anchor_route_decision_text",
    "write_model_capability_required_term_pair_target_anchor_route_decision_outputs",
]
