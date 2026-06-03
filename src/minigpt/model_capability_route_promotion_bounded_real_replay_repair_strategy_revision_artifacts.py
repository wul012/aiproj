from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_strategy_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("strategy_revision_ready", summary.get("bounded_real_replay_repair_strategy_revision_ready")),
        ("blocked_checkpoint", summary.get("blocked_checkpoint")),
        ("regression_detected", summary.get("regression_detected")),
        ("passed_case_delta", summary.get("passed_case_delta")),
        ("pass_rate_delta", summary.get("pass_rate_delta")),
        ("case_action_count", summary.get("case_action_count")),
        ("strategy_action_count", summary.get("strategy_action_count")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "severity", "baseline_pass", "repair_pass", "recommended_seed_change", "required_guardrail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_actions")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay repair strategy revision'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_real_replay_repair_strategy_revision_ready')}`",
        f"- Blocked checkpoint: `{summary.get('blocked_checkpoint')}`",
        f"- Pass delta: `{summary.get('passed_case_delta')}`",
        f"- Rate delta: `{summary.get('pass_rate_delta')}`",
        f"- Next artifact: `{summary.get('proposed_next_artifact')}`",
        "",
        "## Case Actions",
        "",
        "| Case | Severity | Baseline pass | Repair pass | Seed change | Guardrail |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_actions")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("severity")),
                    markdown_cell(row.get("baseline_pass")),
                    markdown_cell(row.get("repair_pass")),
                    markdown_cell(row.get("recommended_seed_change")),
                    markdown_cell(row.get("required_guardrail")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Strategy Actions", "", "| Action | Category | Evidence | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("strategy_actions")):
        lines.append("| " + " | ".join([markdown_cell(row.get("action_id")), markdown_cell(row.get("category")), markdown_cell(row.get("evidence")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Blocked", summary.get("blocked_checkpoint")),
        ("Regression", summary.get("regression_detected")),
        ("Pass delta", summary.get("passed_case_delta")),
        ("Rate delta", summary.get("pass_rate_delta")),
        ("Next", summary.get("next_step")),
    ]
    case_rows = "".join(_case_row(item) for item in list_of_dicts(report.get("case_actions")))
    strategy_rows = "".join(_strategy_row(item) for item in list_of_dicts(report.get("strategy_actions")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay repair strategy revision'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay repair strategy revision'))}</h1><p>Turns the regressed repair checkpoint comparison into a concrete next repair strategy while keeping promotion blocked.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Actions</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Severity</th><th>Baseline pass</th><th>Repair pass</th><th>Seed change</th><th>Guardrail</th></tr></thead>
<tbody>{case_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Strategy Actions</h2><div class="table-wrap"><table>
<thead><tr><th>Action</th><th>Category</th><th>Evidence</th><th>Detail</th></tr></thead>
<tbody>{strategy_rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('severity'))}</td>"
        f"<td>{html_escape(row.get('baseline_pass'))}</td>"
        f"<td>{html_escape(row.get('repair_pass'))}</td>"
        f"<td>{html_escape(row.get('recommended_seed_change'))}</td>"
        f"<td>{html_escape(row.get('required_guardrail'))}</td>"
        "</tr>"
    )


def _strategy_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('action_id'))}</td>"
        f"<td>{html_escape(row.get('category'))}</td>"
        f"<td>{html_escape(row.get('evidence'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#667381;--line:#d8dee4;--panel:#f8fafc;--accent:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:#eef2f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_html",
    "render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_text",
    "write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_outputs",
]
