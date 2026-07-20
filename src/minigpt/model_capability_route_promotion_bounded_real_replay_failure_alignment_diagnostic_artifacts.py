from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("diagnostic_ready", summary.get("bounded_real_replay_failure_alignment_diagnostic_ready")),
        ("case_count", summary.get("case_count")),
        ("failed_case_count", summary.get("failed_case_count")),
        ("prompt_gap_count", summary.get("prompt_gap_count")),
        ("root_cause_count", summary.get("root_cause_count")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "prompt_in_corpus", "repair_pass", "missed_terms", "diagnosis", "recommended_action"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_diagnostics")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay failure alignment diagnostic'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_real_replay_failure_alignment_diagnostic_ready')}`",
        f"- Failed cases: `{summary.get('failed_case_count')}/{summary.get('case_count')}`",
        f"- Prompt gaps: `{summary.get('prompt_gap_count')}`",
        f"- Root causes: `{summary.get('root_cause_count')}`",
        "",
        "## Case Diagnostics",
        "",
        "| Case | Prompt in corpus | Repair pass | Missed terms | Diagnosis | Action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_diagnostics")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("prompt_in_corpus")),
                    markdown_cell(row.get("repair_pass")),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    markdown_cell(row.get("diagnosis")),
                    markdown_cell(row.get("recommended_action")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Root Causes", "", "| Cause | Severity | Evidence | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("root_causes")):
        lines.append("| " + " | ".join([markdown_cell(row.get("cause_id")), markdown_cell(row.get("severity")), markdown_cell(row.get("evidence")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Failed", f"{summary.get('failed_case_count')}/{summary.get('case_count')}"),
        ("Prompt gaps", summary.get("prompt_gap_count")),
        ("Causes", summary.get("root_cause_count")),
        ("Next", summary.get("next_step")),
    ]
    case_rows = "".join(_case_row(item) for item in list_of_dicts(report.get("case_diagnostics")))
    cause_rows = "".join(_cause_row(item) for item in list_of_dicts(report.get("root_causes")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay failure alignment diagnostic'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay failure alignment diagnostic'))}</h1><p>Diagnoses why revised repair training still failed bounded replay by comparing benchmark prompts, corpus coverage, and generated continuations.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Diagnostics</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Prompt in corpus</th><th>Pass</th><th>Missed</th><th>Diagnosis</th><th>Action</th></tr></thead>
<tbody>{case_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Root Causes</h2><div class="table-wrap"><table>
<thead><tr><th>Cause</th><th>Severity</th><th>Evidence</th><th>Detail</th></tr></thead>
<tbody>{cause_rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('prompt_in_corpus'))}</td>"
        f"<td>{html_escape(row.get('repair_pass'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('diagnosis'))}</td>"
        f"<td>{html_escape(row.get('recommended_action'))}</td>"
        "</tr>"
    )


def _cause_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('cause_id'))}</td>"
        f"<td>{html_escape(row.get('severity'))}</td>"
        f"<td>{html_escape(row.get('evidence'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#667381;--line:#d8dee4;--panel:#f8fafc;--accent:#9a3412}
*{box-sizing:border-box}
body{margin:0;background:#f1f3f6;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
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
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_html",
    "render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_text",
    "write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_outputs",
]
