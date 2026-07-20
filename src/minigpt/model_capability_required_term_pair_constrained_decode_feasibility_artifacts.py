from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_constrained_decode_feasibility import (
    PAIR_CONSTRAINED_DECODE_FEASIBILITY_CSV_FILENAME,
    PAIR_CONSTRAINED_DECODE_FEASIBILITY_HTML_FILENAME,
    PAIR_CONSTRAINED_DECODE_FEASIBILITY_JSON_FILENAME,
    PAIR_CONSTRAINED_DECODE_FEASIBILITY_MARKDOWN_FILENAME,
    PAIR_CONSTRAINED_DECODE_FEASIBILITY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_constrained_decode_feasibility_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("default_hit_count", summary.get("default_hit_count")),
        ("constrained_hit_count", summary.get("constrained_hit_count")),
        ("hit_delta", summary.get("hit_delta")),
        ("constrained_pair_full", summary.get("constrained_pair_full")),
        ("fixed_constrained_hit", summary.get("fixed_constrained_hit")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_constrained_decode_feasibility_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "profile_id",
        "term",
        "prompt",
        "blocked_token_texts",
        "blocked_token_count",
        "continuation_hit",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_constrained_decode_feasibility_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Constrained Decode Feasibility",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Hit delta: `{summary.get('hit_delta')}`",
            f"- Constrained pair-full: `{summary.get('constrained_pair_full')}`",
            "",
            "## Profiles",
            "",
            *_profile_markdown_rows(report),
            "",
            "## Cases",
            "",
            *_case_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_constrained_decode_feasibility_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Default hits", summary.get("default_hit_count")),
        ("Constrained hits", summary.get("constrained_hit_count")),
        ("Hit delta", summary.get("hit_delta")),
        ("Pair full", summary.get("constrained_pair_full")),
    ]
    profiles = "\n".join(_profile_html(row) for row in list_of_dicts(report.get("profile_rows")))
    cases = "\n".join(_case_html(row) for row in list_of_dicts(report.get("case_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT constrained decode feasibility</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT constrained decode feasibility</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Profiles</h2>
<div class="table-wrap"><table>
<thead><tr><th>Profile</th><th>Hit terms</th><th>Missed terms</th><th>Pair full</th><th>Blocked tokens</th></tr></thead>
<tbody>{profiles}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Cases</h2>
<div class="table-wrap"><table>
<thead><tr><th>Profile</th><th>Term</th><th>Blocked</th><th>Hit</th><th>Continuation</th></tr></thead>
<tbody>{cases}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_constrained_decode_feasibility_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_CONSTRAINED_DECODE_FEASIBILITY_JSON_FILENAME,
        "csv": root / PAIR_CONSTRAINED_DECODE_FEASIBILITY_CSV_FILENAME,
        "text": root / PAIR_CONSTRAINED_DECODE_FEASIBILITY_TEXT_FILENAME,
        "markdown": root / PAIR_CONSTRAINED_DECODE_FEASIBILITY_MARKDOWN_FILENAME,
        "html": root / PAIR_CONSTRAINED_DECODE_FEASIBILITY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_constrained_decode_feasibility_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_constrained_decode_feasibility_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_constrained_decode_feasibility_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_constrained_decode_feasibility_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _profile_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Profile | Hit terms | Missed terms | Pair full | Blocked tokens |", "| --- | --- | --- | --- | ---: |"]
    for row in list_of_dicts(report.get("profile_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    markdown_cell(row.get("pair_full_hit")),
                    markdown_cell(row.get("blocked_token_count_total")),
                ]
            )
            + " |"
        )
    return rows


def _case_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Profile | Term | Blocked | Hit | Continuation |", "| --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("case_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("term")),
                    markdown_cell(",".join(str(item) for item in row.get("blocked_token_texts", []))),
                    markdown_cell(row.get("continuation_hit")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return rows


def _profile_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('pair_full_hit'))}</td>"
        f"<td>{html_escape(row.get('blocked_token_count_total'))}</td>"
        "</tr>"
    )


def _case_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('blocked_token_texts', [])))}</td>"
        f"<td>{html_escape(row.get('continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
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
    "render_model_capability_required_term_pair_constrained_decode_feasibility_html",
    "render_model_capability_required_term_pair_constrained_decode_feasibility_markdown",
    "render_model_capability_required_term_pair_constrained_decode_feasibility_text",
    "write_model_capability_required_term_pair_constrained_decode_feasibility_outputs",
]
