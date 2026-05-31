from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_fixed_retention_objective_readiness import (
    PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_CSV_FILENAME,
    PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_HTML_FILENAME,
    PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_JSON_FILENAME,
    PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_MARKDOWN_FILENAME,
    PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_fixed_retention_objective_readiness_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("fixed_retention_objective_required", summary.get("fixed_retention_objective_required")),
        ("first_token_gap_confirmed", summary.get("first_token_gap_confirmed")),
        ("missed_seed_count", summary.get("missed_seed_count")),
        ("missed_first_token_gap_count", summary.get("missed_first_token_gap_count")),
        ("required_requirement_count", summary.get("required_requirement_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_fixed_retention_objective_readiness_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        "| Requirement | Required | Reason | Acceptance |",
        "| --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("requirement_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("required")),
                    markdown_cell(row.get("reason")),
                    markdown_cell(row.get("acceptance")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Fixed-Retention Objective Readiness",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Fixed-retention required: `{summary.get('fixed_retention_objective_required')}`",
            f"- First-token gap confirmed: `{summary.get('first_token_gap_confirmed')}`",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            "",
            "## Requirements",
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


def render_fixed_retention_objective_readiness_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Fixed retention", summary.get("fixed_retention_objective_required")),
        ("First-token gap", summary.get("first_token_gap_confirmed")),
        ("Missed seeds", summary.get("missed_seed_count")),
        ("Requirements", summary.get("required_requirement_count")),
    ]
    requirement_rows = "\n".join(_requirement_html(row) for row in list_of_dicts(report.get("requirement_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT fixed-retention objective readiness</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT fixed-retention objective readiness</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Requirements</h2>
<div class="table-wrap"><table>
<thead><tr><th>Requirement</th><th>Required</th><th>Reason</th><th>Acceptance</th></tr></thead>
<tbody>{requirement_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_fixed_retention_objective_readiness_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_JSON_FILENAME,
        "csv": root / PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_CSV_FILENAME,
        "text": root / PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_TEXT_FILENAME,
        "markdown": root / PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_MARKDOWN_FILENAME,
        "html": root / PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_fixed_retention_objective_readiness_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_fixed_retention_objective_readiness_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_fixed_retention_objective_readiness_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    rows = list_of_dicts(report.get("requirement_rows"))
    fieldnames = ["id", "required", "reason", "acceptance"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _requirement_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('required'))}</td>"
        f"<td>{html_escape(row.get('reason'))}</td>"
        f"<td>{html_escape(row.get('acceptance'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


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
    "render_fixed_retention_objective_readiness_html",
    "render_fixed_retention_objective_readiness_markdown",
    "render_fixed_retention_objective_readiness_text",
    "write_fixed_retention_objective_readiness_outputs",
]
