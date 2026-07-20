from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_ladder import (
    LADDER_HTML_FILENAME,
    LADDER_JSON_FILENAME,
    LADDER_MARKDOWN_FILENAME,
    LADDER_TEXT_FILENAME,
)
from minigpt.report_utils import (
    as_dict,
    csv_cell,
    html_escape,
    list_of_dicts,
    markdown_cell,
    write_json_payload,
)
from minigpt.report_utils import html_card as _card


def render_model_capability_ladder_text(report: dict[str, Any]) -> str:
    trend = as_dict(report.get("trend_summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("rung_count", report.get("rung_count")),
        ("successful_rung_count", report.get("successful_rung_count")),
        ("first_max_iters", trend.get("first_max_iters")),
        ("last_max_iters", trend.get("last_max_iters")),
        ("best_loss_max_iters", trend.get("best_loss_max_iters")),
        ("best_score_max_iters", trend.get("best_score_max_iters")),
        ("best_val_loss_delta", trend.get("best_val_loss_delta_first_to_last")),
        ("final_val_loss_delta", trend.get("final_val_loss_delta_first_to_last")),
        ("score_delta", trend.get("score_delta_first_to_last")),
        ("generation_flags_delta", trend.get("generation_flags_delta_first_to_last")),
        ("trend_decision", trend.get("decision")),
        ("model_quality_claim", as_dict(report.get("interpretation")).get("model_quality_claim")),
    ]
    lines = [f"{key}={value}" for key, value in rows]
    for row in _rows(report):
        lines.append(
            "rung="
            + ",".join(
                [
                    f"max_iters={row.get('max_iters')}",
                    f"status={row.get('status')}",
                    f"best_val_loss={row.get('best_val_loss')}",
                    f"score={row.get('scorecard_overall_score')}",
                    f"generation_flags={row.get('generation_quality_total_flags')}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def write_model_capability_ladder_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "index",
        "name",
        "max_iters",
        "status",
        "decision",
        "checkpoint_exists",
        "eval_suite_case_count",
        "best_val_loss",
        "final_val_loss",
        "scorecard_overall_status",
        "scorecard_overall_score",
        "generation_quality_status",
        "generation_quality_total_flags",
        "pair_same_checkpoint_baseline",
        "command_failure_count",
        "summary_path",
        "run_dir",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _rows(report):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_ladder_markdown(report: dict[str, Any]) -> str:
    trend = as_dict(report.get("trend_summary"))
    table = [
        "| Max iters | Status | Best val loss | Final val loss | Score | Gen flags | Checkpoint |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in _rows(report):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("max_iters")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("best_val_loss")),
                    markdown_cell(row.get("final_val_loss")),
                    markdown_cell(row.get("scorecard_overall_score")),
                    markdown_cell(row.get("generation_quality_total_flags")),
                    markdown_cell(row.get("checkpoint_exists")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Ladder",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Trend decision: `{trend.get('decision')}`",
            f"- First max iters: `{trend.get('first_max_iters')}`",
            f"- Last max iters: `{trend.get('last_max_iters')}`",
            f"- Best loss max iters: `{trend.get('best_loss_max_iters')}`",
            f"- Best score max iters: `{trend.get('best_score_max_iters')}`",
            f"- Best val loss delta: `{trend.get('best_val_loss_delta_first_to_last')}`",
            f"- Score delta: `{trend.get('score_delta_first_to_last')}`",
            f"- Generation flags delta: `{trend.get('generation_flags_delta_first_to_last')}`",
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


def render_model_capability_ladder_html(report: dict[str, Any]) -> str:
    trend = as_dict(report.get("trend_summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Rungs", report.get("rung_count")),
        ("Successful", report.get("successful_rung_count")),
        ("Trend", trend.get("decision")),
        ("Best loss iters", trend.get("best_loss_max_iters")),
        ("Best score iters", trend.get("best_score_max_iters")),
        ("Loss delta", trend.get("best_val_loss_delta_first_to_last")),
        ("Score delta", trend.get("score_delta_first_to_last")),
        ("Gen flags delta", trend.get("generation_flags_delta_first_to_last")),
    ]
    rows = "\n".join(_row_html(row) for row in _rows(report))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT model capability ladder</title>
{_style()}
</head>
<body>
<main>
<header>
<h1>MiniGPT model capability ladder</h1>
<p>{html_escape(as_dict(report.get('interpretation')).get('reason'))}</p>
</header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section>
<h2>Rungs</h2>
<div class="table-wrap">
<table>
<thead><tr><th>Max iters</th><th>Status</th><th>Best val loss</th><th>Final val loss</th><th>Score</th><th>Gen flags</th><th>Checkpoint</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_ladder_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / LADDER_JSON_FILENAME,
        "csv": root / "model_capability_ladder.csv",
        "text": root / LADDER_TEXT_FILENAME,
        "markdown": root / LADDER_MARKDOWN_FILENAME,
        "html": root / LADDER_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_ladder_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_ladder_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_ladder_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_ladder_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("rows"))


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('max_iters'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('best_val_loss'))}</td>"
        f"<td>{html_escape(row.get('final_val_loss'))}</td>"
        f"<td>{html_escape(row.get('scorecard_overall_score'))}</td>"
        f"<td>{html_escape(row.get('generation_quality_total_flags'))}</td>"
        f"<td>{html_escape(row.get('checkpoint_exists'))}</td>"
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
