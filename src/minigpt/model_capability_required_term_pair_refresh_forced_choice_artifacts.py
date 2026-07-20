from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_refresh_forced_choice import (
    PAIR_REFRESH_FORCED_CHOICE_CSV_FILENAME,
    PAIR_REFRESH_FORCED_CHOICE_HTML_FILENAME,
    PAIR_REFRESH_FORCED_CHOICE_JSON_FILENAME,
    PAIR_REFRESH_FORCED_CHOICE_MARKDOWN_FILENAME,
    PAIR_REFRESH_FORCED_CHOICE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_refresh_forced_choice_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("prompt_count", summary.get("prompt_count")),
        ("score_row_count", summary.get("score_row_count")),
        ("expected_best_count", summary.get("expected_best_count")),
        ("forced_choice_full_match", summary.get("forced_choice_full_match")),
        ("collapse_candidate", summary.get("collapse_candidate")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_refresh_forced_choice_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "prompt_term",
        "prompt",
        "expected_term",
        "best_candidate_term",
        "expected_is_best",
        "expected_rank",
        "expected_avg_nll",
        "best_avg_nll",
        "expected_margin_vs_best",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("prompt_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_refresh_forced_choice_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Refresh Forced-Choice",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Expected-best prompts: `{summary.get('expected_best_count')}/{summary.get('prompt_count')}`",
            f"- Collapse candidate: `{summary.get('collapse_candidate')}`",
            "",
            "## Prompt Preference",
            "",
            *_prompt_markdown_rows(report),
            "",
            "## Candidate Scores",
            "",
            *_score_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_refresh_forced_choice_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Prompts", summary.get("prompt_count")),
        ("Expected best", summary.get("expected_best_count")),
        ("Full match", summary.get("forced_choice_full_match")),
        ("Collapse", summary.get("collapse_candidate") or "none"),
    ]
    prompts = "\n".join(_prompt_html(row) for row in list_of_dicts(report.get("prompt_rows")))
    scores = "\n".join(_score_html(row) for row in list_of_dicts(report.get("score_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT refresh forced-choice</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT refresh forced-choice</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Prompt Preference</h2>
<div class="table-wrap"><table>
<thead><tr><th>Prompt term</th><th>Prompt</th><th>Expected</th><th>Best</th><th>Expected best</th><th>Margin</th></tr></thead>
<tbody>{prompts}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Candidate Scores</h2>
<div class="table-wrap"><table>
<thead><tr><th>Prompt</th><th>Candidate</th><th>Expected?</th><th>Avg NLL</th><th>First rank</th><th>Status</th></tr></thead>
<tbody>{scores}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_refresh_forced_choice_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_REFRESH_FORCED_CHOICE_JSON_FILENAME,
        "csv": root / PAIR_REFRESH_FORCED_CHOICE_CSV_FILENAME,
        "text": root / PAIR_REFRESH_FORCED_CHOICE_TEXT_FILENAME,
        "markdown": root / PAIR_REFRESH_FORCED_CHOICE_MARKDOWN_FILENAME,
        "html": root / PAIR_REFRESH_FORCED_CHOICE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_refresh_forced_choice_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_refresh_forced_choice_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_refresh_forced_choice_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_refresh_forced_choice_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _prompt_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Prompt term | Prompt | Expected | Best | Expected best | Margin |", "| --- | --- | --- | --- | --- | ---: |"]
    for row in list_of_dicts(report.get("prompt_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("prompt_term")),
                    markdown_cell(row.get("prompt")),
                    markdown_cell(row.get("expected_term")),
                    markdown_cell(row.get("best_candidate_term")),
                    markdown_cell(row.get("expected_is_best")),
                    markdown_cell(row.get("expected_margin_vs_best")),
                ]
            )
            + " |"
        )
    return rows


def _score_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Prompt | Candidate | Expected? | Avg NLL | First rank | Status |", "| --- | --- | --- | ---: | ---: | --- |"]
    for row in list_of_dicts(report.get("score_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("prompt")),
                    markdown_cell(row.get("candidate_term")),
                    markdown_cell(row.get("is_expected_candidate")),
                    markdown_cell(row.get("avg_nll")),
                    markdown_cell(row.get("first_token_rank")),
                    markdown_cell(row.get("status")),
                ]
            )
            + " |"
        )
    return rows


def _prompt_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('prompt_term'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('expected_term'))}</td>"
        f"<td>{html_escape(row.get('best_candidate_term'))}</td>"
        f"<td>{html_escape(row.get('expected_is_best'))}</td>"
        f"<td>{html_escape(row.get('expected_margin_vs_best'))}</td>"
        "</tr>"
    )


def _score_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('candidate_term'))}</td>"
        f"<td>{html_escape(row.get('is_expected_candidate'))}</td>"
        f"<td>{html_escape(row.get('avg_nll'))}</td>"
        f"<td>{html_escape(row.get('first_token_rank'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
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


__all__ = [
    "render_model_capability_required_term_pair_refresh_forced_choice_html",
    "render_model_capability_required_term_pair_refresh_forced_choice_markdown",
    "render_model_capability_required_term_pair_refresh_forced_choice_text",
    "write_model_capability_required_term_pair_refresh_forced_choice_outputs",
]
