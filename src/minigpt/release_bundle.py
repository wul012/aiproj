from __future__ import annotations

from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_release_bundle(
    registry_path: str | Path,
    *,
    model_card_path: str | Path | None = None,
    audit_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    release_name: str | None = None,
    title: str = "MiniGPT release bundle",
    generated_at: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    registry_file = Path(registry_path)
    registry = _read_required_json(registry_file)
    model_file = _resolve_model_card_path(registry_file, model_card_path)
    audit_file = _resolve_audit_path(registry_file, audit_path)
    request_history_summary_file = _resolve_request_history_summary_path(registry_file, audit_file, request_history_summary_path)
    model_card = _read_json(model_file, warnings, "model card") if model_file is not None else None
    audit = _read_json(audit_file, warnings, "project audit") if audit_file is not None else None
    request_history_summary = (
        _read_json(request_history_summary_file, warnings, "request history summary")
        if request_history_summary_file is not None
        else None
    )
    artifacts = _collect_release_artifacts(registry_file, model_file, audit_file, request_history_summary_file)
    top_runs = _top_runs(registry, model_card if isinstance(model_card, dict) else None)
    summary = _build_summary(
        registry,
        model_card if isinstance(model_card, dict) else None,
        audit if isinstance(audit, dict) else None,
        request_history_summary if isinstance(request_history_summary, dict) else None,
        artifacts,
    )

    return {
        "schema_version": 1,
        "title": title,
        "release_name": release_name or _default_release_name(registry_file),
        "generated_at": generated_at or utc_now(),
        "summary": summary,
        "inputs": {
            "registry_path": str(registry_file),
            "model_card_path": None if model_file is None else str(model_file),
            "project_audit_path": None if audit_file is None else str(audit_file),
            "request_history_summary_path": None if request_history_summary_file is None else str(request_history_summary_file),
        },
        "artifacts": artifacts,
        "top_runs": top_runs,
        "audit_checks": _audit_checks(audit if isinstance(audit, dict) else None),
        "request_history_context": _request_history_context(request_history_summary if isinstance(request_history_summary, dict) else None),
        "recommendations": _recommendations(model_card if isinstance(model_card, dict) else None, audit if isinstance(audit, dict) else None, summary),
        "warnings": warnings,
    }


def write_release_bundle_json(bundle: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")


def render_release_bundle_markdown(bundle: dict[str, Any]) -> str:
    summary = _dict(bundle.get("summary"))
    lines = [
        f"# {bundle.get('title', 'MiniGPT release bundle')}",
        "",
        f"- Release: `{bundle.get('release_name')}`",
        f"- Generated: `{bundle.get('generated_at')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Release status", summary.get("release_status")),
                ("Audit status", summary.get("audit_status")),
                ("Audit score", summary.get("audit_score_percent")),
                ("Run count", summary.get("run_count")),
                ("Best run", summary.get("best_run_name")),
                ("Best val loss", _fmt(summary.get("best_val_loss"))),
                ("Ready runs", summary.get("ready_runs")),
                ("Request history status", summary.get("request_history_status")),
                ("Evidence artifacts", summary.get("available_artifacts")),
            ]
        ),
        "",
        "## Inputs",
        "",
        *_markdown_table([(key, value) for key, value in _dict(bundle.get("inputs")).items()]),
        "",
        "## Top Runs",
        "",
        *_run_table(_list_of_dicts(bundle.get("top_runs"))),
        "",
        "## Audit Checks",
        "",
        "| Status | Check | Detail |",
        "| --- | --- | --- |",
    ]
    for check in _list_of_dicts(bundle.get("audit_checks")):
        lines.append(f"| {_md(check.get('status'))} | {_md(check.get('title'))} | {_md(check.get('detail'))} |")
    lines.extend(["", "## Evidence Artifacts", ""])
    lines.extend(_artifact_lines(_list_of_dicts(bundle.get("artifacts"))))
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(bundle.get("recommendations")))
    warnings = _string_list(bundle.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_release_bundle_markdown(bundle: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_bundle_markdown(bundle), encoding="utf-8")


def render_release_bundle_html(bundle: dict[str, Any], *, base_dir: str | Path | None = None) -> str:
    summary = _dict(bundle.get("summary"))
    stats = [
        ("Release", summary.get("release_status")),
        ("Audit", summary.get("audit_status")),
        ("Score", f"{summary.get('audit_score_percent')}%"),
        ("Runs", summary.get("run_count")),
        ("Best run", summary.get("best_run_name")),
        ("Ready", summary.get("ready_runs")),
        ("Req history", summary.get("request_history_status")),
        ("Artifacts", summary.get("available_artifacts")),
        ("Generated", bundle.get("generated_at")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(bundle.get('title', 'MiniGPT release bundle'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(bundle.get('title', 'MiniGPT release bundle'))}</h1><p>{_e(bundle.get('release_name'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _key_value_section("Inputs", _dict(bundle.get("inputs"))),
            _run_section("Top Runs", _list_of_dicts(bundle.get("top_runs")), base_dir),
            _check_section(_list_of_dicts(bundle.get("audit_checks"))),
            _artifact_section(_list_of_dicts(bundle.get("artifacts")), base_dir),
            _list_section("Recommendations", bundle.get("recommendations")),
            _list_section("Warnings", bundle.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT release bundle exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_release_bundle_html(bundle: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_bundle_html(bundle, base_dir=out_path.parent), encoding="utf-8")


def write_release_bundle_outputs(bundle: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "release_bundle.json",
        "markdown": root / "release_bundle.md",
        "html": root / "release_bundle.html",
    }
    write_release_bundle_json(bundle, paths["json"])
    write_release_bundle_markdown(bundle, paths["markdown"])
    write_release_bundle_html(bundle, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release bundle input must be a JSON object: {path}")
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


def _resolve_model_card_path(registry_path: Path, model_card_path: str | Path | None) -> Path | None:
    if model_card_path is not None:
        return Path(model_card_path)
    candidates = [
        registry_path.parent / "model_card.json",
        registry_path.parent / "model-card" / "model_card.json",
        registry_path.parent.parent / "model-card" / "model_card.json",
    ]
    return next((path for path in candidates if path.exists()), None)


def _resolve_audit_path(registry_path: Path, audit_path: str | Path | None) -> Path | None:
    if audit_path is not None:
        return Path(audit_path)
    candidates = [
        registry_path.parent / "project_audit.json",
        registry_path.parent / "audit" / "project_audit.json",
        registry_path.parent.parent / "audit" / "project_audit.json",
    ]
    return next((path for path in candidates if path.exists()), None)


def _resolve_request_history_summary_path(
    registry_path: Path,
    audit_path: Path | None,
    request_history_summary_path: str | Path | None,
) -> Path | None:
    if request_history_summary_path is not None:
        return Path(request_history_summary_path)
    candidates: list[Path] = []
    if audit_path is not None:
        try:
            audit = _read_required_json(audit_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            audit = {}
        path = audit.get("request_history_summary_path") if isinstance(audit, dict) else None
        if path:
            candidates.append(Path(str(path)))
    candidates.extend(
        [
            registry_path.parent / "request_history_summary.json",
            registry_path.parent / "request-history-summary" / "request_history_summary.json",
            registry_path.parent.parent / "request-history-summary" / "request_history_summary.json",
        ]
    )
    return next((path for path in candidates if path.exists()), None)


def _default_release_name(registry_path: Path) -> str:
    return f"{registry_path.parent.name or 'registry'} release"


def _build_summary(
    registry: dict[str, Any],
    model_card: dict[str, Any] | None,
    audit: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    best = _dict(registry.get("best_by_best_val_loss"))
    audit_summary = _dict(audit.get("summary")) if audit else {}
    model_summary = _dict(model_card.get("summary")) if model_card else {}
    request_summary = _dict(request_history_summary.get("summary")) if isinstance(request_history_summary, dict) else {}
    audit_status = audit_summary.get("overall_status")
    release_status = _release_status(audit_status, audit_summary.get("fail_count"), audit_summary.get("warn_count"))
    return {
        "release_status": release_status,
        "audit_status": audit_status or "missing",
        "audit_score_percent": audit_summary.get("score_percent"),
        "run_count": registry.get("run_count") or model_summary.get("run_count"),
        "best_run_name": best.get("name") or model_summary.get("best_run_name"),
        "best_val_loss": best.get("best_val_loss") or model_summary.get("best_val_loss"),
        "ready_runs": audit_summary.get("ready_runs") or model_summary.get("ready_runs"),
        "request_history_status": audit_summary.get("request_history_status") or request_summary.get("status"),
        "request_history_records": audit_summary.get("request_history_records") or request_summary.get("total_log_records"),
        "available_artifacts": sum(1 for artifact in artifacts if artifact.get("exists")),
        "missing_artifacts": sum(1 for artifact in artifacts if not artifact.get("exists")),
    }


def _release_status(audit_status: Any, fail_count: Any, warn_count: Any) -> str:
    if audit_status == "pass":
        return "release-ready"
    if audit_status == "warn":
        return "review-needed"
    if audit_status == "fail" or fail_count:
        return "blocked"
    if warn_count:
        return "review-needed"
    return "needs-audit"


def _collect_release_artifacts(
    registry_path: Path,
    model_card_path: Path | None,
    audit_path: Path | None,
    request_history_summary_path: Path | None,
) -> list[dict[str, Any]]:
    registry_dir = registry_path.parent
    specs = [
        ("registry_json", "Registry JSON", registry_path, "JSON", "machine-readable run registry"),
        ("registry_csv", "Registry CSV", registry_dir / "registry.csv", "CSV", "tabular run registry"),
        ("registry_svg", "Registry SVG", registry_dir / "registry.svg", "SVG", "static run registry chart"),
        ("registry_html", "Registry HTML", registry_dir / "registry.html", "HTML", "interactive run registry"),
    ]
    if model_card_path is not None:
        model_dir = model_card_path.parent
        specs.extend(
            [
                ("model_card_json", "Model card JSON", model_card_path, "JSON", "project model card"),
                ("model_card_md", "Model card Markdown", model_dir / "model_card.md", "MD", "markdown model card"),
                ("model_card_html", "Model card HTML", model_dir / "model_card.html", "HTML", "browser model card"),
            ]
        )
    if audit_path is not None:
        audit_dir = audit_path.parent
        specs.extend(
            [
                ("project_audit_json", "Project audit JSON", audit_path, "JSON", "machine-readable project audit"),
                ("project_audit_md", "Project audit Markdown", audit_dir / "project_audit.md", "MD", "markdown project audit"),
                ("project_audit_html", "Project audit HTML", audit_dir / "project_audit.html", "HTML", "browser project audit"),
            ]
        )
    if request_history_summary_path is not None:
        request_dir = request_history_summary_path.parent
        specs.extend(
            [
                (
                    "request_history_summary_json",
                    "Request history summary JSON",
                    request_history_summary_path,
                    "JSON",
                    "machine-readable local inference request stability summary",
                ),
                (
                    "request_history_summary_md",
                    "Request history summary Markdown",
                    request_dir / "request_history_summary.md",
                    "MD",
                    "markdown local inference request stability summary",
                ),
                (
                    "request_history_summary_html",
                    "Request history summary HTML",
                    request_dir / "request_history_summary.html",
                    "HTML",
                    "browser local inference request stability summary",
                ),
            ]
        )
    return [_artifact(key, title, path, kind, description) for key, title, path, kind, description in specs]


def _request_history_context(request_history_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        return {"available": False, "status": None, "total_log_records": None}
    summary = _dict(request_history_summary.get("summary"))
    return {
        "available": True,
        "request_log": request_history_summary.get("request_log"),
        "status": summary.get("status"),
        "total_log_records": summary.get("total_log_records"),
        "invalid_record_count": summary.get("invalid_record_count"),
        "timeout_rate": summary.get("timeout_rate"),
        "bad_request_rate": summary.get("bad_request_rate"),
        "error_rate": summary.get("error_rate"),
        "latest_timestamp": summary.get("latest_timestamp"),
    }


def _artifact(key: str, title: str, path: Path, kind: str, description: str) -> dict[str, Any]:
    exists = path.exists()
    return {
        "key": key,
        "title": title,
        "path": str(path),
        "kind": kind,
        "description": description,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists and path.is_file() else None,
    }


def _top_runs(registry: dict[str, Any], model_card: dict[str, Any] | None) -> list[dict[str, Any]]:
    if model_card and isinstance(model_card.get("top_runs"), list):
        return _list_of_dicts(model_card.get("top_runs"))[:5]
    by_name = {str(run.get("name")): run for run in _list_of_dicts(registry.get("runs"))}
    rows = []
    for item in _list_of_dicts(registry.get("loss_leaderboard")):
        run = by_name.get(str(item.get("name")), item)
        rows.append(run)
    return rows[:5] or _list_of_dicts(registry.get("runs"))[:5]


def _audit_checks(audit: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not audit:
        return []
    return _list_of_dicts(audit.get("checks"))


def _recommendations(model_card: dict[str, Any] | None, audit: dict[str, Any] | None, summary: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if audit:
        items.extend(_string_list(audit.get("recommendations")))
    if model_card:
        for item in _string_list(model_card.get("recommendations")):
            if item not in items:
                items.append(item)
    if summary.get("release_status") == "release-ready":
        items.insert(0, "Release evidence is complete; keep this bundle with the tagged version.")
    elif summary.get("release_status") == "blocked":
        items.insert(0, "Do not present this release as complete until failed audit checks are fixed.")
    elif summary.get("release_status") == "needs-audit":
        items.insert(0, "Generate project_audit.json before treating this as a release bundle.")
    return items or ["Review release evidence before sharing the project externally."]


def _artifact_lines(artifacts: list[dict[str, Any]]) -> list[str]:
    lines = []
    for artifact in artifacts:
        state = "yes" if artifact.get("exists") else "no"
        lines.append(f"- `{artifact.get('path')}`: {state}, {artifact.get('kind')}, {_fmt_bytes(artifact.get('size_bytes'))}")
    return lines


def _run_table(runs: list[dict[str, Any]]) -> list[str]:
    lines = ["| Rank | Run | Status | Best Val | Delta | Quality | Eval |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for run in runs:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(_rank_label(run.get("best_val_loss_rank"))),
                    _md(run.get("name")),
                    _md(run.get("status")),
                    _md(_fmt(run.get("best_val_loss"))),
                    _md(_fmt_delta(run.get("best_val_loss_delta"))),
                    _md(run.get("dataset_quality")),
                    _md(run.get("eval_suite_cases")),
                ]
            )
            + " |"
        )
    return lines


def _key_value_section(title: str, payload: dict[str, Any]) -> str:
    rows = "".join(f"<tr><th>{_e(key)}</th><td>{_e(_fmt_any(value))}</td></tr>" for key, value in payload.items())
    return f'<section class="panel"><h2>{_e(title)}</h2><table>{rows}</table></section>'


def _run_section(title: str, runs: list[dict[str, Any]], base_dir: str | Path | None) -> str:
    rows = []
    for run in runs:
        card = run.get("experiment_card_html") or run.get("experiment_card_path")
        card_link = _path_link(card, base_dir, "card") if card else '<span class="muted">missing</span>'
        rows.append(
            "<tr>"
            f"<td>{_e(_rank_label(run.get('best_val_loss_rank')))}</td>"
            f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('path'))}</span></td>"
            f"<td>{_e(run.get('status'))}</td>"
            f"<td>{_e(_fmt(run.get('best_val_loss')))}<br><span>{_e(_fmt_delta(run.get('best_val_loss_delta')))}</span></td>"
            f"<td>{_e(run.get('dataset_quality'))}</td>"
            f"<td>{_e(run.get('eval_suite_cases'))}</td>"
            f"<td>{card_link}</td>"
            "</tr>"
        )
    return f'<section class="panel"><h2>{_e(title)}</h2><table><thead><tr><th>Rank</th><th>Run</th><th>Status</th><th>Best Val</th><th>Quality</th><th>Eval</th><th>Card</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _check_section(checks: list[dict[str, Any]]) -> str:
    if not checks:
        return '<section class="panel"><h2>Audit Checks</h2><p class="muted">missing</p></section>'
    rows = []
    for check in checks:
        status = str(check.get("status") or "missing")
        rows.append(
            "<tr>"
            f'<td><span class="pill {status}">{_e(status)}</span></td>'
            f"<td><strong>{_e(check.get('title'))}</strong><br><span>{_e(check.get('id'))}</span></td>"
            f"<td>{_e(check.get('detail'))}</td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Audit Checks</h2><table><thead><tr><th>Status</th><th>Check</th><th>Detail</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _artifact_section(artifacts: list[dict[str, Any]], base_dir: str | Path | None) -> str:
    rows = []
    for artifact in artifacts:
        path = artifact.get("path")
        label = _path_link(path, base_dir, artifact.get("title") or artifact.get("key")) if artifact.get("exists") else _e(path)
        rows.append(
            "<tr>"
            f"<td>{_e(artifact.get('key'))}</td>"
            f"<td>{label}<br><span>{_e(artifact.get('description'))}</span></td>"
            f"<td>{_e('yes' if artifact.get('exists') else 'no')}</td>"
            f"<td>{_e(artifact.get('kind'))}</td>"
            f"<td>{_e(_fmt_bytes(artifact.get('size_bytes')))}</td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Evidence Artifacts</h2><table><thead><tr><th>Key</th><th>Artifact</th><th>Exists</th><th>Kind</th><th>Size</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _list_section(title: str, values: Any, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt_any(value))}</div>' + "</div>"


def _path_link(path: Any, base_dir: str | Path | None, label: Any) -> str:
    if path is None:
        return '<span class="muted">missing</span>'
    href = str(path)
    if base_dir is not None:
        try:
            href = Path(os.path.relpath(Path(str(path)), Path(base_dir))).as_posix()
        except ValueError:
            href = Path(str(path)).as_posix()
    return f'<a href="{_e(href)}">{_e(label)}</a>'


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --green:#047857; --amber:#b45309; --red:#b91c1c; }
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
table { width:100%; border-collapse:collapse; min-width:920px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
a { color:var(--blue); font-weight:700; text-decoration:none; }
.pill { display:inline-block; min-width:54px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {_md(key)} | {_md(value)} |")
    return lines


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_delta(value: Any) -> str:
    if value is None or value == "":
        return "missing"
    return f"{float(value):+.5g}"


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


def _fmt_bytes(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{int(value):,} bytes"


def _rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def _md(value: Any) -> str:
    return _fmt_any(value).replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
