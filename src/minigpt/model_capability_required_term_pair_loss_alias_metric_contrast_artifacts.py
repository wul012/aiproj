from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_metric_contrast import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_HTML_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_JSON_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_loss_alias_metric_contrast_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("metric_contrast_decision", summary.get("metric_contrast_decision")),
        ("source_metric_decision", summary.get("source_metric_decision")),
        ("focus_metric_decision", summary.get("focus_metric_decision")),
        ("source_normalization_gain_count", summary.get("source_normalization_gain_count")),
        ("focus_normalization_gain_count", summary.get("focus_normalization_gain_count")),
        ("normalization_gain_delta", summary.get("normalization_gain_delta")),
        ("source_stable_normalized_full", summary.get("source_stable_normalized_full")),
        ("focus_stable_normalized_full", summary.get("focus_stable_normalized_full")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_loss_alias_metric_contrast_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "stage",
        "status",
        "decision",
        "strict_decision",
        "metric_decision",
        "seed_count",
        "strict_full_seed_count",
        "normalized_full_seed_count",
        "stable_strict_full",
        "stable_normalized_full",
        "normalization_gain_count",
        "source_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("stage_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_loss_alias_metric_contrast_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    table = [
        "| Stage | Strict decision | Metric decision | Strict full | Norm full | Gains | Source |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("stage_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("label")),
                    markdown_cell(row.get("strict_decision")),
                    markdown_cell(row.get("metric_decision")),
                    markdown_cell(row.get("stable_strict_full")),
                    markdown_cell(row.get("stable_normalized_full")),
                    markdown_cell(row.get("normalization_gain_count")),
                    markdown_cell(row.get("source_path")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Alias Metric Contrast",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Contrast decision: `{summary.get('metric_contrast_decision')}`",
            f"- Normalization gain delta: `{summary.get('normalization_gain_delta')}`",
            f"- Source normalized full: `{summary.get('source_stable_normalized_full')}`",
            f"- Focus normalized full: `{summary.get('focus_stable_normalized_full')}`",
            "",
            "## Stages",
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


def render_model_capability_required_term_pair_loss_alias_metric_contrast_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("metric_contrast_decision")),
        ("Gain delta", summary.get("normalization_gain_delta")),
        ("Source norm full", summary.get("source_stable_normalized_full")),
        ("Focus norm full", summary.get("focus_stable_normalized_full")),
        ("Focus strict full", summary.get("focus_stable_strict_full")),
    ]
    rows = "\n".join(_stage_html(row) for row in list_of_dicts(report.get("stage_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-alias metric contrast</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-alias metric contrast</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Stage Contrast</h2>
<div class="table-wrap"><table>
<thead><tr><th>Stage</th><th>Strict decision</th><th>Metric decision</th><th>Strict full</th><th>Norm full</th><th>Gains</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_loss_alias_metric_contrast_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_loss_alias_metric_contrast.csv",
        "text": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_loss_alias_metric_contrast_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_loss_alias_metric_contrast_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_loss_alias_metric_contrast_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_loss_alias_metric_contrast_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _stage_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('label'))}</td>"
        f"<td>{html_escape(row.get('strict_decision'))}</td>"
        f"<td>{html_escape(row.get('metric_decision'))}</td>"
        f"<td>{html_escape(row.get('stable_strict_full'))}</td>"
        f"<td>{html_escape(row.get('stable_normalized_full'))}</td>"
        f"<td>{html_escape(row.get('normalization_gain_count'))}</td>"
        f"<td>{html_escape(row.get('source_path'))}</td>"
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
