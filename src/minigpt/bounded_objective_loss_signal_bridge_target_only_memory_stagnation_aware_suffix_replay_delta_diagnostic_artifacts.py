from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_CSV_FILENAME,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_HTML_FILENAME,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_JSON_FILENAME,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_stagnation_aware_suffix_replay_delta_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("stagnation_aware_suffix_replay_delta_diagnostic_ready", summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic_ready")),
        ("no_contract_gain_confirmed", summary.get("no_contract_gain_confirmed")),
        ("surface_converged_without_suffix_gain", summary.get("surface_converged_without_suffix_gain")),
        ("pass_delta", summary.get("pass_delta")),
        ("any_hit_delta", summary.get("any_hit_delta")),
        ("zero_hit_delta", summary.get("zero_hit_delta")),
        ("continuation_changed_count", summary.get("continuation_changed_count")),
        ("space_to_newline_fixed_l_case_count", summary.get("space_to_newline_fixed_l_case_count")),
        ("loss_newly_hit_case_count", summary.get("loss_newly_hit_case_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_stagnation_aware_suffix_replay_delta_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix replay delta diagnostic'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- No contract gain confirmed: `{summary.get('no_contract_gain_confirmed')}`",
        f"- Surface converged without suffix gain: `{summary.get('surface_converged_without_suffix_gain')}`",
        f"- Pass delta: `{summary.get('pass_delta')}`",
        f"- Any-hit delta: `{summary.get('any_hit_delta')}`",
        f"- Zero-hit delta: `{summary.get('zero_hit_delta')}`",
        f"- Continuation changes: `{summary.get('continuation_changed_count')}`",
        f"- Space-to-newline fixed-l cases: `{summary.get('space_to_newline_fixed_l_case_count')}`",
        f"- Newly hit loss cases: `{summary.get('loss_newly_hit_case_count')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Case Deltas",
        "",
        "| Case | State | Baseline | Current | Baseline hit | Current hit |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("case_diagnostics")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("case_id")),
            markdown_cell(row.get("state_label")),
            markdown_cell(row.get("baseline_continuation")),
            markdown_cell(row.get("current_continuation")),
            markdown_cell(",".join(str(item) for item in row.get("baseline_hit_terms", []))),
            markdown_cell(",".join(str(item) for item in row.get("current_hit_terms", []))),
        ]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_stagnation_aware_suffix_replay_delta_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("No contract gain", summary.get("no_contract_gain_confirmed")),
        ("Surface converged", summary.get("surface_converged_without_suffix_gain")),
        ("Pass delta", summary.get("pass_delta")),
        ("Any delta", summary.get("any_hit_delta")),
        ("Zero delta", summary.get("zero_hit_delta")),
        ("Continuation changes", summary.get("continuation_changed_count")),
        ("Space to newline", summary.get("space_to_newline_fixed_l_case_count")),
        ("Loss new hits", summary.get("loss_newly_hit_case_count")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_case_row(row) for row in list_of_dicts(report.get("case_diagnostics")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix replay delta diagnostic'))}</title>{_style()}</head>
<body><main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix replay delta diagnostic'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Case Deltas</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>State</th><th>Baseline</th><th>Current</th><th>Baseline hit</th><th>Current hit</th></tr></thead><tbody>{rows}</tbody></table></div></section>
</main></body></html>"""


def write_stagnation_aware_suffix_replay_delta_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_stagnation_aware_suffix_replay_delta_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_stagnation_aware_suffix_replay_delta_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_stagnation_aware_suffix_replay_delta_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = [
        "case_id",
        "state_label",
        "baseline_continuation",
        "current_continuation",
        "continuation_changed",
        "space_to_newline_fixed_l",
        "loss_newly_hit",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_diagnostics")):
            writer.writerow({key: csv_cell(row.get(key)) for key in fieldnames})


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('state_label'))}</td>"
        f"<td>{html_escape(row.get('baseline_continuation'))}</td>"
        f"<td>{html_escape(row.get('current_continuation'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('baseline_hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('current_hit_terms', [])))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#18212f;--muted:#607184;--line:#d7dee8;--panel:#f8fafc;--accent:#14532d}
*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1260px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere;white-space:pre-wrap}
</style>"""


__all__ = [
    "render_stagnation_aware_suffix_replay_delta_diagnostic_html",
    "render_stagnation_aware_suffix_replay_delta_diagnostic_markdown",
    "render_stagnation_aware_suffix_replay_delta_diagnostic_text",
    "write_stagnation_aware_suffix_replay_delta_diagnostic_outputs",
]
