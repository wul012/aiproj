from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_dual_boundary_batch_closeout import (
    PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_CSV_FILENAME,
    PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_HTML_FILENAME,
    PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_JSON_FILENAME,
    PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_MARKDOWN_FILENAME,
    PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_dual_boundary_batch_closeout_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("seed_count", summary.get("seed_count")),
        ("generation_pair_full_seed_count", summary.get("generation_pair_full_seed_count")),
        ("internal_pair_full_seed_count", summary.get("internal_pair_full_seed_count")),
        ("aligned_pair_full_seed_count", summary.get("aligned_pair_full_seed_count")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_dual_boundary_batch_closeout_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "generation_pair_full",
        "internal_pair_full",
        "aligned_pair_full",
        "generation_decision",
        "internal_expected_best_terms",
        "classification",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_dual_boundary_batch_closeout_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        "| Seed | Generation pair-full | Internal pair-full | Aligned | Classification |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("seed_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("generation_pair_full")),
                    markdown_cell(row.get("internal_pair_full")),
                    markdown_cell(row.get("aligned_pair_full")),
                    markdown_cell(row.get("classification")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Dual-Boundary Batch Closeout",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Generation pair-full seeds: `{summary.get('generation_pair_full_seed_count')}/{summary.get('seed_count')}`",
            f"- Internal pair-full seeds: `{summary.get('internal_pair_full_seed_count')}/{summary.get('seed_count')}`",
            f"- Promotion ready: `{summary.get('promotion_ready')}`",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            "",
            "## Seeds",
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


def render_dual_boundary_batch_closeout_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Seeds", summary.get("seed_count")),
        ("Generation full", summary.get("generation_pair_full_seed_count")),
        ("Internal full", summary.get("internal_pair_full_seed_count")),
        ("Promotion ready", summary.get("promotion_ready")),
    ]
    seed_rows = "\n".join(_seed_html(row) for row in list_of_dicts(report.get("seed_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT dual-boundary batch closeout</title>
{_style()}
</head>
<body>
<main>
<header>
<h1>MiniGPT dual-boundary batch closeout</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
</header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Seeds</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Generation pair-full</th><th>Internal pair-full</th><th>Aligned</th><th>Classification</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_dual_boundary_batch_closeout_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_JSON_FILENAME,
        "csv": root / PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_CSV_FILENAME,
        "text": root / PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_TEXT_FILENAME,
        "markdown": root / PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_MARKDOWN_FILENAME,
        "html": root / PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_dual_boundary_batch_closeout_csv(report, paths["csv"])
    paths["text"].write_text(render_dual_boundary_batch_closeout_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_dual_boundary_batch_closeout_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_dual_boundary_batch_closeout_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _seed_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('generation_pair_full'))}</td>"
        f"<td>{html_escape(row.get('internal_pair_full'))}</td>"
        f"<td>{html_escape(row.get('aligned_pair_full'))}</td>"
        f"<td>{html_escape(row.get('classification'))}</td>"
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
    "render_dual_boundary_batch_closeout_html",
    "render_dual_boundary_batch_closeout_markdown",
    "render_dual_boundary_batch_closeout_text",
    "write_dual_boundary_batch_closeout_outputs",
]
