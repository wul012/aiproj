from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_fresh_seed_route_decision import (
    PAIR_FRESH_SEED_ROUTE_DECISION_CSV_FILENAME,
    PAIR_FRESH_SEED_ROUTE_DECISION_HTML_FILENAME,
    PAIR_FRESH_SEED_ROUTE_DECISION_JSON_FILENAME,
    PAIR_FRESH_SEED_ROUTE_DECISION_MARKDOWN_FILENAME,
    PAIR_FRESH_SEED_ROUTE_DECISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, html_escape, list_of_dicts, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import route_html as _route_html
from minigpt.report_utils import route_markdown_rows as _route_markdown_rows
from minigpt.report_utils import write_csv_rows_hit_terms as _write_csv


def render_model_capability_required_term_pair_fresh_seed_route_decision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("route_count", summary.get("route_count")),
        ("pair_full_route_count", summary.get("pair_full_route_count")),
        ("best_residual_signal", summary.get("best_residual_signal")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_model_capability_required_term_pair_fresh_seed_route_decision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Fresh-Seed Route Decision",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Routes: `{summary.get('route_count')}`",
            f"- Pair-full routes: `{summary.get('pair_full_route_count')}`",
            f"- Best residual signal: `{summary.get('best_residual_signal')}`",
            "",
            "## Route Rows",
            "",
            *_route_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_fresh_seed_route_decision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Routes", summary.get("route_count")),
        ("Pair-full routes", summary.get("pair_full_route_count")),
        ("Best residual", summary.get("best_residual_signal")),
    ]
    rows = "\n".join(_route_html(row) for row in list_of_dicts(report.get("route_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT fresh-seed route decision</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT fresh-seed route decision</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Route Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Type</th><th>Pair-full</th><th>Hit terms</th><th>Reasons</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_fresh_seed_route_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_FRESH_SEED_ROUTE_DECISION_JSON_FILENAME,
        "csv": root / PAIR_FRESH_SEED_ROUTE_DECISION_CSV_FILENAME,
        "text": root / PAIR_FRESH_SEED_ROUTE_DECISION_TEXT_FILENAME,
        "markdown": root / PAIR_FRESH_SEED_ROUTE_DECISION_MARKDOWN_FILENAME,
        "html": root / PAIR_FRESH_SEED_ROUTE_DECISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_fresh_seed_route_decision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_fresh_seed_route_decision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_fresh_seed_route_decision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#7c2d12}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_required_term_pair_fresh_seed_route_decision_html",
    "render_model_capability_required_term_pair_fresh_seed_route_decision_markdown",
    "render_model_capability_required_term_pair_fresh_seed_route_decision_text",
    "write_model_capability_required_term_pair_fresh_seed_route_decision_outputs",
]
