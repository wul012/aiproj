from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison import (
    PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_CSV_FILENAME,
    PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_HTML_FILENAME,
    PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME,
    PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_MARKDOWN_FILENAME,
    PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_equals_surface_repair_comparison_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("compared_report_count", summary.get("compared_report_count")),
        ("term_case_row_count", summary.get("term_case_row_count")),
        ("branch_competition_seed_count", summary.get("branch_competition_seed_count")),
        ("pair_full_profile_seed_count", summary.get("pair_full_profile_seed_count")),
        ("union_hit_terms", ",".join(str(term) for term in summary.get("union_hit_terms", []))),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_equals_surface_repair_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "branch_competition",
        "compared_report_count",
        "compared_reports",
        "fixed_hit_reports",
        "loss_hit_reports",
        "union_hit_terms",
        "pair_full_profile_reports",
        "best_next_action",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("branch_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_equals_surface_repair_comparison_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Equals-Surface Repair Comparison",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Compared reports: `{summary.get('compared_report_count')}`",
            f"- Branch competition seeds: `{summary.get('branch_competition_seed_count')}`",
            f"- Pair-full profile seeds: `{summary.get('pair_full_profile_seed_count')}`",
            f"- Union hit terms: `{','.join(str(term) for term in summary.get('union_hit_terms', []))}`",
            "",
            "## Source Reports",
            "",
            *_report_markdown_rows(report),
            "",
            "## Branch Rows",
            "",
            *_branch_markdown_rows(report),
            "",
            "## Term Evidence",
            "",
            *_term_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_equals_surface_repair_comparison_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Reports", summary.get("compared_report_count")),
        ("Term rows", summary.get("term_case_row_count")),
        ("Branch competition", summary.get("branch_competition_seed_count")),
        ("Pair-full profiles", summary.get("pair_full_profile_seed_count")),
    ]
    reports = "\n".join(_source_report_html(row) for row in list_of_dicts(report.get("source_reports")))
    branches = "\n".join(_branch_html(row) for row in list_of_dicts(report.get("branch_rows")))
    terms = "\n".join(_term_html(row) for row in list_of_dicts(report.get("term_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT equals-surface repair comparison</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT equals-surface repair comparison</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Source Reports</h2>
<div class="table-wrap"><table>
<thead><tr><th>Label</th><th>Status</th><th>Corpus mode</th><th>Pair-full seeds</th><th>Source</th></tr></thead>
<tbody>{reports}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Branch Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Competition</th><th>Fixed hit reports</th><th>Loss hit reports</th><th>Pair-full reports</th><th>Action</th></tr></thead>
<tbody>{branches}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Term Evidence</h2>
<div class="table-wrap"><table>
<thead><tr><th>Report</th><th>Seed</th><th>Profile</th><th>Term</th><th>Hit</th><th>Prompt</th><th>Preview</th></tr></thead>
<tbody>{terms}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_equals_surface_repair_comparison_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME,
        "csv": root / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_CSV_FILENAME,
        "text": root / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_TEXT_FILENAME,
        "markdown": root / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_MARKDOWN_FILENAME,
        "html": root / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_equals_surface_repair_comparison_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_equals_surface_repair_comparison_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_equals_surface_repair_comparison_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_equals_surface_repair_comparison_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _report_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Label | Status | Corpus mode | Pair-full seeds | Source |", "| --- | --- | --- | ---: | --- |"]
    for row in list_of_dicts(report.get("source_reports")):
        pair_full = f"{row.get('pair_full_seed_count')}/{row.get('seed_count')}"
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_label")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("corpus_mode")),
                    markdown_cell(pair_full),
                    markdown_cell(row.get("source_path")),
                ]
            )
            + " |"
        )
    return rows


def _branch_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Seed | Competition | Fixed hit reports | Loss hit reports | Pair-full reports | Next action |", "| --- | --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("branch_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("branch_competition")),
                    markdown_cell(",".join(str(item) for item in row.get("fixed_hit_reports", []))),
                    markdown_cell(",".join(str(item) for item in row.get("loss_hit_reports", []))),
                    markdown_cell(",".join(str(item) for item in row.get("pair_full_profile_reports", []))),
                    markdown_cell(row.get("best_next_action")),
                ]
            )
            + " |"
        )
    return rows


def _term_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Report | Seed | Profile | Term | Hit | Prompt | Preview |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("term_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_label")),
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("continuation_hit")),
                    markdown_cell(row.get("prompt")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return rows


def _source_report_html(row: dict[str, Any]) -> str:
    pair_full = f"{row.get('pair_full_seed_count')}/{row.get('seed_count')}"
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('corpus_mode'))}</td>"
        f"<td>{html_escape(pair_full)}</td>"
        f"<td>{html_escape(row.get('source_path'))}</td>"
        "</tr>"
    )


def _branch_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('branch_competition'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('fixed_hit_reports', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('loss_hit_reports', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('pair_full_profile_reports', [])))}</td>"
        f"<td>{html_escape(row.get('best_next_action'))}</td>"
        "</tr>"
    )


def _term_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_required_term_pair_equals_surface_repair_comparison_html",
    "render_model_capability_required_term_pair_equals_surface_repair_comparison_markdown",
    "render_model_capability_required_term_pair_equals_surface_repair_comparison_text",
    "write_model_capability_required_term_pair_equals_surface_repair_comparison_outputs",
]
