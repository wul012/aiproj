from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    write_json_payload,
)


def write_release_readiness_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_release_readiness_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = _list_of_dicts(report.get("rows"))
    fieldnames = [
        "readiness_path",
        "release_name",
        "readiness_status",
        "decision",
        "readiness_score",
        "gate_status",
        "audit_status",
        "audit_score_percent",
        "ci_workflow_status",
        "ci_workflow_failed_checks",
        "request_history_status",
        "maturity_status",
        "ready_runs",
        "missing_artifacts",
        "fail_panel_count",
        "warn_panel_count",
        "action_count",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def write_release_readiness_delta_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = _list_of_dicts(report.get("deltas"))
    fieldnames = [
        "baseline_path",
        "compared_path",
        "baseline_release",
        "compared_release",
        "baseline_status",
        "compared_status",
        "status_delta",
        "delta_status",
        "audit_score_delta",
        "ci_workflow_failed_check_delta",
        "ci_workflow_status_changed",
        "missing_artifact_delta",
        "fail_panel_delta",
        "warn_panel_delta",
        "changed_panels",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for delta in deltas:
            writer.writerow({key: _csv_value(delta.get(key)) for key in fieldnames})


def render_release_readiness_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT release readiness comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Baseline: `{report.get('baseline_path')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Readiness reports", summary.get("readiness_count")),
                ("Baseline status", summary.get("baseline_status")),
                ("Ready count", summary.get("ready_count")),
                ("Blocked count", summary.get("blocked_count")),
                ("Improved count", summary.get("improved_count")),
                ("Regressed count", summary.get("regressed_count")),
                ("Changed panel deltas", summary.get("changed_panel_delta_count")),
                ("CI workflow regressions", summary.get("ci_workflow_regression_count")),
            ]
        ),
        "",
        "## Readiness Matrix",
        "",
        "| Release | Status | Decision | Gate | Audit | Score | CI workflow | CI failed | Request history | Maturity | Fail panels | Warn panels |",
        "| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | --- | ---: | ---: |",
    ]
    for row in _list_of_dicts(report.get("rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("release_name") or row.get("readiness_path")),
                    _md(row.get("readiness_status")),
                    _md(row.get("decision")),
                    _md(row.get("gate_status")),
                    _md(row.get("audit_status")),
                    _md(row.get("audit_score_percent")),
                    _md(row.get("ci_workflow_status")),
                    _md(row.get("ci_workflow_failed_checks")),
                    _md(row.get("request_history_status")),
                    _md(row.get("maturity_status")),
                    _md(row.get("fail_panel_count")),
                    _md(row.get("warn_panel_count")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Deltas",
            "",
            "| Compared | Status delta | Panel changes | Explanation |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for delta in _list_of_dicts(report.get("deltas")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(delta.get("compared_release") or delta.get("compared_path")),
                    _md(delta.get("status_delta")),
                    _md(", ".join(_string_list(delta.get("changed_panels")))),
                    _md(delta.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_release_readiness_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_readiness_comparison_markdown(report), encoding="utf-8")


def render_release_readiness_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Reports", summary.get("readiness_count")),
        ("Baseline", summary.get("baseline_status")),
        ("Ready", summary.get("ready_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Improved", summary.get("improved_count")),
        ("Regressed", summary.get("regressed_count")),
        ("Panel deltas", summary.get("changed_panel_delta_count")),
        ("CI regressions", summary.get("ci_workflow_regression_count")),
        ("Generated", report.get("generated_at")),
    ]
    rows = "".join(_html_row(row) for row in _list_of_dicts(report.get("rows")))
    deltas = "".join(_html_delta(delta) for delta in _list_of_dicts(report.get("deltas")))
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT release readiness comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT release readiness comparison'))}</h1><p>baseline: {_e(report.get('baseline_path'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Readiness Matrix</h2><table><thead><tr><th>Release</th><th>Status</th><th>Decision</th><th>Gate</th><th>Audit</th><th>Score</th><th>CI workflow</th><th>CI failed</th><th>Request</th><th>Maturity</th><th>Panels</th></tr></thead><tbody>' + rows + "</tbody></table></section>",
            '<section class="panel"><h2>Deltas</h2><table><thead><tr><th>Compared</th><th>Status delta</th><th>Panel changes</th><th>Explanation</th></tr></thead><tbody>' + deltas + "</tbody></table></section>",
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT release readiness comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_release_readiness_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_readiness_comparison_html(report), encoding="utf-8")


def write_release_readiness_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "release_readiness_comparison.json",
        "csv": root / "release_readiness_comparison.csv",
        "delta_csv": root / "release_readiness_deltas.csv",
        "markdown": root / "release_readiness_comparison.md",
        "html": root / "release_readiness_comparison.html",
    }
    write_release_readiness_comparison_json(report, paths["json"])
    write_release_readiness_comparison_csv(report, paths["csv"])
    write_release_readiness_delta_csv(report, paths["delta_csv"])
    write_release_readiness_comparison_markdown(report, paths["markdown"])
    write_release_readiness_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _html_row(row: dict[str, Any]) -> str:
    status = str(row.get("readiness_status") or "missing")
    return (
        "<tr>"
        f"<td>{_e(row.get('release_name') or row.get('readiness_path'))}<br><span>{_e(row.get('readiness_path'))}</span></td>"
        f'<td><span class="pill {status}">{_e(status)}</span></td>'
        f"<td>{_e(row.get('decision'))}</td>"
        f"<td>{_e(row.get('gate_status'))}</td>"
        f"<td>{_e(row.get('audit_status'))}</td>"
        f"<td>{_e(_fmt(row.get('audit_score_percent')))}</td>"
        f"<td>{_e(row.get('ci_workflow_status'))}</td>"
        f"<td>{_e(row.get('ci_workflow_failed_checks'))}</td>"
        f"<td>{_e(row.get('request_history_status'))}</td>"
        f"<td>{_e(row.get('maturity_status'))}</td>"
        f"<td>{_e(row.get('fail_panel_count'))} fail / {_e(row.get('warn_panel_count'))} warn</td>"
        "</tr>"
    )


def _html_delta(delta: dict[str, Any]) -> str:
    status = str(delta.get("delta_status") or "same")
    return (
        "<tr>"
        f"<td>{_e(delta.get('compared_release') or delta.get('compared_path'))}<br><span>{_e(delta.get('compared_path'))}</span></td>"
        f'<td><span class="pill {status}">{_e(_status_delta_label(delta.get("status_delta")))}</span></td>'
        f"<td>{_e(', '.join(_string_list(delta.get('changed_panels'))))}</td>"
        f"<td>{_e(delta.get('explanation'))}</td>"
        "</tr>"
    )


def _list_section(title: str, values: Any) -> str:
    items = _string_list(values) or ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt(value))}</div>' + "</div>"


def _style() -> str:
    return """<style>
:root { --ink:#17202a; --muted:#566170; --line:#d5dce6; --page:#f6f7f3; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; --blue:#1f5f74; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(145px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:54px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; background:var(--blue); }
.pill.ready, .pill.improved { background:var(--green); }
.pill.review, .pill.incomplete, .pill.panel-changed { background:var(--amber); }
.pill.blocked, .pill.regressed { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _status_delta_label(value: Any) -> str:
    delta = int(value or 0)
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _csv_value(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(_string_list(value))
    return str(csv_cell(value))


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _md(value: Any) -> str:
    return _fmt(value).replace("|", "\\|").replace("\n", " ")


__all__ = [
    "render_release_readiness_comparison_html",
    "render_release_readiness_comparison_markdown",
    "write_release_readiness_comparison_csv",
    "write_release_readiness_comparison_html",
    "write_release_readiness_comparison_json",
    "write_release_readiness_comparison_markdown",
    "write_release_readiness_comparison_outputs",
    "write_release_readiness_delta_csv",
]
