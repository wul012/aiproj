from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_stability import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_HTML_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_loss_alias_stability_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("loss_alias_stability_decision", summary.get("loss_alias_stability_decision")),
        ("loss_alias_stability_metric_decision", summary.get("loss_alias_stability_metric_decision")),
        ("seed_count", summary.get("seed_count")),
        ("pass_count", summary.get("pass_count")),
        ("checkpoint_seed_count", summary.get("checkpoint_seed_count")),
        ("source_loss_hit_seed_count", summary.get("source_loss_hit_seed_count")),
        ("heldout_loss_alias_partial_seed_count", summary.get("heldout_loss_alias_partial_seed_count")),
        ("heldout_loss_alias_full_seed_count", summary.get("heldout_loss_alias_full_seed_count")),
        ("heldout_loss_alias_normalized_partial_seed_count", summary.get("heldout_loss_alias_normalized_partial_seed_count")),
        ("heldout_loss_alias_normalized_full_seed_count", summary.get("heldout_loss_alias_normalized_full_seed_count")),
        ("stable_loss_alias_full_coverage", summary.get("stable_loss_alias_full_coverage")),
        ("stable_loss_alias_normalized_full_coverage", summary.get("stable_loss_alias_normalized_full_coverage")),
        ("normalization_gain_count", summary.get("normalization_gain_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_loss_alias_stability_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "status",
        "decision",
        "loss_alias_decision",
        "checkpoint_exists",
        "generation_hit_case_count",
        "source_loss_hit",
        "heldout_loss_alias_hit_case_count",
        "heldout_loss_alias_full_coverage",
        "source_loss_normalized_hit",
        "heldout_loss_alias_normalized_hit_case_count",
        "heldout_loss_alias_normalized_full_coverage",
        "normalization_gain_count",
        "training_status",
        "out_dir",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_loss_alias_stability_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Seed | Status | Decision | Strict heldout | Strict full | Norm heldout | Norm full | Gains |",
        "| ---: | --- | --- | ---: | --- | ---: | --- | ---: |",
    ]
    for row in list_of_dicts(report.get("seed_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("loss_alias_decision")),
                    markdown_cell(row.get("heldout_loss_alias_hit_case_count")),
                    markdown_cell(row.get("heldout_loss_alias_full_coverage")),
                    markdown_cell(row.get("heldout_loss_alias_normalized_hit_case_count")),
                    markdown_cell(row.get("heldout_loss_alias_normalized_full_coverage")),
                    markdown_cell(row.get("normalization_gain_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Alias Stability",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Stability decision: `{summary.get('loss_alias_stability_decision')}`",
            f"- Metric decision: `{summary.get('loss_alias_stability_metric_decision')}`",
            f"- Seeds: `{summary.get('pass_count')}/{summary.get('seed_count')}`",
            f"- Full coverage seeds: `{summary.get('heldout_loss_alias_full_seed_count')}`",
            f"- Stable full coverage: `{summary.get('stable_loss_alias_full_coverage')}`",
            f"- Normalized full coverage seeds: `{summary.get('heldout_loss_alias_normalized_full_seed_count')}`",
            f"- Normalization gains: `{summary.get('normalization_gain_count')}`",
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


def render_model_capability_required_term_pair_loss_alias_stability_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("loss_alias_stability_metric_decision")),
        ("Seeds", f"{summary.get('pass_count')}/{summary.get('seed_count')}"),
        ("Checkpoints", summary.get("checkpoint_seed_count")),
        ("Strict full seeds", summary.get("heldout_loss_alias_full_seed_count")),
        ("Norm full seeds", summary.get("heldout_loss_alias_normalized_full_seed_count")),
        ("Norm gains", summary.get("normalization_gain_count")),
    ]
    rows = "\n".join(_seed_html(row) for row in list_of_dicts(report.get("seed_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-alias stability</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-alias stability</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Seed Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Status</th><th>Decision</th><th>Strict heldout</th><th>Strict full</th><th>Norm heldout</th><th>Norm full</th><th>Gains</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_loss_alias_stability_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_loss_alias_stability.csv",
        "text": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_loss_alias_stability_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_loss_alias_stability_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_loss_alias_stability_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_loss_alias_stability_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _seed_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('loss_alias_decision'))}</td>"
        f"<td>{html_escape(row.get('heldout_loss_alias_hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('heldout_loss_alias_full_coverage'))}</td>"
        f"<td>{html_escape(row.get('heldout_loss_alias_normalized_hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('heldout_loss_alias_normalized_full_coverage'))}</td>"
        f"<td>{html_escape(row.get('normalization_gain_count'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#2563eb}
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
