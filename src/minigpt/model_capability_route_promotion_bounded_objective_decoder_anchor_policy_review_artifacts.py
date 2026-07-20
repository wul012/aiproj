from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review import (
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_CSV_FILENAME,
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_HTML_FILENAME,
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_JSON_FILENAME,
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_bounded_objective_decoder_anchor_policy_review_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("bounded_objective_decoder_anchor_policy_review_ready", summary.get("bounded_objective_decoder_anchor_policy_review_ready")),
        ("assisted_anchor_path_closed", summary.get("assisted_anchor_path_closed")),
        ("selected_track", summary.get("selected_track")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_objective_decoder_anchor_policy_review_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "priority", "action"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("recommendations")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_bounded_objective_decoder_anchor_policy_review_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    signals = as_dict(report.get("signals"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective decoder anchor policy review'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_objective_decoder_anchor_policy_review_ready')}`",
        f"- Assisted anchor path closed: `{summary.get('assisted_anchor_path_closed')}`",
        f"- Selected track: `{summary.get('selected_track')}`",
        f"- Policy applied pass: `{signals.get('policy_applied_pass_count')}`",
        f"- New-text pass: `{signals.get('new_text_pass_count')}`",
        "",
        "## Recommendations",
        "",
        "| ID | Priority | Action |",
        "| --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("recommendations")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("priority")), markdown_cell(row.get("action"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_objective_decoder_anchor_policy_review_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    signals = as_dict(report.get("signals"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Closed", summary.get("assisted_anchor_path_closed")),
        ("Track", summary.get("selected_track")),
        ("Policy pass", signals.get("policy_applied_pass_count")),
        ("New text", signals.get("new_text_pass_count")),
        ("Promotion", summary.get("promotion_ready")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_recommendation_row(item) for item in list_of_dicts(report.get("recommendations")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective decoder anchor policy review'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective decoder anchor policy review'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Recommendations</h2><div class="table-wrap"><table>
<thead><tr><th>ID</th><th>Priority</th><th>Action</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_bounded_objective_decoder_anchor_policy_review_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_decoder_anchor_policy_review_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_decoder_anchor_policy_review_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_decoder_anchor_policy_review_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_decoder_anchor_policy_review_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _recommendation_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('priority'))}</td>"
        f"<td>{html_escape(row.get('action'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#667381;--line:#d8dee5;--panel:#f7f9fb;--accent:#155e75}
*{box-sizing:border-box}
body{margin:0;background:#f0f3f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_bounded_objective_decoder_anchor_policy_review_html",
    "render_bounded_objective_decoder_anchor_policy_review_markdown",
    "render_bounded_objective_decoder_anchor_policy_review_text",
    "write_bounded_objective_decoder_anchor_policy_review_outputs",
]
