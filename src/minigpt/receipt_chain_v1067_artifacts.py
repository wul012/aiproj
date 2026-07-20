from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.receipt_chain_v1067 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_TEXT_FILENAME,
    READY_KEY,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("receipt_ready", summary.get(READY_KEY)),
        ("receipt_status", summary.get("receipt_status")),
        ("consumer_name", summary.get("consumer_name")),
        ("granted_use", summary.get("granted_use")),
        ("receipt_index_row_count", summary.get("receipt_index_row_count")),
        ("source_evidence_count", summary.get("source_evidence_count")),
        ("lookup_key_count", summary.get("lookup_key_count")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["consumer_name", "lookup_key", "receipt_index_id", "source_receipt_id", "receipt_id", "granted_use", "promotion_ready", "receipt_status"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("consumer_receipts")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    receipt = as_dict(report.get("receipt"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt v1067'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Receipt ready: `{summary.get(READY_KEY)}`",
        f"- Receipt status: `{summary.get('receipt_status')}`",
        f"- Consumer: `{summary.get('consumer_name')}`",
        f"- Granted use: `{summary.get('granted_use')}`",
        f"- Lookup keys: `{summary.get('lookup_key_count')}`",
        f"- Source evidence: `{summary.get('source_evidence_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Receipt Boundary",
        "",
        f"- Source review: `{receipt.get('receipt_index_review_path')}`",
        f"- Source receipt index: `{receipt.get('source_receipt_index_path')}`",
        f"- Source receipt: `{receipt.get('source_receipt_path')}`",
        f"- Source receipt check: `{receipt.get('source_receipt_check_path')}`",
        f"- Source origin review: `{receipt.get('source_review_path')}`",
        f"- Source origin receipt index: `{receipt.get('source_receipt_index_origin_path')}`",
        "",
        "## Consumer Receipts",
        "",
        "| Consumer | Lookup key | Receipt index | Source receipt | Receipt | Granted use | Promotion | Status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("consumer_receipts")):
        lines.append("| " + " | ".join([markdown_cell(row.get("consumer_name")), markdown_cell(row.get("lookup_key")), markdown_cell(row.get("receipt_index_id")), markdown_cell(row.get("source_receipt_id")), markdown_cell(row.get("receipt_id")), markdown_cell(row.get("granted_use")), markdown_cell(row.get("promotion_ready")), markdown_cell(row.get("receipt_status"))]) + " |")
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    receipt = as_dict(report.get("receipt"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Receipt ready", summary.get(READY_KEY)),
        ("Lookup keys", summary.get("lookup_key_count")),
        ("Evidence", summary.get("source_evidence_count")),
        ("Use", summary.get("granted_use")),
        ("Failed", report.get("failed_count")),
    ]
    consumer_rows = "".join(_consumer_row(row) for row in list_of_dicts(report.get("consumer_receipts")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,"><title>{html_escape(report.get('title'))}</title>{_style()}</head>
<body><main>
<header><h1>{html_escape(report.get('title'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Receipt Boundary</h2><dl>{_term('Receipt status', summary.get('receipt_status'))}{_term('Consumer', summary.get('consumer_name'))}{_term('Source review', receipt.get('receipt_index_review_path'))}{_term('Source receipt index', receipt.get('source_receipt_index_path'))}{_term('Source receipt', receipt.get('source_receipt_path'))}{_term('Source check', receipt.get('source_receipt_check_path'))}{_term('Source origin review', receipt.get('source_review_path'))}{_term('Source origin index', receipt.get('source_receipt_index_origin_path'))}{_term('Next step', summary.get('next_step'))}</dl></section>
<section class="panel"><h2>Consumer Receipts</h2><div class="table-wrap"><table><thead><tr><th>Consumer</th><th>Lookup key</th><th>Receipt index</th><th>Source receipt</th><th>Receipt</th><th>Use</th><th>Promotion</th><th>Status</th></tr></thead><tbody>{consumer_rows}</tbody></table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table><thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead><tbody>{checks}</tbody></table></div></section>
</main></body></html>
"""


def write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1067_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _consumer_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["consumer_name", "lookup_key", "receipt_index_id", "source_receipt_id", "receipt_id", "granted_use", "promotion_ready", "receipt_status"]) + "</tr>"


def _check_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _term(label: str, value: Any) -> str:
    return f"<dt>{html_escape(label)}</dt><dd>{html_escape(value)}</dd>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}main{max-width:1120px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}.card strong{display:block;margin-top:6px;font-size:16px;line-height:1.25;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}dl{display:grid;grid-template-columns:minmax(150px,220px) 1fr;gap:8px 16px;margin:0;font-size:14px}dt{color:#334155;font-weight:700}dd{margin:0;overflow-wrap:anywhere}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_html",
    "render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_markdown",
    "render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_text",
    "write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_outputs",
]
