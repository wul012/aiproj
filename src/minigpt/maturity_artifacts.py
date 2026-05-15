from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any


def write_maturity_summary_json(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def write_maturity_summary_csv(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "key",
        "title",
        "status",
        "maturity_level",
        "target_level",
        "score_percent",
        "covered_count",
        "target_count",
        "covered_versions",
        "missing_versions",
        "next_step",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(summary.get("capabilities")):
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_maturity_summary_markdown(summary: dict[str, Any]) -> str:
    overview = _dict(summary.get("summary"))
    lines = [
        f"# {summary.get('title', 'MiniGPT project maturity summary')}",
        "",
        f"- Generated: `{summary.get('generated_at')}`",
        f"- Project root: `{summary.get('project_root')}`",
        "",
        "## Overview",
        "",
        *_markdown_table(
            [
                ("Current version", overview.get("current_version")),
                ("Published versions", overview.get("published_version_count")),
                ("Archive versions", overview.get("archive_version_count")),
                ("Explanation versions", overview.get("explanation_version_count")),
                ("Average maturity level", overview.get("average_maturity_level")),
                ("Overall status", overview.get("overall_status")),
                ("Registry runs", overview.get("registry_runs")),
                ("Release readiness trend", overview.get("release_readiness_trend_status")),
                ("Release readiness deltas", overview.get("release_readiness_delta_count")),
                ("Release readiness regressions", overview.get("release_readiness_regressed_count")),
                ("Request history status", overview.get("request_history_status")),
                ("Request history records", overview.get("request_history_records")),
            ]
        ),
        "",
        "## Capability Matrix",
        "",
        "| Area | Status | Level | Score | Evidence | Next step |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in _list_of_dicts(summary.get("capabilities")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("title")),
                    _md(row.get("status")),
                    _md(f"{row.get('maturity_level')}/{row.get('target_level')}"),
                    _md(f"{row.get('score_percent')}%"),
                    _md(row.get("evidence")),
                    _md(row.get("next_step")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Phase Timeline", "", "| Versions | Phase | Status |", "| --- | --- | --- |"])
    for phase in _list_of_dicts(summary.get("phase_timeline")):
        lines.append(f"| {_md(phase.get('versions'))} | {_md(phase.get('title'))} | {_md(phase.get('status'))} |")
    request_history = _dict(summary.get("request_history_context"))
    lines.extend(
        [
            "",
            "## Request History Context",
            "",
            *_markdown_table(
                [
                    ("Available", request_history.get("available")),
                    ("Status", request_history.get("status")),
                    ("Records", request_history.get("total_log_records")),
                    ("Invalid", request_history.get("invalid_record_count")),
                    ("Timeout rate", request_history.get("timeout_rate")),
                    ("Bad request rate", request_history.get("bad_request_rate")),
                    ("Error rate", request_history.get("error_rate")),
                    ("Checkpoints", request_history.get("unique_checkpoint_count")),
                    ("Latest", request_history.get("latest_timestamp")),
                ]
            ),
        ]
    )
    release_readiness = _dict(summary.get("release_readiness_context"))
    lines.extend(
        [
            "",
            "## Release Readiness Trend Context",
            "",
            *_markdown_table(
                [
                    ("Available", release_readiness.get("available")),
                    ("Trend status", release_readiness.get("trend_status")),
                    ("Comparison counts", _fmt_mapping(release_readiness.get("comparison_counts"))),
                    ("Delta count", release_readiness.get("delta_count")),
                    ("Runs with deltas", release_readiness.get("run_count")),
                    ("Regressed", release_readiness.get("regressed_count")),
                    ("Improved", release_readiness.get("improved_count")),
                    ("Panel changed", release_readiness.get("panel_changed_count")),
                    ("Changed panels", release_readiness.get("changed_panel_delta_count")),
                    ("Max status delta", release_readiness.get("max_abs_status_delta")),
                ]
            ),
        ]
    )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(summary.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_maturity_summary_markdown(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_summary_markdown(summary), encoding="utf-8")


def render_maturity_summary_html(summary: dict[str, Any]) -> str:
    overview = _dict(summary.get("summary"))
    registry = _dict(summary.get("registry_context"))
    release_readiness = _dict(summary.get("release_readiness_context"))
    request_history = _dict(summary.get("request_history_context"))
    stats = [
        ("Current", overview.get("current_version")),
        ("Versions", overview.get("published_version_count")),
        ("Archives", overview.get("archive_version_count")),
        ("Explanations", overview.get("explanation_version_count")),
        ("Maturity", overview.get("average_maturity_level")),
        ("Status", overview.get("overall_status")),
        ("Runs", overview.get("registry_runs")),
        ("Pair deltas", registry.get("pair_delta_cases")),
        ("Release trend", release_readiness.get("trend_status")),
        ("Readiness deltas", release_readiness.get("delta_count")),
        ("Requests", request_history.get("total_log_records")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(summary.get('title', 'MiniGPT project maturity summary'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(summary.get('title', 'MiniGPT project maturity summary'))}</h1><p>{_e(summary.get('project_root'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _capability_section(_list_of_dicts(summary.get("capabilities"))),
            _timeline_section(_list_of_dicts(summary.get("phase_timeline"))),
            _registry_section(registry),
            _release_readiness_section(release_readiness),
            _request_history_section(request_history),
            _recommendation_section(_string_list(summary.get("recommendations"))),
            "<footer>Generated by MiniGPT maturity summary exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_maturity_summary_html(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_summary_html(summary), encoding="utf-8")


def write_maturity_summary_outputs(summary: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "maturity_summary.json",
        "csv": root / "maturity_summary.csv",
        "markdown": root / "maturity_summary.md",
        "html": root / "maturity_summary.html",
    }
    write_maturity_summary_json(summary, paths["json"])
    write_maturity_summary_csv(summary, paths["csv"])
    write_maturity_summary_markdown(summary, paths["markdown"])
    write_maturity_summary_html(summary, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _capability_section(rows: list[dict[str, Any]]) -> str:
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('title'))}</strong><br><span>{_e(row.get('key'))}</span></td>"
            f"<td><span class=\"pill {_e(row.get('status'))}\">{_e(row.get('status'))}</span></td>"
            f"<td>{_e(row.get('maturity_level'))}/{_e(row.get('target_level'))}</td>"
            f"<td>{_e(row.get('score_percent'))}%<br><span>{_e(_version_list(row.get('covered_versions')))}</span></td>"
            f"<td>{_e(row.get('evidence'))}</td>"
            f"<td>{_e(row.get('next_step'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Capability Matrix</h2>'
        '<table><thead><tr><th>Area</th><th>Status</th><th>Level</th><th>Coverage</th><th>Evidence</th><th>Next Step</th></tr></thead><tbody>'
        + "".join(table_rows)
        + "</tbody></table></section>"
    )


def _timeline_section(rows: list[dict[str, Any]]) -> str:
    items = []
    for row in rows:
        items.append(
            "<tr>"
            f"<td>{_e(row.get('versions'))}</td>"
            f"<td>{_e(row.get('title'))}</td>"
            f"<td>{_e(row.get('covered_count'))}/{_e(row.get('target_count'))}</td>"
            f"<td>{_e(row.get('status'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Phase Timeline</h2>'
        '<table><thead><tr><th>Versions</th><th>Phase</th><th>Coverage</th><th>Status</th></tr></thead><tbody>'
        + "".join(items)
        + "</tbody></table></section>"
    )


def _registry_section(registry: dict[str, Any]) -> str:
    rows = [
        ("Available", registry.get("available")),
        ("Runs", registry.get("run_count")),
        ("Pair reports", _fmt_mapping(registry.get("pair_report_counts"))),
        ("Pair delta cases", registry.get("pair_delta_cases")),
        ("Max generated delta", registry.get("pair_delta_max_generated")),
        ("Quality counts", _fmt_mapping(registry.get("quality_counts"))),
        ("Generation quality", _fmt_mapping(registry.get("generation_quality_counts"))),
    ]
    return '<section class="panel"><h2>Registry Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def _release_readiness_section(release_readiness: dict[str, Any]) -> str:
    rows = [
        ("Available", release_readiness.get("available")),
        ("Trend status", release_readiness.get("trend_status")),
        ("Comparison counts", _fmt_mapping(release_readiness.get("comparison_counts"))),
        ("Delta count", release_readiness.get("delta_count")),
        ("Runs with deltas", release_readiness.get("run_count")),
        ("Regressed", release_readiness.get("regressed_count")),
        ("Improved", release_readiness.get("improved_count")),
        ("Panel changed", release_readiness.get("panel_changed_count")),
        ("Changed panels", release_readiness.get("changed_panel_delta_count")),
        ("Max status delta", release_readiness.get("max_abs_status_delta")),
    ]
    return '<section class="panel"><h2>Release Readiness Trend Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def _request_history_section(request_history: dict[str, Any]) -> str:
    rows = [
        ("Available", request_history.get("available")),
        ("Status", request_history.get("status")),
        ("Records", request_history.get("total_log_records")),
        ("Invalid", request_history.get("invalid_record_count")),
        ("OK", request_history.get("ok_count")),
        ("Timeout", request_history.get("timeout_count")),
        ("Bad request", request_history.get("bad_request_count")),
        ("Error", request_history.get("error_count")),
        ("Timeout rate", request_history.get("timeout_rate")),
        ("Error rate", request_history.get("error_rate")),
        ("Checkpoints", request_history.get("unique_checkpoint_count")),
        ("Latest", request_history.get("latest_timestamp")),
    ]
    return '<section class="panel"><h2>Request History Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def _recommendation_section(items: list[str]) -> str:
    return '<section class="panel"><h2>Recommendations</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --green:#047857; --amber:#b45309; --red:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:58px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _version_list(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    return ", ".join(f"v{item}" for item in value)


def _fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value))


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return value


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


__all__ = [
    "render_maturity_summary_html",
    "render_maturity_summary_markdown",
    "write_maturity_summary_csv",
    "write_maturity_summary_html",
    "write_maturity_summary_json",
    "write_maturity_summary_markdown",
    "write_maturity_summary_outputs",
]
