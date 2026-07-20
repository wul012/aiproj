from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_CSV_FILENAME,
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_HTML_FILENAME,
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_JSON_FILENAME,
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_tokenizer_coverage_aware_holdout_dry_run_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        (
            "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_ready",
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_ready"),
        ),
        ("case_count", summary.get("case_count")),
        ("positive_passed_case_count", summary.get("positive_passed_case_count")),
        ("negative_passed_case_count", summary.get("negative_passed_case_count")),
        ("negative_control_passed", summary.get("negative_control_passed")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_tokenizer_coverage_aware_holdout_dry_run_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "positive_case_pass", "negative_case_pass", "positive_hit_terms", "negative_hit_terms"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("dry_run_rows")):
            writer.writerow(
                {
                    "case_id": csv_cell(row.get("case_id")),
                    "positive_case_pass": csv_cell(row.get("positive_case_pass")),
                    "negative_case_pass": csv_cell(row.get("negative_case_pass")),
                    "positive_hit_terms": csv_cell(",".join(str(item) for item in row.get("positive_hit_terms", []))),
                    "negative_hit_terms": csv_cell(",".join(str(item) for item in row.get("negative_hit_terms", []))),
                }
            )


def render_tokenizer_coverage_aware_holdout_dry_run_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT tokenizer-coverage-aware holdout dry-run'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Positive passed: `{summary.get('positive_passed_case_count')}/{summary.get('case_count')}`",
        f"- Negative passed: `{summary.get('negative_passed_case_count')}`",
        f"- Negative control passed: `{summary.get('negative_control_passed')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Dry-Run Rows",
        "",
        "| Case | Positive pass | Negative pass | Positive hit | Negative hit |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("dry_run_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("positive_case_pass")),
                    markdown_cell(row.get("negative_case_pass")),
                    markdown_cell(",".join(str(item) for item in row.get("positive_hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("negative_hit_terms", []))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_tokenizer_coverage_aware_holdout_dry_run_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Cases", summary.get("case_count")),
        ("Positive passed", summary.get("positive_passed_case_count")),
        ("Negative passed", summary.get("negative_passed_case_count")),
        ("Negative control", summary.get("negative_control_passed")),
        ("Promotion", summary.get("promotion_ready")),
        ("Claim", summary.get("model_quality_claim")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("dry_run_rows")))
    checks = "".join(_check_row(item) for item in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT tokenizer-coverage-aware holdout dry-run'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT tokenizer-coverage-aware holdout dry-run'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Dry-Run Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Positive pass</th><th>Negative pass</th><th>Positive hit</th><th>Negative hit</th></tr></thead>
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


def write_tokenizer_coverage_aware_holdout_dry_run_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_tokenizer_coverage_aware_holdout_dry_run_csv(report, paths["csv"])
    paths["text"].write_text(render_tokenizer_coverage_aware_holdout_dry_run_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_tokenizer_coverage_aware_holdout_dry_run_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_tokenizer_coverage_aware_holdout_dry_run_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('positive_case_pass'))}</td>"
        f"<td>{html_escape(row.get('negative_case_pass'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('positive_hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('negative_hit_terms', [])))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#6d28d9}
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
    "render_tokenizer_coverage_aware_holdout_dry_run_html",
    "render_tokenizer_coverage_aware_holdout_dry_run_markdown",
    "render_tokenizer_coverage_aware_holdout_dry_run_text",
    "write_tokenizer_coverage_aware_holdout_dry_run_outputs",
]
