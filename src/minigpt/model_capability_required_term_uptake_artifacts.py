from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_uptake import (
    REQUIRED_TERM_UPTAKE_HTML_FILENAME,
    REQUIRED_TERM_UPTAKE_JSON_FILENAME,
    REQUIRED_TERM_UPTAKE_MARKDOWN_FILENAME,
    REQUIRED_TERM_UPTAKE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_uptake_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("uptake_decision", summary.get("uptake_decision")),
        ("required_term_row_count", summary.get("required_term_row_count")),
        ("generation_observation_count", summary.get("generation_observation_count")),
        ("continuation_hit_count", summary.get("continuation_hit_count")),
        ("generated_hit_count", summary.get("generated_hit_count")),
        ("prompt_hit_count", summary.get("prompt_hit_count")),
        ("expected_hit_count", summary.get("expected_hit_count")),
        ("last_rung_continuation_hit_count", summary.get("last_rung_continuation_hit_count")),
        ("expected_only_unique_term_count", summary.get("expected_only_unique_term_count")),
        ("source_ready_count", summary.get("source_ready_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_uptake_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "token_cap",
        "case",
        "task_type",
        "term",
        "max_iters",
        "continuation_hit",
        "generated_hit",
        "prompt_hit",
        "expected_hit",
        "continuation_occurrences",
        "generated_occurrences",
        "prompt_occurrences",
        "expected_occurrences",
        "continuation_preview",
        "eval_suite_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("observations")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_uptake_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Seed | Case | Term | Max iters | Continuation hit | Expected hit | Preview |",
        "| ---: | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("observations"))[:30]:
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("case")),
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("max_iters")),
                    markdown_cell(row.get("continuation_hit")),
                    markdown_cell(row.get("expected_hit")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Uptake",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Uptake decision: `{summary.get('uptake_decision')}`",
            f"- Generation observations: `{summary.get('generation_observation_count')}`",
            f"- Continuation hits: `{summary.get('continuation_hit_count')}`",
            f"- Last-rung continuation hits: `{summary.get('last_rung_continuation_hit_count')}`",
            f"- Expected hits: `{summary.get('expected_hit_count')}`",
            f"- Prompt hits: `{summary.get('prompt_hit_count')}`",
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


def render_model_capability_required_term_uptake_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Uptake decision", summary.get("uptake_decision")),
        ("Observations", summary.get("generation_observation_count")),
        ("Continuation hits", summary.get("continuation_hit_count")),
        ("Last rung hits", summary.get("last_rung_continuation_hit_count")),
        ("Expected hits", summary.get("expected_hit_count")),
        ("Prompt hits", summary.get("prompt_hit_count")),
        ("Sources ready", summary.get("source_ready_count")),
    ]
    source_rows = "\n".join(_source_html(row) for row in list_of_dicts(report.get("source_rows")))
    observation_rows = "\n".join(_observation_html(row) for row in list_of_dicts(report.get("observations"))[:36])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT required-term uptake audit</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term uptake audit</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Generation Sources</h2>
<div class="table-wrap"><table>
<thead><tr><th>Status</th><th>Token cap root</th><th>Eval suites</th><th>Max iters</th><th>Results</th></tr></thead>
<tbody>{source_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Required-Term Uptake Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Case</th><th>Term</th><th>Max iters</th><th>Continuation</th><th>Generated</th><th>Prompt</th><th>Expected</th><th>Preview</th></tr></thead>
<tbody>{observation_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_uptake_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_UPTAKE_JSON_FILENAME,
        "csv": root / "model_capability_required_term_uptake.csv",
        "text": root / REQUIRED_TERM_UPTAKE_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_UPTAKE_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_UPTAKE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_uptake_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_uptake_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_uptake_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_uptake_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _source_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('token_cap_root'))}</td>"
        f"<td>{html_escape(row.get('eval_suite_count'))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in row.get('max_iters_values') or []))}</td>"
        f"<td>{html_escape(row.get('result_count'))}</td>"
        "</tr>"
    )


def _observation_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('case'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('max_iters'))}</td>"
        f"<td>{html_escape(row.get('continuation_occurrences'))}</td>"
        f"<td>{html_escape(row.get('generated_occurrences'))}</td>"
        f"<td>{html_escape(row.get('prompt_occurrences'))}</td>"
        f"<td>{html_escape(row.get('expected_occurrences'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>'


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f5f6f2; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #dedbd2; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #635f57; line-height: 1.55; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #e2ded6; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #6b655c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 980px; }
th, td { text-align: left; border-bottom: 1px solid #e7e2dc; padding: 10px; vertical-align: top; }
th { color: #4d4942; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
