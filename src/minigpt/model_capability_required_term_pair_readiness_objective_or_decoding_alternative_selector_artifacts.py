from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector import (
    PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_CSV_FILENAME,
    PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_HTML_FILENAME,
    PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_JSON_FILENAME,
    PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_MARKDOWN_FILENAME,
    PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_objective_or_decoding_alternative_selector_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("selector_ready", summary.get("selector_ready")),
        ("selected_route", summary.get("selected_route")),
        ("selected_score", summary.get("selected_score")),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
        ("route_count", summary.get("route_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_objective_or_decoding_alternative_selector_markdown(report: dict[str, Any]) -> str:
    selector = as_dict(report.get("selector"))
    routes = ["| Route | Score | Selected | Next artifact | Risk control |", "| --- | ---: | --- | --- | --- |"]
    for row in list_of_dicts(report.get("route_rows")):
        routes.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("route")),
                    markdown_cell(row.get("score")),
                    markdown_cell(row.get("selected")),
                    markdown_cell(row.get("next_artifact")),
                    markdown_cell(row.get("risk_control")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Objective-Or-Decoding Alternative Selector",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Selected route: `{selector.get('selected_route')}`",
            f"- Proposed next artifact: `{selector.get('proposed_next_artifact')}`",
            "",
            "## Route Scores",
            "",
            *routes,
            "",
            "## Non Goals",
            "",
            *[f"- {markdown_cell(item)}" for item in selector.get("non_goals", [])],
            "",
        ]
    )


def render_objective_or_decoding_alternative_selector_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    selector = as_dict(report.get("selector"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("selector_ready")),
        ("Selected", summary.get("selected_route")),
        ("Score", summary.get("selected_score")),
        ("Next", summary.get("proposed_next_artifact")),
    ]
    routes = "".join(_route_html(row) for row in list_of_dicts(report.get("route_rows")))
    checks = "".join(_check_html(row) for row in list_of_dicts(report.get("check_rows")))
    non_goals = "".join(f"<li>{html_escape(item)}</li>" for item in selector.get("non_goals", []))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT objective-or-decoding alternative selector</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT objective-or-decoding alternative selector</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Route Scores</h2><div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Score</th><th>Selected</th><th>Next artifact</th><th>Selection reason</th><th>Risk control</th></tr></thead>
<tbody>{routes}</tbody>
</table></div></section>
<section class="panel"><h2>Non Goals</h2><ul>{non_goals}</ul></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_objective_or_decoding_alternative_selector_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["route", "score", "selected", "next_artifact", "selection_reason", "risk_control"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("route_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_objective_or_decoding_alternative_selector_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_JSON_FILENAME,
        "csv": root / PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_CSV_FILENAME,
        "text": root / PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_OBJECTIVE_OR_DECODING_ALTERNATIVE_SELECTOR_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_objective_or_decoding_alternative_selector_csv(report, paths["csv"])
    paths["text"].write_text(render_objective_or_decoding_alternative_selector_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_objective_or_decoding_alternative_selector_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_objective_or_decoding_alternative_selector_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _route_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('route'))}</td>"
        f"<td>{html_escape(row.get('score'))}</td>"
        f"<td>{html_escape(row.get('selected'))}</td>"
        f"<td>{html_escape(row.get('next_artifact'))}</td>"
        f"<td>{html_escape(row.get('selection_reason'))}</td>"
        f"<td>{html_escape(row.get('risk_control'))}</td>"
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
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#7c3aed}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
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
    "render_objective_or_decoding_alternative_selector_html",
    "render_objective_or_decoding_alternative_selector_markdown",
    "render_objective_or_decoding_alternative_selector_text",
    "write_objective_or_decoding_alternative_selector_outputs",
]
