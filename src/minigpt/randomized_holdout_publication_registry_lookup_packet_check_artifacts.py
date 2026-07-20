from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_registry_lookup_packet_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_randomized_holdout_publication_registry_lookup_packet_check_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("contract_check_ready", summary.get("contract_check_ready")),
        ("original_decision", summary.get("original_decision")),
        ("rebuilt_decision", summary.get("rebuilt_decision")),
        ("original_lookup_scope", summary.get("original_lookup_scope")),
        ("rebuilt_lookup_scope", summary.get("rebuilt_lookup_scope")),
        ("original_lookup_ready", summary.get("original_lookup_ready")),
        ("rebuilt_lookup_ready", summary.get("rebuilt_lookup_ready")),
        ("original_rejected_use", summary.get("original_rejected_use")),
        ("rebuilt_rejected_use", summary.get("rebuilt_rejected_use")),
        ("original_promotion_ready", summary.get("original_promotion_ready")),
        ("rebuilt_promotion_ready", summary.get("rebuilt_promotion_ready")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_publication_registry_lookup_packet_check_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "actual", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_publication_registry_lookup_packet_check_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout publication registry lookup packet contract check'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('contract_check_ready')}`",
        f"- Source review: `{summary.get('source_manifest_review')}`",
        f"- Original lookup scope: `{summary.get('original_lookup_scope')}`",
        f"- Rebuilt lookup scope: `{summary.get('rebuilt_lookup_scope')}`",
        f"- Original rejected use: `{summary.get('original_rejected_use')}`",
        f"- Rebuilt rejected use: `{summary.get('rebuilt_rejected_use')}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Actual | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_holdout_publication_registry_lookup_packet_check_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Ready", summary.get("contract_check_ready")),
        ("Original", summary.get("original_lookup_scope")),
        ("Rebuilt", summary.get("rebuilt_lookup_scope")),
        ("Rejected", summary.get("original_rejected_use")),
        ("Failed", report.get("failed_count")),
    ]
    rows = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry lookup packet contract check'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry lookup packet contract check'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_randomized_holdout_publication_registry_lookup_packet_check_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_publication_registry_lookup_packet_check_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_publication_registry_lookup_packet_check_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_publication_registry_lookup_packet_check_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_publication_registry_lookup_packet_check_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef1f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:16px;line-height:1.25;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_randomized_holdout_publication_registry_lookup_packet_check_html",
    "render_randomized_holdout_publication_registry_lookup_packet_check_markdown",
    "render_randomized_holdout_publication_registry_lookup_packet_check_text",
    "write_randomized_holdout_publication_registry_lookup_packet_check_outputs",
]
