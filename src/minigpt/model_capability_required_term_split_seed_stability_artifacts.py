from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_split_seed_stability import (
    REQUIRED_TERM_SPLIT_SEED_STABILITY_HTML_FILENAME,
    REQUIRED_TERM_SPLIT_SEED_STABILITY_JSON_FILENAME,
    REQUIRED_TERM_SPLIT_SEED_STABILITY_MARKDOWN_FILENAME,
    REQUIRED_TERM_SPLIT_SEED_STABILITY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_split_seed_stability_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("seed_stability_decision", summary.get("seed_stability_decision")),
        ("seed_count", summary.get("seed_count")),
        ("train_repro_seed_count", summary.get("train_repro_seed_count")),
        ("holdout_hit_seed_count", summary.get("holdout_hit_seed_count")),
        ("min_train_continuation_hit_count", summary.get("min_train_continuation_hit_count")),
        ("max_train_continuation_hit_count", summary.get("max_train_continuation_hit_count")),
        ("max_holdout_continuation_hit_count", summary.get("max_holdout_continuation_hit_count")),
        ("stable_train_repro", summary.get("stable_train_repro")),
        ("stable_holdout_zero", summary.get("stable_holdout_zero")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_split_seed_stability_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "status",
        "holdout_decision",
        "train_example_count",
        "holdout_example_count",
        "train_continuation_hit_count",
        "holdout_continuation_hit_count",
        "train_hit_rate",
        "holdout_hit_rate",
        "report_json",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_split_seed_stability_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    best = as_dict(report.get("best_split"))
    table = [
        "| Seed | Train hits | Holdout hits | Decision |",
        "| ---: | ---: | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("seed_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("train_continuation_hit_count")),
                    markdown_cell(row.get("holdout_continuation_hit_count")),
                    markdown_cell(row.get("holdout_decision")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Split Seed Stability",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Seed stability decision: `{summary.get('seed_stability_decision')}`",
            f"- Best split: `{best.get('id')}`",
            f"- Holdout terms: `{', '.join(str(term) for term in best.get('holdout_terms') or [])}`",
            f"- Train-repro seeds: `{summary.get('train_repro_seed_count')}` / `{summary.get('seed_count')}`",
            f"- Holdout-hit seeds: `{summary.get('holdout_hit_seed_count')}`",
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


def render_model_capability_required_term_split_seed_stability_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    best = as_dict(report.get("best_split"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("seed_stability_decision")),
        ("Seeds", summary.get("seed_count")),
        ("Train repro", summary.get("train_repro_seed_count")),
        ("Holdout hits", summary.get("holdout_hit_seed_count")),
        ("Min train hits", summary.get("min_train_continuation_hit_count")),
        ("Max train hits", summary.get("max_train_continuation_hit_count")),
        ("Stable holdout zero", summary.get("stable_holdout_zero")),
    ]
    rows = "\n".join(_row_html(row) for row in list_of_dicts(report.get("seed_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT required-term split seed stability</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term split seed stability</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Best Split</h2><p>Split: {html_escape(best.get('id'))}</p><p>Holdout terms: {html_escape(', '.join(str(term) for term in best.get('holdout_terms') or []))}</p></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Seed Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Train hits</th><th>Holdout hits</th><th>Train rate</th><th>Holdout rate</th><th>Report</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_split_seed_stability_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_SPLIT_SEED_STABILITY_JSON_FILENAME,
        "csv": root / "model_capability_required_term_split_seed_stability.csv",
        "text": root / REQUIRED_TERM_SPLIT_SEED_STABILITY_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_SPLIT_SEED_STABILITY_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_SPLIT_SEED_STABILITY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_split_seed_stability_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_split_seed_stability_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_split_seed_stability_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_split_seed_stability_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('train_continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('holdout_continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('train_hit_rate'))}</td>"
        f"<td>{html_escape(row.get('holdout_hit_rate'))}</td>"
        f"<td>{html_escape(row.get('report_json'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f5f6f4; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #dde2d9; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #5e655d; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #dfe5dc; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #646d62; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 920px; }
th, td { text-align: left; border-bottom: 1px solid #e4e9e1; padding: 10px; vertical-align: top; }
th { color: #4c544a; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
