from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison import (
    PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_CSV_FILENAME,
    PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_HTML_FILENAME,
    PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME,
    PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_MARKDOWN_FILENAME,
    PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_generation_internal_alignment_comparison_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("generation_pair_full_count", summary.get("generation_pair_full_count")),
        ("internal_pair_full_count", summary.get("internal_pair_full_count")),
        ("aligned_pair_full_count", summary.get("aligned_pair_full_count")),
        ("best_source_labels", ",".join(str(value) for value in summary.get("best_source_labels", []))),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_generation_internal_alignment_comparison_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Generation/Internal Alignment Comparison",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Generation pair-full: `{summary.get('generation_pair_full_count')}`",
            f"- Internal pair-full: `{summary.get('internal_pair_full_count')}`",
            f"- Aligned pair-full: `{summary.get('aligned_pair_full_count')}`",
            f"- Best sources: `{summary.get('best_source_labels')}`",
            "",
            "## Source Rows",
            "",
            *_source_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_generation_internal_alignment_comparison_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Generation full", summary.get("generation_pair_full_count")),
        ("Internal full", summary.get("internal_pair_full_count")),
        ("Aligned full", summary.get("aligned_pair_full_count")),
    ]
    rows = "\n".join(_source_html(row) for row in list_of_dicts(report.get("source_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT generation/internal alignment comparison</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT generation/internal alignment comparison</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel"><h2>Source Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Generation</th><th>Internal</th><th>Class</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_generation_internal_alignment_comparison_outputs(
    report: dict[str, Any], out_dir: str | Path
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME,
        "csv": root / PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_CSV_FILENAME,
        "text": root / PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_TEXT_FILENAME,
        "markdown": root / PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_MARKDOWN_FILENAME,
        "html": root / PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_generation_internal_alignment_comparison_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_generation_internal_alignment_comparison_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_generation_internal_alignment_comparison_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "source_label",
        "corpus_mode",
        "seed",
        "generation_hit_terms",
        "internal_expected_best_terms",
        "generation_pair_full",
        "internal_pair_full",
        "alignment_class",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("source_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _source_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Route | Generation | Internal | Class |", "| --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("source_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_label")),
                    markdown_cell(row.get("generation_hit_terms")),
                    markdown_cell(row.get("internal_expected_best_terms")),
                    markdown_cell(row.get("alignment_class")),
                ]
            )
            + " |"
        )
    return rows


def _source_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('generation_hit_terms'))}</td>"
        f"<td>{html_escape(row.get('internal_expected_best_terms'))}</td>"
        f"<td>{html_escape(row.get('alignment_class'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#335c67}
*{box-sizing:border-box}
body{margin:0;background:#f0f4f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}
</style>"""


__all__ = [
    "render_generation_internal_alignment_comparison_html",
    "render_generation_internal_alignment_comparison_markdown",
    "render_generation_internal_alignment_comparison_text",
    "write_generation_internal_alignment_comparison_outputs",
]
