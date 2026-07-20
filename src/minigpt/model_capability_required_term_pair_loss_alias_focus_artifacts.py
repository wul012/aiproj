from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_focus import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_HTML_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_loss_alias_focus_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("loss_alias_focus_decision", summary.get("loss_alias_focus_decision")),
        ("loss_alias_focus_surface_decision", summary.get("loss_alias_focus_surface_decision")),
        ("loss_alias_focus_metric_decision", summary.get("loss_alias_focus_metric_decision")),
        ("seed_count", summary.get("seed_count")),
        ("pass_count", summary.get("pass_count")),
        ("support_case_count", summary.get("support_case_count")),
        ("focus_case_count", summary.get("focus_case_count")),
        ("focus_full_seed_count", summary.get("focus_full_seed_count")),
        ("support_full_seed_count", summary.get("support_full_seed_count")),
        ("stable_focus_full_coverage", summary.get("stable_focus_full_coverage")),
        ("stable_support_full_coverage", summary.get("stable_support_full_coverage")),
        ("focus_newline_cleanup_full_seed_count", summary.get("focus_newline_cleanup_full_seed_count")),
        ("support_newline_cleanup_full_seed_count", summary.get("support_newline_cleanup_full_seed_count")),
        ("newline_cleanup_gain_count", summary.get("newline_cleanup_gain_count")),
        ("focus_normalized_full_seed_count", summary.get("focus_normalized_full_seed_count")),
        ("support_normalized_full_seed_count", summary.get("support_normalized_full_seed_count")),
        ("normalization_gain_count", summary.get("normalization_gain_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_loss_alias_focus_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "status",
        "focus_hit_case_count",
        "focus_case_count",
        "support_hit_case_count",
        "support_case_count",
        "focus_full_coverage",
        "support_full_coverage",
        "focus_newline_cleanup_hit_case_count",
        "support_newline_cleanup_hit_case_count",
        "focus_newline_cleanup_full_coverage",
        "support_newline_cleanup_full_coverage",
        "newline_cleanup_gain_count",
        "focus_normalized_hit_case_count",
        "support_normalized_hit_case_count",
        "focus_normalized_full_coverage",
        "support_normalized_full_coverage",
        "normalization_gain_count",
        "checkpoint_exists",
        "out_dir",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_loss_alias_focus_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    focus_cases = ["| Case | Prompt | Missed seeds |", "| --- | --- | --- |"]
    for row in list_of_dicts(report.get("focus_cases")):
        focus_cases.append(
            "| "
            + " | ".join([markdown_cell(row.get("case_id")), markdown_cell(row.get("prompt")), markdown_cell(row.get("missed_seeds"))])
            + " |"
        )
    seed_rows = [
        "| Seed | Strict focus | Strict support | Newline focus | Newline support | NL gains | Normalized focus | Normalized support | Gains |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in list_of_dicts(report.get("seed_rows")):
        seed_rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("focus_hit_case_count")),
                    markdown_cell(row.get("support_hit_case_count")),
                    markdown_cell(row.get("focus_newline_cleanup_hit_case_count")),
                    markdown_cell(row.get("support_newline_cleanup_hit_case_count")),
                    markdown_cell(row.get("newline_cleanup_gain_count")),
                    markdown_cell(row.get("focus_normalized_hit_case_count")),
                    markdown_cell(row.get("support_normalized_hit_case_count")),
                    markdown_cell(row.get("normalization_gain_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Alias Focus",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Focus decision: `{summary.get('loss_alias_focus_decision')}`",
            f"- Surface decision: `{summary.get('loss_alias_focus_surface_decision')}`",
            f"- Metric decision: `{summary.get('loss_alias_focus_metric_decision')}`",
            f"- Focus cases: `{summary.get('focus_case_count')}`",
            f"- Stable focus full coverage: `{summary.get('stable_focus_full_coverage')}`",
            f"- Stable support full coverage: `{summary.get('stable_support_full_coverage')}`",
            f"- Newline cleanup gains: `{summary.get('newline_cleanup_gain_count')}`",
            f"- Normalization gains: `{summary.get('normalization_gain_count')}`",
            "",
            "## Focus Cases",
            "",
            *focus_cases,
            "",
            "## Seed Rows",
            "",
            *seed_rows,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_loss_alias_focus_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Surface", summary.get("loss_alias_focus_surface_decision")),
        ("Metric", summary.get("loss_alias_focus_metric_decision")),
        ("Seeds", f"{summary.get('pass_count')}/{summary.get('seed_count')}"),
        ("Focus cases", summary.get("focus_case_count")),
        ("Strict focus full", summary.get("focus_full_seed_count")),
        ("NL support full", summary.get("support_newline_cleanup_full_seed_count")),
        ("NL gains", summary.get("newline_cleanup_gain_count")),
        ("Norm support full", summary.get("support_normalized_full_seed_count")),
        ("Gains", summary.get("normalization_gain_count")),
    ]
    focus_rows = "\n".join(_focus_html(row) for row in list_of_dicts(report.get("focus_cases")))
    seed_rows = "\n".join(_seed_html(row) for row in list_of_dicts(report.get("seed_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-alias focus</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-alias focus</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Focus Cases</h2>
<div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Prompt</th><th>Missed seeds</th></tr></thead>
<tbody>{focus_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Seed Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Strict focus</th><th>Strict support</th><th>Newline focus</th><th>Newline support</th><th>NL gains</th><th>Normalized focus</th><th>Normalized support</th><th>Gains</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_loss_alias_focus_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_loss_alias_focus.csv",
        "text": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_loss_alias_focus_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_loss_alias_focus_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_loss_alias_focus_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_loss_alias_focus_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _focus_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('missed_seeds'))}</td>"
        "</tr>"
    )


def _seed_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('focus_hit_case_count'))}/{html_escape(row.get('focus_case_count'))}</td>"
        f"<td>{html_escape(row.get('support_hit_case_count'))}/{html_escape(row.get('support_case_count'))}</td>"
        f"<td>{html_escape(row.get('focus_newline_cleanup_hit_case_count'))}/{html_escape(row.get('focus_case_count'))}</td>"
        f"<td>{html_escape(row.get('support_newline_cleanup_hit_case_count'))}/{html_escape(row.get('support_case_count'))}</td>"
        f"<td>{html_escape(row.get('newline_cleanup_gain_count'))}</td>"
        f"<td>{html_escape(row.get('focus_normalized_hit_case_count'))}/{html_escape(row.get('focus_case_count'))}</td>"
        f"<td>{html_escape(row.get('support_normalized_hit_case_count'))}/{html_escape(row.get('support_case_count'))}</td>"
        f"<td>{html_escape(row.get('normalization_gain_count'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#be123c}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px}
h2{font-size:18px;margin:0 0 12px}
p{color:var(--muted);line-height:1.55}
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
