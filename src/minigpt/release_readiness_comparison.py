from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)


STATUS_ORDER = {
    "blocked": 0,
    "incomplete": 1,
    "review": 2,
    "ready": 3,
}


def build_release_readiness_comparison(
    readiness_paths: list[str | Path],
    *,
    baseline_path: str | Path | None = None,
    title: str = "MiniGPT release readiness comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    paths = [Path(path) for path in readiness_paths]
    if baseline_path is not None:
        baseline = Path(baseline_path)
        paths = [baseline] + [path for path in paths if path != baseline]
    if not paths:
        raise ValueError("at least one release_readiness.json path is required")
    reports = [_read_required_json(path) for path in paths]
    rows = [_row_from_report(path, report) for path, report in zip(paths, reports)]
    baseline_row = rows[0]
    deltas = [_delta_from_baseline(baseline_row, row) for row in rows[1:]]
    summary = _summary(rows, deltas, baseline_row)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "baseline_path": str(paths[0]),
        "readiness_paths": [str(path) for path in paths],
        "summary": summary,
        "rows": rows,
        "deltas": deltas,
        "recommendations": _recommendations(summary, deltas),
    }


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
            ]
        ),
        "",
        "## Readiness Matrix",
        "",
        "| Release | Status | Decision | Gate | Audit | Score | Request history | Maturity | Fail panels | Warn panels |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | ---: |",
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
            '<section class="panel"><h2>Readiness Matrix</h2><table><thead><tr><th>Release</th><th>Status</th><th>Decision</th><th>Gate</th><th>Audit</th><th>Score</th><th>Request</th><th>Maturity</th><th>Panels</th></tr></thead><tbody>' + rows + "</tbody></table></section>",
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


def _row_from_report(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    panels = _list_of_dicts(report.get("panels"))
    status = str(summary.get("readiness_status") or "missing")
    return {
        "readiness_path": str(path),
        "release_name": summary.get("release_name"),
        "readiness_status": status,
        "decision": summary.get("decision"),
        "readiness_score": STATUS_ORDER.get(status, -1),
        "gate_status": summary.get("gate_status"),
        "audit_status": summary.get("audit_status"),
        "audit_score_percent": summary.get("audit_score_percent"),
        "request_history_status": summary.get("request_history_status"),
        "maturity_status": summary.get("maturity_status"),
        "ready_runs": summary.get("ready_runs"),
        "missing_artifacts": summary.get("missing_artifacts"),
        "fail_panel_count": summary.get("fail_panel_count"),
        "warn_panel_count": summary.get("warn_panel_count"),
        "action_count": len(_string_list(report.get("actions"))),
        "panel_statuses": {str(panel.get("key")): panel.get("status") for panel in panels if panel.get("key")},
    }


def _delta_from_baseline(baseline: dict[str, Any], compared: dict[str, Any]) -> dict[str, Any]:
    status_delta = int(compared.get("readiness_score") or 0) - int(baseline.get("readiness_score") or 0)
    baseline_panels = _dict(baseline.get("panel_statuses"))
    compared_panels = _dict(compared.get("panel_statuses"))
    changed = []
    for key in sorted(set(baseline_panels) | set(compared_panels)):
        before = baseline_panels.get(key)
        after = compared_panels.get(key)
        if before != after:
            changed.append(f"{key}:{before}->{after}")
    delta = {
        "baseline_path": baseline.get("readiness_path"),
        "compared_path": compared.get("readiness_path"),
        "baseline_release": baseline.get("release_name"),
        "compared_release": compared.get("release_name"),
        "baseline_status": baseline.get("readiness_status"),
        "compared_status": compared.get("readiness_status"),
        "status_delta": status_delta,
        "delta_status": _delta_status(status_delta, changed),
        "audit_score_delta": _number_delta(compared.get("audit_score_percent"), baseline.get("audit_score_percent")),
        "missing_artifact_delta": _number_delta(compared.get("missing_artifacts"), baseline.get("missing_artifacts")),
        "fail_panel_delta": _number_delta(compared.get("fail_panel_count"), baseline.get("fail_panel_count")),
        "warn_panel_delta": _number_delta(compared.get("warn_panel_count"), baseline.get("warn_panel_count")),
        "changed_panels": changed,
    }
    delta["explanation"] = _delta_explanation(delta)
    return delta


def _delta_status(status_delta: int, changed_panels: list[str]) -> str:
    if status_delta > 0:
        return "improved"
    if status_delta < 0:
        return "regressed"
    if changed_panels:
        return "panel-changed"
    return "same"


def _delta_explanation(delta: dict[str, Any]) -> str:
    compared = delta.get("compared_release") or delta.get("compared_path")
    status = delta.get("delta_status")
    parts = [
        f"{compared} moves from {delta.get('baseline_status')} to {delta.get('compared_status')} ({status_delta_label(delta.get('status_delta'))})."
    ]
    changed = _string_list(delta.get("changed_panels"))
    if changed:
        parts.append("Changed panel(s): " + ", ".join(changed) + ".")
    if delta.get("audit_score_delta") not in {None, 0, 0.0}:
        parts.append(f"Audit score delta is {delta.get('audit_score_delta')}.")
    if status == "same" and not changed:
        parts.append("No readiness status or panel delta is present.")
    return " ".join(parts)


def status_delta_label(value: Any) -> str:
    delta = int(value or 0)
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def _summary(rows: list[dict[str, Any]], deltas: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "readiness_count": len(rows),
        "baseline_release": baseline.get("release_name"),
        "baseline_status": baseline.get("readiness_status"),
        "ready_count": sum(1 for row in rows if row.get("readiness_status") == "ready"),
        "review_count": sum(1 for row in rows if row.get("readiness_status") == "review"),
        "blocked_count": sum(1 for row in rows if row.get("readiness_status") == "blocked"),
        "incomplete_count": sum(1 for row in rows if row.get("readiness_status") == "incomplete"),
        "improved_count": sum(1 for delta in deltas if delta.get("delta_status") == "improved"),
        "regressed_count": sum(1 for delta in deltas if delta.get("delta_status") == "regressed"),
        "changed_panel_delta_count": sum(1 for delta in deltas if delta.get("changed_panels")),
    }


def _recommendations(summary: dict[str, Any], deltas: list[dict[str, Any]]) -> list[str]:
    if int(summary.get("regressed_count") or 0):
        return ["At least one readiness report regressed from the baseline; inspect delta explanations before release handoff."]
    if int(summary.get("improved_count") or 0):
        return ["Readiness improved against the baseline; keep the comparison report with release evidence."]
    if int(summary.get("blocked_count") or 0):
        return ["At least one readiness report is blocked; fix failed panels before comparing release quality as improved."]
    if any(delta.get("changed_panels") for delta in deltas):
        return ["Readiness status stayed stable, but panel-level changes should be reviewed."]
    return ["Readiness reports are stable against the baseline."]


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release readiness comparison input must be a JSON object: {path}")
    return payload


def _number_delta(left: Any, right: Any) -> float | int | None:
    if left is None or right is None:
        return None
    delta = float(left) - float(right)
    return int(delta) if delta.is_integer() else round(delta, 4)


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
        f'<td><span class="pill {status}">{_e(status_delta_label(delta.get("status_delta")))}</span></td>'
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
