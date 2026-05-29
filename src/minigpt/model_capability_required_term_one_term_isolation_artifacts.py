from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_one_term_isolation import (
    REQUIRED_TERM_ONE_TERM_ISOLATION_HTML_FILENAME,
    REQUIRED_TERM_ONE_TERM_ISOLATION_JSON_FILENAME,
    REQUIRED_TERM_ONE_TERM_ISOLATION_MARKDOWN_FILENAME,
    REQUIRED_TERM_ONE_TERM_ISOLATION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_one_term_isolation_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("one_term_isolation_decision", summary.get("one_term_isolation_decision")),
        ("term_count", summary.get("term_count")),
        ("isolation_count", summary.get("isolation_count")),
        ("training_pass_count", summary.get("training_pass_count")),
        ("checkpoint_exists_count", summary.get("checkpoint_exists_count")),
        ("continuation_hit_count", summary.get("continuation_hit_count")),
        ("term_with_continuation_hit_count", summary.get("term_with_continuation_hit_count")),
        ("term_success_rate", summary.get("term_success_rate")),
        ("previous_continuation_hit_count", summary.get("previous_continuation_hit_count")),
        ("continuation_hit_delta", summary.get("continuation_hit_delta")),
        ("single_term_capacity_observed", summary.get("single_term_capacity_observed")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_one_term_isolation_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "one_term_run_id",
        "case",
        "term",
        "scaffold_prompt",
        "training_status",
        "checkpoint_exists",
        "one_term_line_count",
        "one_term_repeat",
        "generation_seed",
        "prompt_hit_count",
        "generated_hit_count",
        "continuation_hit_count",
        "prompt_truncated",
        "generated_preview",
        "continuation_preview",
        "checkpoint_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("isolation_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_one_term_isolation_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Term | Prompt | Training | Checkpoint | Continuation hit | Preview |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("isolation_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("scaffold_prompt")),
                    markdown_cell(row.get("training_status")),
                    markdown_cell(row.get("checkpoint_exists")),
                    markdown_cell(row.get("continuation_hit_count")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term One-Term Isolation",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- One-term decision: `{summary.get('one_term_isolation_decision')}`",
            f"- Terms: `{summary.get('term_count')}`",
            f"- Training pass count: `{summary.get('training_pass_count')}`",
            f"- Checkpoints: `{summary.get('checkpoint_exists_count')}`",
            f"- Continuation hits: `{summary.get('continuation_hit_count')}`",
            f"- Terms with hits: `{summary.get('term_with_continuation_hit_count')}`",
            f"- Previous continuation hits: `{summary.get('previous_continuation_hit_count')}`",
            f"- Continuation hit delta: `{summary.get('continuation_hit_delta')}`",
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


def render_model_capability_required_term_one_term_isolation_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("one_term_isolation_decision")),
        ("Terms", summary.get("term_count")),
        ("Runs", summary.get("isolation_count")),
        ("Training pass", summary.get("training_pass_count")),
        ("Checkpoints", summary.get("checkpoint_exists_count")),
        ("Continuation hits", summary.get("continuation_hit_count")),
        ("Terms with hits", summary.get("term_with_continuation_hit_count")),
        ("Hit delta", summary.get("continuation_hit_delta")),
        ("Capacity observed", summary.get("single_term_capacity_observed")),
    ]
    rows = "\n".join(_isolation_html(row) for row in list_of_dicts(report.get("isolation_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT required-term one-term isolation</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term one-term isolation</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Isolation Boundary</h2><p>Each row below used a separate one-term corpus and checkpoint. Previous continuation hits: {html_escape(summary.get('previous_continuation_hit_count'))}; current continuation hits: {html_escape(summary.get('continuation_hit_count'))}; delta: {html_escape(summary.get('continuation_hit_delta'))}.</p><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>One-Term Runs</h2>
<div class="table-wrap"><table>
<thead><tr><th>Run</th><th>Term</th><th>Prompt</th><th>Training</th><th>Checkpoint</th><th>Continuation hit</th><th>Preview</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_one_term_isolation_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_ONE_TERM_ISOLATION_JSON_FILENAME,
        "csv": root / "model_capability_required_term_one_term_isolation.csv",
        "text": root / REQUIRED_TERM_ONE_TERM_ISOLATION_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_ONE_TERM_ISOLATION_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_ONE_TERM_ISOLATION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_one_term_isolation_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_one_term_isolation_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_one_term_isolation_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_one_term_isolation_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _isolation_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('one_term_run_id'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('scaffold_prompt'))}</td>"
        f"<td>{html_escape(row.get('training_status'))}</td>"
        f"<td>{html_escape(row.get('checkpoint_exists'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>'


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f5f6f2; color: #182220; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #dde1d5; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #5b675f; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #dde1d5; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(24, 34, 32, 0.05); }
.card span { display: block; color: #68736c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 900px; }
th, td { text-align: left; border-bottom: 1px solid #e6eadf; padding: 10px; vertical-align: top; }
th { color: #52605a; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
