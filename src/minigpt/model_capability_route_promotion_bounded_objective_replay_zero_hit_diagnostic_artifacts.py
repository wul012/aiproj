from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic import (
    BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME,
    BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME,
    BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
    BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_bounded_objective_replay_zero_hit_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("bounded_objective_zero_hit_diagnostic_ready", summary.get("bounded_objective_zero_hit_diagnostic_ready")),
        ("case_count", summary.get("case_count")),
        ("zero_hit_case_count", summary.get("zero_hit_case_count")),
        ("near_miss_case_count", summary.get("near_miss_case_count")),
        ("prompt_in_corpus_count", summary.get("prompt_in_corpus_count")),
        ("root_cause_count", summary.get("root_cause_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_objective_replay_zero_hit_diagnostic_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "zero_hit", "near_miss_terms", "prompt_in_corpus", "diagnosis", "recommended_action", "continuation_preview"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_diagnostics")):
            writer.writerow({
                "case_id": csv_cell(row.get("case_id")),
                "zero_hit": csv_cell(row.get("zero_hit")),
                "near_miss_terms": csv_cell(",".join(str(item) for item in row.get("near_miss_terms", []))),
                "prompt_in_corpus": csv_cell(row.get("prompt_in_corpus")),
                "diagnosis": csv_cell(row.get("diagnosis")),
                "recommended_action": csv_cell(row.get("recommended_action")),
                "continuation_preview": csv_cell(row.get("continuation_preview")),
            })


def render_bounded_objective_replay_zero_hit_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective replay zero-hit diagnostic'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_objective_zero_hit_diagnostic_ready')}`",
        f"- Zero-hit cases: `{summary.get('zero_hit_case_count')}`",
        f"- Near-miss cases: `{summary.get('near_miss_case_count')}`",
        f"- Root causes: `{summary.get('root_cause_count')}`",
        "",
        "## Case Diagnostics",
        "",
        "| Case | Zero Hit | Near Miss | In Corpus | Diagnosis | Action | Continuation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_diagnostics")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("case_id")),
            markdown_cell(row.get("zero_hit")),
            markdown_cell(",".join(str(item) for item in row.get("near_miss_terms", []))),
            markdown_cell(row.get("prompt_in_corpus")),
            markdown_cell(row.get("diagnosis")),
            markdown_cell(row.get("recommended_action")),
            markdown_cell(row.get("continuation_preview")),
        ]) + " |")
    lines.extend(["", "## Root Causes", "", "| Cause | Severity | Evidence | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("root_causes")):
        lines.append("| " + " | ".join([markdown_cell(row.get("cause_id")), markdown_cell(row.get("severity")), markdown_cell(row.get("evidence")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_objective_replay_zero_hit_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Zero hit", summary.get("zero_hit_case_count")),
        ("Near miss", summary.get("near_miss_case_count")),
        ("In corpus", summary.get("prompt_in_corpus_count")),
        ("Causes", summary.get("root_cause_count")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    case_rows = "".join(_case_row(item) for item in list_of_dicts(report.get("case_diagnostics")))
    cause_rows = "".join(_cause_row(item) for item in list_of_dicts(report.get("root_causes")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective replay zero-hit diagnostic'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective replay zero-hit diagnostic'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Diagnostics</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Zero</th><th>Near Miss</th><th>In Corpus</th><th>Diagnosis</th><th>Action</th><th>Continuation</th></tr></thead>
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


def write_bounded_objective_replay_zero_hit_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_replay_zero_hit_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_replay_zero_hit_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_replay_zero_hit_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_replay_zero_hit_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('zero_hit'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('near_miss_terms', [])))}</td>"
        f"<td>{html_escape(row.get('prompt_in_corpus'))}</td>"
        f"<td>{html_escape(row.get('diagnosis'))}</td>"
        f"<td>{html_escape(row.get('recommended_action'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
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


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#a16207}
*{box-sizing:border-box}
body{margin:0;background:#f4f5f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_bounded_objective_replay_zero_hit_diagnostic_html",
    "render_bounded_objective_replay_zero_hit_diagnostic_markdown",
    "render_bounded_objective_replay_zero_hit_diagnostic_text",
    "write_bounded_objective_replay_zero_hit_diagnostic_outputs",
]
