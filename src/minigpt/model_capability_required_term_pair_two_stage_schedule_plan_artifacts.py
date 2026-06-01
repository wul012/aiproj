from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_two_stage_schedule_plan import (
    PAIR_TWO_STAGE_SCHEDULE_PLAN_CSV_FILENAME,
    PAIR_TWO_STAGE_SCHEDULE_PLAN_HTML_FILENAME,
    PAIR_TWO_STAGE_SCHEDULE_PLAN_JSON_FILENAME,
    PAIR_TWO_STAGE_SCHEDULE_PLAN_MARKDOWN_FILENAME,
    PAIR_TWO_STAGE_SCHEDULE_PLAN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_two_stage_schedule_plan_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("stage_count", summary.get("stage_count")),
        ("stage_gate_pass_count", summary.get("stage_gate_pass_count")),
        ("guardrail_fail_count", summary.get("guardrail_fail_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_two_stage_schedule_plan_markdown(report: dict[str, Any]) -> str:
    boundary = as_dict(report.get("schedule_boundary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Two-Stage Schedule Plan",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Boundary: `{boundary.get('training_semantics')}`",
            f"- Failed count: `{report.get('failed_count')}`",
            "",
            "## Stage Rows",
            "",
            *_stage_markdown_rows(report),
            "",
            "## Guardrails",
            "",
            *_guardrail_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_two_stage_schedule_plan_html(report: dict[str, Any]) -> str:
    boundary = as_dict(report.get("schedule_boundary"))
    interpretation = as_dict(report.get("interpretation"))
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Boundary", boundary.get("training_semantics")),
        ("Stage gates", summary.get("stage_gate_pass_count")),
        ("Guardrail fails", summary.get("guardrail_fail_count")),
    ]
    stage_rows = "\n".join(_stage_html(row) for row in list_of_dicts(report.get("stage_rows")))
    guardrail_rows = "\n".join(_guardrail_html(row) for row in list_of_dicts(report.get("guardrails")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT two-stage schedule plan</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT two-stage schedule plan</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel"><h2>Stage Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Stage</th><th>Source</th><th>Gate</th><th>Hits</th><th>Class</th></tr></thead>
<tbody>{stage_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Guardrails</h2><div class="table-wrap"><table>
<thead><tr><th>ID</th><th>Status</th><th>Detail</th></tr></thead>
<tbody>{guardrail_rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_two_stage_schedule_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_TWO_STAGE_SCHEDULE_PLAN_JSON_FILENAME,
        "csv": root / PAIR_TWO_STAGE_SCHEDULE_PLAN_CSV_FILENAME,
        "text": root / PAIR_TWO_STAGE_SCHEDULE_PLAN_TEXT_FILENAME,
        "markdown": root / PAIR_TWO_STAGE_SCHEDULE_PLAN_MARKDOWN_FILENAME,
        "html": root / PAIR_TWO_STAGE_SCHEDULE_PLAN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_two_stage_schedule_plan_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_two_stage_schedule_plan_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_two_stage_schedule_plan_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["stage", "source_label", "goal", "gate", "gate_passed", "alignment_class"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("stage_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _stage_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Stage | Source | Gate | Hits | Class |", "| --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("stage_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("stage")),
                    markdown_cell(row.get("source_label")),
                    markdown_cell(f"{row.get('gate')}={row.get('gate_passed')}"),
                    markdown_cell(row.get("generation_hit_terms")),
                    markdown_cell(row.get("alignment_class")),
                ]
            )
            + " |"
        )
    return rows


def _guardrail_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| ID | Status | Detail |", "| --- | --- | --- |"]
    for row in list_of_dicts(report.get("guardrails")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("detail")),
                ]
            )
            + " |"
        )
    return rows


def _stage_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('stage'))}</td>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('gate'))}={html_escape(row.get('gate_passed'))}</td>"
        f"<td>{html_escape(row.get('generation_hit_terms'))}</td>"
        f"<td>{html_escape(row.get('alignment_class'))}</td>"
        "</tr>"
    )


def _guardrail_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#596775;--line:#d7dde3;--panel:#f6f8fa;--accent:#26636f}
*{box-sizing:border-box}
body{margin:0;background:#eef4f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1160px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}
</style>"""


__all__ = [
    "render_two_stage_schedule_plan_html",
    "render_two_stage_schedule_plan_markdown",
    "render_two_stage_schedule_plan_text",
    "write_two_stage_schedule_plan_outputs",
]
