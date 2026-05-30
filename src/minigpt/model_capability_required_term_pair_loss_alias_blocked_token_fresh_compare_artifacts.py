from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_HTML_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_JSON_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_TEXT_FILENAME,
)
from minigpt.model_capability_required_term_pair_loss_alias_focus_artifacts import (
    write_model_capability_required_term_pair_loss_alias_focus_outputs,
)
from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_probe_artifacts import (
    write_model_capability_required_term_pair_loss_alias_newline_suppression_outputs,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("fresh_focus_decision", summary.get("fresh_focus_decision")),
        ("fresh_focus_surface_decision", summary.get("fresh_focus_surface_decision")),
        ("blocked_token_surface_decision", summary.get("blocked_token_surface_decision")),
        ("case_count", summary.get("case_count")),
        ("baseline_strict_hit_count", summary.get("baseline_strict_hit_count")),
        ("blocked_token_strict_hit_count", summary.get("blocked_token_strict_hit_count")),
        ("blocked_token_strict_gain_count", summary.get("blocked_token_strict_gain_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "profile_id",
        "seed",
        "case_id",
        "is_focus_case",
        "source_strict_hit",
        "strict_hit",
        "newline_cleanup_hit",
        "normalized_hit",
        "strict_gain",
        "excluded_token_count",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    probe = as_dict(report.get("blocked_token_probe_report"))
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(probe.get("case_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    probe = as_dict(report.get("blocked_token_probe_report"))
    case_table = [
        "| Profile | Case | Source strict | Probe strict | Gain | Preview |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(probe.get("case_rows")):
        case_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("source_strict_hit")),
                    markdown_cell(row.get("strict_hit")),
                    markdown_cell(row.get("strict_gain")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Loss-Alias Blocked-Token Fresh Compare",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Fresh focus decision: `{summary.get('fresh_focus_decision')}`",
            f"- Fresh focus surface decision: `{summary.get('fresh_focus_surface_decision')}`",
            f"- Blocked-token surface decision: `{summary.get('blocked_token_surface_decision')}`",
            f"- Baseline strict hits: `{summary.get('baseline_strict_hit_count')}/{summary.get('case_count')}`",
            f"- Blocked-token strict hits: `{summary.get('blocked_token_strict_hit_count')}/{summary.get('case_count')}`",
            f"- Strict gains: `{summary.get('blocked_token_strict_gain_count')}`",
            "",
            "## Cases",
            "",
            *case_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    probe = as_dict(report.get("blocked_token_probe_report"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Cases", summary.get("case_count")),
        ("Baseline strict", summary.get("baseline_strict_hit_count")),
        ("Blocked strict", summary.get("blocked_token_strict_hit_count")),
        ("Strict gains", summary.get("blocked_token_strict_gain_count")),
    ]
    case_rows = "\n".join(_case_html(row) for row in list_of_dicts(probe.get("case_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT loss-alias blocked-token fresh compare</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT loss-alias blocked-token fresh compare</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Fresh Focus</h2><p>decision={html_escape(summary.get('fresh_focus_decision'))}; surface={html_escape(summary.get('fresh_focus_surface_decision'))}</p></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Cases</h2>
<div class="table-wrap"><table>
<thead><tr><th>Profile</th><th>Case</th><th>Source strict</th><th>Probe strict</th><th>Gain</th><th>Preview</th></tr></thead>
<tbody>{case_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    sidecars = as_dict(report.get("sidecar_dirs"))
    sidecar_outputs: dict[str, Any] = {}
    focus_report = as_dict(report.get("fresh_focus_report"))
    if focus_report:
        sidecar_outputs["fresh_focus_report"] = write_model_capability_required_term_pair_loss_alias_focus_outputs(
            focus_report,
            sidecars.get("fresh_focus_report") or root / "fresh-focus-report",
        )
    probe_report = as_dict(report.get("blocked_token_probe_report"))
    if probe_report:
        sidecar_outputs["blocked_token_probe_report"] = write_model_capability_required_term_pair_loss_alias_newline_suppression_outputs(
            probe_report,
            sidecars.get("blocked_token_probe_report") or root / "blocked-token-probe-report",
        )
    if sidecar_outputs:
        report["sidecar_outputs"] = sidecar_outputs
    paths = {
        "json": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.csv",
        "text": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _case_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('source_strict_hit'))}</td>"
        f"<td>{html_escape(row.get('strict_hit'))}</td>"
        f"<td>{html_escape(row.get('strict_gain'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


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
