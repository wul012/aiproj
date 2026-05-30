from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_continuation_span_objective import (
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_HTML_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_JSON_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_continuation_span_objective_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("continuation_span_decision", summary.get("continuation_span_decision")),
        ("training_status", summary.get("training_status")),
        ("checkpoint_exists", summary.get("checkpoint_exists")),
        ("generation_hit_count", summary.get("generation_hit_count")),
        ("candidate_pair_full_generation_hit", summary.get("candidate_pair_full_generation_hit")),
        ("candidate_one_token_prefix_hit_count", summary.get("candidate_one_token_prefix_hit_count")),
        ("prefix_minimum_improved_count", summary.get("prefix_minimum_improved_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_continuation_span_objective_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "term",
        "source_minimum_hit_prefix_token_count",
        "candidate_minimum_hit_prefix_token_count",
        "minimum_hit_prefix_delta",
        "source_one_token_prefix_hit",
        "candidate_one_token_prefix_hit",
        "candidate_full_prefix_hit",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("compare_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_continuation_span_objective_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    training = as_dict(report.get("training"))
    table = ["| Term | Source min prefix | Candidate min prefix | Delta | Candidate one-token |", "| --- | ---: | ---: | ---: | --- |"]
    for row in list_of_dicts(report.get("compare_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("source_minimum_hit_prefix_token_count")),
                    markdown_cell(row.get("candidate_minimum_hit_prefix_token_count")),
                    markdown_cell(row.get("minimum_hit_prefix_delta")),
                    markdown_cell(row.get("candidate_one_token_prefix_hit")),
                ]
            )
            + " |"
        )
    generations = ["| Term | Continuation hit | Preview |", "| --- | --- | --- |"]
    for row in list_of_dicts(report.get("generation_rows")):
        generations.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("term")),
                    markdown_cell(int(row.get("continuation_hit_count") or 0) > 0),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Continuation-Span Objective",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Span decision: `{summary.get('continuation_span_decision')}`",
            f"- Training status: `{summary.get('training_status')}`",
            f"- Checkpoint: `{training.get('checkpoint_path')}`",
            f"- Generation hits: `{summary.get('generation_hit_count')}`",
            f"- Prefix improvements: `{summary.get('prefix_minimum_improved_count')}`",
            "",
            "## Prefix Comparison",
            "",
            *table,
            "",
            "## Free Generation Probes",
            "",
            *generations,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_continuation_span_objective_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("continuation_span_decision")),
        ("Training", summary.get("training_status")),
        ("Generation hits", summary.get("generation_hit_count")),
        ("Full pair", summary.get("candidate_pair_full_generation_hit")),
        ("One-token hits", summary.get("candidate_one_token_prefix_hit_count")),
        ("Prefix gains", summary.get("prefix_minimum_improved_count")),
    ]
    compare_rows = "\n".join(_compare_html(row) for row in list_of_dicts(report.get("compare_rows")))
    generation_rows = "\n".join(_generation_html(row) for row in list_of_dicts(report.get("generation_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT continuation-span objective</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT continuation-span objective</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Prefix Comparison</h2>
<div class="table-wrap"><table>
<thead><tr><th>Term</th><th>Source min</th><th>Candidate min</th><th>Delta</th><th>One-token</th><th>Preview</th></tr></thead>
<tbody>{compare_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Free Generation</h2>
<div class="table-wrap"><table>
<thead><tr><th>Term</th><th>Hit</th><th>Continuation</th></tr></thead>
<tbody>{generation_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_continuation_span_objective_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_continuation_span_objective.csv",
        "text": root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_continuation_span_objective_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_continuation_span_objective_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_continuation_span_objective_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_continuation_span_objective_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _compare_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('source_minimum_hit_prefix_token_count'))}</td>"
        f"<td>{html_escape(row.get('candidate_minimum_hit_prefix_token_count'))}</td>"
        f"<td>{html_escape(row.get('minimum_hit_prefix_delta'))}</td>"
        f"<td>{html_escape(row.get('candidate_one_token_prefix_hit'))}</td>"
        f"<td>{html_escape(row.get('candidate_best_completion_preview'))}</td>"
        "</tr>"
    )


def _generation_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(int(row.get('continuation_hit_count') or 0) > 0)}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px}
h2{font-size:18px;margin:0 0 12px}
p{color:var(--muted);line-height:1.55}
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
</style>"""
