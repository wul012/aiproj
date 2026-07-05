from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_route_promotion_release_readiness_downstream_receipt_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("downstream_receipt_ready", summary.get("downstream_receipt_ready")),
        ("receipt_status", summary.get("receipt_status")),
        ("consumer_name", summary.get("consumer_name")),
        ("route_id", summary.get("route_id")),
        ("granted_scope", summary.get("granted_scope")),
        ("boundary", summary.get("boundary")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("source_digest_count", summary.get("source_digest_count")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_release_readiness_downstream_receipt_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "actual", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_release_readiness_downstream_receipt_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    receipt = as_dict(report.get("receipt"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion release readiness downstream receipt'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Receipt ready: `{summary.get('downstream_receipt_ready')}`",
        f"- Consumer: `{summary.get('consumer_name')}`",
        f"- Route: `{summary.get('route_id')}`",
        f"- Scope: `{summary.get('granted_scope')}`",
        f"- Boundary: `{summary.get('boundary')}`",
        f"- Claim: `{summary.get('model_quality_claim')}`",
        f"- Source check digest: `{receipt.get('source_check_digest')}`",
        "",
        "## Source Digests",
        "",
        "| Kind | SHA-256 | Path |",
        "| --- | --- | --- |",
    ]
    for row in list_of_dicts(receipt.get("source_digest_rows")):
        lines.append(f"| {markdown_cell(row.get('kind'))} | {markdown_cell(row.get('sha256'))} | {markdown_cell(row.get('path'))} |")
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("actual")),
                    markdown_cell(row.get("detail")),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_release_readiness_downstream_receipt_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    receipt = as_dict(report.get("receipt"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("downstream_receipt_ready")),
        ("Consumer", summary.get("consumer_name")),
        ("Route", summary.get("route_id")),
        ("Scope", summary.get("granted_scope")),
        ("Digests", summary.get("source_digest_count")),
    ]
    digests = "".join(_digest_row(row) for row in list_of_dicts(receipt.get("source_digest_rows")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion release readiness downstream receipt'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion release readiness downstream receipt'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Source Digests</h2><div class="table-wrap"><table>
<thead><tr><th>Kind</th><th>SHA-256</th><th>Path</th></tr></thead>
<tbody>{digests}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_release_readiness_downstream_receipt_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_release_readiness_downstream_receipt_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_release_readiness_downstream_receipt_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_release_readiness_downstream_receipt_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _digest_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('kind'))}</td>"
        f"<td>{html_escape(row.get('sha256'))}</td>"
        f"<td>{html_escape(row.get('path'))}</td>"
        "</tr>"
    )


def _check_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('actual'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


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
    "render_model_capability_route_promotion_release_readiness_downstream_receipt_html",
    "render_model_capability_route_promotion_release_readiness_downstream_receipt_markdown",
    "render_model_capability_route_promotion_release_readiness_downstream_receipt_text",
    "write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs",
]
