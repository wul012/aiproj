from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic import (
    TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME,
    TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME,
    TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
    TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_target_only_memory_partial_hit_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("target_only_memory_partial_hit_diagnostic_ready", summary.get("bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic_ready")),
        ("partial_case_count", summary.get("partial_case_count")),
        ("fixed_without_loss_case_count", summary.get("fixed_without_loss_case_count")),
        ("loss_prefix_case_count", summary.get("loss_prefix_case_count")),
        ("loss_hit_case_count", summary.get("loss_hit_case_count")),
        ("all_cases_loss_prefix", summary.get("all_cases_loss_prefix")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_target_only_memory_partial_hit_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory partial-hit diagnostic'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Partial cases: `{summary.get('partial_case_count')}`",
        f"- Loss-prefix cases: `{summary.get('loss_prefix_case_count')}`",
        f"- Loss-hit cases: `{summary.get('loss_hit_case_count')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Case Diagnostics",
        "",
        "| Case | Label | Hit | Missed | Continuation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_diagnostics")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("case_id")),
            markdown_cell(row.get("label")),
            markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
            markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
            markdown_cell(row.get("continuation")),
        ]) + " |")
    lines.extend(["", "## Root Causes", ""])
    for cause in list_of_dicts(report.get("root_causes")):
        lines.append(f"- `{markdown_cell(cause.get('id'))}`: {markdown_cell(cause.get('detail'))}")
    return "\n".join(lines).rstrip() + "\n"


def render_target_only_memory_partial_hit_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Partial", summary.get("partial_case_count")),
        ("Fixed no loss", summary.get("fixed_without_loss_case_count")),
        ("Loss prefix", summary.get("loss_prefix_case_count")),
        ("Loss hit", summary.get("loss_hit_case_count")),
        ("All prefix", summary.get("all_cases_loss_prefix")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_case_row(row) for row in list_of_dicts(report.get("case_diagnostics")))
    causes = "".join(f"<li><strong>{html_escape(cause.get('id'))}</strong>: {html_escape(cause.get('detail'))}</li>" for cause in list_of_dicts(report.get("root_causes")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory partial-hit diagnostic'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory partial-hit diagnostic'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Diagnostics</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Label</th><th>Hit</th><th>Missed</th><th>Continuation</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
<section class="panel"><h2>Root Causes</h2><ul>{causes}</ul></section>
</main>
</body>
</html>
"""


def write_target_only_memory_partial_hit_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_target_only_memory_partial_hit_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_target_only_memory_partial_hit_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_target_only_memory_partial_hit_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["case_id", "label", "hit_terms", "missed_terms", "continuation", "has_loss_prefix"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_diagnostics")):
            writer.writerow({
                "case_id": csv_cell(row.get("case_id")),
                "label": csv_cell(row.get("label")),
                "hit_terms": csv_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                "missed_terms": csv_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                "continuation": csv_cell(row.get("continuation")),
                "has_loss_prefix": csv_cell(row.get("has_loss_prefix")),
            })


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('label'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('continuation'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#7c2d12}
*{box-sizing:border-box}body{margin:0;background:#f6f7f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere}
li{margin:8px 0;line-height:1.5}
</style>"""


__all__ = [
    "render_target_only_memory_partial_hit_diagnostic_html",
    "render_target_only_memory_partial_hit_diagnostic_markdown",
    "render_target_only_memory_partial_hit_diagnostic_text",
    "write_target_only_memory_partial_hit_diagnostic_outputs",
]
