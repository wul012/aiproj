from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_CSV_FILENAME,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_HTML_FILENAME,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_JSON_FILENAME,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_MARKDOWN_FILENAME,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_fixed_preserving_transfer_plan_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("plan_ready", summary.get("plan_ready")),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
        ("closed_route", summary.get("closed_route")),
        ("transfer_row_budget", summary.get("transfer_row_budget")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_fixed_preserving_transfer_plan_markdown(report: dict[str, Any]) -> str:
    plan = as_dict(report.get("plan"))
    rows = [
        "| Check | Status | Actual | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("check_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("actual")),
                    markdown_cell(row.get("detail")),
                ]
            )
            + " |"
        )
    strategy = "\n".join(f"- {markdown_cell(item)}" for item in plan.get("patch_strategy", []))
    return "\n".join(
        [
            "# MiniGPT Fixed-Preserving Transfer Plan",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Proposed next artifact: `{plan.get('proposed_next_artifact')}`",
            f"- Transfer row budget: `{plan.get('transfer_row_budget')}`",
            "",
            "## Checks",
            "",
            *rows,
            "",
            "## Patch Strategy",
            "",
            strategy,
            "",
        ]
    )


def render_fixed_preserving_transfer_plan_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    plan = as_dict(report.get("plan"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("plan_ready")),
        ("Next artifact", summary.get("proposed_next_artifact")),
        ("Row budget", summary.get("transfer_row_budget")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    stat_html = "".join(
        f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"
        for label, value in stats
    )
    rows = "".join(
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('actual'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
        for row in list_of_dicts(report.get("check_rows"))
    )
    strategy = "".join(f"<li>{html_escape(item)}</li>" for item in plan.get("patch_strategy", []))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT fixed-preserving transfer plan</title>
<style>
:root{{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#1d4ed8}}
*{{box-sizing:border-box}}
body{{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}}
main{{max-width:1120px;margin:0 auto;padding:28px}}
h1{{font-size:30px;margin:0 0 8px;letter-spacing:0}}
h2{{font-size:18px;margin:0 0 12px;letter-spacing:0}}
p,li{{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}}
.card,.panel{{background:white;border:1px solid var(--line);border-radius:8px}}
.card{{padding:14px}}
.card span{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}}
.card strong{{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}}
.panel{{padding:16px;margin:14px 0}}
.table-wrap{{overflow:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}}
th{{background:var(--panel);color:#334155}}
</style>
</head>
<body>
<main>
<header><h1>MiniGPT fixed-preserving transfer plan</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{stat_html}</section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
<section class="panel"><h2>Patch Strategy</h2><ul>{strategy}</ul></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_fixed_preserving_transfer_plan_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "status", "actual", "detail"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_fixed_preserving_transfer_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_JSON_FILENAME,
        "csv": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_CSV_FILENAME,
        "text": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_fixed_preserving_transfer_plan_csv(report, paths["csv"])
    paths["text"].write_text(render_fixed_preserving_transfer_plan_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_fixed_preserving_transfer_plan_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_fixed_preserving_transfer_plan_html(report), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


__all__ = [
    "render_fixed_preserving_transfer_plan_html",
    "render_fixed_preserving_transfer_plan_markdown",
    "render_fixed_preserving_transfer_plan_text",
    "write_fixed_preserving_transfer_plan_outputs",
]
