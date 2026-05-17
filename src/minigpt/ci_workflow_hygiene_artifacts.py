from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import csv_cell, html_escape as _e, markdown_cell as _md, string_list as _string_list, write_json_payload


def write_ci_workflow_hygiene_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_ci_workflow_hygiene_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "category", "target", "expected", "actual", "status", "detail"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in _checks(report):
            writer.writerow({field: csv_cell(item.get(field)) for field in fieldnames})


def render_ci_workflow_hygiene_markdown(report: dict[str, Any]) -> str:
    summary = _summary(report)
    lines = [
        f"# {_md(report.get('title', 'MiniGPT CI workflow hygiene'))}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Workflow: `{report.get('workflow_path')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in [
        "check_count",
        "passed_check_count",
        "failed_check_count",
        "action_count",
        "found_required_action_count",
        "node24_native_action_count",
        "forbidden_env_count",
        "missing_step_count",
        "python_version",
    ]:
        lines.append(f"| {_md(key)} | {_md(summary.get(key))} |")
    lines.extend(["", "## Checks", "", "| ID | Category | Target | Expected | Actual | Status | Detail |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for item in _checks(report):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("id")),
                    _md(item.get("category")),
                    _md(item.get("target")),
                    _md(item.get("expected")),
                    _md(item.get("actual")),
                    _md(item.get("status")),
                    _md(item.get("detail")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Actions", "", "| Repository | Version | Line | Node 24 Native |", "| --- | --- | --- | --- |"])
    for item in _actions(report):
        lines.append(f"| {_md(item.get('repository'))} | {_md(item.get('version'))} | {_md(item.get('line'))} | {_md(item.get('node24_native'))} |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_ci_workflow_hygiene_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_ci_workflow_hygiene_markdown(report), encoding="utf-8")


def render_ci_workflow_hygiene_html(report: dict[str, Any]) -> str:
    summary = _summary(report)
    checks = "".join(_check_row(item) for item in _checks(report))
    actions = "".join(_action_row(item) for item in _actions(report))
    stats = [
        ("Status", summary.get("status")),
        ("Decision", summary.get("decision")),
        ("Checks", summary.get("check_count")),
        ("Failures", summary.get("failed_check_count")),
        ("Actions", summary.get("action_count")),
        ("Node 24 native", summary.get("node24_native_action_count")),
        ("Forbidden env", summary.get("forbidden_env_count")),
        ("Python", summary.get("python_version")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT CI workflow hygiene'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT CI workflow hygiene'))}</h1><p>Checks the CI workflow action versions, runtime policy, Python version, and required quality gates.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            "<section><h2>Checks</h2><table><tr><th>ID</th><th>Category</th><th>Target</th><th>Expected</th><th>Actual</th><th>Status</th><th>Detail</th></tr>"
            + checks
            + "</table></section>",
            "<section><h2>Actions</h2><table><tr><th>Repository</th><th>Version</th><th>Line</th><th>Node 24 Native</th></tr>" + actions + "</table></section>",
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT CI workflow hygiene.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_ci_workflow_hygiene_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_ci_workflow_hygiene_html(report), encoding="utf-8")


def write_ci_workflow_hygiene_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "ci_workflow_hygiene.json",
        "csv": root / "ci_workflow_hygiene.csv",
        "markdown": root / "ci_workflow_hygiene.md",
        "html": root / "ci_workflow_hygiene.html",
    }
    write_ci_workflow_hygiene_json(report, paths["json"])
    write_ci_workflow_hygiene_csv(report, paths["csv"])
    write_ci_workflow_hygiene_markdown(report, paths["markdown"])
    write_ci_workflow_hygiene_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _summary(report: dict[str, Any]) -> dict[str, Any]:
    return dict(report.get("summary")) if isinstance(report.get("summary"), dict) else {}


def _actions(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("actions")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("checks")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _check_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('id'))}</td>"
        f"<td>{_e(item.get('category'))}</td>"
        f"<td>{_e(item.get('target'))}</td>"
        f"<td>{_e(item.get('expected'))}</td>"
        f"<td>{_e(item.get('actual'))}</td>"
        f"<td>{_e(item.get('status'))}</td>"
        f"<td>{_e(item.get('detail'))}</td>"
        "</tr>"
    )


def _action_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('repository'))}</td>"
        f"<td>{_e(item.get('version'))}</td>"
        f"<td>{_e(item.get('line'))}</td>"
        f"<td>{_e(item.get('node24_native'))}</td>"
        "</tr>"
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
header, section, footer { max-width: 1100px; margin: 0 auto 18px; }
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
