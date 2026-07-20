from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_CSV_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_HTML_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_decoder_budget_holdout_replay_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        (
            "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_ready",
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_ready"),
        ),
        ("source_objective_contract_recovered", summary.get("source_objective_contract_recovered")),
        ("holdout_model_route_quality_ready", summary.get("holdout_model_route_quality_ready")),
        ("case_count", summary.get("case_count")),
        ("passed_case_count", summary.get("passed_case_count")),
        ("failed_case_count", summary.get("failed_case_count")),
        ("any_hit_case_count", summary.get("any_hit_case_count")),
        ("zero_hit_case_count", summary.get("zero_hit_case_count")),
        ("pass_rate", summary.get("pass_rate")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_decoder_budget_holdout_replay_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "case_pass", "hit_terms", "missed_terms", "max_new_tokens", "continuation"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("replay_rows")):
            writer.writerow(
                {
                    "case_id": csv_cell(row.get("case_id")),
                    "case_pass": csv_cell(row.get("case_pass")),
                    "hit_terms": csv_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    "missed_terms": csv_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    "max_new_tokens": csv_cell(row.get("max_new_tokens")),
                    "continuation": csv_cell(row.get("continuation")),
                }
            )


def render_decoder_budget_holdout_replay_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT decoder-budget holdout replay'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Source contract recovered: `{summary.get('source_objective_contract_recovered')}`",
        f"- Holdout quality ready: `{summary.get('holdout_model_route_quality_ready')}`",
        f"- Passed cases: `{summary.get('passed_case_count')}/{summary.get('case_count')}`",
        f"- Any-hit cases: `{summary.get('any_hit_case_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Model quality claim: `{summary.get('model_quality_claim')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Replay Rows",
        "",
        "| Case | Pass | Hit terms | Missed terms | Budget | Continuation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("replay_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("case_pass")),
                    markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    markdown_cell(row.get("max_new_tokens")),
                    markdown_cell(row.get("continuation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_decoder_budget_holdout_replay_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Source recovered", summary.get("source_objective_contract_recovered")),
        ("Holdout ready", summary.get("holdout_model_route_quality_ready")),
        ("Passed", f"{summary.get('passed_case_count')}/{summary.get('case_count')}"),
        ("Any hits", summary.get("any_hit_case_count")),
        ("Promotion", summary.get("promotion_ready")),
        ("Claim", summary.get("model_quality_claim")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("replay_rows")))
    checks = "".join(_check_row(item) for item in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT decoder-budget holdout replay'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT decoder-budget holdout replay'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Replay Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Pass</th><th>Hit terms</th><th>Missed terms</th><th>Budget</th><th>Continuation</th></tr></thead>
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


def write_decoder_budget_holdout_replay_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_decoder_budget_holdout_replay_csv(report, paths["csv"])
    paths["text"].write_text(render_decoder_budget_holdout_replay_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_decoder_budget_holdout_replay_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_decoder_budget_holdout_replay_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('case_pass'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('max_new_tokens'))}</td>"
        f"<td>{html_escape(row.get('continuation'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#9f1239}
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
    "render_decoder_budget_holdout_replay_html",
    "render_decoder_budget_holdout_replay_markdown",
    "render_decoder_budget_holdout_replay_text",
    "write_decoder_budget_holdout_replay_outputs",
]
