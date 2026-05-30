from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_first_token_preference import (
    PAIR_FIRST_TOKEN_PREFERENCE_CSV_FILENAME,
    PAIR_FIRST_TOKEN_PREFERENCE_HTML_FILENAME,
    PAIR_FIRST_TOKEN_PREFERENCE_JSON_FILENAME,
    PAIR_FIRST_TOKEN_PREFERENCE_MARKDOWN_FILENAME,
    PAIR_FIRST_TOKEN_PREFERENCE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_first_token_preference_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("term_count", summary.get("term_count")),
        ("expected_top_count", summary.get("expected_top_count")),
        ("whitespace_prefix_top_count", summary.get("whitespace_prefix_top_count")),
        ("answer_prefix_top_count", summary.get("answer_prefix_top_count")),
        ("max_expected_rank", summary.get("max_expected_rank")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_first_token_preference_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "term",
        "prompt",
        "expected_first_text",
        "expected_rank",
        "expected_probability",
        "top_token_text",
        "top_probability",
        "answer_prefix_is_top",
        "observed_replay_continuation",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_first_token_preference_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        "| Term | Prompt | Expected | Rank | Top token | Top prob | Observed continuation |",
        "| --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("prompt")),
                    markdown_cell(row.get("expected_first_text")),
                    markdown_cell(row.get("expected_rank")),
                    markdown_cell(row.get("top_token_text")),
                    markdown_cell(row.get("top_probability")),
                    markdown_cell(row.get("observed_replay_continuation")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair First-Token Preference",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
        f"- Expected top count: `{summary.get('expected_top_count')}`",
        f"- Whitespace-prefix top count: `{summary.get('whitespace_prefix_top_count')}`",
        f"- Answer-prefix top count: `{summary.get('answer_prefix_top_count')}`",
            "",
            "## Rows",
            "",
            *rows,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_first_token_preference_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Terms", summary.get("term_count")),
        ("Expected top", summary.get("expected_top_count")),
        ("Whitespace top", summary.get("whitespace_prefix_top_count")),
        ("Answer-prefix top", summary.get("answer_prefix_top_count")),
        ("Max expected rank", summary.get("max_expected_rank")),
    ]
    token_rows = "\n".join(_row_html(row) for row in list_of_dicts(report.get("rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT first-token preference</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT first-token preference</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Token Ranks</h2>
<div class="table-wrap"><table>
<thead><tr><th>Term</th><th>Prompt</th><th>Expected</th><th>Rank</th><th>Top token</th><th>Top prob</th><th>Observed replay</th></tr></thead>
<tbody>{token_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_first_token_preference_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_FIRST_TOKEN_PREFERENCE_JSON_FILENAME,
        "csv": root / PAIR_FIRST_TOKEN_PREFERENCE_CSV_FILENAME,
        "text": root / PAIR_FIRST_TOKEN_PREFERENCE_TEXT_FILENAME,
        "markdown": root / PAIR_FIRST_TOKEN_PREFERENCE_MARKDOWN_FILENAME,
        "html": root / PAIR_FIRST_TOKEN_PREFERENCE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_first_token_preference_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_first_token_preference_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_first_token_preference_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_first_token_preference_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('expected_first_text'))}</td>"
        f"<td>{html_escape(row.get('expected_rank'))}</td>"
        f"<td>{html_escape(row.get('top_token_text'))}</td>"
        f"<td>{html_escape(row.get('top_probability'))}</td>"
        f"<td>{html_escape(row.get('observed_replay_continuation'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


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
    "render_model_capability_required_term_pair_first_token_preference_html",
    "render_model_capability_required_term_pair_first_token_preference_markdown",
    "render_model_capability_required_term_pair_first_token_preference_text",
    "write_model_capability_required_term_pair_first_token_preference_outputs",
]
