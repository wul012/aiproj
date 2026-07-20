from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_readiness_receipt_index import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_model_capability_route_promotion_release_readiness_receipt_index_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("receipt_index_ready", summary.get("receipt_index_ready")),
        ("index_id", summary.get("index_id")),
        ("lookup_scope", summary.get("lookup_scope")),
        ("entry_count", summary.get("entry_count")),
        ("lookup_key_count", summary.get("lookup_key_count")),
        ("lookup_ready", summary.get("lookup_ready")),
        ("consumer_name", summary.get("consumer_name")),
        ("route_id", summary.get("route_id")),
        ("granted_scope", summary.get("granted_scope")),
        ("source_digest_count", summary.get("source_digest_count")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_release_readiness_receipt_index_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "index_id",
        "lookup_key",
        "entry_id",
        "consumer_name",
        "route_id",
        "granted_scope",
        "boundary",
        "model_quality_claim",
        "source_check_digest",
        "downstream_receipt_digest",
        "source_digest_count",
        "promotion_ready",
        "lookup_ready",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    index = as_dict(report.get("receipt_index"))
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(index.get("index_rows")):
            writer.writerow(
                {
                    "index_id": csv_cell(index.get("index_id")),
                    "lookup_key": csv_cell(row.get("lookup_key")),
                    "entry_id": csv_cell(row.get("entry_id")),
                    "consumer_name": csv_cell(row.get("consumer_name")),
                    "route_id": csv_cell(row.get("route_id")),
                    "granted_scope": csv_cell(row.get("granted_scope")),
                    "boundary": csv_cell(row.get("boundary")),
                    "model_quality_claim": csv_cell(row.get("model_quality_claim")),
                    "source_check_digest": csv_cell(row.get("source_check_digest")),
                    "downstream_receipt_digest": csv_cell(row.get("downstream_receipt_digest")),
                    "source_digest_count": csv_cell(row.get("source_digest_count")),
                    "promotion_ready": csv_cell(row.get("promotion_ready")),
                    "lookup_ready": csv_cell(row.get("lookup_ready")),
                }
            )


def render_model_capability_route_promotion_release_readiness_receipt_index_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    index = as_dict(report.get("receipt_index"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion release readiness receipt index'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Index ready: `{summary.get('receipt_index_ready')}`",
        f"- Index id: `{summary.get('index_id')}`",
        f"- Lookup scope: `{summary.get('lookup_scope')}`",
        f"- Entry count: `{summary.get('entry_count')}`",
        f"- Lookup ready: `{summary.get('lookup_ready')}`",
        f"- Route: `{summary.get('route_id')}`",
        f"- Consumer: `{summary.get('consumer_name')}`",
        f"- Granted scope: `{summary.get('granted_scope')}`",
        f"- Source digest count: `{summary.get('source_digest_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Source Evidence",
        "",
        f"- Downstream receipt: `{report.get('downstream_receipt_path')}`",
        f"- Downstream receipt digest: `{report.get('downstream_receipt_digest')}`",
        "",
        "## Lookup Rows",
        "",
        "| Index | Lookup key | Entry | Consumer | Route | Scope | Claim | Receipt digest | Promotion |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(index.get("index_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(index.get("index_id")),
                    markdown_cell(row.get("lookup_key")),
                    markdown_cell(row.get("entry_id")),
                    markdown_cell(row.get("consumer_name")),
                    markdown_cell(row.get("route_id")),
                    markdown_cell(row.get("granted_scope")),
                    markdown_cell(row.get("model_quality_claim")),
                    markdown_cell(row.get("downstream_receipt_digest")),
                    markdown_cell(row.get("promotion_ready")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_release_readiness_receipt_index_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    index = as_dict(report.get("receipt_index"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Index ready", summary.get("receipt_index_ready")),
        ("Entries", summary.get("entry_count")),
        ("Lookup", summary.get("lookup_ready")),
        ("Route", summary.get("route_id")),
        ("Promotion", summary.get("promotion_ready")),
    ]
    rows = "".join(_lookup_row(index, row) for row in list_of_dicts(index.get("index_rows")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion release readiness receipt index'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion release readiness receipt index'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Lookup Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Index</th><th>Lookup key</th><th>Entry</th><th>Consumer</th><th>Route</th><th>Scope</th><th>Claim</th><th>Receipt digest</th><th>Promotion</th></tr></thead>
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


def write_model_capability_route_promotion_release_readiness_receipt_index_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_release_readiness_receipt_index_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_release_readiness_receipt_index_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_release_readiness_receipt_index_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_release_readiness_receipt_index_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _lookup_row(index: dict[str, Any], row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(index.get('index_id'))}</td>"
        f"<td>{html_escape(row.get('lookup_key'))}</td>"
        f"<td>{html_escape(row.get('entry_id'))}</td>"
        f"<td>{html_escape(row.get('consumer_name'))}</td>"
        f"<td>{html_escape(row.get('route_id'))}</td>"
        f"<td>{html_escape(row.get('granted_scope'))}</td>"
        f"<td>{html_escape(row.get('model_quality_claim'))}</td>"
        f"<td>{html_escape(row.get('downstream_receipt_digest'))}</td>"
        f"<td>{html_escape(row.get('promotion_ready'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#64717d;--line:#d8dee4;--panel:#f8fafc;--accent:#166534}
*{box-sizing:border-box}
body{margin:0;background:#eef3f1;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_route_promotion_release_readiness_receipt_index_html",
    "render_model_capability_route_promotion_release_readiness_receipt_index_markdown",
    "render_model_capability_route_promotion_release_readiness_receipt_index_text",
    "write_model_capability_route_promotion_release_readiness_receipt_index_outputs",
]
