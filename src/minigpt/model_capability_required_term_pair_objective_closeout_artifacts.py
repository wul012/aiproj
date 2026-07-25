from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_objective_closeout import (
    PAIR_OBJECTIVE_CLOSEOUT_CSV_FILENAME,
    PAIR_OBJECTIVE_CLOSEOUT_HTML_FILENAME,
    PAIR_OBJECTIVE_CLOSEOUT_JSON_FILENAME,
    PAIR_OBJECTIVE_CLOSEOUT_MARKDOWN_FILENAME,
    PAIR_OBJECTIVE_CLOSEOUT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, html_escape, list_of_dicts, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import evidence_html as _evidence_html
from minigpt.report_utils import evidence_markdown_rows as _evidence_markdown_rows
from minigpt.report_utils import write_csv_rows_decision as _write_csv


def render_model_capability_required_term_pair_objective_closeout_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("branch_binding_stopped", summary.get("branch_binding_stopped")),
        ("target_anchor_residual_only", summary.get("target_anchor_residual_only")),
        ("loss_branch_required", summary.get("loss_branch_required")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_model_capability_required_term_pair_objective_closeout_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Objective Closeout",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Branch-binding stopped: `{summary.get('branch_binding_stopped')}`",
            f"- Target-anchor residual only: `{summary.get('target_anchor_residual_only')}`",
            f"- Loss branch required: `{summary.get('loss_branch_required')}`",
            "",
            "## Evidence",
            "",
            *_evidence_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_objective_closeout_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Branch stopped", summary.get("branch_binding_stopped")),
        ("Target residual", summary.get("target_anchor_residual_only")),
        ("Loss required", summary.get("loss_branch_required")),
    ]
    rows = "\n".join(_evidence_html(row) for row in list_of_dicts(report.get("evidence_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT objective closeout</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT objective closeout</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Evidence Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Label</th><th>Status</th><th>Decision</th><th>Key result</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_objective_closeout_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_OBJECTIVE_CLOSEOUT_JSON_FILENAME,
        "csv": root / PAIR_OBJECTIVE_CLOSEOUT_CSV_FILENAME,
        "text": root / PAIR_OBJECTIVE_CLOSEOUT_TEXT_FILENAME,
        "markdown": root / PAIR_OBJECTIVE_CLOSEOUT_MARKDOWN_FILENAME,
        "html": root / PAIR_OBJECTIVE_CLOSEOUT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_objective_closeout_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_objective_closeout_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_objective_closeout_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#18212b;--muted:#607080;--line:#d7dee6;--panel:#f6f8fb;--accent:#314c5f}
*{box-sizing:border-box}
body{margin:0;background:#eef3f6;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
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
    "render_model_capability_required_term_pair_objective_closeout_html",
    "render_model_capability_required_term_pair_objective_closeout_markdown",
    "render_model_capability_required_term_pair_objective_closeout_text",
    "write_model_capability_required_term_pair_objective_closeout_outputs",
]
