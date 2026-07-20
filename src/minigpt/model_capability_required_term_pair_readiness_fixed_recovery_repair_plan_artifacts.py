from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_recovery_repair_plan import (
    PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_CSV_FILENAME,
    PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_HTML_FILENAME,
    PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_JSON_FILENAME,
    PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_MARKDOWN_FILENAME,
    PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_fixed_recovery_repair_plan_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("plan_ready", summary.get("plan_ready")),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
        ("repair_focus", summary.get("repair_focus")),
        ("source_structured_hit_terms", summary.get("source_structured_hit_terms")),
        ("source_structured_missed_terms", summary.get("source_structured_missed_terms")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_fixed_recovery_repair_plan_markdown(report: dict[str, Any]) -> str:
    plan = as_dict(report.get("plan"))
    checks = ["| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("check_rows")):
        checks.append(
            "| "
            + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))])
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Pair-Readiness Fixed-Recovery Repair Plan",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Proposed next artifact: `{plan.get('proposed_next_artifact')}`",
            "",
            "## Checks",
            "",
            *checks,
            "",
            "## Contract Patch",
            "",
            *[f"- `{row}`" for row in plan.get("contract_patch", [])],
            "",
        ]
    )


def render_fixed_recovery_repair_plan_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    plan = as_dict(report.get("plan"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("plan_ready")),
        ("Next artifact", summary.get("proposed_next_artifact")),
        ("Hit terms", summary.get("source_structured_hit_terms")),
        ("Missed terms", summary.get("source_structured_missed_terms")),
    ]
    checks = "".join(_check_html(row) for row in list_of_dicts(report.get("check_rows")))
    patch = "".join(f"<li>{html_escape(row)}</li>" for row in plan.get("contract_patch", []))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT fixed-recovery repair plan</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT fixed-recovery repair plan</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
<section class="panel"><h2>Contract Patch</h2><ul>{patch}</ul></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_fixed_recovery_repair_plan_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "actual", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_fixed_recovery_repair_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_JSON_FILENAME,
        "csv": root / PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_CSV_FILENAME,
        "text": root / PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_fixed_recovery_repair_plan_csv(report, paths["csv"])
    paths["text"].write_text(render_fixed_recovery_repair_plan_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_fixed_recovery_repair_plan_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_fixed_recovery_repair_plan_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _check_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('actual'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#14532d}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p,li{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:18px 0}
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
    "render_fixed_recovery_repair_plan_html",
    "render_fixed_recovery_repair_plan_markdown",
    "render_fixed_recovery_repair_plan_text",
    "write_fixed_recovery_repair_plan_outputs",
]
