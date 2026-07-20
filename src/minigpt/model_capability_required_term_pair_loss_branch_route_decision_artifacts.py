from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_branch_route_decision import (
    PAIR_LOSS_BRANCH_ROUTE_DECISION_CSV_FILENAME,
    PAIR_LOSS_BRANCH_ROUTE_DECISION_HTML_FILENAME,
    PAIR_LOSS_BRANCH_ROUTE_DECISION_JSON_FILENAME,
    PAIR_LOSS_BRANCH_ROUTE_DECISION_MARKDOWN_FILENAME,
    PAIR_LOSS_BRANCH_ROUTE_DECISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_loss_branch_route_decision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("route_count", summary.get("route_count")),
        ("pair_full_route_count", summary.get("pair_full_route_count")),
        ("loss_only_tradeoff_route_count", summary.get("loss_only_tradeoff_route_count")),
        ("selected_stability_route", summary.get("selected_stability_route")),
        ("selected_stability_corpus_mode", summary.get("selected_stability_corpus_mode")),
        ("fixed_retention_objective_required", summary.get("fixed_retention_objective_required")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_loss_branch_route_decision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        "| Route | Type | Hit terms | Missed terms | Candidate | Rejection reasons |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("route_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_label")),
                    markdown_cell(row.get("route_type")),
                    markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    markdown_cell(row.get("stability_replay_candidate")),
                    markdown_cell(",".join(str(item) for item in row.get("rejection_reasons", []))),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Branch Route Decision",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Selected stability route: `{summary.get('selected_stability_route')}`",
            f"- Fixed-retention required: `{summary.get('fixed_retention_objective_required')}`",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            "",
            "## Routes",
            "",
            *rows,
            "",
            "## Boundary",
            "",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_loss_branch_route_decision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Routes", summary.get("route_count")),
        ("Pair-full", summary.get("pair_full_route_count")),
        ("Selected", summary.get("selected_stability_route")),
        ("Fixed retention", summary.get("fixed_retention_objective_required")),
    ]
    route_rows = "\n".join(_route_html(row) for row in list_of_dicts(report.get("route_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-branch route decision</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-branch route decision</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Routes</h2>
<div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Type</th><th>Hit terms</th><th>Missed terms</th><th>Candidate</th><th>Rejection reasons</th></tr></thead>
<tbody>{route_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_loss_branch_route_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_LOSS_BRANCH_ROUTE_DECISION_JSON_FILENAME,
        "csv": root / PAIR_LOSS_BRANCH_ROUTE_DECISION_CSV_FILENAME,
        "text": root / PAIR_LOSS_BRANCH_ROUTE_DECISION_TEXT_FILENAME,
        "markdown": root / PAIR_LOSS_BRANCH_ROUTE_DECISION_MARKDOWN_FILENAME,
        "html": root / PAIR_LOSS_BRANCH_ROUTE_DECISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_loss_branch_route_decision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_loss_branch_route_decision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_loss_branch_route_decision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    rows = list_of_dicts(report.get("route_rows"))
    fieldnames = ["source_label", "route_type", "hit_terms", "missed_terms", "stability_replay_candidate", "rejection_reasons"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _route_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('route_type'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('stability_replay_candidate'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('rejection_reasons', [])))}</td>"
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
p{color:var(--muted);line-height:1.55}
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
    "render_loss_branch_route_decision_html",
    "render_loss_branch_route_decision_markdown",
    "render_loss_branch_route_decision_text",
    "write_loss_branch_route_decision_outputs",
]
