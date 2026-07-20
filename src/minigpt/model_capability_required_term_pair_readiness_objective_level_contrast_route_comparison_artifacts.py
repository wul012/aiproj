from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_CSV_FILENAME,
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_HTML_FILENAME,
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_JSON_FILENAME,
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_MARKDOWN_FILENAME,
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_objective_level_contrast_route_comparison_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("selected_route", summary.get("selected_route")),
        ("objective_route_best", summary.get("objective_route_best")),
        ("objective_pair_full_count", summary.get("objective_pair_full_count")),
        ("promotion_guard_required", summary.get("promotion_guard_required")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_objective_level_contrast_route_comparison_markdown(report: dict[str, Any]) -> str:
    rows = ["| Route | Decision | Exact full | Required all | Pair-full count | Exact hits |", "| --- | --- | --- | --- | ---: | ---: |"]
    for row in list_of_dicts(report.get("route_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("route")),
                    markdown_cell(row.get("decision")),
                    markdown_cell(row.get("exact_heldout_pair_full")),
                    markdown_cell(row.get("required_all_pair_full")),
                    markdown_cell(row.get("pair_full_count")),
                    markdown_cell(row.get("exact_default_hit_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Objective-Level Contrast Route Comparison",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            "",
            "## Route Rows",
            "",
            *rows,
            "",
        ]
    )


def render_objective_level_contrast_route_comparison_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Selected", summary.get("selected_route")),
        ("Objective best", summary.get("objective_route_best")),
        ("Objective pair-full", summary.get("objective_pair_full_count")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_route_html(row) for row in list_of_dicts(report.get("route_rows")))
    checks = "".join(_check_html(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT objective-level contrast route comparison</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT objective-level contrast route comparison</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Route Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Decision</th><th>Exact full</th><th>Required all</th><th>Pair-full count</th><th>Exact hits</th></tr></thead>
<tbody>{rows}</tbody>
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


def write_objective_level_contrast_route_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["route", "decision", "exact_heldout_pair_full", "required_all_pair_full", "pair_full_count", "exact_default_hit_count"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("route_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_objective_level_contrast_route_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_JSON_FILENAME,
        "csv": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_CSV_FILENAME,
        "text": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_objective_level_contrast_route_comparison_csv(report, paths["csv"])
    paths["text"].write_text(render_objective_level_contrast_route_comparison_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_objective_level_contrast_route_comparison_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_objective_level_contrast_route_comparison_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _route_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('route'))}</td>"
        f"<td>{html_escape(row.get('decision'))}</td>"
        f"<td>{html_escape(row.get('exact_heldout_pair_full'))}</td>"
        f"<td>{html_escape(row.get('required_all_pair_full'))}</td>"
        f"<td>{html_escape(row.get('pair_full_count'))}</td>"
        f"<td>{html_escape(row.get('exact_default_hit_count'))}</td>"
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
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_objective_level_contrast_route_comparison_html",
    "render_objective_level_contrast_route_comparison_markdown",
    "render_objective_level_contrast_route_comparison_text",
    "write_objective_level_contrast_route_comparison_outputs",
]
