from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_CSV_FILENAME,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_HTML_FILENAME,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_stagnation_aware_suffix_repair_plan_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("stagnation_aware_suffix_repair_plan_ready", summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready")),
        ("action_count", summary.get("action_count")),
        ("required_action_count", summary.get("required_action_count")),
        ("source_no_contract_gain_confirmed", summary.get("source_no_contract_gain_confirmed")),
        ("source_surface_format_changed_without_suffix_gain", summary.get("source_surface_format_changed_without_suffix_gain")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_stagnation_aware_suffix_repair_plan_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix repair plan'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Action count: `{summary.get('action_count')}`",
        f"- Required actions: `{summary.get('required_action_count')}`",
        f"- No contract gain source: `{summary.get('source_no_contract_gain_confirmed')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Plan Actions",
        "",
        "| Action | Category | Priority | Purpose | Implementation hint |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("plan_actions")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("action_id")),
            markdown_cell(row.get("category")),
            markdown_cell(row.get("priority")),
            markdown_cell(row.get("purpose")),
            markdown_cell(row.get("implementation_hint")),
        ]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_stagnation_aware_suffix_repair_plan_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready")),
        ("Actions", summary.get("action_count")),
        ("Required", summary.get("required_action_count")),
        ("No contract gain", summary.get("source_no_contract_gain_confirmed")),
        ("Format delta source", summary.get("source_surface_format_changed_without_suffix_gain")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_action_row(row) for row in list_of_dicts(report.get("plan_actions")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix repair plan'))}</title>{_style()}</head>
<body><main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix repair plan'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Plan Actions</h2><div class="table-wrap"><table><thead><tr><th>Action</th><th>Category</th><th>Priority</th><th>Purpose</th><th>Implementation hint</th></tr></thead><tbody>{rows}</tbody></table></div></section>
</main></body></html>"""


def write_stagnation_aware_suffix_repair_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_stagnation_aware_suffix_repair_plan_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_stagnation_aware_suffix_repair_plan_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_stagnation_aware_suffix_repair_plan_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["action_id", "category", "priority", "purpose", "implementation_hint", "evidence_count", "next_artifact_role"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("plan_actions")):
            writer.writerow({key: csv_cell(row.get(key)) for key in fieldnames})


def _action_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('action_id'))}</td>"
        f"<td>{html_escape(row.get('category'))}</td>"
        f"<td>{html_escape(row.get('priority'))}</td>"
        f"<td>{html_escape(row.get('purpose'))}</td>"
        f"<td>{html_escape(row.get('implementation_hint'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#64717d;--line:#d8dee4;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}body{margin:0;background:#eef1f6;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_stagnation_aware_suffix_repair_plan_html",
    "render_stagnation_aware_suffix_repair_plan_markdown",
    "render_stagnation_aware_suffix_repair_plan_text",
    "write_stagnation_aware_suffix_repair_plan_outputs",
]
