from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_CSV_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_HTML_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_decoder_budget_holdout_gap_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        (
            "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic_ready",
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic_ready"),
        ),
        ("dominant_gap", summary.get("dominant_gap")),
        ("case_count", summary.get("case_count")),
        ("passed_case_count", summary.get("passed_case_count")),
        ("tokenizer_prompt_coverage_gap_count", summary.get("tokenizer_prompt_coverage_gap_count")),
        ("holdout_prompt_unseen_surface_gap_count", summary.get("holdout_prompt_unseen_surface_gap_count")),
        ("required_term_generation_gap_count", summary.get("required_term_generation_gap_count")),
        ("continuation_replacement_row_count", summary.get("continuation_replacement_row_count")),
        ("prompt_unknown_row_count", summary.get("prompt_unknown_row_count")),
        ("prompt_unknown_token_count", summary.get("prompt_unknown_token_count")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_decoder_budget_holdout_gap_diagnostic_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "case_id",
        "case_pass",
        "failure_class",
        "prompt_unknown_count",
        "prompt_unknown_rate",
        "prompt_exact_in_corpus",
        "continuation_replacement_count",
        "hit_terms",
        "missed_terms",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("diagnostic_rows")):
            writer.writerow(
                {
                    "case_id": csv_cell(row.get("case_id")),
                    "case_pass": csv_cell(row.get("case_pass")),
                    "failure_class": csv_cell(row.get("failure_class")),
                    "prompt_unknown_count": csv_cell(row.get("prompt_unknown_count")),
                    "prompt_unknown_rate": csv_cell(row.get("prompt_unknown_rate")),
                    "prompt_exact_in_corpus": csv_cell(row.get("prompt_exact_in_corpus")),
                    "continuation_replacement_count": csv_cell(row.get("continuation_replacement_count")),
                    "hit_terms": csv_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    "missed_terms": csv_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                }
            )


def render_decoder_budget_holdout_gap_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT decoder-budget holdout gap diagnostic'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Dominant gap: `{summary.get('dominant_gap')}`",
        f"- Tokenizer coverage gaps: `{summary.get('tokenizer_prompt_coverage_gap_count')}`",
        f"- Unseen prompt surface gaps: `{summary.get('holdout_prompt_unseen_surface_gap_count')}`",
        f"- Required-term generation gaps: `{summary.get('required_term_generation_gap_count')}`",
        f"- Prompt unknown tokens: `{summary.get('prompt_unknown_token_count')}`",
        f"- Prompt unknown rows: `{summary.get('prompt_unknown_row_count')}`",
        f"- Replacement rows: `{summary.get('continuation_replacement_row_count')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Diagnostic Rows",
        "",
        "| Case | Pass | Failure class | Unknown | In corpus | Replacement | Hit terms | Missed terms |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("diagnostic_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("case_pass")),
                    markdown_cell(row.get("failure_class")),
                    markdown_cell(row.get("prompt_unknown_count")),
                    markdown_cell(row.get("prompt_exact_in_corpus")),
                    markdown_cell(row.get("continuation_replacement_count")),
                    markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_decoder_budget_holdout_gap_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Dominant gap", summary.get("dominant_gap")),
        ("Tokenizer gaps", summary.get("tokenizer_prompt_coverage_gap_count")),
        ("Unknown tokens", summary.get("prompt_unknown_token_count")),
        ("Unknown rows", summary.get("prompt_unknown_row_count")),
        ("Replacement rows", summary.get("continuation_replacement_row_count")),
        ("Passed", summary.get("passed_case_count")),
        ("Promotion", summary.get("promotion_ready")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("diagnostic_rows")))
    checks = "".join(_check_row(item) for item in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT decoder-budget holdout gap diagnostic'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT decoder-budget holdout gap diagnostic'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Diagnostic Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Pass</th><th>Failure class</th><th>Unknown</th><th>In corpus</th><th>Replacement</th><th>Hit</th><th>Missed</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_decoder_budget_holdout_gap_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_decoder_budget_holdout_gap_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_decoder_budget_holdout_gap_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_decoder_budget_holdout_gap_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_decoder_budget_holdout_gap_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('case_pass'))}</td>"
        f"<td>{html_escape(row.get('failure_class'))}</td>"
        f"<td>{html_escape(row.get('prompt_unknown_count'))}</td>"
        f"<td>{html_escape(row.get('prompt_exact_in_corpus'))}</td>"
        f"<td>{html_escape(row.get('continuation_replacement_count'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#f2f4f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_decoder_budget_holdout_gap_diagnostic_html",
    "render_decoder_budget_holdout_gap_diagnostic_markdown",
    "render_decoder_budget_holdout_gap_diagnostic_text",
    "write_decoder_budget_holdout_gap_diagnostic_outputs",
]
