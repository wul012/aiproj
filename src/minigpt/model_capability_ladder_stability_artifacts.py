from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_ladder_stability import (
    STABILITY_HTML_FILENAME,
    STABILITY_JSON_FILENAME,
    STABILITY_MARKDOWN_FILENAME,
    STABILITY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_ladder_stability_text(report: dict[str, Any]) -> str:
    stability = as_dict(report.get("stability_summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("seed_count", report.get("seed_count")),
        ("successful_seed_count", report.get("successful_seed_count")),
        ("stability_decision", stability.get("decision")),
        ("loss_improvement_seed_count", stability.get("loss_improvement_seed_count")),
        ("eval_improvement_seed_count", stability.get("eval_improvement_seed_count")),
        ("mean_best_val_loss_delta", stability.get("mean_best_val_loss_delta")),
        ("mean_score_delta", stability.get("mean_score_delta")),
        ("mean_generation_flags_delta", stability.get("mean_generation_flags_delta")),
        ("model_quality_claim", as_dict(report.get("interpretation")).get("model_quality_claim")),
    ]
    lines = [f"{key}={value}" for key, value in rows]
    for row in _rows(report):
        lines.append(
            "seed="
            + ",".join(
                [
                    f"value={row.get('seed')}",
                    f"status={row.get('status')}",
                    f"trend={row.get('trend_decision')}",
                    f"best_val_loss_delta={row.get('best_val_loss_delta')}",
                    f"score_delta={row.get('score_delta')}",
                    f"generation_flags_delta={row.get('generation_flags_delta')}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def write_model_capability_ladder_stability_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "index",
        "seed",
        "status",
        "decision",
        "rung_count",
        "successful_rung_count",
        "trend_decision",
        "first_max_iters",
        "last_max_iters",
        "best_loss_max_iters",
        "best_score_max_iters",
        "best_val_loss_delta",
        "score_delta",
        "generation_flags_delta",
        "report_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _rows(report):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_ladder_stability_markdown(report: dict[str, Any]) -> str:
    stability = as_dict(report.get("stability_summary"))
    table = [
        "| Seed | Status | Trend | Loss delta | Score delta | Gen flags delta |",
        "| ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for row in _rows(report):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("trend_decision")),
                    markdown_cell(row.get("best_val_loss_delta")),
                    markdown_cell(row.get("score_delta")),
                    markdown_cell(row.get("generation_flags_delta")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Ladder Stability",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Stability decision: `{stability.get('decision')}`",
            f"- Loss improvement seeds: `{stability.get('loss_improvement_seed_count')}`",
            f"- Eval improvement seeds: `{stability.get('eval_improvement_seed_count')}`",
            f"- Mean loss delta: `{stability.get('mean_best_val_loss_delta')}`",
            f"- Mean score delta: `{stability.get('mean_score_delta')}`",
            f"- Mean generation flags delta: `{stability.get('mean_generation_flags_delta')}`",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            "",
        ]
    )


def render_model_capability_ladder_stability_html(report: dict[str, Any]) -> str:
    stability = as_dict(report.get("stability_summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Seeds", report.get("seed_count")),
        ("Successful", report.get("successful_seed_count")),
        ("Stability", stability.get("decision")),
        ("Loss improved", stability.get("loss_improvement_seed_count")),
        ("Eval improved", stability.get("eval_improvement_seed_count")),
        ("Mean loss delta", stability.get("mean_best_val_loss_delta")),
        ("Mean score delta", stability.get("mean_score_delta")),
        ("Mean flags delta", stability.get("mean_generation_flags_delta")),
    ]
    rows = "\n".join(_row_html(row) for row in _rows(report))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT model capability ladder stability</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT model capability ladder stability</h1><p>{html_escape(as_dict(report.get('interpretation')).get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section>
<h2>Seed Replays</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Status</th><th>Trend</th><th>Loss delta</th><th>Score delta</th><th>Gen flags delta</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_ladder_stability_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / STABILITY_JSON_FILENAME,
        "csv": root / "model_capability_ladder_stability.csv",
        "text": root / STABILITY_TEXT_FILENAME,
        "markdown": root / STABILITY_MARKDOWN_FILENAME,
        "html": root / STABILITY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_ladder_stability_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_ladder_stability_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_ladder_stability_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_ladder_stability_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("rows"))


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('trend_decision'))}</td>"
        f"<td>{html_escape(row.get('best_val_loss_delta'))}</td>"
        f"<td>{html_escape(row.get('score_delta'))}</td>"
        f"<td>{html_escape(row.get('generation_flags_delta'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f5f7f3; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1120px; margin: 0 auto; }
header, section { margin: 0 0 18px; }
header { border-bottom: 1px solid #d5ded2; padding-bottom: 16px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #58675d; line-height: 1.55; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.card, section:not(.stats) { background: #fff; border: 1px solid #d9e0d6; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #617064; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e2e8df; padding: 10px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
</style>"""
