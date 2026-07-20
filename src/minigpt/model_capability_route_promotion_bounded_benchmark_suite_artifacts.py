from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_model_capability_route_promotion_bounded_benchmark_suite_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("bounded_benchmark_suite_ready", summary.get("bounded_benchmark_suite_ready")),
        ("suite_name", summary.get("suite_name")),
        ("route_id", summary.get("route_id")),
        ("case_count", summary.get("case_count")),
        ("expected_terms", ",".join(str(item) for item in summary.get("expected_terms", []))),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_benchmark_suite_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "prompt", "expected_terms", "task_type", "seed"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    suite = as_dict(report.get("benchmark_suite"))
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(suite.get("cases")):
            prompt_case = as_dict(row.get("prompt_case"))
            writer.writerow(
                {
                    "case_id": csv_cell(row.get("case_id")),
                    "prompt": csv_cell(prompt_case.get("prompt")),
                    "expected_terms": csv_cell(",".join(str(item) for item in row.get("expected_terms", []))),
                    "task_type": csv_cell(prompt_case.get("task_type")),
                    "seed": csv_cell(prompt_case.get("seed")),
                }
            )


def render_model_capability_route_promotion_bounded_benchmark_suite_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    suite = as_dict(report.get("benchmark_suite"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded benchmark suite'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_benchmark_suite_ready')}`",
        f"- Route: `{summary.get('route_id')}`",
        f"- Cases: `{summary.get('case_count')}`",
        f"- Expected terms: `{', '.join(str(item) for item in summary.get('expected_terms', []))}`",
        "",
        "## Cases",
        "",
        "| Case | Prompt | Expected terms |",
        "| --- | --- | --- |",
    ]
    for row in list_of_dicts(suite.get("cases")):
        prompt_case = as_dict(row.get("prompt_case"))
        lines.append("| " + " | ".join([markdown_cell(row.get("case_id")), markdown_cell(prompt_case.get("prompt")), markdown_cell(",".join(str(item) for item in row.get("expected_terms", [])))]) + " |")
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_benchmark_suite_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    suite = as_dict(report.get("benchmark_suite"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("bounded_benchmark_suite_ready")),
        ("Route", summary.get("route_id")),
        ("Cases", summary.get("case_count")),
        ("Next", summary.get("proposed_next_artifact")),
    ]
    cases = "".join(_case_row(row) for row in list_of_dicts(suite.get("cases")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded benchmark suite'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded benchmark suite'))}</h1><p>Defines bounded prompt cases and expected terms for the verified route.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Cases</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Prompt</th><th>Expected terms</th></tr></thead>
<tbody>{cases}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_benchmark_suite_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_benchmark_suite_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_benchmark_suite_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_benchmark_suite_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_benchmark_suite_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_row(row: dict[str, Any]) -> str:
    prompt_case = as_dict(row.get("prompt_case"))
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(prompt_case.get('prompt'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('expected_terms', [])))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#64717d;--line:#d8dee4;--panel:#f8fafc;--accent:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:#f0f3f8;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_model_capability_route_promotion_bounded_benchmark_suite_html",
    "render_model_capability_route_promotion_bounded_benchmark_suite_markdown",
    "render_model_capability_route_promotion_bounded_benchmark_suite_text",
    "write_model_capability_route_promotion_bounded_benchmark_suite_outputs",
]
