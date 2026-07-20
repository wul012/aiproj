from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_objective import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_HTML_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_JSON_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_loss_alias_objective_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("loss_alias_decision", summary.get("loss_alias_decision")),
        ("training_status", summary.get("training_status")),
        ("checkpoint_exists", summary.get("checkpoint_exists")),
        ("case_count", summary.get("case_count")),
        ("generation_count", summary.get("generation_count")),
        ("generation_hit_case_count", summary.get("generation_hit_case_count")),
        ("source_loss_hit", summary.get("source_loss_hit")),
        ("heldout_loss_alias_hit_case_count", summary.get("heldout_loss_alias_hit_case_count")),
        ("heldout_loss_alias_full_coverage", summary.get("heldout_loss_alias_full_coverage")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_loss_alias_objective_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "case_id",
        "case_type",
        "alias_group",
        "prompt",
        "expected_term",
        "source_hit_count",
        "generation_count",
        "generation_hit_count",
        "generation_hit_rate",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_loss_alias_objective_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    training = as_dict(report.get("training"))
    cases = ["| Case | Type | Prompt | Source hits | Candidate hits |", "| --- | --- | --- | ---: | ---: |"]
    for row in list_of_dicts(report.get("case_rows")):
        cases.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("case_type")),
                    markdown_cell(row.get("prompt")),
                    markdown_cell(row.get("source_hit_count")),
                    markdown_cell(row.get("generation_hit_count")),
                ]
            )
            + " |"
        )
    generations = ["| Case | Hit | Continuation |", "| --- | --- | --- |"]
    for row in list_of_dicts(report.get("generation_rows")):
        generations.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("continuation_hit")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Alias Objective",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Loss alias decision: `{summary.get('loss_alias_decision')}`",
            f"- Training status: `{summary.get('training_status')}`",
            f"- Checkpoint: `{training.get('checkpoint_path')}`",
            f"- Heldout loss alias hits: `{summary.get('heldout_loss_alias_hit_case_count')}/{summary.get('heldout_case_count')}`",
            f"- Full heldout coverage: `{summary.get('heldout_loss_alias_full_coverage')}`",
            "",
            "## Case Summary",
            "",
            *cases,
            "",
            "## Generation Rows",
            "",
            *generations,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_loss_alias_objective_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("loss_alias_decision")),
        ("Training", summary.get("training_status")),
        ("Checkpoint", summary.get("checkpoint_exists")),
        ("Cases", summary.get("case_count")),
        ("Hits", summary.get("generation_hit_case_count")),
        ("Heldout hits", f"{summary.get('heldout_loss_alias_hit_case_count')}/{summary.get('heldout_case_count')}"),
    ]
    case_rows = "\n".join(_case_html(row) for row in list_of_dicts(report.get("case_rows")))
    generation_rows = "\n".join(_generation_html(row) for row in list_of_dicts(report.get("generation_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-alias objective</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-alias objective</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Case Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Type</th><th>Prompt</th><th>Source hits</th><th>Candidate hits</th><th>Hit rate</th></tr></thead>
<tbody>{case_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Generation Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Seed</th><th>Hit</th><th>Continuation</th></tr></thead>
<tbody>{generation_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_loss_alias_objective_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_loss_alias_objective.csv",
        "text": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_loss_alias_objective_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_loss_alias_objective_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_loss_alias_objective_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_loss_alias_objective_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('case_type'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('source_hit_count'))}</td>"
        f"<td>{html_escape(row.get('generation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('generation_hit_rate'))}</td>"
        "</tr>"
    )


def _generation_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('generation_seed'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
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
