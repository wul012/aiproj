from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_token_budget_stability import (
    TOKEN_BUDGET_STABILITY_HTML_FILENAME,
    TOKEN_BUDGET_STABILITY_JSON_FILENAME,
    TOKEN_BUDGET_STABILITY_MARKDOWN_FILENAME,
    TOKEN_BUDGET_STABILITY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_token_budget_stability_text(report: dict[str, Any]) -> str:
    stability = as_dict(report.get("stability_summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("seed_count", report.get("seed_count")),
        ("successful_seed_count", report.get("successful_seed_count")),
        ("stability_decision", stability.get("decision")),
        ("token_relief_seed_count", stability.get("token_relief_seed_count")),
        ("persistent_fail_relief_seed_count", stability.get("persistent_fail_relief_seed_count")),
        ("score_or_pass_progress_seed_count", stability.get("score_or_pass_progress_seed_count")),
        ("mean_token_budget_or_shape_limit_delta", stability.get("mean_token_budget_or_shape_limit_delta")),
        ("mean_persistent_fail_count_delta", stability.get("mean_persistent_fail_count_delta")),
        ("mean_score_improved_count_delta", stability.get("mean_score_improved_count_delta")),
        ("mean_pass_transition_count_delta", stability.get("mean_pass_transition_count_delta")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    lines = [f"{key}={value}" for key, value in rows]
    for row in _rows(report):
        lines.append(
            "seed="
            + ",".join(
                [
                    f"value={row.get('seed')}",
                    f"status={row.get('status')}",
                    f"token_stall_delta={row.get('token_budget_or_shape_limit_delta')}",
                    f"persistent_fail_delta={row.get('persistent_fail_count_delta')}",
                    f"score_improved_delta={row.get('score_improved_count_delta')}",
                    f"pass_transition_delta={row.get('pass_transition_count_delta')}",
                    f"decision={row.get('summary_decision')}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def write_model_capability_token_budget_stability_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "index",
        "seed",
        "status",
        "decision",
        "token_budget_count",
        "baseline_token_cap",
        "largest_token_cap",
        "token_budget_or_shape_limit_delta",
        "persistent_fail_count_delta",
        "score_improved_count_delta",
        "pass_transition_count_delta",
        "avg_score_delta_change",
        "summary_decision",
        "report_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _rows(report):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_token_budget_stability_markdown(report: dict[str, Any]) -> str:
    stability = as_dict(report.get("stability_summary"))
    interpretation = as_dict(report.get("interpretation"))
    table = [
        "| Seed | Status | Token stall delta | Persistent fail delta | Score delta | Pass delta | Decision |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in _rows(report):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("token_budget_or_shape_limit_delta")),
                    markdown_cell(row.get("persistent_fail_count_delta")),
                    markdown_cell(row.get("score_improved_count_delta")),
                    markdown_cell(row.get("pass_transition_count_delta")),
                    markdown_cell(row.get("summary_decision")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Token Budget Stability",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Stability decision: `{stability.get('decision')}`",
            f"- Token relief seeds: `{stability.get('token_relief_seed_count')}`",
            f"- Persistent fail relief seeds: `{stability.get('persistent_fail_relief_seed_count')}`",
            f"- Score/pass progress seeds: `{stability.get('score_or_pass_progress_seed_count')}`",
            f"- Mean token stall delta: `{stability.get('mean_token_budget_or_shape_limit_delta')}`",
            f"- Mean persistent fail delta: `{stability.get('mean_persistent_fail_count_delta')}`",
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


def render_model_capability_token_budget_stability_html(report: dict[str, Any]) -> str:
    stability = as_dict(report.get("stability_summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", stability.get("decision")),
        ("Seeds", report.get("seed_count")),
        ("Successful", report.get("successful_seed_count")),
        ("Token relief", stability.get("token_relief_seed_count")),
        ("Score/pass progress", stability.get("score_or_pass_progress_seed_count")),
        ("Mean token stall delta", stability.get("mean_token_budget_or_shape_limit_delta")),
        ("Mean persistent fail delta", stability.get("mean_persistent_fail_count_delta")),
    ]
    rows = "\n".join(_row_html(row) for row in _rows(report))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT model capability token budget stability</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT model capability token budget stability</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Seed Probes</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Status</th><th>Token stall delta</th><th>Persistent fail delta</th><th>Score delta</th><th>Pass delta</th><th>Decision</th><th>Source probe</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_token_budget_stability_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TOKEN_BUDGET_STABILITY_JSON_FILENAME,
        "csv": root / "model_capability_token_budget_stability.csv",
        "text": root / TOKEN_BUDGET_STABILITY_TEXT_FILENAME,
        "markdown": root / TOKEN_BUDGET_STABILITY_MARKDOWN_FILENAME,
        "html": root / TOKEN_BUDGET_STABILITY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_token_budget_stability_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_token_budget_stability_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_token_budget_stability_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_token_budget_stability_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("rows"))


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('token_budget_or_shape_limit_delta'))}</td>"
        f"<td>{html_escape(row.get('persistent_fail_count_delta'))}</td>"
        f"<td>{html_escape(row.get('score_improved_count_delta'))}</td>"
        f"<td>{html_escape(row.get('pass_transition_count_delta'))}</td>"
        f"<td>{html_escape(row.get('summary_decision'))}</td>"
        f"<td>{html_escape(row.get('report_path'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f6f2; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #dedbd2; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #635f57; line-height: 1.55; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #e2ded6; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #6b655c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 960px; }
th, td { text-align: left; border-bottom: 1px solid #e7e2dc; padding: 10px; vertical-align: top; }
th { color: #4d4942; font-size: 12px; text-transform: uppercase; }
td:last-child { overflow-wrap: anywhere; max-width: 340px; }
</style>"""
