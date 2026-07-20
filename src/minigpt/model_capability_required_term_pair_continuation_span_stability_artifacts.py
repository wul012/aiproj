from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_continuation_span_stability import (
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_HTML_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_JSON_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_continuation_span_stability_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("continuation_span_stability_decision", summary.get("continuation_span_stability_decision")),
        ("seed_count", summary.get("seed_count")),
        ("pass_count", summary.get("pass_count")),
        ("prefix_gain_seed_count", summary.get("prefix_gain_seed_count")),
        ("full_pair_generation_seed_count", summary.get("full_pair_generation_seed_count")),
        ("stable_prefix_gain", summary.get("stable_prefix_gain")),
        ("stable_full_pair_generation", summary.get("stable_full_pair_generation")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_continuation_span_stability_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "status",
        "decision",
        "continuation_span_decision",
        "checkpoint_exists",
        "generation_hit_count",
        "candidate_pair_full_generation_hit",
        "candidate_one_token_prefix_hit_count",
        "prefix_minimum_improved_count",
        "out_dir",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_continuation_span_stability_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = ["| Seed | Status | Decision | Prefix gains | One-token hits | Full generation |", "| ---: | --- | --- | ---: | ---: | --- |"]
    for row in list_of_dicts(report.get("seed_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("decision")),
                    markdown_cell(row.get("prefix_minimum_improved_count")),
                    markdown_cell(row.get("candidate_one_token_prefix_hit_count")),
                    markdown_cell(row.get("candidate_pair_full_generation_hit")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Continuation-Span Stability",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Stability decision: `{summary.get('continuation_span_stability_decision')}`",
            f"- Seeds: `{summary.get('pass_count')}/{summary.get('seed_count')}`",
            f"- Prefix gain seeds: `{summary.get('prefix_gain_seed_count')}`",
            f"- Stable prefix gain: `{summary.get('stable_prefix_gain')}`",
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


def render_model_capability_required_term_pair_continuation_span_stability_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("continuation_span_stability_decision")),
        ("Seeds", f"{summary.get('pass_count')}/{summary.get('seed_count')}"),
        ("Prefix gain seeds", summary.get("prefix_gain_seed_count")),
        ("Full generation seeds", summary.get("full_pair_generation_seed_count")),
        ("Stable prefix", summary.get("stable_prefix_gain")),
    ]
    rows = "\n".join(_seed_html(row) for row in list_of_dicts(report.get("seed_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT continuation-span stability</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT continuation-span stability</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Seed Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Status</th><th>Decision</th><th>Prefix gains</th><th>One-token hits</th><th>Full generation</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_continuation_span_stability_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_continuation_span_stability.csv",
        "text": root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_continuation_span_stability_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_continuation_span_stability_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_continuation_span_stability_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_continuation_span_stability_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _seed_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('decision'))}</td>"
        f"<td>{html_escape(row.get('prefix_minimum_improved_count'))}</td>"
        f"<td>{html_escape(row.get('candidate_one_token_prefix_hit_count'))}</td>"
        f"<td>{html_escape(row.get('candidate_pair_full_generation_hit'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#7c3aed}
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
