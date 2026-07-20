from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_rebalanced_intervention_decision import (
    BOUNDED_REBALANCED_INTERVENTION_DECISION_CSV_FILENAME,
    BOUNDED_REBALANCED_INTERVENTION_DECISION_HTML_FILENAME,
    BOUNDED_REBALANCED_INTERVENTION_DECISION_JSON_FILENAME,
    BOUNDED_REBALANCED_INTERVENTION_DECISION_MARKDOWN_FILENAME,
    BOUNDED_REBALANCED_INTERVENTION_DECISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_bounded_rebalanced_intervention_decision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("intervention_decision_ready", summary.get("intervention_decision_ready")),
        ("selected_intervention_track", summary.get("selected_intervention_track")),
        ("fallback_intervention_track", summary.get("fallback_intervention_track")),
        ("recommended_next_artifact", summary.get("recommended_next_artifact")),
        ("promotion_allowed", summary.get("promotion_allowed")),
        ("new_training_allowed", summary.get("new_training_allowed")),
        ("profile_sweep_no_recovery", summary.get("profile_sweep_no_recovery")),
        ("best_any_hit_case_count", summary.get("best_any_hit_case_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_rebalanced_intervention_decision_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["stage", "status", "signal", "values"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("evidence_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_bounded_rebalanced_intervention_decision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    route = as_dict(report.get("route"))
    interpretation = as_dict(report.get("interpretation"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded rebalanced intervention decision'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Selected intervention: `{summary.get('selected_intervention_track')}`",
        f"- Recommended next artifact: `{summary.get('recommended_next_artifact')}`",
        f"- Model-quality claim: `{interpretation.get('model_quality_claim')}`",
        "",
        "## Route",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key in ("closed_route", "evidence_window", "selected_intervention_track", "fallback_intervention_track", "promotion_allowed", "new_training_allowed"):
        lines.append(f"| {markdown_cell(key)} | {markdown_cell(route.get(key))} |")
    lines.extend(["", "## Evidence", "", "| Stage | Status | Signal | Values |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("evidence_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("stage")), markdown_cell(row.get("status")), markdown_cell(row.get("signal")), markdown_cell(row.get("values"))]) + " |")
    lines.extend(["", "## Stop Reasons", ""])
    for reason in route.get("stop_reasons", []):
        lines.append(f"- `{markdown_cell(reason)}`")
    lines.extend(["", "## Blocked Actions", ""])
    for action in route.get("blocked_actions", []):
        lines.append(f"- `{markdown_cell(action)}`")
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_rebalanced_intervention_decision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    route = as_dict(report.get("route"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Selected", summary.get("selected_intervention_track")),
        ("Promotion", summary.get("promotion_allowed")),
        ("New training", summary.get("new_training_allowed")),
        ("Best hits", summary.get("best_any_hit_case_count")),
        ("Claim", interpretation.get("model_quality_claim")),
        ("Next", summary.get("recommended_next_artifact")),
    ]
    evidence_rows = "".join(_evidence_row(item) for item in list_of_dicts(report.get("evidence_rows")))
    stop_reasons = "".join(f"<li>{html_escape(item)}</li>" for item in route.get("stop_reasons", []))
    blocked_actions = "".join(f"<li>{html_escape(item)}</li>" for item in route.get("blocked_actions", []))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded rebalanced intervention decision'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded rebalanced intervention decision'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Route</h2><div class="route-grid">
<div><span>Closed route</span><strong>{html_escape(route.get('closed_route'))}</strong></div>
<div><span>Evidence window</span><strong>{html_escape(route.get('evidence_window'))}</strong></div>
<div><span>Fallback</span><strong>{html_escape(route.get('fallback_intervention_track'))}</strong></div>
</div></section>
<section class="panel"><h2>Evidence</h2><div class="table-wrap"><table>
<thead><tr><th>Stage</th><th>Status</th><th>Signal</th><th>Values</th></tr></thead>
<tbody>{evidence_rows}</tbody>
</table></div></section>
<section class="columns"><div class="panel"><h2>Stop Reasons</h2><ul>{stop_reasons}</ul></div><div class="panel"><h2>Blocked Actions</h2><ul>{blocked_actions}</ul></div></section>
</main>
</body>
</html>
"""


def write_bounded_rebalanced_intervention_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_REBALANCED_INTERVENTION_DECISION_JSON_FILENAME,
        "csv": root / BOUNDED_REBALANCED_INTERVENTION_DECISION_CSV_FILENAME,
        "text": root / BOUNDED_REBALANCED_INTERVENTION_DECISION_TEXT_FILENAME,
        "markdown": root / BOUNDED_REBALANCED_INTERVENTION_DECISION_MARKDOWN_FILENAME,
        "html": root / BOUNDED_REBALANCED_INTERVENTION_DECISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_rebalanced_intervention_decision_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_rebalanced_intervention_decision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_rebalanced_intervention_decision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_rebalanced_intervention_decision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _evidence_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('stage'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('signal'))}</td>"
        f"<td>{html_escape(row.get('values'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#667381;--line:#d8dee5;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats,.route-grid,.columns{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card,.route-grid div{padding:14px}
.card span,.route-grid span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong,.route-grid strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td,li{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_bounded_rebalanced_intervention_decision_html",
    "render_bounded_rebalanced_intervention_decision_markdown",
    "render_bounded_rebalanced_intervention_decision_text",
    "write_bounded_rebalanced_intervention_decision_outputs",
]
