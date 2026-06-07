from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_ready", summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_ready")),
        ("packet_index_id", summary.get("packet_index_id")),
        ("consumer_name", summary.get("consumer_name")),
        ("lookup_scope", summary.get("lookup_scope")),
        ("granted_use", summary.get("granted_use")),
        ("lookup_ready", summary.get("lookup_ready")),
        ("contract_check_ready", summary.get("contract_check_ready")),
        ("packet_index_row_count", summary.get("packet_index_row_count")),
        ("source_evidence_count", summary.get("source_evidence_count")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "packet_index_id",
        "lookup_key",
        "packet_id",
        "packet_status",
        "consumer_name",
        "granted_use",
        "source_evidence_count",
        "contract_check_ready",
        "promotion_ready",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    index = as_dict(report.get("packet_index"))
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(index.get("packet_index_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    index = as_dict(report.get("packet_index"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Index ready: `{summary.get('randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_ready')}`",
        f"- Packet index: `{summary.get('packet_index_id')}`",
        f"- Consumer: `{summary.get('consumer_name')}`",
        f"- Lookup scope: `{summary.get('lookup_scope')}`",
        f"- Granted use: `{summary.get('granted_use')}`",
        f"- Lookup ready: `{summary.get('lookup_ready')}`",
        f"- Contract check ready: `{summary.get('contract_check_ready')}`",
        f"- Source evidence count: `{summary.get('source_evidence_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Source Artifacts",
        "",
        f"- Receipt packet: `{report.get('receipt_packet_path')}`",
        f"- Receipt packet check: `{report.get('receipt_packet_check_path')}`",
        "",
        "## Packet Index Rows",
        "",
        "| Index | Lookup key | Packet | Status | Consumer | Granted use | Evidence | Contract | Promotion |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(index.get("packet_index_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("packet_index_id")), markdown_cell(row.get("lookup_key")), markdown_cell(row.get("packet_id")), markdown_cell(row.get("packet_status")), markdown_cell(row.get("consumer_name")), markdown_cell(row.get("granted_use")), markdown_cell(row.get("source_evidence_count")), markdown_cell(row.get("contract_check_ready")), markdown_cell(row.get("promotion_ready"))]) + " |")
    lines.extend(["", "## Source Evidence", "", "| Kind | Path | SHA-256 | Status | Decision | Failed |", "| --- | --- | --- | --- | --- | --- |"])
    for row in list_of_dicts(index.get("source_evidence_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("kind")), markdown_cell(row.get("path")), markdown_cell(row.get("sha256")), markdown_cell(row.get("status")), markdown_cell(row.get("decision")), markdown_cell(row.get("failed_count"))]) + " |")
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    index = as_dict(report.get("packet_index"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Index ready", summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_ready")),
        ("Lookup", summary.get("lookup_ready")),
        ("Contract", summary.get("contract_check_ready")),
        ("Evidence", summary.get("source_evidence_count")),
        ("Failed", report.get("failed_count")),
    ]
    packet_rows = "".join(_packet_index_row(row) for row in list_of_dicts(index.get("packet_index_rows")))
    evidence_rows = "".join(_evidence_row(row) for row in list_of_dicts(index.get("source_evidence_rows")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Lookup Boundary</h2><dl>
<dt>Packet index</dt><dd>{html_escape(summary.get('packet_index_id'))}</dd>
<dt>Lookup scope</dt><dd>{html_escape(summary.get('lookup_scope'))}</dd>
<dt>Granted use</dt><dd>{html_escape(summary.get('granted_use'))}</dd>
<dt>Source packet</dt><dd>{html_escape(report.get('receipt_packet_path'))}</dd>
<dt>Source packet check</dt><dd>{html_escape(report.get('receipt_packet_check_path'))}</dd>
<dt>Next step</dt><dd>{html_escape(summary.get('next_step'))}</dd>
</dl></section>
<section class="panel"><h2>Packet Index Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Index</th><th>Lookup key</th><th>Packet</th><th>Status</th><th>Consumer</th><th>Granted use</th><th>Evidence</th><th>Contract</th><th>Promotion</th></tr></thead>
<tbody>{packet_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Source Evidence</h2><div class="table-wrap"><table>
<thead><tr><th>Kind</th><th>Path</th><th>SHA-256</th><th>Status</th><th>Decision</th><th>Failed</th></tr></thead>
<tbody>{evidence_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _packet_index_row(row: dict[str, Any]) -> str:
    keys = ["packet_index_id", "lookup_key", "packet_id", "packet_status", "consumer_name", "granted_use", "source_evidence_count", "contract_check_ready", "promotion_ready"]
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in keys) + "</tr>"


def _evidence_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["kind", "path", "sha256", "status", "decision", "failed_count"]) + "</tr>"


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
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_html",
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_markdown",
    "render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_text",
    "write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_outputs",
]
