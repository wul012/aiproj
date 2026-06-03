from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("comparison_ready", summary.get("rebalanced_checkpoint_comparison_ready")),
        ("baseline_passed_case_count", summary.get("baseline_passed_case_count")),
        ("prompt_aligned_passed_case_count", summary.get("prompt_aligned_passed_case_count")),
        ("decoder_anchor_passed_case_count", summary.get("decoder_anchor_passed_case_count")),
        ("rebalanced_passed_case_count", summary.get("rebalanced_passed_case_count")),
        ("rebalanced_vs_baseline_pass_rate_delta", summary.get("rebalanced_vs_baseline_pass_rate_delta")),
        ("rebalanced_vs_decoder_anchor_pass_rate_delta", summary.get("rebalanced_vs_decoder_anchor_pass_rate_delta")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["label", "status", "executed", "case_count", "passed_case_count", "failed_case_count", "pass_rate", "model_route_quality_ready"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("route_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced checkpoint comparison'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('rebalanced_checkpoint_comparison_ready')}`",
        f"- Rebalanced vs baseline delta: `{summary.get('rebalanced_vs_baseline_pass_rate_delta')}`",
        f"- Rebalanced vs decoder-anchor delta: `{summary.get('rebalanced_vs_decoder_anchor_pass_rate_delta')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Model-quality claim: `{interpretation.get('model_quality_claim')}`",
        "",
        "## Routes",
        "",
        "| Route | Passed | Cases | Pass rate | Ready |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("route_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("label")), markdown_cell(row.get("passed_case_count")), markdown_cell(row.get("case_count")), markdown_cell(row.get("pass_rate")), markdown_cell(row.get("model_route_quality_ready"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Baseline pass", summary.get("baseline_passed_case_count")),
        ("Rebalanced pass", summary.get("rebalanced_passed_case_count")),
        ("Delta baseline", summary.get("rebalanced_vs_baseline_pass_rate_delta")),
        ("Promotion", summary.get("promotion_ready")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_route_row(item) for item in list_of_dicts(report.get("route_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced checkpoint comparison'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced checkpoint comparison'))}</h1><p>Compares baseline, prompt-aligned, decoder-anchor, and rebalanced checkpoint replay before any promotion claim.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Routes</h2><div class="table-wrap"><table>
<thead><tr><th>Route</th><th>Passed</th><th>Cases</th><th>Pass rate</th><th>Ready</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _route_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('label'))}</td>"
        f"<td>{html_escape(row.get('passed_case_count'))}</td>"
        f"<td>{html_escape(row.get('case_count'))}</td>"
        f"<td>{html_escape(row.get('pass_rate'))}</td>"
        f"<td>{html_escape(row.get('model_route_quality_ready'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#667381;--line:#d8dee5;--panel:#f7f9fb;--accent:#7c2d12}
*{box-sizing:border-box}
body{margin:0;background:#f1f4f8;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1200px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_html",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_text",
    "write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_outputs",
]
