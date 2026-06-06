from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_candidate_promotion_packet import (
    RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_holdout_candidate_promotion_packet_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("randomized_holdout_candidate_promotion_packet_ready", summary.get("randomized_holdout_candidate_promotion_packet_ready")),
        ("handoff_status", summary.get("handoff_status")),
        ("candidate_case_count", summary.get("candidate_case_count")),
        ("random_seed", summary.get("random_seed")),
        ("pass_rate", summary.get("pass_rate")),
        ("clean_randomized_case_count", summary.get("clean_randomized_case_count")),
        ("candidate_packet_authorized", summary.get("candidate_packet_authorized")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("next_step", summary.get("next_step")),
        ("evidence_count", summary.get("evidence_count")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_candidate_promotion_packet_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["kind", "status", "decision", "ready_key", "ready_value", "promotion_ready", "exists", "path", "role"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("evidence_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_candidate_promotion_packet_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout candidate promotion packet'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Packet ready: `{summary.get('randomized_holdout_candidate_promotion_packet_ready')}`",
        f"- Candidate cases: `{summary.get('candidate_case_count')}`",
        f"- Random seed: `{summary.get('random_seed')}`",
        f"- Pass rate: `{summary.get('pass_rate')}`",
        f"- Clean randomized cases: `{summary.get('clean_randomized_case_count')}`",
        f"- Candidate packet authorized: `{summary.get('candidate_packet_authorized')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Evidence Manifest",
        "",
        "| Kind | Status | Ready | Promotion | Exists | Path | Role |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("evidence_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("kind")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("ready_value")),
                    markdown_cell(row.get("promotion_ready")),
                    markdown_cell(row.get("exists")),
                    markdown_cell(row.get("path")),
                    markdown_cell(row.get("role")),
                ]
            )
            + " |"
        )
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


def render_randomized_holdout_candidate_promotion_packet_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Packet ready", summary.get("randomized_holdout_candidate_promotion_packet_ready")),
        ("Cases", summary.get("candidate_case_count")),
        ("Seed", summary.get("random_seed")),
        ("Pass rate", summary.get("pass_rate")),
        ("Clean", summary.get("clean_randomized_case_count")),
        ("Candidate", summary.get("candidate_packet_authorized")),
        ("Promotion", summary.get("promotion_ready")),
        ("Next", summary.get("next_step")),
    ]
    evidence = "".join(_evidence_row(row) for row in list_of_dicts(report.get("evidence_rows")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized holdout candidate promotion packet'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT randomized holdout candidate promotion packet'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Evidence Manifest</h2><div class="table-wrap"><table>
<thead><tr><th>Kind</th><th>Status</th><th>Decision</th><th>Ready</th><th>Promotion</th><th>Exists</th><th>Path</th><th>Role</th></tr></thead>
<tbody>{evidence}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_randomized_holdout_candidate_promotion_packet_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_candidate_promotion_packet_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_candidate_promotion_packet_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_candidate_promotion_packet_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_candidate_promotion_packet_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _evidence_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(
        f"<td>{html_escape(row.get(key))}</td>"
        for key in ["kind", "status", "decision", "ready_value", "promotion_ready", "exists", "path", "role"]
    ) + "</tr>"


def _check_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#f2f4f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1220px;margin:0 auto;padding:28px}
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
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_randomized_holdout_candidate_promotion_packet_html",
    "render_randomized_holdout_candidate_promotion_packet_markdown",
    "render_randomized_holdout_candidate_promotion_packet_text",
    "write_randomized_holdout_candidate_promotion_packet_outputs",
]
