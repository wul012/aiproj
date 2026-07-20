from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison import (
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_CSV_FILENAME,
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_HTML_FILENAME,
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME,
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_bounded_objective_replay_comparison_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("bounded_objective_replay_comparison_ready", summary.get("bounded_objective_replay_comparison_ready")),
        ("objective_contract_recovered", summary.get("objective_contract_recovered")),
        ("canonical_case_pass", summary.get("canonical_case_pass")),
        ("case_count", summary.get("case_count")),
        ("passed_case_count", summary.get("passed_case_count")),
        ("any_hit_case_count", summary.get("any_hit_case_count")),
        ("zero_hit_case_count", summary.get("zero_hit_case_count")),
        ("pass_rate", summary.get("pass_rate")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_objective_replay_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "case_pass", "any_hit", "hit_terms", "missed_terms", "continuation"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("replay_rows")):
            writer.writerow({
                "case_id": csv_cell(row.get("case_id")),
                "case_pass": csv_cell(row.get("case_pass")),
                "any_hit": csv_cell(row.get("any_hit")),
                "hit_terms": csv_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                "missed_terms": csv_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                "continuation": csv_cell(row.get("continuation")),
            })


def render_bounded_objective_replay_comparison_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective replay comparison'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Contract recovered: `{summary.get('objective_contract_recovered')}`",
        f"- Passed cases: `{summary.get('passed_case_count')}/{summary.get('case_count')}`",
        f"- Any-hit cases: `{summary.get('any_hit_case_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        "",
        "## Replay Rows",
        "",
        "| Case | Pass | Hit Terms | Missed Terms | Continuation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("replay_rows")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("case_id")),
            markdown_cell(row.get("case_pass")),
            markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
            markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
            markdown_cell(row.get("continuation")),
        ]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_objective_replay_comparison_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Recovered", summary.get("objective_contract_recovered")),
        ("Cases", summary.get("case_count")),
        ("Passed", summary.get("passed_case_count")),
        ("Any hits", summary.get("any_hit_case_count")),
        ("Zero hits", summary.get("zero_hit_case_count")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("replay_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective replay comparison'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective replay comparison'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Replay Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Pass</th><th>Hit</th><th>Missed</th><th>Continuation</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_bounded_objective_replay_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_replay_comparison_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_replay_comparison_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_replay_comparison_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_replay_comparison_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('case_pass'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('continuation'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#991b1b}
*{box-sizing:border-box}
body{margin:0;background:#f3f4f6;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_bounded_objective_replay_comparison_html",
    "render_bounded_objective_replay_comparison_markdown",
    "render_bounded_objective_replay_comparison_text",
    "write_bounded_objective_replay_comparison_outputs",
]
