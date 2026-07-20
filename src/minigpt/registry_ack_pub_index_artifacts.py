from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.registry_ack_pub_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_ready", summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_ready")),
        ("publication_index_id", summary.get("publication_index_id")),
        ("lookup_scope", summary.get("lookup_scope")),
        ("published_use", summary.get("published_use")),
        ("publication_index_row_count", summary.get("publication_index_row_count")),
        ("lookup_ready", summary.get("lookup_ready")),
        ("contract_check_ready", summary.get("contract_check_ready")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["publication_index_id", "lookup_key", "publication_id", "publication_status", "consumer_name", "published_use", "receipt_packet_index_row_count", "source_packet_row_count", "contract_check_ready", "promotion_ready"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    index = as_dict(report.get("publication_index"))
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(index.get("publication_index_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    index = as_dict(report.get("publication_index"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Index ready: `{summary.get('randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_ready')}`",
        f"- Publication index: `{summary.get('publication_index_id')}`",
        f"- Lookup scope: `{summary.get('lookup_scope')}`",
        f"- Published use: `{summary.get('published_use')}`",
        f"- Rows: `{summary.get('publication_index_row_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Source",
        "",
        f"- Publication: `{report.get('publication_path')}`",
        f"- Publication check: `{report.get('publication_check_path')}`",
        f"- Source review: `{index.get('source_review_path')}`",
        f"- Source index: `{index.get('source_index_path')}`",
        "",
        "## Publication Index Rows",
        "",
        "| Index | Lookup key | Publication | Status | Use | Contract | Promotion |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(index.get("publication_index_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("publication_index_id")), markdown_cell(row.get("lookup_key")), markdown_cell(row.get("publication_id")), markdown_cell(row.get("publication_status")), markdown_cell(row.get("published_use")), markdown_cell(row.get("contract_check_ready")), markdown_cell(row.get("promotion_ready"))]) + " |")
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    index = as_dict(report.get("publication_index"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Index ready", summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_ready")),
        ("Lookup", summary.get("lookup_ready")),
        ("Contract", summary.get("contract_check_ready")),
        ("Rows", summary.get("publication_index_row_count")),
        ("Failed", report.get("failed_count")),
    ]
    rows = "".join(_index_row(row) for row in list_of_dicts(index.get("publication_index_rows")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Lookup Boundary</h2><dl>
<dt>Publication index</dt><dd>{html_escape(summary.get('publication_index_id'))}</dd>
<dt>Lookup scope</dt><dd>{html_escape(summary.get('lookup_scope'))}</dd>
<dt>Publication</dt><dd>{html_escape(report.get('publication_path'))}</dd>
<dt>Publication check</dt><dd>{html_escape(report.get('publication_check_path'))}</dd>
<dt>Next step</dt><dd>{html_escape(summary.get('next_step'))}</dd>
</dl></section>
<section class="panel"><h2>Publication Index Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Index</th><th>Lookup key</th><th>Publication</th><th>Status</th><th>Use</th><th>Contract</th><th>Promotion</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _index_row(row: dict[str, Any]) -> str:
    keys = ["publication_index_id", "lookup_key", "publication_id", "publication_status", "published_use", "contract_check_ready", "promotion_ready"]
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in keys) + "</tr>"


def _check_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef1f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
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
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_html",
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_markdown",
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_text",
    "write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_outputs",
]
