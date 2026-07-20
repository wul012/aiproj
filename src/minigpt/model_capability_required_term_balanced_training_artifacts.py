from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_balanced_training import (
    REQUIRED_TERM_BALANCED_TRAINING_HTML_FILENAME,
    REQUIRED_TERM_BALANCED_TRAINING_JSON_FILENAME,
    REQUIRED_TERM_BALANCED_TRAINING_MARKDOWN_FILENAME,
    REQUIRED_TERM_BALANCED_TRAINING_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_balanced_training_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("balanced_training_decision", summary.get("balanced_training_decision")),
        ("term_count", summary.get("term_count")),
        ("generation_count", summary.get("generation_count")),
        ("continuation_hit_count", summary.get("continuation_hit_count")),
        ("generated_hit_count", summary.get("generated_hit_count")),
        ("case_with_continuation_hit_count", summary.get("case_with_continuation_hit_count")),
        ("continuation_hit_rate", summary.get("continuation_hit_rate")),
        ("training_status", summary.get("training_status")),
        ("checkpoint_exists", summary.get("checkpoint_exists")),
        ("prompt_alignment_ready", summary.get("prompt_alignment_ready")),
        ("prompt_leading_line_count", summary.get("prompt_leading_line_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_balanced_training_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "generation_seed",
        "case",
        "term",
        "scaffold_prompt",
        "balanced_line_count",
        "balanced_pattern_count",
        "prompt_hit_count",
        "generated_hit_count",
        "continuation_hit_count",
        "prompt_truncated",
        "generated_preview",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("generation_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_balanced_training_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    source_corpus = as_dict(report.get("source_corpus"))
    training = as_dict(report.get("training"))
    table = [
        "| Case | Term | Prompt | Continuation hit | Preview |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("generation_rows"))[:40]:
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case")),
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("scaffold_prompt")),
                    markdown_cell(row.get("continuation_hit_count")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Balanced Training",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Balanced training decision: `{summary.get('balanced_training_decision')}`",
            f"- Terms: `{summary.get('term_count')}`",
            f"- Generations: `{summary.get('generation_count')}`",
            f"- Continuation hits: `{summary.get('continuation_hit_count')}`",
            f"- Hit rate: `{summary.get('continuation_hit_rate')}`",
            f"- Prompt alignment ready: `{summary.get('prompt_alignment_ready')}`",
            f"- Prompt-leading lines: `{summary.get('prompt_leading_line_count')}`",
            f"- Source corpus: `{source_corpus.get('path')}`",
            f"- Checkpoint: `{training.get('checkpoint_path')}`",
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


def render_model_capability_required_term_balanced_training_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    source_corpus = as_dict(report.get("source_corpus"))
    training = as_dict(report.get("training"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("balanced_training_decision")),
        ("Terms", summary.get("term_count")),
        ("Generations", summary.get("generation_count")),
        ("Continuation hits", summary.get("continuation_hit_count")),
        ("Case hits", summary.get("case_with_continuation_hit_count")),
        ("Hit rate", summary.get("continuation_hit_rate")),
        ("Prompt aligned", summary.get("prompt_alignment_ready")),
        ("Prompt-leading lines", summary.get("prompt_leading_line_count")),
        ("Checkpoint", summary.get("checkpoint_exists")),
    ]
    rows = "\n".join(_generation_html(row) for row in list_of_dicts(report.get("generation_rows"))[:60])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT required-term balanced training</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term balanced training</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Training Evidence</h2><p>Corpus: {html_escape(source_corpus.get('path'))}</p><p>Checkpoint: {html_escape(training.get('checkpoint_path'))}</p><p>Command: {html_escape(training.get('command_text'))}</p></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Required-Term Generations</h2>
<div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Term</th><th>Prompt</th><th>Generated hit</th><th>Continuation hit</th><th>Continuation preview</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_balanced_training_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_BALANCED_TRAINING_JSON_FILENAME,
        "csv": root / "model_capability_required_term_balanced_training.csv",
        "text": root / REQUIRED_TERM_BALANCED_TRAINING_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_BALANCED_TRAINING_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_BALANCED_TRAINING_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_balanced_training_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_balanced_training_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_balanced_training_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_balanced_training_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _generation_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('scaffold_prompt'))}</td>"
        f"<td>{html_escape(row.get('generated_hit_count'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f4f7f6; color: #17212b; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #dae4e3; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #5a6668; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #dae4e3; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 33, 43, 0.05); }
.card span { display: block; color: #607072; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 900px; }
th, td { text-align: left; border-bottom: 1px solid #e2ebe9; padding: 10px; vertical-align: top; }
th { color: #4e5c5f; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
