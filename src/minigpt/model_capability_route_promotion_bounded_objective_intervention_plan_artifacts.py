from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_intervention_plan import (
    BOUNDED_OBJECTIVE_INTERVENTION_PLAN_CSV_FILENAME,
    BOUNDED_OBJECTIVE_INTERVENTION_PLAN_HTML_FILENAME,
    BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME,
    BOUNDED_OBJECTIVE_INTERVENTION_PLAN_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_INTERVENTION_PLAN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_bounded_objective_intervention_plan_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("objective_intervention_plan_ready", summary.get("objective_intervention_plan_ready")),
        ("plan_id", summary.get("plan_id")),
        ("contract_id", summary.get("contract_id")),
        ("work_item_count", summary.get("work_item_count")),
        ("acceptance_gate_count", summary.get("acceptance_gate_count")),
        ("unchanged_suite_check_required", summary.get("unchanged_suite_check_required")),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_objective_intervention_plan_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["item_id", "action", "expected_output"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("work_items")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_bounded_objective_intervention_plan_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    contract = as_dict(report.get("objective_contract"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective intervention plan'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Contract: `{summary.get('contract_id')}`",
        f"- Next artifact: `{summary.get('proposed_next_artifact')}`",
        "",
        "## Objective Contract",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Target terms | {markdown_cell(','.join(str(item) for item in contract.get('target_terms', [])))} |",
        f"| Canonical prompt | {markdown_cell(contract.get('canonical_prompt'))} |",
        f"| Canonical completion | {markdown_cell(contract.get('canonical_completion'))} |",
        f"| Unchanged suite check required | {markdown_cell(contract.get('unchanged_suite_check_required'))} |",
        "",
        "## Work Items",
        "",
        "| Item | Action | Output |",
        "| --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("work_items")):
        lines.append("| " + " | ".join([markdown_cell(row.get("item_id")), markdown_cell(row.get("action")), markdown_cell(row.get("expected_output"))]) + " |")
    lines.extend(["", "## Acceptance Gates", ""])
    for row in list_of_dicts(report.get("acceptance_gates")):
        lines.append(f"- `{markdown_cell(row.get('gate_id'))}`: {markdown_cell(row.get('detail'))}")
    lines.extend(["", "## Non Goals", ""])
    for item in report.get("non_goals", []):
        lines.append(f"- `{markdown_cell(item)}`")
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_objective_intervention_plan_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    contract = as_dict(report.get("objective_contract"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Contract", summary.get("contract_id")),
        ("Work items", summary.get("work_item_count")),
        ("Gates", summary.get("acceptance_gate_count")),
        ("Unchanged suite", summary.get("unchanged_suite_check_required")),
        ("Claim", interpretation.get("model_quality_claim")),
        ("Next", summary.get("proposed_next_artifact")),
    ]
    work_rows = "".join(_work_row(row) for row in list_of_dicts(report.get("work_items")))
    gates = "".join(f"<li><strong>{html_escape(row.get('gate_id'))}</strong>: {html_escape(row.get('detail'))}</li>" for row in list_of_dicts(report.get("acceptance_gates")))
    non_goals = "".join(f"<li>{html_escape(item)}</li>" for item in report.get("non_goals", []))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective intervention plan'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective intervention plan'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Objective Contract</h2><div class="contract">
<div><span>Target</span><strong>{html_escape(','.join(str(item) for item in contract.get('target_terms', [])))}</strong></div>
<div><span>Prompt</span><strong>{html_escape(contract.get('canonical_prompt'))}</strong></div>
<div><span>Completion</span><strong>{html_escape(contract.get('canonical_completion'))}</strong></div>
</div></section>
<section class="panel"><h2>Work Items</h2><div class="table-wrap"><table>
<thead><tr><th>Item</th><th>Action</th><th>Output</th></tr></thead>
<tbody>{work_rows}</tbody>
</table></div></section>
<section class="columns"><div class="panel"><h2>Acceptance Gates</h2><ul>{gates}</ul></div><div class="panel"><h2>Non Goals</h2><ul>{non_goals}</ul></div></section>
</main>
</body>
</html>
"""


def write_bounded_objective_intervention_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_INTERVENTION_PLAN_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_INTERVENTION_PLAN_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_INTERVENTION_PLAN_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_INTERVENTION_PLAN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_intervention_plan_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_intervention_plan_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_intervention_plan_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_intervention_plan_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _work_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('item_id'))}</td>"
        f"<td>{html_escape(row.get('action'))}</td>"
        f"<td>{html_escape(row.get('expected_output'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#6b21a8}
*{box-sizing:border-box}
body{margin:0;background:#f1f3f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats,.contract,.columns{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card,.contract div{padding:14px}
.card span,.contract span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong,.contract strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td,li{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_bounded_objective_intervention_plan_html",
    "render_bounded_objective_intervention_plan_markdown",
    "render_bounded_objective_intervention_plan_text",
    "write_bounded_objective_intervention_plan_outputs",
]
