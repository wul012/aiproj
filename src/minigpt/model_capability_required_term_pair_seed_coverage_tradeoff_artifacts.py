from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_seed_coverage_tradeoff import (
    PAIR_SEED_COVERAGE_TRADEOFF_CSV_FILENAME,
    PAIR_SEED_COVERAGE_TRADEOFF_HTML_FILENAME,
    PAIR_SEED_COVERAGE_TRADEOFF_JSON_FILENAME,
    PAIR_SEED_COVERAGE_TRADEOFF_MARKDOWN_FILENAME,
    PAIR_SEED_COVERAGE_TRADEOFF_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_seed_coverage_tradeoff_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("config_count", summary.get("config_count")),
        ("seed_count", summary.get("seed_count")),
        ("union_pair_full_seed_count", summary.get("union_pair_full_seed_count")),
        ("best_single_config_id", summary.get("best_single_config_id")),
        ("best_single_pair_full_seed_count", summary.get("best_single_pair_full_seed_count")),
        ("tradeoff_detected", summary.get("tradeoff_detected")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_seed_coverage_tradeoff_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "covered_by_union",
        "winning_config_id",
        "covering_config_ids",
        "covering_config_count",
        "per_config_pair_full",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_seed_coverage_tradeoff_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    config_rows = [
        "| Config | Pair-full seeds | Seed count | Corpus | Decode |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in list_of_dicts(report.get("config_rows")):
        config_rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("config_id")),
                    markdown_cell(row.get("pair_full_seed_count")),
                    markdown_cell(row.get("seed_count")),
                    markdown_cell(row.get("corpus_mode")),
                    markdown_cell(f"k={row.get('top_k')} t={row.get('temperature')}"),
                ]
            )
            + " |"
        )
    seed_rows = [
        "| Seed | Covered | Winning config | Covering configs |",
        "| ---: | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("seed_rows")):
        seed_rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("covered_by_union")),
                    markdown_cell(row.get("winning_config_id")),
                    markdown_cell(", ".join(str(item) for item in row.get("covering_config_ids", []))),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Seed Coverage Tradeoff",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Union pair-full seeds: `{summary.get('union_pair_full_seed_count')}/{summary.get('seed_count')}`",
            f"- Best single config: `{summary.get('best_single_config_id')}`",
            f"- Best single pair-full seeds: `{summary.get('best_single_pair_full_seed_count')}`",
            f"- Tradeoff detected: `{summary.get('tradeoff_detected')}`",
            "",
            "## Configs",
            "",
            *config_rows,
            "",
            "## Seeds",
            "",
            *seed_rows,
            "",
            "## Boundary",
            "",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_seed_coverage_tradeoff_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Union pair-full", f"{summary.get('union_pair_full_seed_count')}/{summary.get('seed_count')}"),
        ("Best config", summary.get("best_single_config_id")),
        ("Best pair-full", summary.get("best_single_pair_full_seed_count")),
        ("Tradeoff", summary.get("tradeoff_detected")),
    ]
    config_rows = "\n".join(_config_html(row) for row in list_of_dicts(report.get("config_rows")))
    seed_rows = "\n".join(_seed_html(row) for row in list_of_dicts(report.get("seed_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair seed coverage tradeoff</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair seed coverage tradeoff</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Configs</h2>
<div class="table-wrap"><table>
<thead><tr><th>Config</th><th>Pair-full seeds</th><th>Seed count</th><th>Corpus</th><th>Decode</th><th>Source</th></tr></thead>
<tbody>{config_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Seeds</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Covered</th><th>Winning config</th><th>Covering configs</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_seed_coverage_tradeoff_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SEED_COVERAGE_TRADEOFF_JSON_FILENAME,
        "csv": root / PAIR_SEED_COVERAGE_TRADEOFF_CSV_FILENAME,
        "text": root / PAIR_SEED_COVERAGE_TRADEOFF_TEXT_FILENAME,
        "markdown": root / PAIR_SEED_COVERAGE_TRADEOFF_MARKDOWN_FILENAME,
        "html": root / PAIR_SEED_COVERAGE_TRADEOFF_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_seed_coverage_tradeoff_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_seed_coverage_tradeoff_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_seed_coverage_tradeoff_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_seed_coverage_tradeoff_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _config_html(row: dict[str, Any]) -> str:
    decode = f"k={row.get('top_k')} t={row.get('temperature')}"
    return (
        "<tr>"
        f"<td>{html_escape(row.get('config_id'))}</td>"
        f"<td>{html_escape(row.get('pair_full_seed_count'))}</td>"
        f"<td>{html_escape(row.get('seed_count'))}</td>"
        f"<td>{html_escape(row.get('corpus_mode'))}</td>"
        f"<td>{html_escape(decode)}</td>"
        f"<td>{html_escape(row.get('source_path'))}</td>"
        "</tr>"
    )


def _seed_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('covered_by_union'))}</td>"
        f"<td>{html_escape(row.get('winning_config_id'))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in row.get('covering_config_ids', [])))}</td>"
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
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_required_term_pair_seed_coverage_tradeoff_html",
    "render_model_capability_required_term_pair_seed_coverage_tradeoff_markdown",
    "render_model_capability_required_term_pair_seed_coverage_tradeoff_text",
    "write_model_capability_required_term_pair_seed_coverage_tradeoff_outputs",
]
