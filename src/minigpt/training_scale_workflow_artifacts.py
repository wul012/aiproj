from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_json_payload,
)


def write_training_scale_workflow_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_workflow_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = _dict(report.get("summary"))
    fieldnames = [
        "profile",
        "status",
        "allowed",
        "gate_status",
        "batch_status",
        "readiness_score",
        "run_json",
        "decision_status",
        "selected_profile",
        "recommended_action",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("runs")):
            writer.writerow(
                {
                    "profile": row.get("profile"),
                    "status": row.get("status"),
                    "allowed": row.get("allowed"),
                    "gate_status": row.get("gate_status"),
                    "batch_status": row.get("batch_status"),
                    "readiness_score": row.get("readiness_score"),
                    "run_json": row.get("outputs", {}).get("json") if isinstance(row.get("outputs"), dict) else None,
                    "decision_status": summary.get("decision_status"),
                    "selected_profile": summary.get("selected_profile"),
                    "recommended_action": summary.get("recommended_action"),
                }
            )


def render_training_scale_workflow_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    plan = _dict(report.get("plan_summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale workflow')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Scale: `{plan.get('scale_tier')}`",
        f"- Characters: `{plan.get('char_count')}`",
        f"- Profiles: `{', '.join(_string_list(report.get('profiles')))}`",
        f"- Decision: `{summary.get('decision_status')}`",
        f"- Selected profile: `{summary.get('selected_profile')}`",
        f"- Action: `{summary.get('recommended_action')}`",
        "",
        "## Runs",
        "",
        "| Profile | Status | Allowed | Gate | Batch | Score |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in _list_of_dicts(report.get("runs")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("profile")),
                    _md(row.get("status")),
                    _md(row.get("allowed")),
                    _md(row.get("gate_status")),
                    _md(row.get("batch_status")),
                    _md(row.get("readiness_score")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Execute command",
            "",
            "```powershell",
            str(report.get("execute_command_text") or ""),
            "```",
            "",
            "## Artifacts",
            "",
            f"- Plan: `{_dict(report.get('plan_outputs')).get('json')}`",
            f"- Comparison: `{_dict(report.get('comparison_outputs')).get('json')}`",
            f"- Decision: `{_dict(report.get('decision_outputs')).get('json')}`",
            "",
            "## Recommendations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_workflow_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_workflow_markdown(report), encoding="utf-8")


def render_training_scale_workflow_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    plan = _dict(report.get("plan_summary"))
    stats = [
        ("Scale", plan.get("scale_tier")),
        ("Chars", plan.get("char_count")),
        ("Profiles", summary.get("profile_count")),
        ("Allowed", summary.get("allowed_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Decision", summary.get("decision_status")),
        ("Selected", summary.get("selected_profile")),
        ("Action", summary.get("recommended_action")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale workflow'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale workflow'))}</h1><p>{_e(report.get('out_root'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _runs_table(report),
            _command_section(report),
            _artifact_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale workflow.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_workflow_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_workflow_html(report), encoding="utf-8")


def write_training_scale_workflow_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_workflow.json",
        "csv": root / "training_scale_workflow.csv",
        "markdown": root / "training_scale_workflow.md",
        "html": root / "training_scale_workflow.html",
    }
    write_training_scale_workflow_json(report, paths["json"])
    write_training_scale_workflow_csv(report, paths["csv"])
    write_training_scale_workflow_markdown(report, paths["markdown"])
    write_training_scale_workflow_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _runs_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("runs")):
        outputs = _dict(row.get("outputs"))
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('profile'))}</td>"
            f"<td>{_e(row.get('status'))}</td>"
            f"<td>{_e(row.get('allowed'))}</td>"
            f"<td>{_e(row.get('gate_status'))}</td>"
            f"<td>{_e(row.get('batch_status'))}</td>"
            f"<td>{_e(row.get('readiness_score'))}</td>"
            f"<td>{_link(outputs.get('html'), 'run html')}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Profile Runs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Profile</th><th>Status</th><th>Allowed</th><th>Gate</th><th>Batch</th><th>Score</th><th>Artifact</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _command_section(report: dict[str, Any]) -> str:
    text = str(report.get("execute_command_text") or "No execute command because the workflow decision is blocked.")
    return f"<section><h2>Decision Execute Command</h2><pre>{_e(text)}</pre></section>"


def _artifact_section(report: dict[str, Any]) -> str:
    rows = [
        ("Plan", _dict(report.get("plan_outputs")).get("html")),
        ("Comparison", _dict(report.get("comparison_outputs")).get("html")),
        ("Decision", _dict(report.get("decision_outputs")).get("html")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_link(path, path)}</td></tr>" for label, path in rows)
    return f"<section><h2>Workflow Artifacts</h2><table>{body}</table></section>"


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f8f3; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1180px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
a { color: #1f6f68; text-decoration: none; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _link(path: Any, label: Any) -> str:
    if not path:
        return ""
    return f'<a href="{_e(path)}">{_e(label)}</a>'
