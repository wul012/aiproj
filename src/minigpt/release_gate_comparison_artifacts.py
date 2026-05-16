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


def write_release_gate_profile_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_release_gate_profile_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = _list_of_dicts(report.get("rows"))
    fieldnames = [
        "bundle_path",
        "release_name",
        "policy_profile",
        "gate_status",
        "decision",
        "audit_score_percent",
        "minimum_audit_score",
        "ready_runs",
        "minimum_ready_runs",
        "require_generation_quality_audit_checks",
        "require_request_history_summary_audit_check",
        "pass_count",
        "warn_count",
        "fail_count",
        "failed_checks",
        "warned_checks",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def write_release_gate_profile_delta_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = _list_of_dicts(report.get("deltas"))
    fieldnames = [
        "bundle_path",
        "release_name",
        "baseline_profile",
        "compared_profile",
        "baseline_decision",
        "compared_decision",
        "delta_status",
        "decision_changed",
        "baseline_minimum_audit_score",
        "compared_minimum_audit_score",
        "baseline_require_generation_quality",
        "compared_require_generation_quality",
        "baseline_require_request_history_summary",
        "compared_require_request_history_summary",
        "added_failed_checks",
        "removed_failed_checks",
        "added_warned_checks",
        "removed_warned_checks",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for delta in deltas:
            writer.writerow({key: _csv_value(delta.get(key)) for key in fieldnames})


def render_release_gate_profile_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT release gate profile comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Bundles: `{summary.get('bundle_count', 0)}`",
        f"- Profiles: `{', '.join(_string_list(report.get('policy_profiles')))}`",
        f"- Baseline profile: `{report.get('baseline_profile')}`",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Total rows | {_md(summary.get('row_count'))} |",
        f"| Approved | {_md(summary.get('approved_count'))} |",
        f"| Needs review | {_md(summary.get('needs_review_count'))} |",
        f"| Blocked | {_md(summary.get('blocked_count'))} |",
        f"| Baseline profile | {_md(summary.get('baseline_profile'))} |",
        f"| Profile deltas | {_md(summary.get('delta_count'))} |",
        f"| Decision deltas | {_md(summary.get('decision_delta_count'))} |",
        f"| Check deltas | {_md(summary.get('check_delta_count'))} |",
        "",
        "## Profile Matrix",
        "",
        "| Bundle | Profile | Decision | Gate | Audit score | Min score | Generation quality required | Request history required | Failed checks | Warned checks |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("release_name") or row.get("bundle_path")),
                    _md(row.get("policy_profile")),
                    _md(row.get("decision")),
                    _md(row.get("gate_status")),
                    _md(row.get("audit_score_percent")),
                    _md(row.get("minimum_audit_score")),
                    _md(row.get("require_generation_quality_audit_checks")),
                    _md(row.get("require_request_history_summary_audit_check")),
                    _md(", ".join(_string_list(row.get("failed_checks")))),
                    _md(", ".join(_string_list(row.get("warned_checks")))),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Profile Deltas",
            "",
            "| Bundle | Baseline | Compared | Decision delta | Added failed checks | Removed failed checks | Explanation |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for delta in _list_of_dicts(report.get("deltas")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(delta.get("release_name") or delta.get("bundle_path")),
                    _md(delta.get("baseline_profile")),
                    _md(delta.get("compared_profile")),
                    _md(f"{delta.get('baseline_decision')} -> {delta.get('compared_decision')}"),
                    _md(", ".join(_string_list(delta.get("added_failed_checks")))),
                    _md(", ".join(_string_list(delta.get("removed_failed_checks")))),
                    _md(delta.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_release_gate_profile_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_gate_profile_comparison_markdown(report), encoding="utf-8")


def render_release_gate_profile_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Bundles", summary.get("bundle_count")),
        ("Profiles", summary.get("profile_count")),
        ("Approved", summary.get("approved_count")),
        ("Review", summary.get("needs_review_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Baseline", summary.get("baseline_profile")),
        ("Decision deltas", summary.get("decision_delta_count")),
        ("Generated", report.get("generated_at")),
    ]
    rows = "".join(_html_row(row) for row in _list_of_dicts(report.get("rows")))
    deltas = "".join(_html_delta_row(delta) for delta in _list_of_dicts(report.get("deltas")))
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT release gate profile comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT release gate profile comparison'))}</h1><p>profiles: {_e(', '.join(_string_list(report.get('policy_profiles'))))}; baseline: {_e(report.get('baseline_profile'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Profile Matrix</h2><table><thead><tr>'
            "<th>Bundle</th><th>Profile</th><th>Decision</th><th>Gate</th><th>Audit</th><th>Min</th><th>Generation</th><th>Request history</th><th>Failed</th><th>Warned</th>"
            "</tr></thead><tbody>"
            + rows
            + "</tbody></table></section>",
            '<section class="panel"><h2>Profile Deltas</h2><table><thead><tr>'
            "<th>Bundle</th><th>Baseline</th><th>Compared</th><th>Decision</th><th>Added failed</th><th>Removed failed</th><th>Explanation</th>"
            "</tr></thead><tbody>"
            + deltas
            + "</tbody></table></section>",
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT release gate profile comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_release_gate_profile_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_gate_profile_comparison_html(report), encoding="utf-8")


def write_release_gate_profile_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "release_gate_profile_comparison.json",
        "csv": root / "release_gate_profile_comparison.csv",
        "delta_csv": root / "release_gate_profile_deltas.csv",
        "markdown": root / "release_gate_profile_comparison.md",
        "html": root / "release_gate_profile_comparison.html",
    }
    write_release_gate_profile_comparison_json(report, paths["json"])
    write_release_gate_profile_comparison_csv(report, paths["csv"])
    write_release_gate_profile_delta_csv(report, paths["delta_csv"])
    write_release_gate_profile_comparison_markdown(report, paths["markdown"])
    write_release_gate_profile_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _html_row(row: dict[str, Any]) -> str:
    status = str(row.get("gate_status") or "missing")
    return (
        "<tr>"
        f"<td>{_e(row.get('release_name') or row.get('bundle_path'))}<br><span>{_e(row.get('bundle_path'))}</span></td>"
        f"<td><strong>{_e(row.get('policy_profile'))}</strong><br><span>{_e(row.get('profile_description'))}</span></td>"
        f"<td>{_e(row.get('decision'))}</td>"
        f'<td><span class="pill {status}">{_e(status)}</span></td>'
        f"<td>{_e(row.get('audit_score_percent'))}</td>"
        f"<td>{_e(row.get('minimum_audit_score'))}</td>"
        f"<td>{_e(row.get('require_generation_quality_audit_checks'))}</td>"
        f"<td>{_e(row.get('require_request_history_summary_audit_check'))}</td>"
        f"<td>{_e(', '.join(_string_list(row.get('failed_checks'))))}</td>"
        f"<td>{_e(', '.join(_string_list(row.get('warned_checks'))))}</td>"
        "</tr>"
    )


def _html_delta_row(delta: dict[str, Any]) -> str:
    status = str(delta.get("delta_status") or "same")
    return (
        "<tr>"
        f"<td>{_e(delta.get('release_name') or delta.get('bundle_path'))}<br><span>{_e(delta.get('bundle_path'))}</span></td>"
        f"<td>{_e(delta.get('baseline_profile'))}</td>"
        f"<td><strong>{_e(delta.get('compared_profile'))}</strong><br><span>{_e(status)}</span></td>"
        f"<td>{_e(delta.get('baseline_decision'))} -> {_e(delta.get('compared_decision'))}</td>"
        f"<td>{_e(', '.join(_string_list(delta.get('added_failed_checks'))))}</td>"
        f"<td>{_e(', '.join(_string_list(delta.get('removed_failed_checks'))))}</td>"
        f"<td>{_e(delta.get('explanation'))}</td>"
        "</tr>"
    )


def _list_section(title: str, values: Any) -> str:
    items = _string_list(values) or ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt_any(value))}</div>' + "</div>"


def _style() -> str:
    return """<style>
:root { --ink:#101828; --muted:#4b5563; --line:#d7dce5; --page:#f6f8fb; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:54px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _csv_value(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(_string_list(value))
    return str(csv_cell(value))


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


def _md(value: Any) -> str:
    return _fmt_any(value).replace("|", "\\|").replace("\n", " ")


__all__ = [
    "render_release_gate_profile_comparison_html",
    "render_release_gate_profile_comparison_markdown",
    "write_release_gate_profile_comparison_csv",
    "write_release_gate_profile_comparison_html",
    "write_release_gate_profile_comparison_json",
    "write_release_gate_profile_comparison_markdown",
    "write_release_gate_profile_comparison_outputs",
    "write_release_gate_profile_delta_csv",
]
