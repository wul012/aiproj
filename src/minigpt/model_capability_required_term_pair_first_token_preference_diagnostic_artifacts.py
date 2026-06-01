from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_first_token_preference_diagnostic import (
    PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_CSV_FILENAME,
    PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_HTML_FILENAME,
    PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_JSON_FILENAME,
    PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_MARKDOWN_FILENAME,
    PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_first_token_preference_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("source_report_count", summary.get("source_report_count")),
        ("first_token_conflict_confirmed", summary.get("first_token_conflict_confirmed")),
        ("mixed_branch_tradeoff_confirmed", summary.get("mixed_branch_tradeoff_confirmed")),
        ("other_term_start_count", summary.get("other_term_start_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_model_capability_required_term_pair_first_token_preference_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair First-Token Preference Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- First-token conflict confirmed: `{summary.get('first_token_conflict_confirmed')}`",
            f"- Mixed branch tradeoff confirmed: `{summary.get('mixed_branch_tradeoff_confirmed')}`",
            f"- Other-term start count: `{summary.get('other_term_start_count')}`",
            "",
            "## Prompt Rows",
            "",
            *_prompt_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_first_token_preference_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Conflict", summary.get("first_token_conflict_confirmed")),
        ("Tradeoff", summary.get("mixed_branch_tradeoff_confirmed")),
        ("Other starts", summary.get("other_term_start_count")),
    ]
    rows = "\n".join(_prompt_html(row) for row in list_of_dicts(report.get("prompt_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT first-token preference diagnostic</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT first-token preference diagnostic</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Prompt Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Source</th><th>Profile</th><th>Term</th><th>First</th><th>Vote</th><th>Hit</th><th>Continuation</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_first_token_preference_diagnostic_outputs(
    report: dict[str, Any], out_dir: str | Path
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_CSV_FILENAME,
        "text": root / PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_first_token_preference_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_first_token_preference_diagnostic_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_first_token_preference_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "source_label",
        "profile_id",
        "term",
        "expected_first_char",
        "observed_first_char",
        "first_char_expected",
        "branch_vote",
        "continuation_hit",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("prompt_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _prompt_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = [
        "| Source | Profile | Term | First | Vote | Hit | Continuation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("prompt_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_label")),
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("term")),
                    markdown_cell(f"{row.get('observed_first_char')}/{row.get('expected_first_char')}"),
                    markdown_cell(row.get("branch_vote")),
                    markdown_cell(row.get("continuation_hit")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return rows


def _prompt_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('observed_first_char'))}/{html_escape(row.get('expected_first_char'))}</td>"
        f"<td>{html_escape(row.get('branch_vote'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#18212b;--muted:#5f6f7d;--line:#d7dee6;--panel:#f7f9fb;--accent:#355c7d}
*{box-sizing:border-box}
body{margin:0;background:#eef3f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_required_term_pair_first_token_preference_diagnostic_html",
    "render_model_capability_required_term_pair_first_token_preference_diagnostic_markdown",
    "render_model_capability_required_term_pair_first_token_preference_diagnostic_text",
    "write_model_capability_required_term_pair_first_token_preference_diagnostic_outputs",
]
