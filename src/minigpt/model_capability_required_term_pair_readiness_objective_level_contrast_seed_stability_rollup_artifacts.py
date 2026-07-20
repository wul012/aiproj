from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_CSV_FILENAME,
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_HTML_FILENAME,
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_JSON_FILENAME,
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_MARKDOWN_FILENAME,
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_objective_level_contrast_seed_stability_rollup_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("acceptance_review_ready", summary.get("acceptance_review_ready")),
        ("promotion_allowed", summary.get("promotion_allowed")),
        ("observed_seed_count", summary.get("observed_seed_count")),
        ("ready_replay_count", summary.get("ready_replay_count")),
        ("pair_full_counts", summary.get("pair_full_counts")),
        ("uniform_pair_full_strength", summary.get("uniform_pair_full_strength")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_objective_level_contrast_seed_stability_rollup_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return "\n".join(
        [
            "# MiniGPT Objective-Level Contrast Seed Stability Rollup",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Acceptance review ready: `{summary.get('acceptance_review_ready')}`",
            f"- Promotion allowed: `{summary.get('promotion_allowed')}`",
            f"- Ready replay count: `{summary.get('ready_replay_count')}`",
            f"- Pair-full counts: `{markdown_cell(summary.get('pair_full_counts'))}`",
            "",
        ]
    )


def render_objective_level_contrast_seed_stability_rollup_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Review ready", summary.get("acceptance_review_ready")),
        ("Promotion", summary.get("promotion_allowed")),
        ("Seeds", f"{summary.get('observed_seed_count')}/{summary.get('expected_seed_count')}"),
        ("Ready replays", f"{summary.get('ready_replay_count')}/{summary.get('minimum_ready_replay_count')}"),
        ("Pair counts", summary.get("pair_full_counts")),
        ("Uniform", summary.get("uniform_pair_full_strength")),
    ]
    seed_rows = "".join(_seed_row_html(row) for row in list_of_dicts(report.get("seed_rows")))
    check_rows = "".join(_check_row_html(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT objective-level contrast seed stability rollup</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT objective-level contrast seed stability rollup</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Seed Replays</h2><div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Ready</th><th>Exact</th><th>Required</th><th>Pair-full</th><th>Decision</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{check_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_objective_level_contrast_seed_stability_rollup_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["seed", "ready", "status", "decision", "exact_heldout_pair_full", "required_all_pair_full", "pair_full_count", "source_path"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_objective_level_contrast_seed_stability_rollup_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_JSON_FILENAME,
        "csv": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_CSV_FILENAME,
        "text": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_objective_level_contrast_seed_stability_rollup_csv(report, paths["csv"])
    paths["text"].write_text(render_objective_level_contrast_seed_stability_rollup_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_objective_level_contrast_seed_stability_rollup_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_objective_level_contrast_seed_stability_rollup_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _seed_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('ready'))}</td>"
        f"<td>{html_escape(row.get('exact_heldout_pair_full'))}</td>"
        f"<td>{html_escape(row.get('required_all_pair_full'))}</td>"
        f"<td>{html_escape(row.get('pair_full_count'))}</td>"
        f"<td>{html_escape(row.get('decision'))}</td>"
        "</tr>"
    )


def _check_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('actual'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p,li{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
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
    "render_objective_level_contrast_seed_stability_rollup_html",
    "render_objective_level_contrast_seed_stability_rollup_markdown",
    "render_objective_level_contrast_seed_stability_rollup_text",
    "write_objective_level_contrast_seed_stability_rollup_outputs",
]
