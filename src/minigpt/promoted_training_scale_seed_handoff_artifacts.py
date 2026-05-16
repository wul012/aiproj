from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    display_command as _display_command,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_csv_row,
    write_json_payload,
)


def write_promoted_training_scale_seed_handoff_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_seed_handoff_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    fieldnames = [
        "handoff_status",
        "seed_status",
        "decision_status",
        "execute",
        "returncode",
        "elapsed_seconds",
        "artifact_count",
        "available_artifact_count",
        "plan_status",
        "plan_variant_count",
        "next_batch_command_available",
        "blocked_reason",
    ]
    write_csv_row(
        {
            "handoff_status": summary.get("handoff_status"),
            "seed_status": report.get("seed_status"),
            "decision_status": summary.get("decision_status"),
            "execute": report.get("execute"),
            "returncode": execution.get("returncode"),
            "elapsed_seconds": execution.get("elapsed_seconds"),
            "artifact_count": summary.get("artifact_count"),
            "available_artifact_count": summary.get("available_artifact_count"),
            "plan_status": summary.get("plan_status"),
            "plan_variant_count": summary.get("plan_variant_count"),
            "next_batch_command_available": summary.get("next_batch_command_available"),
            "blocked_reason": report.get("blocked_reason"),
        },
        out_path,
        fieldnames,
    )


def render_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale seed handoff')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Handoff status: `{summary.get('handoff_status')}`",
        f"- Seed status: `{report.get('seed_status')}`",
        f"- Decision status: `{summary.get('decision_status')}`",
        f"- Execute: `{report.get('execute')}`",
        f"- Return code: `{execution.get('returncode')}`",
        f"- Artifacts: `{summary.get('available_artifact_count')}/{summary.get('artifact_count')}`",
        f"- Plan status: `{summary.get('plan_status')}`",
        f"- Next batch command: `{summary.get('next_batch_command_available')}`",
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
        "## Plan Artifacts",
        "",
        "| Key | Exists | Path |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("artifact_rows")):
        lines.append(f"| {_md(row.get('key'))} | {_md(row.get('exists'))} | {_md(row.get('path'))} |")
    if report.get("next_batch_command"):
        lines.extend(
            ["", "## Next Batch Command", "", "```powershell", str(report.get("next_batch_command_text") or ""), "```"]
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_markdown(report), encoding="utf-8")


def render_promoted_training_scale_seed_handoff_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    stats = [
        ("Status", summary.get("handoff_status")),
        ("Seed", report.get("seed_status")),
        ("Decision", summary.get("decision_status")),
        ("Execute", report.get("execute")),
        ("Return", execution.get("returncode")),
        ("Artifacts", f"{summary.get('available_artifact_count')}/{summary.get('artifact_count')}"),
        ("Plan", summary.get("plan_status")),
        ("Batch", summary.get("next_batch_command_available")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale seed handoff'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale seed handoff'))}</h1><p>{_e(report.get('seed_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _command_section(report),
            _execution_section(execution),
            _artifact_section(report),
            _plan_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale seed handoff.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_promoted_training_scale_seed_handoff_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_html(report), encoding="utf-8")


def write_promoted_training_scale_seed_handoff_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_seed_handoff.json",
        "csv": root / "promoted_training_scale_seed_handoff.csv",
        "markdown": root / "promoted_training_scale_seed_handoff.md",
        "html": root / "promoted_training_scale_seed_handoff.html",
    }
    write_promoted_training_scale_seed_handoff_json(report, paths["json"])
    write_promoted_training_scale_seed_handoff_csv(report, paths["csv"])
    write_promoted_training_scale_seed_handoff_markdown(report, paths["markdown"])
    write_promoted_training_scale_seed_handoff_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _plan_section(report: dict[str, Any]) -> str:
    plan = _dict(report.get("plan_report"))
    if not plan:
        return "<section><h2>Plan Report</h2><p>No plan report was loaded.</p></section>"
    dataset = _dict(plan.get("dataset"))
    batch = _dict(plan.get("batch"))
    rows = [
        ("Scale tier", dataset.get("scale_tier")),
        ("Source count", dataset.get("source_count")),
        ("Character count", dataset.get("char_count")),
        ("Quality status", dataset.get("quality_status")),
        ("Warning count", dataset.get("warning_count")),
        ("Variant count", len(_list_of_dicts(plan.get("variants")))),
        ("Batch baseline", batch.get("baseline")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    next_batch = _display_command(report.get("next_batch_command"))
    extra = (
        f"<p><strong>Next batch command:</strong></p><pre>{_e(next_batch)}</pre>"
        if next_batch
        else "<p>No next batch command is available yet.</p>"
    )
    return f"<section><h2>Plan Report</h2><table>{body}</table>{extra}</section>"


def _command_section(report: dict[str, Any]) -> str:
    return f"<section><h2>Seed Command</h2><pre>{_e(report.get('command_text'))}</pre></section>"


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
        '<section><h2>Plan Artifacts</h2><div class="table-wrap"><table>'
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
th { color: #435047; font-size: 12px; text-transform: uppercase; width: 180px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


__all__ = [
    "render_promoted_training_scale_seed_handoff_html",
    "render_promoted_training_scale_seed_handoff_markdown",
    "write_promoted_training_scale_seed_handoff_csv",
    "write_promoted_training_scale_seed_handoff_html",
    "write_promoted_training_scale_seed_handoff_json",
    "write_promoted_training_scale_seed_handoff_markdown",
    "write_promoted_training_scale_seed_handoff_outputs",
]
