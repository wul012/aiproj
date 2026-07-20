from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("comparison_ready", summary.get("bounded_prompt_aligned_checkpoint_comparison_ready")),
        ("prompt_aligned_checkpoint_improved", summary.get("prompt_aligned_checkpoint_improved")),
        ("prompt_aligned_checkpoint_regressed", summary.get("prompt_aligned_checkpoint_regressed")),
        ("baseline_passed_case_count", summary.get("baseline_passed_case_count")),
        ("prompt_aligned_passed_case_count", summary.get("prompt_aligned_passed_case_count")),
        ("passed_case_delta", summary.get("passed_case_delta")),
        ("pass_rate_delta", summary.get("pass_rate_delta")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "baseline_pass", "prompt_aligned_pass", "delta", "baseline_hit_terms", "prompt_aligned_hit_terms", "prompt_aligned_missed_terms"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_rows")):
            writer.writerow({
                "case_id": csv_cell(row.get("case_id")),
                "baseline_pass": csv_cell(row.get("baseline_pass")),
                "prompt_aligned_pass": csv_cell(row.get("prompt_aligned_pass")),
                "delta": csv_cell(row.get("delta")),
                "baseline_hit_terms": csv_cell(row.get("baseline_hit_terms")),
                "prompt_aligned_hit_terms": csv_cell(row.get("prompt_aligned_hit_terms")),
                "prompt_aligned_missed_terms": csv_cell(row.get("prompt_aligned_missed_terms")),
            })


def render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay prompt-aligned checkpoint comparison'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Baseline passed: `{summary.get('baseline_passed_case_count')}`",
        f"- Prompt-aligned passed: `{summary.get('prompt_aligned_passed_case_count')}`",
        f"- Pass rate delta: `{summary.get('pass_rate_delta')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Case Comparison",
        "",
        "| Case | Baseline pass | Prompt-aligned pass | Delta | Baseline hits | Prompt-aligned hits | Prompt-aligned misses |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("baseline_pass")),
                    markdown_cell(row.get("prompt_aligned_pass")),
                    markdown_cell(row.get("delta")),
                    markdown_cell(",".join(str(item) for item in row.get("baseline_hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("prompt_aligned_hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("prompt_aligned_missed_terms", []))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Baseline passed", summary.get("baseline_passed_case_count")),
        ("Prompt-aligned passed", summary.get("prompt_aligned_passed_case_count")),
        ("Pass delta", summary.get("passed_case_delta")),
        ("Rate delta", summary.get("pass_rate_delta")),
        ("Promotion ready", summary.get("promotion_ready")),
    ]
    rows = "".join(_case_row(item) for item in list_of_dicts(report.get("case_rows")))
    checks = "".join(_check_row(item) for item in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay prompt-aligned checkpoint comparison'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay prompt-aligned checkpoint comparison'))}</h1><p>Compares the v806 baseline replay with the prompt-aligned checkpoint replay and keeps promotion blocked unless the prompt-aligned checkpoint beats the baseline.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Comparison</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Baseline pass</th><th>Prompt-aligned pass</th><th>Delta</th><th>Baseline hits</th><th>Prompt hits</th><th>Prompt misses</th></tr></thead>
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


def write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('baseline_pass'))}</td>"
        f"<td>{html_escape(row.get('prompt_aligned_pass'))}</td>"
        f"<td>{html_escape(row.get('delta'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('baseline_hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('prompt_aligned_hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('prompt_aligned_missed_terms', [])))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#667381;--line:#d8dee5;--panel:#f7f9fb;--accent:#9a3412}
*{box-sizing:border-box}
body{margin:0;background:#f0f3f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_html",
    "render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_text",
    "write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_outputs",
]
