from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_route_promotion_bounded_real_replay_repair_plan_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("bounded_real_replay_repair_plan_ready", summary.get("bounded_real_replay_repair_plan_ready")),
        ("task_count", summary.get("task_count")),
        ("source_pass_rate", summary.get("source_pass_rate")),
        ("target_pass_rate", summary.get("target_pass_rate")),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_repair_plan_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["task_id", "case_id", "repair_type", "missed_terms", "surface_probe", "training_focus"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("repair_tasks")):
            writer.writerow(
                {
                    "task_id": csv_cell(row.get("task_id")),
                    "case_id": csv_cell(row.get("case_id")),
                    "repair_type": csv_cell(row.get("repair_type")),
                    "missed_terms": csv_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    "surface_probe": csv_cell(row.get("surface_probe")),
                    "training_focus": csv_cell(row.get("training_focus")),
                }
            )


def render_model_capability_route_promotion_bounded_real_replay_repair_plan_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay repair plan'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_real_replay_repair_plan_ready')}`",
        f"- Task count: `{summary.get('task_count')}`",
        f"- Source pass rate: `{summary.get('source_pass_rate')}`",
        f"- Target pass rate: `{summary.get('target_pass_rate')}`",
        f"- Next artifact: `{summary.get('proposed_next_artifact')}`",
        "",
        "## Repair Tasks",
        "",
        "| Task | Case | Type | Missed terms | Surface probe | Focus |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("repair_tasks")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("task_id")),
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("repair_type")),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    markdown_cell(row.get("surface_probe")),
                    markdown_cell(row.get("training_focus")),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_repair_plan_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("bounded_real_replay_repair_plan_ready")),
        ("Tasks", summary.get("task_count")),
        ("Source pass", summary.get("source_pass_rate")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("repair_tasks")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay repair plan'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay repair plan'))}</h1><p>Turns bounded real replay misses into targeted repair tasks without claiming new model quality.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Repair Tasks</h2><div class="table-wrap"><table>
<thead><tr><th>Task</th><th>Case</th><th>Type</th><th>Missed</th><th>Surface</th><th>Focus</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_repair_plan_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_repair_plan_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_repair_plan_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_repair_plan_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('task_id'))}</td>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('repair_type'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('surface_probe'))}</td>"
        f"<td>{html_escape(row.get('training_focus'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#64717d;--line:#d8dee4;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eff3f6;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1200px;margin:0 auto;padding:28px}
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
    "render_model_capability_route_promotion_bounded_real_replay_repair_plan_html",
    "render_model_capability_route_promotion_bounded_real_replay_repair_plan_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_repair_plan_text",
    "write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs",
]
