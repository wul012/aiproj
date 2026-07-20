from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic import (
    PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_CSV_FILENAME,
    PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_HTML_FILENAME,
    PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_JSON_FILENAME,
    PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_MARKDOWN_FILENAME,
    PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.model_capability_required_term_pair_first_token_preference_artifacts import (
    write_model_capability_required_term_pair_first_token_preference_outputs,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("seed_count", summary.get("seed_count")),
        ("missed_seed_count", summary.get("missed_seed_count")),
        ("missed_expected_top_count", summary.get("missed_expected_top_count")),
        ("missed_first_token_gap_count", summary.get("missed_first_token_gap_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "seed",
        "status",
        "pair_full_observed",
        "first_token_decision",
        "expected_top_count",
        "term_count",
        "expected_all_top",
        "max_expected_rank",
        "fixed_expected_rank",
        "loss_expected_rank",
        "fixed_top_token",
        "loss_top_token",
        "observed_continuation_hit_count",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_markdown(
    report: dict[str, Any],
) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        "| Seed | Pair full | First-token decision | Expected top | Fixed rank | Loss rank | Continuation hits |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in list_of_dicts(report.get("seed_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("pair_full_observed")),
                    markdown_cell(row.get("first_token_decision")),
                    markdown_cell(f"{row.get('expected_top_count')}/{row.get('term_count')}"),
                    markdown_cell(row.get("fixed_expected_rank")),
                    markdown_cell(row.get("loss_expected_rank")),
                    markdown_cell(row.get("observed_continuation_hit_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Colon-Immediate Missed-Seed Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Missed seeds: `{summary.get('missed_seed_count')}`",
            f"- Missed expected-top seeds: `{summary.get('missed_expected_top_count')}`",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            "",
            "## Seeds",
            "",
            *rows,
            "",
            "## Boundary",
            "",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_html(
    report: dict[str, Any],
) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Seeds", summary.get("seed_count")),
        ("Missed seeds", summary.get("missed_seed_count")),
        ("Missed expected top", summary.get("missed_expected_top_count")),
        ("First-token gaps", summary.get("missed_first_token_gap_count")),
    ]
    seed_rows = "\n".join(_seed_html(row) for row in list_of_dicts(report.get("seed_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT colon-immediate missed-seed diagnostic</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT colon-immediate missed-seed diagnostic</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Seeds</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Pair full</th><th>First-token decision</th><th>Expected top</th><th>Fixed rank</th><th>Loss rank</th><th>Continuation hits</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    sidecar_outputs = {}
    for entry in list_of_dicts(report.get("first_token_reports")):
        seed = entry.get("seed")
        child = as_dict(entry.get("report"))
        if seed and child:
            sidecar_outputs[str(seed)] = write_model_capability_required_term_pair_first_token_preference_outputs(
                child,
                root / "first-token-reports" / f"seed-{seed}",
            )
    report["sidecar_outputs"] = {"first_token_reports": sidecar_outputs}
    paths = {
        "json": root / PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_CSV_FILENAME,
        "text": root / PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(
        render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_text(report),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_html(report),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _seed_html(row: dict[str, Any]) -> str:
    expected_top = f"{row.get('expected_top_count')}/{row.get('term_count')}"
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('pair_full_observed'))}</td>"
        f"<td>{html_escape(row.get('first_token_decision'))}</td>"
        f"<td>{html_escape(expected_top)}</td>"
        f"<td>{html_escape(row.get('fixed_expected_rank'))}</td>"
        f"<td>{html_escape(row.get('loss_expected_rank'))}</td>"
        f"<td>{html_escape(row.get('observed_continuation_hit_count'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#7c2d12}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_html",
    "render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_markdown",
    "render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_text",
    "write_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_outputs",
]
