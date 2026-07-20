from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_holdout import (
    REQUIRED_TERM_HOLDOUT_HTML_FILENAME,
    REQUIRED_TERM_HOLDOUT_JSON_FILENAME,
    REQUIRED_TERM_HOLDOUT_MARKDOWN_FILENAME,
    REQUIRED_TERM_HOLDOUT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_holdout_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("holdout_decision", summary.get("holdout_decision")),
        ("train_example_count", summary.get("train_example_count")),
        ("holdout_example_count", summary.get("holdout_example_count")),
        ("train_continuation_hit_count", summary.get("train_continuation_hit_count")),
        ("holdout_continuation_hit_count", summary.get("holdout_continuation_hit_count")),
        ("train_hit_rate", summary.get("train_hit_rate")),
        ("holdout_hit_rate", summary.get("holdout_hit_rate")),
        ("training_status", summary.get("training_status")),
        ("checkpoint_exists", summary.get("checkpoint_exists")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_holdout_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "split",
        "seed",
        "case",
        "task_type",
        "term",
        "scaffold_prompt",
        "generation_seed",
        "prompt_hit_count",
        "generated_hit_count",
        "continuation_hit_count",
        "prompt_truncated",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("generation_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_holdout_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    split = as_dict(report.get("split"))
    corpus = as_dict(report.get("corpus"))
    table = [
        "| Split | Case | Term | Prompt | Hit | Preview |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("generation_rows"))[:32]:
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("split")),
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
            "# MiniGPT Model Capability Required-Term Holdout",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Holdout decision: `{summary.get('holdout_decision')}`",
            f"- Train examples: `{summary.get('train_example_count')}`",
            f"- Holdout examples: `{summary.get('holdout_example_count')}`",
            f"- Train hits: `{summary.get('train_continuation_hit_count')}`",
            f"- Holdout hits: `{summary.get('holdout_continuation_hit_count')}`",
            f"- Train terms: `{', '.join(str(item) for item in split.get('train_terms') or [])}`",
            f"- Holdout terms: `{', '.join(str(item) for item in split.get('holdout_terms') or [])}`",
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


def render_model_capability_required_term_holdout_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    split = as_dict(report.get("split"))
    corpus = as_dict(report.get("corpus"))
    training = as_dict(report.get("training"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("holdout_decision")),
        ("Train examples", summary.get("train_example_count")),
        ("Holdout examples", summary.get("holdout_example_count")),
        ("Train hits", summary.get("train_continuation_hit_count")),
        ("Holdout hits", summary.get("holdout_continuation_hit_count")),
        ("Train rate", summary.get("train_hit_rate")),
        ("Holdout rate", summary.get("holdout_hit_rate")),
    ]
    rows = "\n".join(_generation_html(row) for row in list_of_dicts(report.get("generation_rows"))[:32])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT required-term holdout</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term holdout</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Split</h2><p>Train terms: {html_escape(', '.join(str(item) for item in split.get('train_terms') or []))}</p><p>Holdout terms: {html_escape(', '.join(str(item) for item in split.get('holdout_terms') or []))}</p></section>
<section class="panel"><h2>Training Evidence</h2><p>Corpus: {html_escape(corpus.get('path'))}</p><p>Checkpoint: {html_escape(training.get('checkpoint_path'))}</p><p>Boundary: {html_escape(corpus.get('vocab_boundary'))}</p></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Train vs Holdout Generations</h2>
<div class="table-wrap"><table>
<thead><tr><th>Split</th><th>Case</th><th>Term</th><th>Prompt</th><th>Generated hit</th><th>Continuation hit</th><th>Continuation preview</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_holdout_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_HOLDOUT_JSON_FILENAME,
        "csv": root / "model_capability_required_term_holdout.csv",
        "text": root / REQUIRED_TERM_HOLDOUT_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_HOLDOUT_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_HOLDOUT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_holdout_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_holdout_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_holdout_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_holdout_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _generation_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('split'))}</td>"
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
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f6f1; color: #162128; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #e1ded4; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #605e55; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #e4dfd5; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(22, 33, 40, 0.05); }
.card span { display: block; color: #6a665d; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 940px; }
th, td { text-align: left; border-bottom: 1px solid #e8e3db; padding: 10px; vertical-align: top; }
th { color: #504c44; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
