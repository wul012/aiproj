from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_prompt_leading_corpus import (
    REQUIRED_TERM_PROMPT_LEADING_CORPUS_HTML_FILENAME,
    REQUIRED_TERM_PROMPT_LEADING_CORPUS_JSON_FILENAME,
    REQUIRED_TERM_PROMPT_LEADING_CORPUS_MARKDOWN_FILENAME,
    REQUIRED_TERM_PROMPT_LEADING_CORPUS_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_prompt_leading_corpus_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("prompt_leading_corpus_decision", summary.get("prompt_leading_corpus_decision")),
        ("term_count", summary.get("term_count")),
        ("line_count", summary.get("line_count")),
        ("unique_line_rate", summary.get("unique_line_rate")),
        ("term_line_spread", summary.get("term_line_spread")),
        ("prompt_alignment_ready", summary.get("prompt_alignment_ready")),
        ("prompt_leading_line_count", summary.get("prompt_leading_line_count")),
        ("previous_prompt_alignment_ready", summary.get("previous_prompt_alignment_ready")),
        ("previous_prompt_leading_line_count", summary.get("previous_prompt_leading_line_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_prompt_leading_corpus_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "case",
        "term",
        "scaffold_prompt",
        "line_count",
        "expected_line_count",
        "pattern_count",
        "repeat",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("term_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_prompt_leading_corpus_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    corpus = as_dict(report.get("corpus"))
    table = [
        "| Case | Term | Prompt | Lines |",
        "| --- | --- | --- | ---: |",
    ]
    for row in list_of_dicts(report.get("term_rows"))[:40]:
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case")),
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("scaffold_prompt")),
                    markdown_cell(row.get("line_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Prompt-Leading Corpus",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Prompt-leading corpus decision: `{summary.get('prompt_leading_corpus_decision')}`",
            f"- Prompt alignment ready: `{summary.get('prompt_alignment_ready')}`",
            f"- Prompt-leading lines: `{summary.get('prompt_leading_line_count')}`",
            f"- Previous prompt alignment: `{summary.get('previous_prompt_alignment_ready')}`",
            f"- Previous prompt-leading lines: `{summary.get('previous_prompt_leading_line_count')}`",
            f"- Term line spread: `{summary.get('term_line_spread')}`",
            f"- Corpus: `{corpus.get('path')}`",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_prompt_leading_corpus_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    corpus = as_dict(report.get("corpus"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("prompt_leading_corpus_decision")),
        ("Terms", summary.get("term_count")),
        ("Lines", summary.get("line_count")),
        ("Prompt aligned", summary.get("prompt_alignment_ready")),
        ("Prompt-leading lines", summary.get("prompt_leading_line_count")),
        ("Previous aligned", summary.get("previous_prompt_alignment_ready")),
        ("Term spread", summary.get("term_line_spread")),
    ]
    rows = "\n".join(_term_row_html(row) for row in list_of_dicts(report.get("term_rows"))[:60])
    pattern_rows = "\n".join(
        f"<tr><td>{html_escape(key)}</td><td>{html_escape(value)}</td></tr>"
        for key, value in as_dict(summary.get("pattern_counts")).items()
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT required-term prompt-leading corpus</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term prompt-leading corpus</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Corpus</h2><p>{html_escape(corpus.get('path'))}</p><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel"><h2>Pattern Counts</h2><div class="table-wrap"><table><thead><tr><th>Pattern</th><th>Lines</th></tr></thead><tbody>{pattern_rows}</tbody></table></div></section>
<section class="panel">
<h2>Term Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Term</th><th>Prompt</th><th>Lines</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_prompt_leading_corpus_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PROMPT_LEADING_CORPUS_JSON_FILENAME,
        "csv": root / "model_capability_required_term_prompt_leading_corpus.csv",
        "text": root / REQUIRED_TERM_PROMPT_LEADING_CORPUS_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PROMPT_LEADING_CORPUS_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PROMPT_LEADING_CORPUS_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_prompt_leading_corpus_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_prompt_leading_corpus_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_prompt_leading_corpus_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_prompt_leading_corpus_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _term_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('scaffold_prompt'))}</td>"
        f"<td>{html_escape(row.get('line_count'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f7f2; color: #20251c; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #e0e5da; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #62695c; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #e0e5da; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(32, 37, 28, 0.05); }
.card span { display: block; color: #697160; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e7ebdf; padding: 10px; vertical-align: top; }
th { color: #555d50; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
