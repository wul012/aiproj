from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.receipt_chain_review_v1038 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_TEXT_FILENAME,
    READY_KEY,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("review_ready", summary.get(READY_KEY)),
        ("review_status", summary.get("review_status")),
        ("receipt_index_row_count", summary.get("receipt_index_row_count")),
        ("lookup_key_count", summary.get("lookup_key_count")),
        ("source_evidence_count", summary.get("source_evidence_count")),
        ("lookup_ready", summary.get("lookup_ready")),
        ("contract_check_ready", summary.get("contract_check_ready")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "actual", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    review = as_dict(report.get("review"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index review v1038'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Review ready: `{summary.get(READY_KEY)}`",
        f"- Review status: `{summary.get('review_status')}`",
        f"- Receipt index rows: `{summary.get('receipt_index_row_count')}`",
        f"- Lookup keys: `{summary.get('lookup_key_count')}`",
        f"- Source evidence: `{summary.get('source_evidence_count')}`",
        f"- Lookup ready: `{summary.get('lookup_ready')}`",
        f"- Contract check ready: `{summary.get('contract_check_ready')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Review Summary",
        "",
        f"- Receipt index path: `{review.get('receipt_index_path')}`",
        f"- Source receipt: `{review.get('source_receipt_path')}`",
        f"- Source receipt check: `{review.get('source_receipt_check_path')}`",
        f"- Source review: `{review.get('source_review_path')}`",
        f"- Source receipt index: `{review.get('source_receipt_index_path')}`",
        "",
        "## Receipt Index Rows",
        "",
        "| Lookup key | Receipt | Status | Use | Contract | Promotion |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("receipt_index_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("lookup_key")), markdown_cell(row.get("receipt_id")), markdown_cell(row.get("receipt_status")), markdown_cell(row.get("granted_use")), markdown_cell(row.get("contract_check_ready")), markdown_cell(row.get("promotion_ready"))]) + " |")
    lines.extend(["", "## Source Evidence", "", "| Kind | Path | SHA-256 | Status |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("source_evidence_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("kind")), markdown_cell(row.get("path")), markdown_cell(row.get("sha256")), markdown_cell(row.get("status"))]) + " |")
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    review = as_dict(report.get("review"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Review ready", summary.get(READY_KEY)),
        ("Rows", summary.get("receipt_index_row_count")),
        ("Lookup keys", summary.get("lookup_key_count")),
        ("Evidence", summary.get("source_evidence_count")),
        ("Failed", report.get("failed_count")),
    ]
    index_rows = "".join(_receipt_index_row(row) for row in list_of_dicts(report.get("receipt_index_rows")))
    evidence_rows = "".join(_evidence_row(row) for row in list_of_dicts(report.get("source_evidence_rows")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,"><title>{html_escape(report.get('title'))}</title>{_style()}</head>
<body><main>
<header><h1>{html_escape(report.get('title'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Review Summary</h2><dl>{_term('Review status', summary.get('review_status'))}{_term('Receipt index path', review.get('receipt_index_path'))}{_term('Source receipt', review.get('source_receipt_path'))}{_term('Source receipt check', review.get('source_receipt_check_path'))}{_term('Source review', review.get('source_review_path'))}{_term('Source receipt index', review.get('source_receipt_index_path'))}{_term('Next step', summary.get('next_step'))}</dl></section>
<section class="panel"><h2>Receipt Index Rows</h2><div class="table-wrap"><table><thead><tr><th>Lookup key</th><th>Receipt</th><th>Status</th><th>Use</th><th>Contract</th><th>Promotion</th></tr></thead><tbody>{index_rows}</tbody></table></div></section>
<section class="panel"><h2>Source Evidence</h2><div class="table-wrap"><table><thead><tr><th>Kind</th><th>Path</th><th>SHA-256</th><th>Status</th></tr></thead><tbody>{evidence_rows}</tbody></table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table><thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead><tbody>{checks}</tbody></table></div></section>
</main></body></html>
"""


def write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1038_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _receipt_index_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["lookup_key", "receipt_id", "receipt_status", "granted_use", "contract_check_ready", "promotion_ready"]) + "</tr>"


def _evidence_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["kind", "path", "sha256", "status"]) + "</tr>"


def _check_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _term(label: str, value: Any) -> str:
    return f"<dt>{html_escape(label)}</dt><dd>{html_escape(value)}</dd>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}main{max-width:1120px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}.card strong{display:block;margin-top:6px;font-size:16px;line-height:1.25;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere}dl{display:grid;grid-template-columns:minmax(160px,220px)1fr;gap:8px 12px;margin:0}dt{color:var(--muted);font-weight:700}dd{margin:0;overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_html",
    "render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_markdown",
    "render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_text",
    "write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_outputs",
]
