from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_branch_batch_closeout import (
    PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_CSV_FILENAME,
    PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_HTML_FILENAME,
    PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_JSON_FILENAME,
    PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_MARKDOWN_FILENAME,
    PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_loss_branch_batch_closeout_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("version_range", report.get("version_range")),
        ("source_report_count", report.get("source_report_count")),
        ("single_seed_pair_full_count", summary.get("single_seed_pair_full_count")),
        ("stability_pair_full_seed_count", summary.get("stability_pair_full_seed_count")),
        ("diagnostic_first_token_gap_count", summary.get("diagnostic_first_token_gap_count")),
        ("readiness_ready_for_design", summary.get("readiness_ready_for_design")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_loss_branch_batch_closeout_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Branch Ten-Version Closeout",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Version range: `{report.get('version_range')}`",
            f"- Single-seed pair-full count: `{summary.get('single_seed_pair_full_count')}`",
            f"- Stability pair-full seed count: `{summary.get('stability_pair_full_seed_count')}`",
            f"- First-token gap count: `{summary.get('diagnostic_first_token_gap_count')}`",
            f"- Readiness ready: `{summary.get('readiness_ready_for_design')}`",
            "",
            "## Evidence",
            "",
            *_evidence_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_loss_branch_batch_closeout_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Range", report.get("version_range")),
        ("Pair-full seeds", summary.get("stability_pair_full_seed_count")),
        ("First-token gaps", summary.get("diagnostic_first_token_gap_count")),
        ("Ready", summary.get("readiness_ready_for_design")),
    ]
    rows = "\n".join(_evidence_html(row) for row in list_of_dicts(report.get("evidence_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-branch batch closeout</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-branch batch closeout</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Evidence Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Version</th><th>Label</th><th>Status</th><th>Decision</th><th>Key result</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_loss_branch_batch_closeout_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_JSON_FILENAME,
        "csv": root / PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_CSV_FILENAME,
        "text": root / PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_TEXT_FILENAME,
        "markdown": root / PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_MARKDOWN_FILENAME,
        "html": root / PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_loss_branch_batch_closeout_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_loss_branch_batch_closeout_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_loss_branch_batch_closeout_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["version", "label", "status", "decision", "key_result", "path"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("evidence_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _evidence_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Version | Label | Status | Decision | Key result |", "| --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("evidence_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("version")),
                    markdown_cell(row.get("label")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("decision")),
                    markdown_cell(row.get("key_result")),
                ]
            )
            + " |"
        )
    return rows


def _evidence_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('version'))}</td>"
        f"<td>{html_escape(row.get('label'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('decision'))}</td>"
        f"<td>{html_escape(row.get('key_result'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#1b222a;--muted:#5d6b78;--line:#d8dde5;--panel:#f6f8fb;--accent:#38586d}
*{box-sizing:border-box}
body{margin:0;background:#eef3f6;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
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
    "render_loss_branch_batch_closeout_html",
    "render_loss_branch_batch_closeout_markdown",
    "render_loss_branch_batch_closeout_text",
    "write_loss_branch_batch_closeout_outputs",
]
