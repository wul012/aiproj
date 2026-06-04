from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_training_run import (
    BOUNDED_OBJECTIVE_TRAINING_RUN_CSV_FILENAME,
    BOUNDED_OBJECTIVE_TRAINING_RUN_HTML_FILENAME,
    BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME,
    BOUNDED_OBJECTIVE_TRAINING_RUN_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_TRAINING_RUN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_bounded_objective_training_run_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("bounded_objective_training_ready", summary.get("bounded_objective_training_ready")),
        ("final_step", summary.get("final_step")),
        ("final_train_loss", summary.get("final_train_loss")),
        ("final_val_loss", summary.get("final_val_loss")),
        ("train_loss_delta", summary.get("train_loss_delta")),
        ("objective_example_count", summary.get("objective_example_count")),
        ("direct_example_count", summary.get("direct_example_count")),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_objective_training_run_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["key", "exists", "size", "path"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("artifacts")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_bounded_objective_training_run_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective training run'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_objective_training_ready')}`",
        f"- Final step: `{summary.get('final_step')}`",
        f"- Final train loss: `{summary.get('final_train_loss')}`",
        f"- Final val loss: `{summary.get('final_val_loss')}`",
        f"- Objective examples: `{summary.get('objective_example_count')}`",
        f"- Direct examples: `{summary.get('direct_example_count')}`",
        f"- Model-quality claim: `{interpretation.get('model_quality_claim')}`",
        "",
        "## Artifacts",
        "",
        "| Key | Exists | Size | Path |",
        "| --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("artifacts")):
        lines.append("| " + " | ".join([markdown_cell(row.get("key")), markdown_cell(row.get("exists")), markdown_cell(row.get("size")), markdown_cell(row.get("path"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_objective_training_run_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("bounded_objective_training_ready")),
        ("Final step", summary.get("final_step")),
        ("Val loss", summary.get("final_val_loss")),
        ("Direct examples", summary.get("direct_example_count")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("artifacts")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective training run'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective training run'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Artifacts</h2><div class="table-wrap"><table>
<thead><tr><th>Key</th><th>Exists</th><th>Size</th><th>Path</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_bounded_objective_training_run_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_TRAINING_RUN_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_TRAINING_RUN_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_TRAINING_RUN_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_TRAINING_RUN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_training_run_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_training_run_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_training_run_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_training_run_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('key'))}</td>"
        f"<td>{html_escape(row.get('exists'))}</td>"
        f"<td>{html_escape(row.get('size'))}</td>"
        f"<td>{html_escape(row.get('path'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#64717d;--line:#d8dee4;--panel:#f8fafc;--accent:#047857}
*{box-sizing:border-box}
body{margin:0;background:#eef1f6;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1200px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
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
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_bounded_objective_training_run_html",
    "render_bounded_objective_training_run_markdown",
    "render_bounded_objective_training_run_text",
    "write_bounded_objective_training_run_outputs",
]
