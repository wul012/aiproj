from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)


def build_release_readiness_dashboard(
    bundle_path: str | Path,
    *,
    gate_path: str | Path | None = None,
    audit_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    maturity_path: str | Path | None = None,
    title: str = "MiniGPT release readiness dashboard",
    generated_at: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    bundle_file = Path(bundle_path)
    bundle = _read_required_json(bundle_file)
    inputs = _dict(bundle.get("inputs"))
    root = bundle_file.parent.parent

    registry_file = _resolve_path(inputs.get("registry_path"))
    audit_file = _resolve_optional_path(audit_path, inputs.get("project_audit_path"), _candidate(root, "audit", "project_audit.json"))
    request_file = _resolve_optional_path(
        request_history_summary_path,
        inputs.get("request_history_summary_path"),
        _candidate(root, "request-history-summary", "request_history_summary.json"),
    )
    gate_file = _resolve_optional_path(gate_path, None, _candidate(root, "release-gate", "gate_report.json"))
    maturity_file = _resolve_optional_path(maturity_path, None, _candidate(root, "maturity-summary", "maturity_summary.json"))

    registry = _read_json(registry_file, warnings, "registry") if registry_file is not None else None
    audit = _read_json(audit_file, warnings, "project audit") if audit_file is not None else None
    request_history = _read_json(request_file, warnings, "request history summary") if request_file is not None else None
    gate = _read_json(gate_file, warnings, "release gate") if gate_file is not None else None
    maturity = _read_json(maturity_file, warnings, "maturity summary") if maturity_file is not None else None

    panels = [
        _registry_panel(registry_file, registry),
        _bundle_panel(bundle_file, bundle),
        _audit_panel(audit_file, audit),
        _gate_panel(gate_file, gate),
        _request_history_panel(request_file, request_history),
        _maturity_panel(maturity_file, maturity),
    ]
    actions = _actions(bundle, gate if isinstance(gate, dict) else None, audit if isinstance(audit, dict) else None, panels)
    summary = _summary(bundle, gate if isinstance(gate, dict) else None, audit if isinstance(audit, dict) else None, request_history if isinstance(request_history, dict) else None, maturity if isinstance(maturity, dict) else None, panels)
    evidence = _evidence(bundle)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "bundle_path": str(bundle_file),
        "inputs": {
            "registry_path": None if registry_file is None else str(registry_file),
            "project_audit_path": None if audit_file is None else str(audit_file),
            "release_gate_path": None if gate_file is None else str(gate_file),
            "request_history_summary_path": None if request_file is None else str(request_file),
            "maturity_summary_path": None if maturity_file is None else str(maturity_file),
        },
        "summary": summary,
        "panels": panels,
        "actions": actions,
        "evidence": evidence,
        "warnings": warnings,
    }


def write_release_readiness_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def render_release_readiness_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT release readiness dashboard')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Bundle: `{report.get('bundle_path')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Readiness status", summary.get("readiness_status")),
                ("Decision", summary.get("decision")),
                ("Release", summary.get("release_name")),
                ("Gate", summary.get("gate_status")),
                ("Audit", summary.get("audit_status")),
                ("Audit score", summary.get("audit_score_percent")),
                ("Request history", summary.get("request_history_status")),
                ("Maturity", summary.get("maturity_status")),
                ("Ready runs", summary.get("ready_runs")),
                ("Missing artifacts", summary.get("missing_artifacts")),
            ]
        ),
        "",
        "## Panels",
        "",
        "| Status | Panel | Detail | Source |",
        "| --- | --- | --- | --- |",
    ]
    for panel in _list_of_dicts(report.get("panels")):
        lines.append(f"| {_md(panel.get('status'))} | {_md(panel.get('title'))} | {_md(panel.get('detail'))} | {_md(panel.get('source_path'))} |")
    lines.extend(["", "## Actions", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("actions")))
    lines.extend(["", "## Evidence", ""])
    lines.extend(_evidence_lines(_list_of_dicts(report.get("evidence"))))
    warnings = _string_list(report.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_release_readiness_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_readiness_markdown(report), encoding="utf-8")


def render_release_readiness_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Readiness", summary.get("readiness_status")),
        ("Decision", summary.get("decision")),
        ("Release", summary.get("release_status")),
        ("Gate", summary.get("gate_status")),
        ("Audit", summary.get("audit_status")),
        ("Score", _fmt(summary.get("audit_score_percent"))),
        ("Requests", summary.get("request_history_status")),
        ("Maturity", summary.get("maturity_status")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT release readiness dashboard'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT release readiness dashboard'))}</h1><p>{_e(report.get('bundle_path'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _panel_section(_list_of_dicts(report.get("panels"))),
            _list_section("Actions", report.get("actions")),
            _evidence_section(_list_of_dicts(report.get("evidence"))),
            _list_section("Warnings", report.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT release readiness dashboard.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_release_readiness_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_readiness_html(report), encoding="utf-8")


def write_release_readiness_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "release_readiness.json",
        "markdown": root / "release_readiness.md",
        "html": root / "release_readiness.html",
    }
    write_release_readiness_json(report, paths["json"])
    write_release_readiness_markdown(report, paths["markdown"])
    write_release_readiness_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _summary(
    bundle: dict[str, Any],
    gate: dict[str, Any] | None,
    audit: dict[str, Any] | None,
    request_history: dict[str, Any] | None,
    maturity: dict[str, Any] | None,
    panels: list[dict[str, Any]],
) -> dict[str, Any]:
    bundle_summary = _dict(bundle.get("summary"))
    gate_summary = _dict(gate.get("summary")) if isinstance(gate, dict) else {}
    audit_summary = _dict(audit.get("summary")) if isinstance(audit, dict) else {}
    request_summary = _dict(request_history.get("summary")) if isinstance(request_history, dict) else {}
    maturity_summary = _dict(maturity.get("summary")) if isinstance(maturity, dict) else {}
    status = _readiness_status(panels, gate)
    return {
        "readiness_status": status,
        "decision": _decision(status),
        "release_name": bundle.get("release_name"),
        "release_status": bundle_summary.get("release_status"),
        "gate_status": gate_summary.get("gate_status"),
        "gate_decision": gate_summary.get("decision"),
        "audit_status": audit_summary.get("overall_status") or bundle_summary.get("audit_status"),
        "audit_score_percent": audit_summary.get("score_percent") or bundle_summary.get("audit_score_percent"),
        "request_history_status": request_summary.get("status") or bundle_summary.get("request_history_status"),
        "request_history_records": request_summary.get("total_log_records") or bundle_summary.get("request_history_records"),
        "maturity_status": maturity_summary.get("overall_status"),
        "current_version": maturity_summary.get("current_version"),
        "ready_runs": bundle_summary.get("ready_runs") or audit_summary.get("ready_runs"),
        "missing_artifacts": bundle_summary.get("missing_artifacts"),
        "panel_count": len(panels),
        "fail_panel_count": sum(1 for panel in panels if panel.get("status") == "fail"),
        "warn_panel_count": sum(1 for panel in panels if panel.get("status") == "warn"),
    }


def _readiness_status(panels: list[dict[str, Any]], gate: dict[str, Any] | None) -> str:
    if not isinstance(gate, dict):
        return "incomplete"
    statuses = [panel.get("status") for panel in panels]
    if "fail" in statuses:
        return "blocked"
    if "warn" in statuses:
        return "review"
    return "ready"


def _decision(status: str) -> str:
    return {
        "ready": "ship",
        "review": "review",
        "blocked": "block",
        "incomplete": "collect-evidence",
    }.get(status, "review")


def _registry_panel(path: Path | None, registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return _panel("registry", "Registry", "warn", "registry evidence missing", path)
    best = _dict(registry.get("best_by_best_val_loss"))
    return _panel(
        "registry",
        "Registry",
        "pass" if registry.get("run_count") else "warn",
        f"runs={_fmt(registry.get('run_count'))}; best={best.get('name') or 'missing'}; best_val_loss={_fmt(best.get('best_val_loss'))}",
        path,
    )


def _bundle_panel(path: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(bundle.get("summary"))
    release_status = summary.get("release_status")
    status = "pass" if release_status == "release-ready" else "fail"
    return _panel(
        "release_bundle",
        "Release Bundle",
        status,
        f"release_status={release_status or 'missing'}; artifacts={_fmt(summary.get('available_artifacts'))} available/{_fmt(summary.get('missing_artifacts'))} missing",
        path,
    )


def _audit_panel(path: Path | None, audit: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(audit, dict):
        return _panel("project_audit", "Project Audit", "warn", "project_audit.json missing", path)
    summary = _dict(audit.get("summary"))
    audit_status = str(summary.get("overall_status") or "missing")
    return _panel(
        "project_audit",
        "Project Audit",
        _status_from_check_status(audit_status),
        f"overall={audit_status}; score={_fmt(summary.get('score_percent'))}; checks={_fmt(summary.get('pass_count'))} pass/{_fmt(summary.get('warn_count'))} warn/{_fmt(summary.get('fail_count'))} fail",
        path,
    )


def _gate_panel(path: Path | None, gate: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(gate, dict):
        return _panel("release_gate", "Release Gate", "warn", "gate_report.json missing", path)
    summary = _dict(gate.get("summary"))
    gate_status = str(summary.get("gate_status") or "missing")
    return _panel(
        "release_gate",
        "Release Gate",
        _status_from_check_status(gate_status),
        f"gate={gate_status}; decision={summary.get('decision') or 'missing'}; checks={_fmt(summary.get('pass_count'))} pass/{_fmt(summary.get('warn_count'))} warn/{_fmt(summary.get('fail_count'))} fail",
        path,
    )


def _request_history_panel(path: Path | None, request_history: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history, dict):
        return _panel("request_history", "Request History Summary", "warn", "request_history_summary.json missing", path)
    summary = _dict(request_history.get("summary"))
    request_status = str(summary.get("status") or "missing")
    return _panel(
        "request_history",
        "Request History Summary",
        "pass" if request_status == "pass" else "warn",
        f"status={request_status}; records={_fmt(summary.get('total_log_records'))}; invalid={_fmt(summary.get('invalid_record_count'))}; timeout_rate={_fmt(summary.get('timeout_rate'))}",
        path,
    )


def _maturity_panel(path: Path | None, maturity: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(maturity, dict):
        return _panel("maturity", "Maturity Summary", "warn", "maturity_summary.json missing", path)
    summary = _dict(maturity.get("summary"))
    status = str(summary.get("overall_status") or "missing")
    return _panel(
        "maturity",
        "Maturity Summary",
        _status_from_check_status(status),
        f"overall={status}; current_version={_fmt(summary.get('current_version'))}; average_level={_fmt(summary.get('average_maturity_level'))}",
        path,
    )


def _panel(key: str, title: str, status: str, detail: str, source_path: Path | None) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "status": status,
        "detail": detail,
        "source_path": None if source_path is None else str(source_path),
    }


def _actions(bundle: dict[str, Any], gate: dict[str, Any] | None, audit: dict[str, Any] | None, panels: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    has_issue = False
    for panel in panels:
        if panel.get("status") == "fail":
            has_issue = True
            items.append(f"Fix failing panel: {panel.get('title')} ({panel.get('detail')}).")
        elif panel.get("status") == "warn":
            has_issue = True
            items.append(f"Review warning panel: {panel.get('title')} ({panel.get('detail')}).")
    if isinstance(gate, dict):
        for check in _list_of_dicts(gate.get("checks")):
            if check.get("status") in {"fail", "warn"}:
                has_issue = True
                items.append(f"Gate {check.get('status')}: {check.get('id')} - {check.get('detail')}")
    if not has_issue:
        items.append("All readiness panels are clean; keep this dashboard with the release evidence.")
    if isinstance(audit, dict):
        for item in _string_list(audit.get("recommendations")):
            if item not in items:
                items.append(item)
    for item in _string_list(bundle.get("recommendations")):
        if item not in items:
            items.append(item)
    return items


def _evidence(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for artifact in _list_of_dicts(bundle.get("artifacts")):
        rows.append(
            {
                "key": artifact.get("key"),
                "title": artifact.get("title"),
                "path": artifact.get("path"),
                "kind": artifact.get("kind"),
                "exists": artifact.get("exists"),
                "size_bytes": artifact.get("size_bytes"),
            }
        )
    return rows


def _status_from_check_status(value: str) -> str:
    if value == "pass":
        return "pass"
    if value == "fail" or value == "blocked":
        return "fail"
    return "warn"


def _resolve_optional_path(explicit: str | Path | None, hinted: Any, candidate: Path) -> Path | None:
    if explicit is not None:
        return Path(explicit)
    resolved = _resolve_path(hinted)
    if resolved is not None:
        return resolved
    return candidate if candidate.exists() else None


def _resolve_path(value: Any) -> Path | None:
    if value in {None, ""}:
        return None
    return Path(str(value))


def _candidate(root: Path, directory: str, filename: str) -> Path:
    return root / directory / filename


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release readiness input must be a JSON object: {path}")
    return payload


def _read_json(path: Path, warnings: list[str], label: str) -> dict[str, Any] | None:
    if not path.exists():
        warnings.append(f"{label} not found: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"{path} must contain a JSON object")
        return None
    return payload


def _panel_section(panels: list[dict[str, Any]]) -> str:
    cards = []
    for panel in panels:
        status = str(panel.get("status") or "warn")
        cards.append(
            '<article class="panel-card">'
            f'<span class="pill {status}">{_e(status)}</span>'
            f"<h2>{_e(panel.get('title'))}</h2>"
            f"<p>{_e(panel.get('detail'))}</p>"
            f"<code>{_e(panel.get('source_path') or 'missing')}</code>"
            "</article>"
        )
    return '<section class="panel-grid">' + "".join(cards) + "</section>"


def _evidence_section(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<section class="panel"><h2>Evidence</h2><p class="muted">missing</p></section>'
    rows = []
    for item in items:
        exists = "yes" if item.get("exists") else "no"
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('key'))}</td>"
            f"<td><strong>{_e(item.get('title'))}</strong><br><span>{_e(item.get('path'))}</span></td>"
            f"<td>{_e(exists)}</td>"
            f"<td>{_e(item.get('kind'))}</td>"
            f"<td>{_e(_fmt_bytes(item.get('size_bytes')))}</td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Evidence</h2><table><thead><tr><th>Key</th><th>Artifact</th><th>Exists</th><th>Kind</th><th>Size</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _list_section(title: str, values: Any, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["missing"]
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
h2 { margin:8px 0 8px; font-size:18px; }
span, .muted { color:var(--muted); }
code { display:block; margin-top:8px; color:var(--muted); overflow-wrap:anywhere; }
.stats, .panel-grid { display:grid; gap:12px; padding:18px 32px 4px; }
.stats { grid-template-columns:repeat(auto-fit, minmax(145px, 1fr)); }
.panel-grid { grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); }
.card, .panel, .panel-card { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.panel-card { padding:16px; min-height:150px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:920px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:54px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats, .panel-grid { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _evidence_lines(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- missing"]
    return [
        f"- `{item.get('path')}`: {'yes' if item.get('exists') else 'no'}, {item.get('kind')}, {_fmt_bytes(item.get('size_bytes'))}"
        for item in items
    ]


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_bytes(value: Any) -> str:
    if value in {None, ""}:
        return "missing"
    size = int(value)
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _md(value: Any) -> str:
    return _fmt(value).replace("|", "\\|").replace("\n", " ")
