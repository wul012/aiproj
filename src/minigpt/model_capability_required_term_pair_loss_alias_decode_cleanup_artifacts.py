from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_decode_cleanup import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_HTML_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_JSON_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_loss_alias_decode_cleanup_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("decode_cleanup_decision", summary.get("decode_cleanup_decision")),
        ("case_count", summary.get("case_count")),
        ("raw_hit_count", summary.get("raw_hit_count")),
        ("remove_newlines_hit_count", summary.get("remove_newlines_hit_count")),
        ("collapse_whitespace_hit_count", summary.get("collapse_whitespace_hit_count")),
        ("remove_all_whitespace_hit_count", summary.get("remove_all_whitespace_hit_count")),
        ("alnum_only_hit_count", summary.get("alnum_only_hit_count")),
        ("minimal_recovery_strategy", summary.get("minimal_recovery_strategy")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_loss_alias_decode_cleanup_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "case_id",
        "case_type",
        "alias_group",
        "raw_hit",
        "normalized_hit",
        "normalization_gain",
        "remove_newlines_hit",
        "collapse_whitespace_hit",
        "remove_all_whitespace_hit",
        "alnum_only_hit",
        "minimal_recovery_strategy",
        "continuation_preview",
        "remove_newlines_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_loss_alias_decode_cleanup_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    table = [
        "| Case | Raw | Remove newlines | Collapse whitespace | Remove all whitespace | Minimal |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("raw_hit")),
                    markdown_cell(row.get("remove_newlines_hit")),
                    markdown_cell(row.get("collapse_whitespace_hit")),
                    markdown_cell(row.get("remove_all_whitespace_hit")),
                    markdown_cell(row.get("minimal_recovery_strategy")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Alias Decode Cleanup",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Cleanup decision: `{summary.get('decode_cleanup_decision')}`",
            f"- Raw hits: `{summary.get('raw_hit_count')}/{summary.get('case_count')}`",
            f"- Remove-newlines hits: `{summary.get('remove_newlines_hit_count')}/{summary.get('case_count')}`",
            f"- Minimal strategy: `{summary.get('minimal_recovery_strategy')}`",
            "",
            "## Cases",
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


def render_model_capability_required_term_pair_loss_alias_decode_cleanup_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("decode_cleanup_decision")),
        ("Cases", summary.get("case_count")),
        ("Raw hits", summary.get("raw_hit_count")),
        ("Remove newlines", summary.get("remove_newlines_hit_count")),
        ("All whitespace", summary.get("remove_all_whitespace_hit_count")),
        ("Minimal", summary.get("minimal_recovery_strategy")),
    ]
    rows = "\n".join(_case_html(row) for row in list_of_dicts(report.get("case_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-alias decode cleanup</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-alias decode cleanup</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Cleanup Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Raw</th><th>Remove newlines</th><th>Collapse ws</th><th>All ws</th><th>Minimal</th><th>Cleaned preview</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_loss_alias_decode_cleanup_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_loss_alias_decode_cleanup.csv",
        "text": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_loss_alias_decode_cleanup_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_loss_alias_decode_cleanup_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_loss_alias_decode_cleanup_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_loss_alias_decode_cleanup_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('raw_hit'))}</td>"
        f"<td>{html_escape(row.get('remove_newlines_hit'))}</td>"
        f"<td>{html_escape(row.get('collapse_whitespace_hit'))}</td>"
        f"<td>{html_escape(row.get('remove_all_whitespace_hit'))}</td>"
        f"<td>{html_escape(row.get('minimal_recovery_strategy'))}</td>"
        f"<td>{html_escape(row.get('remove_newlines_preview'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#2563eb}
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
