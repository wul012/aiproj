from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_coverage import (
    REQUIRED_TERM_COVERAGE_HTML_FILENAME,
    REQUIRED_TERM_COVERAGE_JSON_FILENAME,
    REQUIRED_TERM_COVERAGE_MARKDOWN_FILENAME,
    REQUIRED_TERM_COVERAGE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_coverage_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("coverage_decision", summary.get("coverage_decision")),
        ("missing_term_row_count", summary.get("missing_term_row_count")),
        ("unique_missing_term_count", summary.get("unique_missing_term_count")),
        ("corpus_missing_term_row_count", summary.get("corpus_missing_term_row_count")),
        ("corpus_missing_unique_terms", ",".join(str(item) for item in summary.get("corpus_missing_unique_terms") or [])),
        ("suite_missing_unique_terms", ",".join(str(item) for item in summary.get("suite_missing_unique_terms") or [])),
        ("source_ready_count", summary.get("source_ready_count")),
        ("source_missing_count", summary.get("source_missing_count")),
        ("top_missing_terms", _top_items(summary.get("dominant_missing_terms"))),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_coverage_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "token_cap",
        "case",
        "task_type",
        "stall_reason",
        "term",
        "covered_in_corpus",
        "covered_in_suite",
        "corpus_occurrences",
        "suite_occurrences",
        "suite_prompt_occurrences",
        "suite_expected_occurrences",
        "source_diagnostic",
        "token_cap_root",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("term_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_coverage_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Seed | Case | Term | Corpus occurrences | Suite occurrences | Stall reason |",
        "| ---: | --- | --- | ---: | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("term_rows"))[:30]:
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("case")),
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("corpus_occurrences")),
                    markdown_cell(row.get("suite_occurrences")),
                    markdown_cell(row.get("stall_reason")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Coverage",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Coverage decision: `{summary.get('coverage_decision')}`",
            f"- Missing term rows: `{summary.get('missing_term_row_count')}`",
            f"- Unique missing terms: `{summary.get('unique_missing_term_count')}`",
            f"- Corpus missing unique terms: `{', '.join(str(item) for item in summary.get('corpus_missing_unique_terms') or []) or 'none'}`",
            f"- Top missing terms: `{_top_items(summary.get('dominant_missing_terms'))}`",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_coverage_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Coverage decision", summary.get("coverage_decision")),
        ("Term rows", summary.get("missing_term_row_count")),
        ("Unique terms", summary.get("unique_missing_term_count")),
        ("Corpus covered rows", summary.get("corpus_covered_term_row_count")),
        ("Corpus missing rows", summary.get("corpus_missing_term_row_count")),
        ("Sources ready", summary.get("source_ready_count")),
        ("Top terms", _top_items(summary.get("dominant_missing_terms"))),
    ]
    source_rows = "\n".join(_source_html(row) for row in list_of_dicts(report.get("source_rows")))
    term_rows = "\n".join(_term_html(row) for row in list_of_dicts(report.get("term_rows"))[:36])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT required-term coverage audit</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term coverage audit</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Source Material</h2>
<div class="table-wrap"><table>
<thead><tr><th>Status</th><th>Source diagnostic</th><th>Suites</th><th>Corpora</th><th>Suite cases</th><th>Corpus chars</th></tr></thead>
<tbody>{source_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Required-Term Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Case</th><th>Term</th><th>Corpus</th><th>Suite</th><th>Prompt</th><th>Expected</th><th>Reason</th></tr></thead>
<tbody>{term_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_coverage_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_COVERAGE_JSON_FILENAME,
        "csv": root / "model_capability_required_term_coverage.csv",
        "text": root / REQUIRED_TERM_COVERAGE_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_COVERAGE_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_COVERAGE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_coverage_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_coverage_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_coverage_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_coverage_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _top_items(value: Any, limit: int = 4) -> str:
    items = list(as_dict(value).items())[:limit]
    return "none" if not items else ", ".join(f"{key}:{count}" for key, count in items)


def _source_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('source_diagnostic'))}</td>"
        f"<td>{html_escape(row.get('suite_count'))}</td>"
        f"<td>{html_escape(row.get('corpus_count'))}</td>"
        f"<td>{html_escape(row.get('suite_case_count'))}</td>"
        f"<td>{html_escape(row.get('corpus_char_count'))}</td>"
        "</tr>"
    )


def _term_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('case'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('corpus_occurrences'))}</td>"
        f"<td>{html_escape(row.get('suite_occurrences'))}</td>"
        f"<td>{html_escape(row.get('suite_prompt_occurrences'))}</td>"
        f"<td>{html_escape(row.get('suite_expected_occurrences'))}</td>"
        f"<td>{html_escape(row.get('stall_reason'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>'


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f6f2; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #dedbd2; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #635f57; line-height: 1.55; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #e2ded6; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #6b655c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 960px; }
th, td { text-align: left; border-bottom: 1px solid #e7e2dc; padding: 10px; vertical-align: top; }
th { color: #4d4942; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
