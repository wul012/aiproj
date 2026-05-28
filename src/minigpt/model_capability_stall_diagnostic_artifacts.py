from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_stall_diagnostic import (
    STALL_HTML_FILENAME,
    STALL_JSON_FILENAME,
    STALL_MARKDOWN_FILENAME,
    STALL_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_stall_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("case_count", summary.get("case_count")),
        ("score_improved_count", summary.get("score_improved_count")),
        ("score_degraded_count", summary.get("score_degraded_count")),
        ("score_unchanged_count", summary.get("score_unchanged_count")),
        ("persistent_fail_count", summary.get("persistent_fail_count")),
        ("token_budget_or_shape_limit_count", summary.get("token_budget_or_shape_limit_count")),
        ("avg_score_delta", summary.get("avg_score_delta")),
        ("summary_decision", summary.get("decision")),
        ("model_quality_claim", as_dict(report.get("interpretation")).get("model_quality_claim")),
        ("next_action", as_dict(report.get("interpretation")).get("next_action")),
    ]
    lines = [f"{key}={value}" for key, value in rows]
    for case in list_of_dicts(report.get("cases"))[:12]:
        lines.append(
            "case="
            + ",".join(
                [
                    f"seed={case.get('seed')}",
                    f"name={case.get('case')}",
                    f"score_delta={case.get('score_delta')}",
                    f"reason={case.get('stall_reason')}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def write_model_capability_stall_diagnostic_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "case",
        "task_type",
        "difficulty",
        "first_max_iters",
        "last_max_iters",
        "first_status",
        "last_status",
        "first_score",
        "last_score",
        "score_delta",
        "stall_reason",
        "last_failed_checks",
        "last_missing_terms",
        "preview_changed",
        "first_preview",
        "last_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in list_of_dicts(report.get("cases")):
            writer.writerow({field: csv_cell(case.get(field)) for field in fieldnames})


def render_model_capability_stall_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    table = [
        "| Seed | Case | First | Last | Score delta | Reason | Failed checks |",
        "| ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for case in list_of_dicts(report.get("cases"))[:20]:
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(case.get("seed")),
                    markdown_cell(case.get("case")),
                    markdown_cell(case.get("first_score")),
                    markdown_cell(case.get("last_score")),
                    markdown_cell(case.get("score_delta")),
                    markdown_cell(case.get("stall_reason")),
                    markdown_cell(", ".join(str(item) for item in case.get("last_failed_checks") or [])),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Stall Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Summary decision: `{summary.get('decision')}`",
            f"- Cases: `{summary.get('case_count')}`",
            f"- Score improved/degraded/unchanged: `{summary.get('score_improved_count')}` / `{summary.get('score_degraded_count')}` / `{summary.get('score_unchanged_count')}`",
            f"- Persistent fail cases: `{summary.get('persistent_fail_count')}`",
            f"- Token budget or shape limits: `{summary.get('token_budget_or_shape_limit_count')}`",
            f"- Average score delta: `{summary.get('avg_score_delta')}`",
            "",
            "## Interpretation",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
            "## Top Stall Cases",
            "",
            *table,
            "",
            "## Dominant Failed Checks",
            "",
            *_mapping_lines(as_dict(summary.get("dominant_failed_checks"))),
            "",
            "## Dominant Missing Terms",
            "",
            *_mapping_lines(as_dict(summary.get("dominant_missing_terms"))),
            "",
        ]
    )


def render_model_capability_stall_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("decision")),
        ("Cases", summary.get("case_count")),
        ("Improved", summary.get("score_improved_count")),
        ("Degraded", summary.get("score_degraded_count")),
        ("Unchanged", summary.get("score_unchanged_count")),
        ("Persistent fail", summary.get("persistent_fail_count")),
        ("Token/shape limits", summary.get("token_budget_or_shape_limit_count")),
        ("Avg score delta", summary.get("avg_score_delta")),
    ]
    rows = "\n".join(_case_html(case) for case in list_of_dicts(report.get("cases"))[:40])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT model capability stall diagnostic</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT model capability stall diagnostic</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Prompt-Level Cases</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Case</th><th>Scores</th><th>Delta</th><th>Reason</th><th>Failed checks</th><th>Preview</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_stall_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / STALL_JSON_FILENAME,
        "csv": root / "model_capability_stall_diagnostic.csv",
        "text": root / STALL_TEXT_FILENAME,
        "markdown": root / STALL_MARKDOWN_FILENAME,
        "html": root / STALL_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_stall_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_stall_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_stall_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_stall_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _mapping_lines(values: dict[str, Any]) -> list[str]:
    if not values:
        return ["- none"]
    return [f"- `{key}`: `{values[key]}`" for key in sorted(values)]


def _case_html(case: dict[str, Any]) -> str:
    failed = ", ".join(str(item) for item in case.get("last_failed_checks") or [])
    preview = f"{case.get('first_preview') or ''} -> {case.get('last_preview') or ''}"
    return (
        "<tr>"
        f"<td>{html_escape(case.get('seed'))}</td>"
        f"<td>{html_escape(case.get('case'))}</td>"
        f"<td>{html_escape(case.get('first_score'))} / {html_escape(case.get('last_score'))}</td>"
        f"<td>{html_escape(case.get('score_delta'))}</td>"
        f"<td>{html_escape(case.get('stall_reason'))}</td>"
        f"<td>{html_escape(failed)}</td>"
        f"<td>{html_escape(preview)}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>'


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f4f6f8; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #d9dde2; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #55616d; line-height: 1.55; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #dce2e8; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #61707c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 880px; }
th, td { text-align: left; border-bottom: 1px solid #e2e7ec; padding: 10px; vertical-align: top; }
th { color: #43505a; font-size: 12px; text-transform: uppercase; }
</style>"""
