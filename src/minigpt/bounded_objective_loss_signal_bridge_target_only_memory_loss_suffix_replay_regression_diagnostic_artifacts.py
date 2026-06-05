from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_CSV_FILENAME,
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_HTML_FILENAME,
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_loss_suffix_replay_regression_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("loss_suffix_replay_regression_diagnostic_ready", summary.get("bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_ready")),
        ("sample_contract_gap", summary.get("sample_contract_gap")),
        ("objective_contract_recovered", summary.get("objective_contract_recovered")),
        ("any_hit_delta", summary.get("any_hit_delta")),
        ("zero_hit_delta", summary.get("zero_hit_delta")),
        ("completion_surface_regressed_to_zero", summary.get("completion_surface_regressed_to_zero")),
        ("fixed_l_partial_case_count", summary.get("fixed_l_partial_case_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_loss_suffix_replay_regression_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    sample = as_dict(report.get("sample_diagnostic"))
    regression = as_dict(report.get("regression"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory loss-suffix replay regression diagnostic'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Sample has `fixed loss`: `{sample.get('sample_fixed_loss')}`",
        f"- Objective recovered: `{summary.get('objective_contract_recovered')}`",
        f"- Any-hit delta: `{summary.get('any_hit_delta')}`",
        f"- Zero-hit delta: `{summary.get('zero_hit_delta')}`",
        f"- Completion surface regressed to zero: `{summary.get('completion_surface_regressed_to_zero')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Regression",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in sorted(regression):
        lines.append(f"| {markdown_cell(key)} | {markdown_cell(regression.get(key))} |")
    lines.extend(["", "## Current Case Diagnostics", "", "| Case | Label | Any hit | Hit | Missed | Continuation |", "| --- | --- | --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("current_case_diagnostics")):
        lines.append(_case_markdown_row(row))
    lines.extend(["", "## Baseline Case Diagnostics", "", "| Case | Label | Any hit | Hit | Missed | Continuation |", "| --- | --- | --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("baseline_case_diagnostics")):
        lines.append(_case_markdown_row(row))
    return "\n".join(lines).rstrip() + "\n"


def render_loss_suffix_replay_regression_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Sample gap", summary.get("sample_contract_gap")),
        ("Recovered", summary.get("objective_contract_recovered")),
        ("Any-hit delta", summary.get("any_hit_delta")),
        ("Zero-hit delta", summary.get("zero_hit_delta")),
        ("Completion zero", summary.get("completion_surface_regressed_to_zero")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    current_rows = "".join(_case_html_row(row) for row in list_of_dicts(report.get("current_case_diagnostics")))
    baseline_rows = "".join(_case_html_row(row) for row in list_of_dicts(report.get("baseline_case_diagnostics")))
    regression_rows = "".join(_metric_row(key, value) for key, value in sorted(as_dict(report.get("regression")).items()))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory loss-suffix replay regression diagnostic'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory loss-suffix replay regression diagnostic'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Regression Summary</h2><div class="table-wrap"><table><tbody>{regression_rows}</tbody></table></div></section>
<section class="panel"><h2>Current Replay Cases</h2><div class="table-wrap"><table>{_case_header()}<tbody>{current_rows}</tbody></table></div></section>
<section class="panel"><h2>Baseline Replay Cases</h2><div class="table-wrap"><table>{_case_header()}<tbody>{baseline_rows}</tbody></table></div></section>
</main>
</body>
</html>
"""


def write_loss_suffix_replay_regression_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_loss_suffix_replay_regression_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_loss_suffix_replay_regression_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_loss_suffix_replay_regression_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["source", "case_id", "label", "any_hit", "hit_terms", "missed_terms", "continuation"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for source, rows in (
            ("current", list_of_dicts(report.get("current_case_diagnostics"))),
            ("baseline", list_of_dicts(report.get("baseline_case_diagnostics"))),
        ):
            for row in rows:
                writer.writerow({
                    "source": source,
                    "case_id": csv_cell(row.get("case_id")),
                    "label": csv_cell(row.get("label")),
                    "any_hit": csv_cell(row.get("any_hit")),
                    "hit_terms": csv_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    "missed_terms": csv_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    "continuation": csv_cell(row.get("continuation")),
                })


def _case_markdown_row(row: dict[str, Any]) -> str:
    return "| " + " | ".join([
        markdown_cell(row.get("case_id")),
        markdown_cell(row.get("label")),
        markdown_cell(row.get("any_hit")),
        markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
        markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
        markdown_cell(row.get("continuation")),
    ]) + " |"


def _case_header() -> str:
    return "<thead><tr><th>Case</th><th>Label</th><th>Any hit</th><th>Hit</th><th>Missed</th><th>Continuation</th></tr></thead>"


def _case_html_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('label'))}</td>"
        f"<td>{html_escape(row.get('any_hit'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('continuation'))}</td>"
        "</tr>"
    )


def _metric_row(key: str, value: Any) -> str:
    return f"<tr><th>{html_escape(key)}</th><td>{html_escape(value)}</td></tr>"


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#5f6f7d;--line:#d6dde5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}body{margin:0;background:#f5f7f8;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_loss_suffix_replay_regression_diagnostic_html",
    "render_loss_suffix_replay_regression_diagnostic_markdown",
    "render_loss_suffix_replay_regression_diagnostic_text",
    "write_loss_suffix_replay_regression_diagnostic_outputs",
]
