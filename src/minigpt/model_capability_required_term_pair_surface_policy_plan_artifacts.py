from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_policy_plan import (
    PAIR_SURFACE_POLICY_PLAN_CSV_FILENAME,
    PAIR_SURFACE_POLICY_PLAN_HTML_FILENAME,
    PAIR_SURFACE_POLICY_PLAN_JSON_FILENAME,
    PAIR_SURFACE_POLICY_PLAN_MARKDOWN_FILENAME,
    PAIR_SURFACE_POLICY_PLAN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_surface_policy_plan_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("failure_terms", summary.get("failure_terms")),
        ("policy_count", summary.get("policy_count")),
        ("replay_policy_count", summary.get("replay_policy_count")),
        ("recommended_replay_policy_ids", summary.get("recommended_replay_policy_ids")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_surface_policy_plan_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "policy_id",
        "prompt_template",
        "generation_profile",
        "leakage_level",
        "replay_scope",
        "included_in_replay",
        "target_failure_terms",
        "purpose",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("policy_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_surface_policy_plan_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        "| Policy | Profile | Leakage | Replay | Purpose |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("policy_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("policy_id")),
                    markdown_cell(row.get("generation_profile")),
                    markdown_cell(row.get("leakage_level")),
                    markdown_cell(row.get("included_in_replay")),
                    markdown_cell(row.get("purpose")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Policy Plan",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Failure terms: `{summary.get('failure_terms')}`",
            f"- Replay policies: `{summary.get('recommended_replay_policy_ids')}`",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            "",
            "## Policies",
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


def render_surface_policy_plan_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Failure terms", summary.get("failure_terms")),
        ("Policies", summary.get("policy_count")),
        ("Replay policies", summary.get("replay_policy_count")),
        ("Excluded upper-bound", summary.get("excluded_upper_bound_policy_count")),
    ]
    policy_rows = "\n".join(_policy_html(row) for row in list_of_dicts(report.get("policy_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT surface policy plan</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT surface policy plan</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Policies</h2>
<div class="table-wrap"><table>
<thead><tr><th>Policy</th><th>Prompt template</th><th>Profile</th><th>Leakage</th><th>Replay</th><th>Purpose</th></tr></thead>
<tbody>{policy_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_surface_policy_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_POLICY_PLAN_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_POLICY_PLAN_CSV_FILENAME,
        "text": root / PAIR_SURFACE_POLICY_PLAN_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_POLICY_PLAN_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_POLICY_PLAN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_surface_policy_plan_csv(report, paths["csv"])
    paths["text"].write_text(render_surface_policy_plan_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_surface_policy_plan_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_surface_policy_plan_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _policy_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('policy_id'))}</td>"
        f"<td>{html_escape(row.get('prompt_template'))}</td>"
        f"<td>{html_escape(row.get('generation_profile'))}</td>"
        f"<td>{html_escape(row.get('leakage_level'))}</td>"
        f"<td>{html_escape(row.get('included_in_replay'))}</td>"
        f"<td>{html_escape(row.get('purpose'))}</td>"
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
    "render_surface_policy_plan_html",
    "render_surface_policy_plan_markdown",
    "render_surface_policy_plan_text",
    "write_surface_policy_plan_outputs",
]
