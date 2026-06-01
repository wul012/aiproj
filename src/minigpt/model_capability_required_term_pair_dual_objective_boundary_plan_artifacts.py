from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_dual_objective_boundary_plan import (
    PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_CSV_FILENAME,
    PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_HTML_FILENAME,
    PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_JSON_FILENAME,
    PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_MARKDOWN_FILENAME,
    PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_dual_objective_boundary_plan_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("proposed_corpus_mode", report.get("proposed_corpus_mode")),
        ("constraint_count", summary.get("constraint_count")),
        ("fixed_miss_class", summary.get("fixed_miss_class")),
        ("loss_constrained_hit", summary.get("loss_constrained_hit")),
        ("ready_to_add_corpus_mode", summary.get("ready_to_add_corpus_mode")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_dual_objective_boundary_plan_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "source", "required", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("constraints")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_dual_objective_boundary_plan_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Dual-Objective Boundary Plan",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Proposed corpus mode: `{report.get('proposed_corpus_mode')}`",
            f"- Fixed miss class: `{summary.get('fixed_miss_class')}`",
            "",
            "## Constraints",
            "",
            "| ID | Source | Required | Detail |",
            "| --- | --- | --- | --- |",
            *_constraint_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_dual_objective_boundary_plan_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    metric_rows = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Proposed corpus mode", report.get("proposed_corpus_mode")),
        ("Constraint count", summary.get("constraint_count")),
        ("Fixed miss class", summary.get("fixed_miss_class")),
        ("Ready to add corpus mode", summary.get("ready_to_add_corpus_mode")),
    ]
    metrics = "\n".join(f"<div><strong>{html_escape(key)}</strong><span>{html_escape(value)}</span></div>" for key, value in metric_rows)
    constraints = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('source'))}</td>"
        f"<td>{html_escape(row.get('required'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
        for row in list_of_dicts(report.get("constraints"))
    )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>MiniGPT dual-objective boundary plan</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
header {{ border-bottom: 1px solid #d1d5db; margin-bottom: 20px; padding-bottom: 12px; }}
.metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; margin: 20px 0; }}
.metrics div {{ border: 1px solid #d1d5db; padding: 10px; border-radius: 6px; background: #f9fafb; }}
.metrics strong {{ display: block; font-size: 12px; color: #4b5563; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #f3f4f6; }}
</style>
</head>
<body>
<header><h1>MiniGPT dual-objective boundary plan</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class=\"metrics\">{metrics}</section>
<section>
<h2>Constraints</h2>
<table>
<thead><tr><th>ID</th><th>Source</th><th>Required</th><th>Detail</th></tr></thead>
<tbody>{constraints}</tbody>
</table>
</section>
<section>
<h2>Next Action</h2>
<p>{html_escape(interpretation.get('next_action'))}</p>
</section>
</body>
</html>
"""


def write_dual_objective_boundary_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_JSON_FILENAME,
        "csv": root / PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_CSV_FILENAME,
        "text": root / PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_TEXT_FILENAME,
        "markdown": root / PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_MARKDOWN_FILENAME,
        "html": root / PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_dual_objective_boundary_plan_csv(report, paths["csv"])
    paths["text"].write_text(render_dual_objective_boundary_plan_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_dual_objective_boundary_plan_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_dual_objective_boundary_plan_html(report), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _constraint_rows(report: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for row in list_of_dicts(report.get("constraints")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("source")),
                    markdown_cell(row.get("required")),
                    markdown_cell(row.get("detail")),
                ]
            )
            + " |"
        )
    return rows


__all__ = [
    "render_dual_objective_boundary_plan_html",
    "render_dual_objective_boundary_plan_markdown",
    "render_dual_objective_boundary_plan_text",
    "write_dual_objective_boundary_plan_outputs",
]
