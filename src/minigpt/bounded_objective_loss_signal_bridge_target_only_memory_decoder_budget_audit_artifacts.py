from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_CSV_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_HTML_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_decoder_budget_audit_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("decoder_budget_audit_ready", summary.get("bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_ready")),
        ("budget_exhausted_case_count", summary.get("budget_exhausted_case_count")),
        ("loss_suffix_top1_case_count", summary.get("loss_suffix_top1_case_count")),
        ("recommended_max_new_tokens", summary.get("recommended_max_new_tokens")),
        ("max_additional_tokens_needed", summary.get("max_additional_tokens_needed")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_decoder_budget_audit_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory decoder budget audit'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Budget exhausted cases: `{summary.get('budget_exhausted_case_count')}`",
        f"- Loss suffix top-1 cases: `{summary.get('loss_suffix_top1_case_count')}`",
        f"- Recommended max new tokens: `{summary.get('recommended_max_new_tokens')}`",
        f"- Max additional tokens needed: `{summary.get('max_additional_tokens_needed')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Case Budget Rows",
        "",
        "| Case | Continuation tokens | Max new | Remaining | Suffix | Suffix tokens | Needed max | State |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_rows")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("case_id")),
            markdown_cell(row.get("continuation_token_count")),
            markdown_cell(row.get("max_new_tokens")),
            markdown_cell(row.get("remaining_budget")),
            markdown_cell(row.get("target_suffix")),
            markdown_cell(row.get("target_suffix_token_count")),
            markdown_cell(row.get("needed_max_new_tokens")),
            markdown_cell(row.get("state_label")),
        ]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_decoder_budget_audit_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Budget exhausted", summary.get("budget_exhausted_case_count")),
        ("Suffix top-1", summary.get("loss_suffix_top1_case_count")),
        ("Recommended max", summary.get("recommended_max_new_tokens")),
        ("Additional needed", summary.get("max_additional_tokens_needed")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_case_row(row) for row in list_of_dicts(report.get("case_rows")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory decoder budget audit'))}</title>{_style()}</head>
<body><main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory decoder budget audit'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Budget Rows</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>Continuation tokens</th><th>Max new</th><th>Remaining</th><th>Suffix</th><th>Suffix tokens</th><th>Needed max</th><th>State</th></tr></thead><tbody>{rows}</tbody></table></div></section>
</main></body></html>"""


def write_decoder_budget_audit_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_decoder_budget_audit_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_decoder_budget_audit_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_decoder_budget_audit_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = [
        "case_id",
        "continuation_token_count",
        "max_new_tokens",
        "remaining_budget",
        "target_suffix",
        "target_suffix_token_count",
        "needed_max_new_tokens",
        "additional_tokens_needed",
        "loss_suffix_top1",
        "state_label",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_rows")):
            writer.writerow({key: csv_cell(row.get(key)) for key in fieldnames})


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('continuation_token_count'))}</td>"
        f"<td>{html_escape(row.get('max_new_tokens'))}</td>"
        f"<td>{html_escape(row.get('remaining_budget'))}</td>"
        f"<td>{html_escape(row.get('target_suffix'))}</td>"
        f"<td>{html_escape(row.get('target_suffix_token_count'))}</td>"
        f"<td>{html_escape(row.get('needed_max_new_tokens'))}</td>"
        f"<td>{html_escape(row.get('state_label'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172033;--muted:#607184;--line:#d7dee8;--panel:#f8fafc;--accent:#7f1d1d}
*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1260px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere;white-space:pre-wrap}
</style>"""


__all__ = [
    "render_decoder_budget_audit_html",
    "render_decoder_budget_audit_markdown",
    "render_decoder_budget_audit_text",
    "write_decoder_budget_audit_outputs",
]
