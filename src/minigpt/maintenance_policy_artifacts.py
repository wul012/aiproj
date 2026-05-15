from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_csv_row,
    write_json_payload,
)


def write_maintenance_batching_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_maintenance_batching_csv(report: dict[str, Any], path: str | Path) -> None:
    summary = _dict(report.get("summary"))
    proposal = _dict(report.get("proposal"))
    row = {
        "status": summary.get("status"),
        "decision": summary.get("decision"),
        "entry_count": summary.get("entry_count"),
        "single_module_utils_count": summary.get("single_module_utils_count"),
        "batched_utils_count": summary.get("batched_utils_count"),
        "longest_single_module_utils_run": summary.get("longest_single_module_utils_run"),
        "single_module_utils_limit": _dict(report.get("policy")).get("single_module_utils_limit"),
        "proposal_decision": proposal.get("decision"),
        "proposal_target_version_kind": proposal.get("target_version_kind"),
        "proposal_item_count": proposal.get("item_count"),
    }
    write_csv_row(
        row,
        path,
        [
            "status",
            "decision",
            "entry_count",
            "single_module_utils_count",
            "batched_utils_count",
            "longest_single_module_utils_run",
            "single_module_utils_limit",
            "proposal_decision",
            "proposal_target_version_kind",
            "proposal_item_count",
        ],
    )


def render_maintenance_batching_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    proposal = _dict(report.get("proposal"))
    lines = [
        f"# {report.get('title', 'MiniGPT maintenance batching policy')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in [
        "entry_count",
        "single_module_utils_count",
        "batched_utils_count",
        "longest_single_module_utils_run",
        "single_module_utils_limit",
    ]:
        lines.append(f"| {_md(key)} | {_md(summary.get(key))} |")
    lines.extend(["", "## Single Module Utility Runs", "", "| Start | End | Length | Versions |", "| --- | --- | --- | --- |"])
    runs = _list_of_dicts(report.get("single_module_utils_runs"))
    if runs:
        for run in runs:
            versions = ", ".join(_string_list(run.get("versions")))
            lines.append(f"| {_md(run.get('start_version'))} | {_md(run.get('end_version'))} | {_md(run.get('length'))} | {_md(versions)} |")
    else:
        lines.append("|  |  | 0 |  |")
    lines.extend(["", "## Proposal", "", f"- Decision: `{proposal.get('decision')}`", f"- Target version kind: `{proposal.get('target_version_kind')}`", ""])
    for reason in _string_list(proposal.get("reasons")):
        lines.append(f"- {reason}")
    groups = _list_of_dicts(proposal.get("groups"))
    if groups:
        lines.extend(["", "| Category | Count | Items |", "| --- | --- | --- |"])
        for group in groups:
            lines.append(f"| {_md(group.get('category'))} | {_md(group.get('count'))} | {_md(', '.join(_string_list(group.get('items'))))} |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_maintenance_batching_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maintenance_batching_markdown(report), encoding="utf-8")


def render_maintenance_batching_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    proposal = _dict(report.get("proposal"))
    stats = [
        ("Status", summary.get("status")),
        ("Decision", summary.get("decision")),
        ("Entries", summary.get("entry_count")),
        ("Single utils", summary.get("single_module_utils_count")),
        ("Batched utils", summary.get("batched_utils_count")),
        ("Longest run", summary.get("longest_single_module_utils_run")),
        ("Proposal", proposal.get("decision")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT maintenance batching policy'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT maintenance batching policy'))}</h1><p>Low-risk maintenance should be batched; high-risk changes keep focused evidence.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _runs_section(_list_of_dicts(report.get("single_module_utils_runs"))),
            _proposal_section(proposal),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT maintenance batching policy.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_maintenance_batching_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maintenance_batching_html(report), encoding="utf-8")


def write_maintenance_batching_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "maintenance_batching.json",
        "csv": root / "maintenance_batching.csv",
        "markdown": root / "maintenance_batching.md",
        "html": root / "maintenance_batching.html",
    }
    write_maintenance_batching_json(report, paths["json"])
    write_maintenance_batching_csv(report, paths["csv"])
    write_maintenance_batching_markdown(report, paths["markdown"])
    write_maintenance_batching_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def write_module_pressure_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_module_pressure_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "path",
        "status",
        "line_count",
        "byte_count",
        "function_count",
        "class_count",
        "max_function_lines",
        "largest_function",
        "recommendation",
    ]
    rows = []
    for item in _list_of_dicts(report.get("modules")):
        rows.append({field: csv_cell(item.get(field)) for field in fieldnames})
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_module_pressure_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT module pressure audit')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in [
        "module_count",
        "warning_lines",
        "critical_lines",
        "warn_count",
        "critical_count",
        "largest_module",
        "largest_line_count",
        "largest_function",
        "largest_function_lines",
    ]:
        lines.append(f"| {_md(key)} | {_md(summary.get(key))} |")
    lines.extend(
        [
            "",
            "## Top Modules",
            "",
            "| Path | Status | Lines | Functions | Classes | Largest Function | Recommendation |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in _list_of_dicts(report.get("top_modules")):
        largest_function = item.get("largest_function") or ""
        if largest_function:
            largest_function = f"{largest_function} ({item.get('max_function_lines')} lines)"
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("path")),
                    _md(item.get("status")),
                    _md(item.get("line_count")),
                    _md(item.get("function_count")),
                    _md(item.get("class_count")),
                    _md(largest_function),
                    _md(item.get("recommendation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_module_pressure_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_module_pressure_markdown(report), encoding="utf-8")


def render_module_pressure_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Status", summary.get("status")),
        ("Decision", summary.get("decision")),
        ("Modules", summary.get("module_count")),
        ("Warn", summary.get("warn_count")),
        ("Critical", summary.get("critical_count")),
        ("Largest", f"{summary.get('largest_module')} ({summary.get('largest_line_count')} lines)"),
    ]
    rows = "".join(_module_pressure_html_row(item) for item in _list_of_dicts(report.get("top_modules")))
    if not rows:
        rows = '<tr><td colspan="7" class="muted">No modules scanned.</td></tr>'
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT module pressure audit'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT module pressure audit'))}</h1><p>Large modules are refactor candidates, not automatic rewrite targets.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            "<section><h2>Top Module Pressure</h2><table><tr><th>Path</th><th>Status</th><th>Lines</th><th>Functions</th><th>Classes</th><th>Largest Function</th><th>Recommendation</th></tr>"
            + rows
            + "</table></section>",
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT maintenance policy.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_module_pressure_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_module_pressure_html(report), encoding="utf-8")


def write_module_pressure_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "module_pressure.json",
        "csv": root / "module_pressure.csv",
        "markdown": root / "module_pressure.md",
        "html": root / "module_pressure.html",
    }
    write_module_pressure_json(report, paths["json"])
    write_module_pressure_csv(report, paths["csv"])
    write_module_pressure_markdown(report, paths["markdown"])
    write_module_pressure_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _module_pressure_html_row(item: dict[str, Any]) -> str:
    largest_function = item.get("largest_function") or ""
    if largest_function:
        largest_function = f"{largest_function} ({item.get('max_function_lines')} lines)"
    return (
        "<tr>"
        f"<td>{_e(item.get('path'))}</td>"
        f"<td>{_e(item.get('status'))}</td>"
        f"<td>{_e(item.get('line_count'))}</td>"
        f"<td>{_e(item.get('function_count'))}</td>"
        f"<td>{_e(item.get('class_count'))}</td>"
        f"<td>{_e(largest_function)}</td>"
        f"<td>{_e(item.get('recommendation'))}</td>"
        "</tr>"
    )


def _runs_section(runs: list[dict[str, Any]]) -> str:
    if not runs:
        return '<section><h2>Single Module Utility Runs</h2><p class="muted">No consecutive single-module utility runs detected.</p></section>'
    rows = [
        "<tr><th>Start</th><th>End</th><th>Length</th><th>Versions</th></tr>",
        *[
            f"<tr><td>{_e(run.get('start_version'))}</td><td>{_e(run.get('end_version'))}</td><td>{_e(run.get('length'))}</td><td>{_e(', '.join(_string_list(run.get('versions'))))}</td></tr>"
            for run in runs
        ],
    ]
    return "<section><h2>Single Module Utility Runs</h2><table>" + "".join(rows) + "</table></section>"


def _proposal_section(proposal: dict[str, Any]) -> str:
    groups = _list_of_dicts(proposal.get("groups"))
    group_rows = "".join(
        f"<tr><td>{_e(group.get('category'))}</td><td>{_e(group.get('count'))}</td><td>{_e(', '.join(_string_list(group.get('items'))))}</td></tr>"
        for group in groups
    )
    groups_html = ""
    if groups:
        groups_html = "<table><tr><th>Category</th><th>Count</th><th>Items</th></tr>" + group_rows + "</table>"
    reasons = _string_list(proposal.get("reasons"))
    reasons_html = "<p class=\"muted\">No proposal reasons.</p>"
    if reasons:
        reasons_html = "<ul>" + "".join(f"<li>{_e(item)}</li>" for item in reasons) + "</ul>"
    return (
        "<section><h2>Proposal</h2>"
        f"<p><strong>{_e(proposal.get('decision'))}</strong> -> {_e(proposal.get('target_version_kind'))}</p>"
        + reasons_html
        + groups_html
        + "</section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return f"<section><h2>{_e(title)}</h2><p class=\"muted\">None.</p></section>"
    return f"<section><h2>{_e(title)}</h2><ul>" + "".join(f"<li>{_e(item)}</li>" for item in values) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return f'<article class="stat"><span>{_e(label)}</span><strong>{_e(value)}</strong></article>'


def _style() -> str:
    return """
<style>
:root { color-scheme: light; font-family: Arial, "Microsoft YaHei", sans-serif; color: #172026; background: #f6f8fa; }
body { margin: 0; padding: 24px; }
header, section, footer { max-width: 1040px; margin: 0 auto 18px; }
header { padding: 18px 0 8px; border-bottom: 3px solid #1f7a5c; }
h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
h2 { margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }
p { margin: 0 0 10px; line-height: 1.5; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.stat { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 12px; min-height: 64px; }
.stat span { display: block; color: #5c6b73; font-size: 12px; margin-bottom: 8px; }
.stat strong { display: block; font-size: 18px; overflow-wrap: anywhere; }
section { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px; border-bottom: 1px solid #e5e9ef; text-align: left; vertical-align: top; }
th { background: #eef3f6; }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; }
.muted { color: #687782; }
footer { color: #687782; font-size: 12px; }
</style>
""".strip()


__all__ = [
    "render_maintenance_batching_html",
    "render_maintenance_batching_markdown",
    "render_module_pressure_html",
    "render_module_pressure_markdown",
    "write_maintenance_batching_csv",
    "write_maintenance_batching_html",
    "write_maintenance_batching_json",
    "write_maintenance_batching_markdown",
    "write_maintenance_batching_outputs",
    "write_module_pressure_csv",
    "write_module_pressure_html",
    "write_module_pressure_json",
    "write_module_pressure_markdown",
    "write_module_pressure_outputs",
]
