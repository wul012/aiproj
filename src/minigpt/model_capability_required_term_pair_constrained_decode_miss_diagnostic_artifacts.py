from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_constrained_decode_miss_diagnostic import (
    PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_CSV_FILENAME,
    PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_HTML_FILENAME,
    PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_JSON_FILENAME,
    PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_MARKDOWN_FILENAME,
    PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_pair_constrained_decode_miss_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("fixed_constrained_hit", summary.get("fixed_constrained_hit")),
        ("loss_constrained_hit", summary.get("loss_constrained_hit")),
        ("fixed_miss_class", summary.get("fixed_miss_class")),
        ("remaining_missed_terms", ",".join(str(item) for item in summary.get("remaining_missed_terms", []))),
        ("recommended_next_route", summary.get("recommended_next_route")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_pair_constrained_decode_miss_diagnostic_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "term",
        "profile_id",
        "continuation_hit",
        "miss_class",
        "term_prefix_present",
        "full_term_present",
        "blocked_token_texts",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("diagnostic_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_pair_constrained_decode_miss_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Constrained Decode Miss Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Fixed constrained hit: `{summary.get('fixed_constrained_hit')}`",
            f"- Loss constrained hit: `{summary.get('loss_constrained_hit')}`",
            f"- Fixed miss class: `{summary.get('fixed_miss_class')}`",
            f"- Recommended next route: `{summary.get('recommended_next_route')}`",
            "",
            "## Diagnostic Rows",
            "",
            "| Term | Profile | Hit | Miss class | Prefix present | Preview |",
            "| --- | --- | --- | --- | --- | --- |",
            *_diagnostic_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_pair_constrained_decode_miss_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    metric_rows = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Fixed constrained hit", summary.get("fixed_constrained_hit")),
        ("Loss constrained hit", summary.get("loss_constrained_hit")),
        ("Fixed miss class", summary.get("fixed_miss_class")),
        ("Remaining missed terms", ",".join(str(item) for item in summary.get("remaining_missed_terms", []))),
        ("Recommended next route", summary.get("recommended_next_route")),
    ]
    metrics = "\n".join(f"<div><strong>{html_escape(key)}</strong><span>{html_escape(value)}</span></div>" for key, value in metric_rows)
    diagnostic_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('miss_class'))}</td>"
        f"<td>{html_escape(row.get('term_prefix_present'))}</td>"
        f"<td><code>{html_escape(row.get('continuation_preview'))}</code></td>"
        "</tr>"
        for row in list_of_dicts(report.get("diagnostic_rows"))
    )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>MiniGPT constrained decode miss diagnostic</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
header {{ border-bottom: 1px solid #d1d5db; margin-bottom: 20px; padding-bottom: 12px; }}
.metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin: 20px 0; }}
.metrics div {{ border: 1px solid #d1d5db; padding: 10px; border-radius: 6px; background: #f9fafb; }}
.metrics strong {{ display: block; font-size: 12px; color: #4b5563; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #f3f4f6; }}
code {{ white-space: pre-wrap; }}
</style>
</head>
<body>
<header><h1>MiniGPT constrained decode miss diagnostic</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class=\"metrics\">{metrics}</section>
<section>
<h2>Diagnostic Rows</h2>
<table>
<thead><tr><th>Term</th><th>Profile</th><th>Hit</th><th>Miss class</th><th>Prefix present</th><th>Preview</th></tr></thead>
<tbody>{diagnostic_rows}</tbody>
</table>
</section>
<section>
<h2>Next Action</h2>
<p>{html_escape(interpretation.get('next_action'))}</p>
</section>
</body>
</html>
"""


def write_pair_constrained_decode_miss_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_CSV_FILENAME,
        "text": root / PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_pair_constrained_decode_miss_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_pair_constrained_decode_miss_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_pair_constrained_decode_miss_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_pair_constrained_decode_miss_diagnostic_html(report), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _diagnostic_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for row in list_of_dicts(report.get("diagnostic_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("continuation_hit")),
                    markdown_cell(row.get("miss_class")),
                    markdown_cell(row.get("term_prefix_present")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return rows


__all__ = [
    "render_pair_constrained_decode_miss_diagnostic_html",
    "render_pair_constrained_decode_miss_diagnostic_markdown",
    "render_pair_constrained_decode_miss_diagnostic_text",
    "write_pair_constrained_decode_miss_diagnostic_outputs",
]
