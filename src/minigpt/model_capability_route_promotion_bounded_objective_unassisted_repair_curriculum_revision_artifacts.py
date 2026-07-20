from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_CSV_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_HTML_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_bounded_objective_unassisted_repair_curriculum_revision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("bounded_objective_unassisted_repair_curriculum_revision_ready", summary.get("bounded_objective_unassisted_repair_curriculum_revision_ready")),
        ("revision_item_count", summary.get("revision_item_count")),
        ("acceptance_gate_count", summary.get("acceptance_gate_count")),
        ("decoder_anchor_allowed", summary.get("decoder_anchor_allowed")),
        ("promotion_claim_allowed", summary.get("promotion_claim_allowed")),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_objective_unassisted_repair_curriculum_revision_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["item_id", "priority", "stage", "decoder_anchor_allowed", "promotion_claim_allowed", "action"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("revision_items")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_bounded_objective_unassisted_repair_curriculum_revision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective unassisted repair curriculum revision'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_objective_unassisted_repair_curriculum_revision_ready')}`",
        f"- Revision items: `{summary.get('revision_item_count')}`",
        f"- Acceptance gates: `{summary.get('acceptance_gate_count')}`",
        f"- Decoder anchors allowed: `{summary.get('decoder_anchor_allowed')}`",
        "",
        "## Revision Items",
        "",
        "| Item | Priority | Stage | Anchor | Action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("revision_items")):
        lines.append("| " + " | ".join([markdown_cell(row.get("item_id")), markdown_cell(row.get("priority")), markdown_cell(row.get("stage")), markdown_cell(row.get("decoder_anchor_allowed")), markdown_cell(row.get("action"))]) + " |")
    lines.extend(["", "## Acceptance Gates", "", "| Gate | Required | Detail |", "| --- | --- | --- |"])
    for row in list_of_dicts(report.get("acceptance_gates")):
        lines.append("| " + " | ".join([markdown_cell(row.get("gate_id")), markdown_cell(row.get("required")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_objective_unassisted_repair_curriculum_revision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Items", summary.get("revision_item_count")),
        ("Gates", summary.get("acceptance_gate_count")),
        ("Anchors", summary.get("decoder_anchor_allowed")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    item_rows = "".join(_item_row(item) for item in list_of_dicts(report.get("revision_items")))
    gate_rows = "".join(_gate_row(item) for item in list_of_dicts(report.get("acceptance_gates")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective unassisted repair curriculum revision'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective unassisted repair curriculum revision'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Revision Items</h2><div class="table-wrap"><table>
<thead><tr><th>Item</th><th>Priority</th><th>Stage</th><th>Anchor</th><th>Action</th></tr></thead>
<tbody>{item_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Acceptance Gates</h2><div class="table-wrap"><table>
<thead><tr><th>Gate</th><th>Required</th><th>Detail</th></tr></thead>
<tbody>{gate_rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_bounded_objective_unassisted_repair_curriculum_revision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_unassisted_repair_curriculum_revision_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_unassisted_repair_curriculum_revision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_unassisted_repair_curriculum_revision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_unassisted_repair_curriculum_revision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _item_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('item_id'))}</td>"
        f"<td>{html_escape(row.get('priority'))}</td>"
        f"<td>{html_escape(row.get('stage'))}</td>"
        f"<td>{html_escape(row.get('decoder_anchor_allowed'))}</td>"
        f"<td>{html_escape(row.get('action'))}</td>"
        "</tr>"
    )


def _gate_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('gate_id'))}</td>"
        f"<td>{html_escape(row.get('required'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#0369a1}
*{box-sizing:border-box}
body{margin:0;background:#f4f7fb;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
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
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_bounded_objective_unassisted_repair_curriculum_revision_html",
    "render_bounded_objective_unassisted_repair_curriculum_revision_markdown",
    "render_bounded_objective_unassisted_repair_curriculum_revision_text",
    "write_bounded_objective_unassisted_repair_curriculum_revision_outputs",
]
