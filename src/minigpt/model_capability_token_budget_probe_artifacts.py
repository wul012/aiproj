from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_token_budget_probe import (
    TOKEN_BUDGET_HTML_FILENAME,
    TOKEN_BUDGET_JSON_FILENAME,
    TOKEN_BUDGET_MARKDOWN_FILENAME,
    TOKEN_BUDGET_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_token_budget_probe_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("token_budget_count", report.get("token_budget_count")),
        ("summary_decision", summary.get("decision")),
        ("baseline_token_cap", summary.get("baseline_token_cap")),
        ("largest_token_cap", summary.get("largest_token_cap")),
        ("token_budget_or_shape_limit_delta", summary.get("token_budget_or_shape_limit_delta")),
        ("score_improved_count_delta", summary.get("score_improved_count_delta")),
        ("pass_transition_count_delta", summary.get("pass_transition_count_delta")),
        ("persistent_fail_count_delta", summary.get("persistent_fail_count_delta")),
        ("avg_score_delta_change", summary.get("avg_score_delta_change")),
        ("model_quality_claim", as_dict(report.get("interpretation")).get("model_quality_claim")),
        ("next_action", as_dict(report.get("interpretation")).get("next_action")),
    ]
    lines = [f"{key}={value}" for key, value in rows]
    for row in _rows(report):
        lines.append(
            "token_cap="
            + ",".join(
                [
                    f"value={row.get('case_token_cap')}",
                    f"status={row.get('status')}",
                    f"token_stalls={row.get('token_budget_or_shape_limit_count')}",
                    f"score_improved={row.get('score_improved_count')}",
                    f"decision={row.get('summary_decision')}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def write_model_capability_token_budget_probe_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "case_token_cap",
        "status",
        "case_count",
        "score_improved_count",
        "score_degraded_count",
        "score_unchanged_count",
        "persistent_fail_count",
        "pass_transition_count",
        "preview_changed_count",
        "token_budget_or_shape_limit_count",
        "avg_score_delta",
        "summary_decision",
        "source_diagnostic",
        "source_ladder_report",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _rows(report):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_token_budget_probe_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    table = [
        "| Token cap | Status | Token stalls | Score improved | Pass transitions | Avg score delta | Decision |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in _rows(report):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_token_cap")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("token_budget_or_shape_limit_count")),
                    markdown_cell(row.get("score_improved_count")),
                    markdown_cell(row.get("pass_transition_count")),
                    markdown_cell(row.get("avg_score_delta")),
                    markdown_cell(row.get("summary_decision")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Token Budget Probe",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Summary decision: `{summary.get('decision')}`",
            f"- Baseline token cap: `{summary.get('baseline_token_cap')}`",
            f"- Largest token cap: `{summary.get('largest_token_cap')}`",
            f"- Token stall delta: `{summary.get('token_budget_or_shape_limit_delta')}`",
            f"- Score improved delta: `{summary.get('score_improved_count_delta')}`",
            f"- Pass transition delta: `{summary.get('pass_transition_count_delta')}`",
            f"- Persistent fail delta: `{summary.get('persistent_fail_count_delta')}`",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_token_budget_probe_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("decision")),
        ("Baseline cap", summary.get("baseline_token_cap")),
        ("Largest cap", summary.get("largest_token_cap")),
        ("Token stall delta", summary.get("token_budget_or_shape_limit_delta")),
        ("Score improved delta", summary.get("score_improved_count_delta")),
        ("Pass transition delta", summary.get("pass_transition_count_delta")),
        ("Persistent fail delta", summary.get("persistent_fail_count_delta")),
        ("Avg score delta change", summary.get("avg_score_delta_change")),
    ]
    rows = "\n".join(_row_html(row) for row in _rows(report))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT model capability token budget probe</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT model capability token budget probe</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Token Budgets</h2>
<div class="table-wrap"><table>
<thead><tr><th>Token cap</th><th>Status</th><th>Cases</th><th>Token stalls</th><th>Score improved</th><th>Pass transitions</th><th>Decision</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_token_budget_probe_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TOKEN_BUDGET_JSON_FILENAME,
        "csv": root / "model_capability_token_budget_probe.csv",
        "text": root / TOKEN_BUDGET_TEXT_FILENAME,
        "markdown": root / TOKEN_BUDGET_MARKDOWN_FILENAME,
        "html": root / TOKEN_BUDGET_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_token_budget_probe_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_token_budget_probe_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_token_budget_probe_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_token_budget_probe_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("rows"))


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_token_cap'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('case_count'))}</td>"
        f"<td>{html_escape(row.get('token_budget_or_shape_limit_count'))}</td>"
        f"<td>{html_escape(row.get('score_improved_count'))}</td>"
        f"<td>{html_escape(row.get('pass_transition_count'))}</td>"
        f"<td>{html_escape(row.get('summary_decision'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>'


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f5f2; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1120px; margin: 0 auto; }
header { border-bottom: 1px solid #dedbd2; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #635f57; line-height: 1.55; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #e1ded6; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #6b655c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 780px; }
th, td { text-align: left; border-bottom: 1px solid #e6e2dc; padding: 10px; vertical-align: top; }
th { color: #4d4942; font-size: 12px; text-transform: uppercase; }
</style>"""
