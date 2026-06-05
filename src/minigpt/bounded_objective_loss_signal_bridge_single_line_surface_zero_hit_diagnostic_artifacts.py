from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic import (
    SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME,
    SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME,
    SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
    SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME,
    SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_single_line_surface_zero_hit_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"zero_hit_diagnostic_ready={summary.get('bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic_ready')}",
            f"case_count={summary.get('case_count')}",
            f"exact_label_echo_case_count={summary.get('exact_label_echo_case_count')}",
            f"label_prefix_fragment_case_count={summary.get('label_prefix_fragment_case_count')}",
            f"zero_hit_case_count={summary.get('zero_hit_case_count')}",
            f"loss_improved_without_required_term_uptake={summary.get('loss_improved_without_required_term_uptake')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def write_single_line_surface_zero_hit_diagnostic_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "continuation_class", "exact_label_echo", "label_prefix_fragment", "any_hit", "missed_terms", "continuation"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_diagnostics")):
            writer.writerow({
                "case_id": csv_cell(row.get("case_id")),
                "continuation_class": csv_cell(row.get("continuation_class")),
                "exact_label_echo": csv_cell(row.get("exact_label_echo")),
                "label_prefix_fragment": csv_cell(row.get("label_prefix_fragment")),
                "any_hit": csv_cell(row.get("any_hit")),
                "missed_terms": csv_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                "continuation": csv_cell(row.get("continuation")),
            })


def render_single_line_surface_zero_hit_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT single-line surface zero-hit diagnostic'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Exact label echo: `{summary.get('exact_label_echo_case_count')}/{summary.get('case_count')}`",
        f"- Label fragments: `{summary.get('label_prefix_fragment_case_count')}/{summary.get('case_count')}`",
        f"- Loss improved without uptake: `{summary.get('loss_improved_without_required_term_uptake')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Case Diagnostics",
        "",
        "| Case | Class | Exact echo | Fragment | Missed | Continuation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_diagnostics")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("case_id")),
            markdown_cell(row.get("continuation_class")),
            markdown_cell(row.get("exact_label_echo")),
            markdown_cell(row.get("label_prefix_fragment")),
            markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
            markdown_cell(row.get("continuation")),
        ]) + " |")
    lines.extend(["", "## Root Causes", ""])
    for cause in list_of_dicts(report.get("root_causes")):
        lines.append(f"- `{markdown_cell(cause.get('id'))}`: {markdown_cell(cause.get('detail'))}")
    return "\n".join(lines).rstrip() + "\n"


def render_single_line_surface_zero_hit_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Cases", summary.get("case_count")),
        ("Exact echo", summary.get("exact_label_echo_case_count")),
        ("Fragments", summary.get("label_prefix_fragment_case_count")),
        ("Zero hit", summary.get("zero_hit_case_count")),
        ("Loss improved no uptake", summary.get("loss_improved_without_required_term_uptake")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_row(row) for row in list_of_dicts(report.get("case_diagnostics")))
    causes = "".join(f"<li><strong>{html_escape(cause.get('id'))}</strong>: {html_escape(cause.get('detail'))}</li>" for cause in list_of_dicts(report.get("root_causes")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT single-line surface zero-hit diagnostic'))}</title>{_style()}</head>
<body><main>
<header><h1>{html_escape(report.get('title', 'MiniGPT single-line surface zero-hit diagnostic'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Diagnostics</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>Class</th><th>Echo</th><th>Fragment</th><th>Missed</th><th>Continuation</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="panel"><h2>Root Causes</h2><ul>{causes}</ul></section>
</main></body></html>"""


def write_single_line_surface_zero_hit_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME,
        "text": root / SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_single_line_surface_zero_hit_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_single_line_surface_zero_hit_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_single_line_surface_zero_hit_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_single_line_surface_zero_hit_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('continuation_class'))}</td>"
        f"<td>{html_escape(row.get('exact_label_echo'))}</td>"
        f"<td>{html_escape(row.get('label_prefix_fragment'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('continuation'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#991b1b}
*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere}li{margin:8px 0;line-height:1.5}
</style>"""


__all__ = [
    "render_single_line_surface_zero_hit_diagnostic_html",
    "render_single_line_surface_zero_hit_diagnostic_markdown",
    "render_single_line_surface_zero_hit_diagnostic_text",
    "write_single_line_surface_zero_hit_diagnostic_outputs",
]
