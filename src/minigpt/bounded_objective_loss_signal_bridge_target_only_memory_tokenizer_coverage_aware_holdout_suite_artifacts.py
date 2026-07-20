from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_CSV_FILENAME,
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_HTML_FILENAME,
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_tokenizer_coverage_aware_holdout_suite_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        (
            "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready",
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready"),
        ),
        ("source_case_count", summary.get("source_case_count")),
        ("candidate_case_count", summary.get("candidate_case_count")),
        ("tokenizer_covered_case_count", summary.get("tokenizer_covered_case_count")),
        ("candidate_prompt_unknown_token_count", summary.get("candidate_prompt_unknown_token_count")),
        ("source_prompt_unknown_row_count", summary.get("source_prompt_unknown_row_count")),
        ("source_prompt_unknown_token_count", summary.get("source_prompt_unknown_token_count")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_tokenizer_coverage_aware_holdout_suite_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "source_case_id", "tokenizer_covered", "prompt_unknown_count", "prompt"]
    suite = as_dict(report.get("benchmark_suite"))
    cases_by_id = {str(row.get("case_id")): row for row in list_of_dicts(suite.get("cases"))}
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("coverage_rows")):
            case = as_dict(cases_by_id.get(str(row.get("case_id"))))
            prompt_case = as_dict(case.get("prompt_case"))
            writer.writerow(
                {
                    "case_id": csv_cell(row.get("case_id")),
                    "source_case_id": csv_cell(row.get("source_case_id")),
                    "tokenizer_covered": csv_cell(row.get("tokenizer_covered")),
                    "prompt_unknown_count": csv_cell(row.get("prompt_unknown_count")),
                    "prompt": csv_cell(prompt_case.get("prompt")),
                }
            )


def render_tokenizer_coverage_aware_holdout_suite_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    suite = as_dict(report.get("benchmark_suite"))
    cases = {str(row.get("case_id")): row for row in list_of_dicts(suite.get("cases"))}
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT tokenizer-coverage-aware holdout suite'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Candidate cases: `{summary.get('candidate_case_count')}`",
        f"- Tokenizer-covered cases: `{summary.get('tokenizer_covered_case_count')}`",
        f"- Candidate unknown tokens: `{summary.get('candidate_prompt_unknown_token_count')}`",
        f"- Source unknown rows: `{summary.get('source_prompt_unknown_row_count')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Coverage Rows",
        "",
        "| Case | Source | Covered | Unknown | Prompt |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("coverage_rows")):
        case = as_dict(cases.get(str(row.get("case_id"))))
        prompt_case = as_dict(case.get("prompt_case"))
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("source_case_id")),
                    markdown_cell(row.get("tokenizer_covered")),
                    markdown_cell(row.get("prompt_unknown_count")),
                    markdown_cell(prompt_case.get("prompt")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_tokenizer_coverage_aware_holdout_suite_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Candidate cases", summary.get("candidate_case_count")),
        ("Covered cases", summary.get("tokenizer_covered_case_count")),
        ("Candidate unknown", summary.get("candidate_prompt_unknown_token_count")),
        ("Source unknown rows", summary.get("source_prompt_unknown_row_count")),
        ("Source unknown tokens", summary.get("source_prompt_unknown_token_count")),
        ("Promotion", summary.get("promotion_ready")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_coverage_row(item, report) for item in list_of_dicts(report.get("coverage_rows")))
    checks = "".join(_check_row(item) for item in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT tokenizer-coverage-aware holdout suite'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT tokenizer-coverage-aware holdout suite'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Coverage Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Source</th><th>Covered</th><th>Unknown</th><th>Prompt</th></tr></thead>
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


def write_tokenizer_coverage_aware_holdout_suite_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_tokenizer_coverage_aware_holdout_suite_csv(report, paths["csv"])
    paths["text"].write_text(render_tokenizer_coverage_aware_holdout_suite_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_tokenizer_coverage_aware_holdout_suite_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_tokenizer_coverage_aware_holdout_suite_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _coverage_row(row: dict[str, Any], report: dict[str, Any]) -> str:
    suite = as_dict(report.get("benchmark_suite"))
    cases = {str(item.get("case_id")): item for item in list_of_dicts(suite.get("cases"))}
    prompt = as_dict(as_dict(cases.get(str(row.get("case_id")))).get("prompt_case")).get("prompt")
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('source_case_id'))}</td>"
        f"<td>{html_escape(row.get('tokenizer_covered'))}</td>"
        f"<td>{html_escape(row.get('prompt_unknown_count'))}</td>"
        f"<td>{html_escape(prompt)}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:#f2f4f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
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
    "render_tokenizer_coverage_aware_holdout_suite_html",
    "render_tokenizer_coverage_aware_holdout_suite_markdown",
    "render_tokenizer_coverage_aware_holdout_suite_text",
    "write_tokenizer_coverage_aware_holdout_suite_outputs",
]
