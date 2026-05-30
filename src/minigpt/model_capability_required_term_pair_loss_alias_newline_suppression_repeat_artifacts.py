from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_repeat import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_HTML_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_JSON_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("newline_suppression_repeat_decision", summary.get("newline_suppression_repeat_decision")),
        ("source_count", summary.get("source_count")),
        ("pass_source_count", summary.get("pass_source_count")),
        ("baseline_strict_full_source_count", summary.get("baseline_strict_full_source_count")),
        ("suppressed_strict_full_source_count", summary.get("suppressed_strict_full_source_count")),
        ("suppressed_strict_gain_count", summary.get("suppressed_strict_gain_count")),
        ("stable_suppressed_strict_full_coverage", summary.get("stable_suppressed_strict_full_coverage")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "source_id",
        "status",
        "decision",
        "case_count",
        "baseline_strict_hit_count",
        "baseline_strict_full_coverage",
        "suppressed_strict_hit_count",
        "suppressed_strict_full_coverage",
        "suppressed_focus_strict_hit_count",
        "suppressed_focus_strict_full_coverage",
        "suppressed_strict_gain_count",
        "source_loss_alias_focus",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("source_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    table = [
        "| Source | Baseline strict | Suppressed strict | Suppressed full | Gains |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for row in list_of_dicts(report.get("source_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_id")),
                    markdown_cell(row.get("baseline_strict_hit_count")),
                    markdown_cell(row.get("suppressed_strict_hit_count")),
                    markdown_cell(row.get("suppressed_strict_full_coverage")),
                    markdown_cell(row.get("suppressed_strict_gain_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Alias Newline Suppression Repeat",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Repeat decision: `{summary.get('newline_suppression_repeat_decision')}`",
            f"- Sources: `{summary.get('pass_source_count')}/{summary.get('source_count')}`",
            f"- Baseline full sources: `{summary.get('baseline_strict_full_source_count')}`",
            f"- Suppressed full sources: `{summary.get('suppressed_strict_full_source_count')}`",
            f"- Strict gains: `{summary.get('suppressed_strict_gain_count')}`",
            "",
            "## Sources",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Sources", f"{summary.get('pass_source_count')}/{summary.get('source_count')}"),
        ("Baseline full", summary.get("baseline_strict_full_source_count")),
        ("Suppressed full", summary.get("suppressed_strict_full_source_count")),
        ("Gains", summary.get("suppressed_strict_gain_count")),
    ]
    rows = "\n".join(_source_html(row) for row in list_of_dicts(report.get("source_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-alias newline suppression repeat</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-alias newline suppression repeat</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Source Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Source</th><th>Baseline strict</th><th>Suppressed strict</th><th>Suppressed full</th><th>Focus strict</th><th>Gains</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_loss_alias_newline_suppression_repeat.csv",
        "text": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _source_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_id'))}</td>"
        f"<td>{html_escape(row.get('baseline_strict_hit_count'))}/{html_escape(row.get('case_count'))}</td>"
        f"<td>{html_escape(row.get('suppressed_strict_hit_count'))}/{html_escape(row.get('case_count'))}</td>"
        f"<td>{html_escape(row.get('suppressed_strict_full_coverage'))}</td>"
        f"<td>{html_escape(row.get('suppressed_focus_strict_hit_count'))}</td>"
        f"<td>{html_escape(row.get('suppressed_strict_gain_count'))}</td>"
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
h1{font-size:30px;margin:0 0 8px}
h2{font-size:18px;margin:0 0 12px}
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
