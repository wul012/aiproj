from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_first_failure_analysis import (
    SURFACE_FIRST_FAILURE_ANALYSIS_CSV_FILENAME,
    SURFACE_FIRST_FAILURE_ANALYSIS_HTML_FILENAME,
    SURFACE_FIRST_FAILURE_ANALYSIS_JSON_FILENAME,
    SURFACE_FIRST_FAILURE_ANALYSIS_MARKDOWN_FILENAME,
    SURFACE_FIRST_FAILURE_ANALYSIS_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_surface_first_failure_analysis_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("generation_hit_terms", ",".join(summary.get("generation_hit_terms", []))),
        ("forced_choice_expected_terms", ",".join(summary.get("forced_choice_expected_terms", []))),
        ("alignment_class", summary.get("alignment_class")),
        ("fixed_collapse_confirmed", summary.get("fixed_collapse_confirmed")),
        ("next_objective", summary.get("next_objective")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_surface_first_failure_analysis_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Surface-First Failure Analysis",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Fixed collapse: `{summary.get('fixed_collapse_confirmed')}`",
            f"- Next objective: `{summary.get('next_objective')}`",
            "",
            "## Evidence Rows",
            "",
            *_evidence_markdown_rows(report),
            "",
            "## Recommendations",
            "",
            *_recommendation_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_surface_first_failure_analysis_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Generation", summary.get("generation_hit_terms")),
        ("Internal", summary.get("forced_choice_expected_terms")),
        ("Fixed collapse", summary.get("fixed_collapse_confirmed")),
    ]
    evidence_rows = "\n".join(_evidence_html(row) for row in list_of_dicts(report.get("evidence_rows")))
    recommendation_rows = "\n".join(_recommendation_html(row) for row in list_of_dicts(report.get("recommendations")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT surface-first failure analysis</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT surface-first failure analysis</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel"><h2>Evidence Rows</h2><table><thead><tr><th>ID</th><th>Status</th><th>Value</th><th>Detail</th></tr></thead><tbody>{evidence_rows}</tbody></table></section>
<section class="panel"><h2>Recommendations</h2><table><thead><tr><th>ID</th><th>Action</th></tr></thead><tbody>{recommendation_rows}</tbody></table></section>
</main>
</body>
</html>
"""


def write_surface_first_failure_analysis_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / SURFACE_FIRST_FAILURE_ANALYSIS_JSON_FILENAME,
        "csv": root / SURFACE_FIRST_FAILURE_ANALYSIS_CSV_FILENAME,
        "text": root / SURFACE_FIRST_FAILURE_ANALYSIS_TEXT_FILENAME,
        "markdown": root / SURFACE_FIRST_FAILURE_ANALYSIS_MARKDOWN_FILENAME,
        "html": root / SURFACE_FIRST_FAILURE_ANALYSIS_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_surface_first_failure_analysis_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_surface_first_failure_analysis_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_surface_first_failure_analysis_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "value", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("evidence_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _evidence_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| ID | Status | Value | Detail |", "| --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("evidence_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("value")),
                    markdown_cell(row.get("detail")),
                ]
            )
            + " |"
        )
    return rows


def _recommendation_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| ID | Action |", "| --- | --- |"]
    for row in list_of_dicts(report.get("recommendations")):
        rows.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("action"))]) + " |")
    return rows


def _evidence_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('value'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _recommendation_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('action'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#284f68}
*{box-sizing:border-box}
body{margin:0;background:#f1f5f6;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1160px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}
</style>"""


__all__ = [
    "render_surface_first_failure_analysis_html",
    "render_surface_first_failure_analysis_markdown",
    "render_surface_first_failure_analysis_text",
    "write_surface_first_failure_analysis_outputs",
]
