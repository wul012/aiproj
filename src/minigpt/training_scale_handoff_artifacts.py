from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_csv_row,
    write_json_payload,
)


def write_training_scale_handoff_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_handoff_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    fieldnames = [
        "handoff_status",
        "decision_status",
        "execute",
        "returncode",
        "elapsed_seconds",
        "artifact_count",
        "available_artifact_count",
        "decision_require_suite_consistency",
        "suite_consistency",
        "suite_mismatch_count",
        "selected_suite_path",
        "selected_batch_review_status",
        "selected_batch_comparison_review_action_count",
        "selected_batch_comparison_blocker_action_count",
        "selected_batch_maturity_coverage_regression_count",
        "batch_comparison_review_action_count",
        "batch_comparison_blocker_action_count",
        "batch_maturity_coverage_regression_count",
        "command",
        "blocked_reason",
    ]
    write_csv_row(
        {
            "handoff_status": summary.get("handoff_status"),
            "decision_status": report.get("decision_status"),
            "execute": report.get("execute"),
            "returncode": execution.get("returncode"),
            "elapsed_seconds": execution.get("elapsed_seconds"),
            "artifact_count": summary.get("artifact_count"),
            "available_artifact_count": summary.get("available_artifact_count"),
            "decision_require_suite_consistency": summary.get("decision_require_suite_consistency"),
            "suite_consistency": summary.get("suite_consistency"),
            "suite_mismatch_count": summary.get("suite_mismatch_count"),
            "selected_suite_path": summary.get("selected_suite_path"),
            "selected_batch_review_status": summary.get("selected_batch_review_status"),
            "selected_batch_comparison_review_action_count": summary.get("selected_batch_comparison_review_action_count"),
            "selected_batch_comparison_blocker_action_count": summary.get("selected_batch_comparison_blocker_action_count"),
            "selected_batch_maturity_coverage_regression_count": summary.get("selected_batch_maturity_coverage_regression_count"),
            "batch_comparison_review_action_count": summary.get("batch_comparison_review_action_count"),
            "batch_comparison_blocker_action_count": summary.get("batch_comparison_blocker_action_count"),
            "batch_maturity_coverage_regression_count": summary.get("batch_maturity_coverage_regression_count"),
            "command": report.get("command_text"),
            "blocked_reason": report.get("blocked_reason"),
        },
        out_path,
        fieldnames,
    )


def render_training_scale_handoff_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale execution handoff')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Handoff status: `{summary.get('handoff_status')}`",
        f"- Decision status: `{report.get('decision_status')}`",
        f"- Execute: `{report.get('execute')}`",
        f"- Return code: `{execution.get('returncode')}`",
        f"- Artifacts: `{summary.get('available_artifact_count')}/{summary.get('artifact_count')}`",
        f"- Require suite consistency: `{summary.get('decision_require_suite_consistency')}`",
        f"- Suite consistency: `{summary.get('suite_consistency')}`",
        f"- Selected suite path: `{summary.get('selected_suite_path')}`",
        f"- Selected batch review status: `{summary.get('selected_batch_review_status')}`",
        f"- Selected batch reviews: `{summary.get('selected_batch_comparison_review_action_count')}`",
        f"- Selected batch blockers: `{summary.get('selected_batch_comparison_blocker_action_count')}`",
        f"- Batch comparison reviews: `{summary.get('batch_comparison_review_action_count')}`",
        f"- Batch comparison blockers: `{summary.get('batch_comparison_blocker_action_count')}`",
        "",
        "## Command",
        "",
        "```powershell",
        str(report.get("command_text") or ""),
        "```",
        "",
        "## Execution",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Status | {_md(execution.get('status'))} |",
        f"| Elapsed seconds | {_md(execution.get('elapsed_seconds'))} |",
        f"| Stdout tail | {_md(execution.get('stdout_tail'))} |",
        f"| Stderr tail | {_md(execution.get('stderr_tail'))} |",
        "",
        "## Artifacts",
        "",
        "| Key | Exists | Path |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("artifact_rows")):
        lines.append(f"| {_md(row.get('key'))} | {_md(row.get('exists'))} | {_md(row.get('path'))} |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_handoff_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_handoff_markdown(report), encoding="utf-8")


def render_training_scale_handoff_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    stats = [
        ("Status", summary.get("handoff_status")),
        ("Decision", report.get("decision_status")),
        ("Execute", report.get("execute")),
        ("Return", execution.get("returncode")),
        ("Elapsed", execution.get("elapsed_seconds")),
        ("Artifacts", f"{summary.get('available_artifact_count')}/{summary.get('artifact_count')}"),
        ("Require suite consistency", summary.get("decision_require_suite_consistency")),
        ("Suite", summary.get("suite_consistency")),
        ("Batch review status", summary.get("selected_batch_review_status")),
        ("Selected reviews", summary.get("selected_batch_comparison_review_action_count")),
        ("Selected blockers", summary.get("selected_batch_comparison_blocker_action_count")),
        ("Batch reviews", summary.get("batch_comparison_review_action_count")),
        ("Batch blockers", summary.get("batch_comparison_blocker_action_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale execution handoff'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale execution handoff'))}</h1><p>{_e(report.get('workflow_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _command_section(report),
            _execution_section(execution),
            _artifact_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale execution handoff.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_handoff_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_handoff_html(report), encoding="utf-8")


def write_training_scale_handoff_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_handoff.json",
        "csv": root / "training_scale_handoff.csv",
        "markdown": root / "training_scale_handoff.md",
        "html": root / "training_scale_handoff.html",
    }
    write_training_scale_handoff_json(report, paths["json"])
    write_training_scale_handoff_csv(report, paths["csv"])
    write_training_scale_handoff_markdown(report, paths["markdown"])
    write_training_scale_handoff_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _command_section(report: dict[str, Any]) -> str:
    return f"<section><h2>Command</h2><pre>{_e(report.get('command_text'))}</pre></section>"


def _execution_section(execution: dict[str, Any]) -> str:
    rows = [
        ("Status", execution.get("status")),
        ("Return code", execution.get("returncode")),
        ("Elapsed seconds", execution.get("elapsed_seconds")),
        ("Blocked reason", execution.get("blocked_reason")),
        ("Stdout tail", execution.get("stdout_tail")),
        ("Stderr tail", execution.get("stderr_tail")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return f"<section><h2>Execution</h2><table>{body}</table></section>"


def _artifact_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("artifact_rows")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('key'))}</td>"
            f"<td>{_e(row.get('exists'))}</td>"
            f"<td>{_e(row.get('count'))}</td>"
            f"<td>{_e(row.get('path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Artifacts</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Key</th><th>Exists</th><th>Count</th><th>Path</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


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
th { color: #435047; font-size: 12px; text-transform: uppercase; width: 160px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'
