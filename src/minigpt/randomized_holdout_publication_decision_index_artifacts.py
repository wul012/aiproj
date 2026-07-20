from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_decision_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_randomized_holdout_publication_decision_index_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("randomized_holdout_publication_decision_index_ready", summary.get("randomized_holdout_publication_decision_index_ready")),
        ("indexed_decision", summary.get("indexed_decision")),
        ("bounded_publication_accepted", summary.get("bounded_publication_accepted")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("accepted_claim_count", summary.get("accepted_claim_count")),
        ("blocked_claim_count", summary.get("blocked_claim_count")),
        ("candidate_case_count", summary.get("candidate_case_count")),
        ("random_seed", summary.get("random_seed")),
        ("pass_rate", summary.get("pass_rate")),
        ("allowed_use", summary.get("allowed_use")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("source_count", summary.get("source_count")),
        ("next_step", summary.get("next_step")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_publication_decision_index_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "kind",
        "exists",
        "status",
        "decision",
        "ready_key",
        "ready_value",
        "accepted_claim_count",
        "blocked_claim_count",
        "candidate_case_count",
        "random_seed",
        "pass_rate",
        "allowed_use",
        "model_quality_claim",
        "next_step",
        "path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("source_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_publication_decision_index_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout publication decision index'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Index ready: `{summary.get('randomized_holdout_publication_decision_index_ready')}`",
        f"- Indexed decision: `{summary.get('indexed_decision')}`",
        f"- Bounded accepted: `{summary.get('bounded_publication_accepted')}`",
        f"- Promotion: `{summary.get('promotion_ready')}`",
        f"- Accepted claims: `{summary.get('accepted_claim_count')}`",
        f"- Blocked claims: `{summary.get('blocked_claim_count')}`",
        f"- Candidate cases: `{summary.get('candidate_case_count')}`",
        f"- Random seed: `{summary.get('random_seed')}`",
        f"- Pass rate: `{summary.get('pass_rate')}`",
        f"- Allowed use: `{summary.get('allowed_use')}`",
        f"- Claim: `{summary.get('model_quality_claim')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Source Rows",
        "",
        "| Kind | Exists | Status | Ready | Accepted | Blocked | Cases | Seed | Use | Next | Path |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("source_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("kind")),
                    markdown_cell(row.get("exists")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("ready_value")),
                    markdown_cell(row.get("accepted_claim_count")),
                    markdown_cell(row.get("blocked_claim_count")),
                    markdown_cell(row.get("candidate_case_count")),
                    markdown_cell(row.get("random_seed")),
                    markdown_cell(row.get("allowed_use")),
                    markdown_cell(row.get("next_step")),
                    markdown_cell(row.get("path")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_holdout_publication_decision_index_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Index ready", summary.get("randomized_holdout_publication_decision_index_ready")),
        ("Bounded accepted", summary.get("bounded_publication_accepted")),
        ("Promotion", summary.get("promotion_ready")),
        ("Accepted", summary.get("accepted_claim_count")),
        ("Blocked", summary.get("blocked_claim_count")),
        ("Cases", summary.get("candidate_case_count")),
        ("Sources", summary.get("source_count")),
        ("Next", summary.get("next_step")),
    ]
    sources = "".join(_source_row(row) for row in list_of_dicts(report.get("source_rows")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized holdout publication decision index'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT randomized holdout publication decision index'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Source Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Kind</th><th>Status</th><th>Ready</th><th>Accepted</th><th>Blocked</th><th>Cases</th><th>Use</th><th>Next</th><th>Path</th></tr></thead>
<tbody>{sources}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_randomized_holdout_publication_decision_index_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_publication_decision_index_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_publication_decision_index_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_publication_decision_index_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_publication_decision_index_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _source_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('kind'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('ready_value'))}</td>"
        f"<td>{html_escape(row.get('accepted_claim_count'))}</td>"
        f"<td>{html_escape(row.get('blocked_claim_count'))}</td>"
        f"<td>{html_escape(row.get('candidate_case_count'))}</td>"
        f"<td>{html_escape(row.get('allowed_use'))}</td>"
        f"<td>{html_escape(row.get('next_step'))}</td>"
        f"<td>{html_escape(row.get('path'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#334155;--ok:#0f766e}
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
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--ok);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:var(--accent)}
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_randomized_holdout_publication_decision_index_html",
    "render_randomized_holdout_publication_decision_index_markdown",
    "render_randomized_holdout_publication_decision_index_text",
    "write_randomized_holdout_publication_decision_index_outputs",
]
