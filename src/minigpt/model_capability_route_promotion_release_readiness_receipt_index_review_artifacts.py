from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_readiness_receipt_index_review import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_model_capability_route_promotion_release_readiness_receipt_index_review_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("receipt_index_review_ready", summary.get("receipt_index_review_ready")),
        ("review_id", summary.get("review_id")),
        ("review_status", summary.get("review_status")),
        ("entry_count", summary.get("entry_count")),
        ("lookup_key_count", summary.get("lookup_key_count")),
        ("lookup_ready", summary.get("lookup_ready")),
        ("consumer_name", summary.get("consumer_name")),
        ("route_id", summary.get("route_id")),
        ("allowed_use", summary.get("allowed_use")),
        ("source_digest_count", summary.get("source_digest_count")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_release_readiness_receipt_index_review_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "actual", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_release_readiness_receipt_index_review_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    review = as_dict(report.get("review"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion release readiness receipt index review'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Review ready: `{summary.get('receipt_index_review_ready')}`",
        f"- Review id: `{summary.get('review_id')}`",
        f"- Review status: `{summary.get('review_status')}`",
        f"- Entry count: `{summary.get('entry_count')}`",
        f"- Lookup ready: `{summary.get('lookup_ready')}`",
        f"- Route: `{summary.get('route_id')}`",
        f"- Consumer: `{summary.get('consumer_name')}`",
        f"- Allowed use: `{summary.get('allowed_use')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Receipt index digest: `{review.get('receipt_index_digest')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Lookup Keys",
        "",
    ]
    for key in list(review.get("lookup_keys") or []):
        lines.append(f"- `{markdown_cell(key)}`")
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_release_readiness_receipt_index_review_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    review = as_dict(report.get("review"))
    stats = [
        ("Status", report.get("status")),
        ("Review ready", summary.get("receipt_index_review_ready")),
        ("Entries", summary.get("entry_count")),
        ("Lookup", summary.get("lookup_ready")),
        ("Route", summary.get("route_id")),
        ("Promotion", summary.get("promotion_ready")),
    ]
    keys = "".join(f"<li>{html_escape(key)}</li>" for key in list(review.get("lookup_keys") or []))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion release readiness receipt index review'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion release readiness receipt index review'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Lookup Keys</h2><ul>{keys}</ul></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_release_readiness_receipt_index_review_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_release_readiness_receipt_index_review_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_release_readiness_receipt_index_review_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_release_readiness_receipt_index_review_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_release_readiness_receipt_index_review_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


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
    "render_model_capability_route_promotion_release_readiness_receipt_index_review_html",
    "render_model_capability_route_promotion_release_readiness_receipt_index_review_markdown",
    "render_model_capability_route_promotion_release_readiness_receipt_index_review_text",
    "write_model_capability_route_promotion_release_readiness_receipt_index_review_outputs",
]
