from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe import (
    TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_CSV_FILENAME,
    TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_HTML_FILENAME,
    TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME,
    TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_loss_token_probability_probe_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("loss_token_probability_probe_ready", summary.get("bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_ready")),
        ("target_top1_rate", summary.get("target_top1_rate")),
        ("target_topk_rate", summary.get("target_topk_rate")),
        ("min_target_probability", summary.get("min_target_probability")),
        ("mean_target_probability", summary.get("mean_target_probability")),
        ("max_target_rank", summary.get("max_target_rank")),
        ("low_probability_step_count", summary.get("low_probability_step_count")),
        ("all_cases_loss_suffix_top1", summary.get("all_cases_loss_suffix_top1")),
        ("all_cases_loss_suffix_topk", summary.get("all_cases_loss_suffix_topk")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_loss_token_probability_probe_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory loss-token probability probe'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Target top-1 rate: `{summary.get('target_top1_rate')}`",
        f"- Target top-k rate: `{summary.get('target_topk_rate')}`",
        f"- Min target probability: `{summary.get('min_target_probability')}`",
        f"- Mean target probability: `{summary.get('mean_target_probability')}`",
        f"- Max target rank: `{summary.get('max_target_rank')}`",
        f"- Low-probability steps: `{summary.get('low_probability_step_count')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Probe Steps",
        "",
        "| Case | Step | Target | Probability | Rank | Top token | State |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("probe_rows")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("case_id")),
            markdown_cell(row.get("step_index")),
            markdown_cell(row.get("target_token")),
            markdown_cell(row.get("target_probability")),
            markdown_cell(row.get("target_rank")),
            markdown_cell(row.get("top_token")),
            markdown_cell(row.get("state_label")),
        ]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_loss_token_probability_probe_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Top-1 rate", summary.get("target_top1_rate")),
        ("Top-k rate", summary.get("target_topk_rate")),
        ("Min probability", summary.get("min_target_probability")),
        ("Mean probability", summary.get("mean_target_probability")),
        ("Max rank", summary.get("max_target_rank")),
        ("Low-prob steps", summary.get("low_probability_step_count")),
        ("All suffix top-1", summary.get("all_cases_loss_suffix_top1")),
        ("All suffix top-k", summary.get("all_cases_loss_suffix_topk")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    probe_rows = "".join(_probe_row(row) for row in list_of_dicts(report.get("probe_rows")))
    case_rows = "".join(_case_row(row) for row in list_of_dicts(report.get("case_rows")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory loss-token probability probe'))}</title>{_style()}</head>
<body><main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory loss-token probability probe'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Summary</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>Suffix</th><th>Product</th><th>Min probability</th><th>Max rank</th><th>Top-k steps</th></tr></thead><tbody>{case_rows}</tbody></table></div></section>
<section class="panel"><h2>Probe Steps</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>Step</th><th>Target</th><th>Probability</th><th>Rank</th><th>Top token</th><th>State</th></tr></thead><tbody>{probe_rows}</tbody></table></div></section>
</main></body></html>"""


def write_loss_token_probability_probe_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_loss_token_probability_probe_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_loss_token_probability_probe_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_loss_token_probability_probe_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = [
        "case_id",
        "step_index",
        "target_token",
        "target_probability",
        "target_rank",
        "target_in_top_k",
        "top_token",
        "top_token_probability",
        "state_label",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("probe_rows")):
            writer.writerow({key: csv_cell(row.get(key)) for key in fieldnames})


def _probe_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('step_index'))}</td>"
        f"<td>{html_escape(row.get('target_token'))}</td>"
        f"<td>{html_escape(row.get('target_probability'))}</td>"
        f"<td>{html_escape(row.get('target_rank'))}</td>"
        f"<td>{html_escape(row.get('top_token'))}</td>"
        f"<td>{html_escape(row.get('state_label'))}</td>"
        "</tr>"
    )


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('target_suffix'))}</td>"
        f"<td>{html_escape(row.get('target_probability_product'))}</td>"
        f"<td>{html_escape(row.get('min_target_probability'))}</td>"
        f"<td>{html_escape(row.get('max_target_rank'))}</td>"
        f"<td>{html_escape(row.get('topk_step_count'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172033;--muted:#5f7186;--line:#d7dee8;--panel:#f8fafc;--accent:#7c2d12}
*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1280px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:17px;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere;white-space:pre-wrap}
</style>"""


__all__ = [
    "render_loss_token_probability_probe_html",
    "render_loss_token_probability_probe_markdown",
    "render_loss_token_probability_probe_text",
    "write_loss_token_probability_probe_outputs",
]
