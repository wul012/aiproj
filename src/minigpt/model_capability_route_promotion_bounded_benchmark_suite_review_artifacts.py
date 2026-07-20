from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_benchmark_suite_review import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_route_promotion_bounded_benchmark_suite_review_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("bounded_benchmark_suite_review_ready", summary.get("bounded_benchmark_suite_review_ready")),
        ("approved_for_execution", summary.get("approved_for_execution")),
        ("case_count", summary.get("case_count")),
        ("passed_case_review_count", summary.get("passed_case_review_count")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_benchmark_suite_review_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "review_status", "expected_terms", "forbidden_surface_hits"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_reviews")):
            writer.writerow(
                {
                    "case_id": csv_cell(row.get("case_id")),
                    "review_status": csv_cell(row.get("review_status")),
                    "expected_terms": csv_cell(",".join(str(item) for item in row.get("expected_terms", []))),
                    "forbidden_surface_hits": csv_cell(",".join(str(item) for item in row.get("forbidden_surface_hits", []))),
                }
            )


def render_model_capability_route_promotion_bounded_benchmark_suite_review_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded benchmark suite review'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_benchmark_suite_review_ready')}`",
        f"- Approved for execution: `{summary.get('approved_for_execution')}`",
        f"- Case count: `{summary.get('case_count')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Case Reviews",
        "",
        "| Case | Status | Expected terms | Forbidden hits |",
        "| --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_reviews")):
        lines.append("| " + " | ".join([markdown_cell(row.get("case_id")), markdown_cell(row.get("review_status")), markdown_cell(",".join(str(item) for item in row.get("expected_terms", []))), markdown_cell(",".join(str(item) for item in row.get("forbidden_surface_hits", [])))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_benchmark_suite_review_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("bounded_benchmark_suite_review_ready")),
        ("Approved", summary.get("approved_for_execution")),
        ("Cases", summary.get("case_count")),
        ("Next", summary.get("next_step")),
    ]
    cases = "".join(_case_row(row) for row in list_of_dicts(report.get("case_reviews")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded benchmark suite review'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded benchmark suite review'))}</h1><p>Reviews prompt cases, expected terms, and bounded execution guardrails before replay.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Reviews</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Status</th><th>Expected terms</th><th>Forbidden hits</th></tr></thead>
<tbody>{cases}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_benchmark_suite_review_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_benchmark_suite_review_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_benchmark_suite_review_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_benchmark_suite_review_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_benchmark_suite_review_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('review_status'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('expected_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('forbidden_surface_hits', [])))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#64717d;--line:#d8dee4;--panel:#f8fafc;--accent:#7c3aed}
*{box-sizing:border-box}
body{margin:0;background:#f3f4f8;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
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
    "render_model_capability_route_promotion_bounded_benchmark_suite_review_html",
    "render_model_capability_route_promotion_bounded_benchmark_suite_review_markdown",
    "render_model_capability_route_promotion_bounded_benchmark_suite_review_text",
    "write_model_capability_route_promotion_bounded_benchmark_suite_review_outputs",
]
