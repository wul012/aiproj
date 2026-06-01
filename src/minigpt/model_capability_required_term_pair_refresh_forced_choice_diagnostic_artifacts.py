from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_refresh_forced_choice_diagnostic import (
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_CSV_FILENAME,
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_HTML_FILENAME,
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_MARKDOWN_FILENAME,
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("expected_best_prompt_count", summary.get("expected_best_prompt_count")),
        ("forced_choice_full_match_source_count", summary.get("forced_choice_full_match_source_count")),
        ("best_internal_sources", ",".join(str(value) for value in summary.get("best_internal_sources", []))),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Expected-best prompt count: `{summary.get('expected_best_prompt_count')}`",
            f"- Full-match source count: `{summary.get('forced_choice_full_match_source_count')}`",
            "",
            "## Prompt Summaries",
            "",
            *_prompt_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Expected-best", summary.get("expected_best_prompt_count")),
        ("Full match", summary.get("forced_choice_full_match_source_count")),
    ]
    rows = "\n".join(_prompt_html(row) for row in list_of_dicts(report.get("prompt_summaries")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT refresh forced-choice diagnostic</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT refresh forced-choice diagnostic</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel"><h2>Prompt Summaries</h2><div class="table-wrap"><table>
<thead><tr><th>Source</th><th>Prompt</th><th>Best</th><th>Expected best</th><th>Expected NLL</th><th>Best NLL</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_refresh_forced_choice_diagnostic_outputs(
    report: dict[str, Any], out_dir: str | Path
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_CSV_FILENAME,
        "text": root / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["source_label", "prompt_term", "best_candidate", "expected_candidate", "expected_best", "expected_avg_nll", "best_avg_nll"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("prompt_summaries")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _prompt_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Source | Prompt | Best | Expected best | Expected NLL | Best NLL |", "| --- | --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("prompt_summaries")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_label")),
                    markdown_cell(row.get("prompt_term")),
                    markdown_cell(row.get("best_candidate")),
                    markdown_cell(row.get("expected_best")),
                    markdown_cell(row.get("expected_avg_nll")),
                    markdown_cell(row.get("best_avg_nll")),
                ]
            )
            + " |"
        )
    return rows


def _prompt_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('prompt_term'))}</td>"
        f"<td>{html_escape(row.get('best_candidate'))}</td>"
        f"<td>{html_escape(row.get('expected_best'))}</td>"
        f"<td>{html_escape(row.get('expected_avg_nll'))}</td>"
        f"<td>{html_escape(row.get('best_avg_nll'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#2f5f5b}
*{box-sizing:border-box}
body{margin:0;background:#eef4f3;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1160px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}
</style>"""


__all__ = [
    "render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_html",
    "render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_markdown",
    "render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_text",
    "write_model_capability_required_term_pair_refresh_forced_choice_diagnostic_outputs",
]
