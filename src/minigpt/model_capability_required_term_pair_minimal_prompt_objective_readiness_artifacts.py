from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_minimal_prompt_objective_readiness import (
    PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_CSV_FILENAME,
    PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_HTML_FILENAME,
    PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_JSON_FILENAME,
    PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_MARKDOWN_FILENAME,
    PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_minimal_prompt_objective_readiness_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    objective = as_dict(report.get("objective"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("objective_ready", summary.get("objective_ready")),
        ("objective_id", summary.get("objective_id")),
        ("recommended_corpus_mode", summary.get("recommended_corpus_mode")),
        ("success_criterion", objective.get("success_criterion")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_minimal_prompt_objective_readiness_markdown(report: dict[str, Any]) -> str:
    objective = as_dict(report.get("objective"))
    interpretation = as_dict(report.get("interpretation"))
    rows = ["| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("check_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("actual")),
                    markdown_cell(row.get("detail")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Minimal Prompt Objective Readiness",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Objective: `{objective.get('objective_id')}`",
            f"- Claim boundary: `{objective.get('claim_boundary')}`",
            f"- Recommended corpus mode: `{objective.get('recommended_corpus_mode')}`",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            "",
            "## Checks",
            "",
            *rows,
            "",
            "## Next Objective",
            "",
            f"- Success criterion: {objective.get('success_criterion')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_minimal_prompt_objective_readiness_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    objective = as_dict(report.get("objective"))
    interpretation = as_dict(report.get("interpretation"))
    rows = "".join(_check_html(row) for row in list_of_dicts(report.get("check_rows")))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Objective ready", summary.get("objective_ready")),
        ("Checks", f"{summary.get('passed_check_count')}/{summary.get('check_count')}"),
        ("Corpus mode", objective.get("recommended_corpus_mode")),
        ("Next version", objective.get("recommended_next_version")),
    ]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT minimal prompt objective readiness</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT minimal prompt objective readiness</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Objective Boundary</h2><p>{html_escape(objective.get('claim_boundary'))}</p><p>{html_escape(objective.get('success_criterion'))}</p></section>
<section class="panel">
<h2>Readiness Checks</h2>
<div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_minimal_prompt_objective_readiness_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "actual", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_minimal_prompt_objective_readiness_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_JSON_FILENAME,
        "csv": root / PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_CSV_FILENAME,
        "text": root / PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_TEXT_FILENAME,
        "markdown": root / PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_MARKDOWN_FILENAME,
        "html": root / PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_minimal_prompt_objective_readiness_csv(report, paths["csv"])
    paths["text"].write_text(render_minimal_prompt_objective_readiness_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_minimal_prompt_objective_readiness_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_minimal_prompt_objective_readiness_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _check_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('actual'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_minimal_prompt_objective_readiness_html",
    "render_minimal_prompt_objective_readiness_markdown",
    "render_minimal_prompt_objective_readiness_text",
    "write_minimal_prompt_objective_readiness_outputs",
]
