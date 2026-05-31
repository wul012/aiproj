from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_seed_config_selection import (
    PAIR_SEED_CONFIG_SELECTION_CSV_FILENAME,
    PAIR_SEED_CONFIG_SELECTION_HTML_FILENAME,
    PAIR_SEED_CONFIG_SELECTION_JSON_FILENAME,
    PAIR_SEED_CONFIG_SELECTION_MARKDOWN_FILENAME,
    PAIR_SEED_CONFIG_SELECTION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_seed_config_selection_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("seed_count", summary.get("seed_count")),
        ("selection_ready_seed_count", summary.get("selection_ready_seed_count")),
        ("selected_config_count", summary.get("selected_config_count")),
        ("requires_multi_config_policy", summary.get("requires_multi_config_policy")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_seed_config_selection_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "selected_config_id",
        "selection_ready",
        "selected_pair_full",
        "covering_config_ids",
        "covering_config_count",
        "fallback_required",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("selection_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_seed_config_selection_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    seed_rows = [
        "| Seed | Selected config | Ready | Covering configs |",
        "| ---: | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("selection_rows")):
        seed_rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("selected_config_id")),
                    markdown_cell(row.get("selection_ready")),
                    markdown_cell(", ".join(str(item) for item in row.get("covering_config_ids", []))),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Seed Config Selection",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Ready seeds: `{summary.get('selection_ready_seed_count')}/{summary.get('seed_count')}`",
            f"- Selected configs: `{', '.join(str(item) for item in summary.get('selected_config_ids', []))}`",
            f"- Multi-config policy: `{summary.get('requires_multi_config_policy')}`",
            "",
            "## Selections",
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


def render_model_capability_required_term_pair_seed_config_selection_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready seeds", f"{summary.get('selection_ready_seed_count')}/{summary.get('seed_count')}"),
        ("Selected configs", summary.get("selected_config_count")),
        ("Multi-config", summary.get("requires_multi_config_policy")),
    ]
    config_rows = "\n".join(_config_html(row) for row in list_of_dicts(report.get("config_rows")))
    seed_rows = "\n".join(_seed_html(row) for row in list_of_dicts(report.get("selection_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair seed config selection</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair seed config selection</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Selections</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Selected config</th><th>Ready</th><th>Covering configs</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Configs</h2>
<div class="table-wrap"><table>
<thead><tr><th>Config</th><th>Selected seeds</th><th>Pair-full seeds</th><th>Source</th></tr></thead>
<tbody>{config_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_seed_config_selection_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SEED_CONFIG_SELECTION_JSON_FILENAME,
        "csv": root / PAIR_SEED_CONFIG_SELECTION_CSV_FILENAME,
        "text": root / PAIR_SEED_CONFIG_SELECTION_TEXT_FILENAME,
        "markdown": root / PAIR_SEED_CONFIG_SELECTION_MARKDOWN_FILENAME,
        "html": root / PAIR_SEED_CONFIG_SELECTION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_seed_config_selection_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_seed_config_selection_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_seed_config_selection_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_seed_config_selection_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _seed_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('selected_config_id'))}</td>"
        f"<td>{html_escape(row.get('selection_ready'))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in row.get('covering_config_ids', [])))}</td>"
        "</tr>"
    )


def _config_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('config_id'))}</td>"
        f"<td>{html_escape(row.get('selected_seed_count'))}</td>"
        f"<td>{html_escape(row.get('pair_full_seed_count'))}</td>"
        f"<td>{html_escape(row.get('source_path'))}</td>"
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
    "render_model_capability_required_term_pair_seed_config_selection_html",
    "render_model_capability_required_term_pair_seed_config_selection_markdown",
    "render_model_capability_required_term_pair_seed_config_selection_text",
    "write_model_capability_required_term_pair_seed_config_selection_outputs",
]
