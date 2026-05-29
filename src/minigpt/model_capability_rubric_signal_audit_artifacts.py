from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_rubric_signal_audit import (
    RUBRIC_SIGNAL_AUDIT_HTML_FILENAME,
    RUBRIC_SIGNAL_AUDIT_JSON_FILENAME,
    RUBRIC_SIGNAL_AUDIT_MARKDOWN_FILENAME,
    RUBRIC_SIGNAL_AUDIT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_rubric_signal_audit_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("audit_decision", summary.get("decision")),
        ("target_token_cap", report.get("target_token_cap")),
        ("seed_count", report.get("seed_count")),
        ("case_count", report.get("case_count")),
        ("score_improved_count", summary.get("score_improved_count")),
        ("pass_transition_count", summary.get("pass_transition_count")),
        ("persistent_fail_count", summary.get("persistent_fail_count")),
        ("preview_changed_count", summary.get("preview_changed_count")),
        ("top_failed_checks", _top_items(summary.get("dominant_failed_checks"))),
        ("top_stall_reasons", _top_items(summary.get("dominant_stall_reasons"))),
        ("cross_seed_failed_checks", ",".join(str(item) for item in summary.get("cross_seed_failed_checks") or [])),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    lines = [f"{key}={value}" for key, value in rows]
    for seed in list_of_dicts(report.get("seeds")):
        lines.append(
            "seed="
            + ",".join(
                [
                    f"value={seed.get('seed')}",
                    f"token_cap={seed.get('token_cap')}",
                    f"status={seed.get('status')}",
                    f"case_count={seed.get('case_count')}",
                    f"persistent_fail={seed.get('persistent_fail_count')}",
                    f"preview_changed={seed.get('preview_changed_count')}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def write_model_capability_rubric_signal_audit_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "token_cap",
        "case",
        "task_type",
        "difficulty",
        "first_status",
        "last_status",
        "first_score",
        "last_score",
        "score_delta",
        "stall_reason",
        "last_failed_checks",
        "last_missing_terms",
        "preview_changed",
        "source_diagnostic",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in list_of_dicts(report.get("cases")):
            writer.writerow({field: csv_cell(case.get(field)) for field in fieldnames})


def render_model_capability_rubric_signal_audit_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Seed | Case | Last status | Score delta | Stall reason | Failed checks | Missing terms |",
        "| ---: | --- | --- | ---: | --- | --- | --- |",
    ]
    for case in list_of_dicts(report.get("cases"))[:20]:
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(case.get("seed")),
                    markdown_cell(case.get("case")),
                    markdown_cell(case.get("last_status")),
                    markdown_cell(case.get("score_delta")),
                    markdown_cell(case.get("stall_reason")),
                    markdown_cell(", ".join(str(item) for item in case.get("last_failed_checks") or [])),
                    markdown_cell(", ".join(str(item) for item in case.get("last_missing_terms") or [])),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Rubric Signal Audit",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Audit decision: `{summary.get('decision')}`",
            f"- Target token cap: `{report.get('target_token_cap')}`",
            f"- Case count: `{report.get('case_count')}`",
            f"- Top failed checks: `{_top_items(summary.get('dominant_failed_checks'))}`",
            f"- Top stall reasons: `{_top_items(summary.get('dominant_stall_reasons'))}`",
            f"- Cross-seed failed checks: `{', '.join(str(item) for item in summary.get('cross_seed_failed_checks') or [])}`",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_rubric_signal_audit_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Audit decision", summary.get("decision")),
        ("Token cap", report.get("target_token_cap")),
        ("Seeds", report.get("seed_count")),
        ("Cases", report.get("case_count")),
        ("Score improved", summary.get("score_improved_count")),
        ("Pass transitions", summary.get("pass_transition_count")),
        ("Top failed checks", _top_items(summary.get("dominant_failed_checks"))),
    ]
    seed_rows = "\n".join(_seed_html(seed) for seed in list_of_dicts(report.get("seeds")))
    case_rows = "\n".join(_case_html(case) for case in list_of_dicts(report.get("cases"))[:24])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT model capability rubric signal audit</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT model capability rubric signal audit</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Seed Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Token cap</th><th>Status</th><th>Cases</th><th>Persistent fail</th><th>Preview changed</th><th>Failed checks</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Case Signals</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Case</th><th>Status</th><th>Score delta</th><th>Reason</th><th>Failed checks</th><th>Missing terms</th></tr></thead>
<tbody>{case_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_rubric_signal_audit_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RUBRIC_SIGNAL_AUDIT_JSON_FILENAME,
        "csv": root / "model_capability_rubric_signal_audit.csv",
        "text": root / RUBRIC_SIGNAL_AUDIT_TEXT_FILENAME,
        "markdown": root / RUBRIC_SIGNAL_AUDIT_MARKDOWN_FILENAME,
        "html": root / RUBRIC_SIGNAL_AUDIT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_rubric_signal_audit_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_rubric_signal_audit_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_rubric_signal_audit_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_rubric_signal_audit_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _top_items(value: Any, limit: int = 4) -> str:
    items = list(as_dict(value).items())[:limit]
    return "none" if not items else ", ".join(f"{key}:{count}" for key, count in items)


def _seed_html(seed: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(seed.get('seed'))}</td>"
        f"<td>{html_escape(seed.get('token_cap'))}</td>"
        f"<td>{html_escape(seed.get('status'))}</td>"
        f"<td>{html_escape(seed.get('case_count'))}</td>"
        f"<td>{html_escape(seed.get('persistent_fail_count'))}</td>"
        f"<td>{html_escape(seed.get('preview_changed_count'))}</td>"
        f"<td>{html_escape(_top_items(seed.get('dominant_failed_checks')))}</td>"
        "</tr>"
    )


def _case_html(case: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(case.get('seed'))}</td>"
        f"<td>{html_escape(case.get('case'))}</td>"
        f"<td>{html_escape(case.get('last_status'))}</td>"
        f"<td>{html_escape(case.get('score_delta'))}</td>"
        f"<td>{html_escape(case.get('stall_reason'))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in case.get('last_failed_checks') or []))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in case.get('last_missing_terms') or []))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>'


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f5f2; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #dedbd2; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #635f57; line-height: 1.55; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #e2ded6; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #6b655c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 960px; }
th, td { text-align: left; border-bottom: 1px solid #e7e2dc; padding: 10px; vertical-align: top; }
th { color: #4d4942; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
