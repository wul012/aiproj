from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_ready", summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_ready")),
        ("receipt_id", summary.get("receipt_id")),
        ("receipt_status", summary.get("receipt_status")),
        ("consumer_name", summary.get("consumer_name")),
        ("granted_use", summary.get("granted_use")),
        ("publication_index_row_count", summary.get("publication_index_row_count")),
        ("lookup_key_count", summary.get("lookup_key_count")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("blocked_uses", summary.get("blocked_uses")),
        ("next_step", summary.get("next_step")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["consumer_name", "lookup_key", "publication_id", "granted_use", "blocked_uses", "promotion_ready", "receipt_status"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("consumer_receipts")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Receipt ready: `{summary.get('randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_ready')}`",
        f"- Receipt status: `{summary.get('receipt_status')}`",
        f"- Consumer: `{summary.get('consumer_name')}`",
        f"- Granted use: `{summary.get('granted_use')}`",
        f"- Publication index rows: `{summary.get('publication_index_row_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Index review digest: `{report.get('index_review_sha256')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Consumer Receipts",
        "",
        "| Consumer | Lookup key | Publication | Granted use | Blocked uses | Promotion | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("consumer_receipts")):
        lines.append("| " + " | ".join([markdown_cell(row.get("consumer_name")), markdown_cell(row.get("lookup_key")), markdown_cell(row.get("publication_id")), markdown_cell(row.get("granted_use")), markdown_cell(row.get("blocked_uses")), markdown_cell(row.get("promotion_ready")), markdown_cell(row.get("receipt_status"))]) + " |")
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Receipt ready", summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_ready")),
        ("Consumer", summary.get("consumer_name")),
        ("Granted use", summary.get("granted_use")),
        ("Promotion", summary.get("promotion_ready")),
        ("Failed", report.get("failed_count")),
    ]
    receipts = "".join(_receipt_row(row) for row in list_of_dicts(report.get("consumer_receipts")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Receipt Boundary</h2><dl>
<dt>Blocked uses</dt><dd>{html_escape(summary.get('blocked_uses'))}</dd>
<dt>Index review digest</dt><dd>{html_escape(report.get('index_review_sha256'))}</dd>
<dt>Index review path</dt><dd>{html_escape(report.get('index_review_path'))}</dd>
<dt>Next step</dt><dd>{html_escape(summary.get('next_step'))}</dd>
</dl></section>
<section class="panel"><h2>Consumer Receipts</h2><div class="table-wrap"><table>
<thead><tr><th>Consumer</th><th>Lookup key</th><th>Publication</th><th>Granted use</th><th>Blocked uses</th><th>Promotion</th><th>Status</th></tr></thead>
<tbody>{receipts}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _receipt_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["consumer_name", "lookup_key", "publication_id", "granted_use", "blocked_uses", "promotion_ready", "receipt_status"]) + "</tr>"


def _check_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef1f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1160px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:16px;line-height:1.25;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
dl{display:grid;grid-template-columns:minmax(150px,220px) 1fr;gap:8px 16px;margin:0;font-size:14px}
dt{color:#334155;font-weight:700}
dd{margin:0;overflow-wrap:anywhere}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_html",
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_markdown",
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_text",
    "write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_outputs",
]
