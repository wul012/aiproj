from __future__ import annotations

from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_release_gate(
    bundle_path: str | Path,
    *,
    minimum_audit_score: float = 90.0,
    minimum_ready_runs: int = 1,
    require_generation_quality: bool = True,
    title: str = "MiniGPT release gate",
    generated_at: str | None = None,
) -> dict[str, Any]:
    bundle_file = Path(bundle_path)
    bundle = _read_required_json(bundle_file)
    checks = _build_checks(
        bundle,
        minimum_audit_score=minimum_audit_score,
        minimum_ready_runs=minimum_ready_runs,
        require_generation_quality=require_generation_quality,
    )
    summary = _build_summary(bundle, checks)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "bundle_path": str(bundle_file),
        "release_name": bundle.get("release_name"),
        "policy": {
            "required_release_status": "release-ready",
            "required_audit_status": "pass",
            "minimum_audit_score": float(minimum_audit_score),
            "minimum_ready_runs": int(minimum_ready_runs),
            "require_all_evidence_artifacts": True,
            "require_generation_quality_audit_checks": bool(require_generation_quality),
        },
        "summary": summary,
        "checks": checks,
        "recommendations": _recommendations(summary, checks, bundle),
        "bundle_recommendations": _string_list(bundle.get("recommendations")),
        "warnings": _string_list(bundle.get("warnings")),
    }


def write_release_gate_json(gate: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")


def render_release_gate_markdown(gate: dict[str, Any]) -> str:
    summary = _dict(gate.get("summary"))
    policy = _dict(gate.get("policy"))
    lines = [
        f"# {gate.get('title', 'MiniGPT release gate')}",
        "",
        f"- Release: `{gate.get('release_name')}`",
        f"- Generated: `{gate.get('generated_at')}`",
        f"- Bundle: `{gate.get('bundle_path')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Gate status", summary.get("gate_status")),
                ("Decision", summary.get("decision")),
                ("Release status", summary.get("release_status")),
                ("Audit status", summary.get("audit_status")),
                ("Audit score", summary.get("audit_score_percent")),
                ("Ready runs", summary.get("ready_runs")),
                ("Missing artifacts", summary.get("missing_artifacts")),
                ("Pass checks", summary.get("pass_count")),
                ("Warn checks", summary.get("warn_count")),
                ("Fail checks", summary.get("fail_count")),
            ]
        ),
        "",
        "## Policy",
        "",
        *_markdown_table([(key, value) for key, value in policy.items()]),
        "",
        "## Checks",
        "",
        "| Status | Check | Detail |",
        "| --- | --- | --- |",
    ]
    for check in _list_of_dicts(gate.get("checks")):
        lines.append(f"| {_md(check.get('status'))} | {_md(check.get('title'))} | {_md(check.get('detail'))} |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(gate.get("recommendations")))
    bundle_recommendations = _string_list(gate.get("bundle_recommendations"))
    if bundle_recommendations:
        lines.extend(["", "## Bundle Recommendations", ""])
        lines.extend(f"- {item}" for item in bundle_recommendations)
    warnings = _string_list(gate.get("warnings"))
    if warnings:
        lines.extend(["", "## Bundle Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_release_gate_markdown(gate: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_gate_markdown(gate), encoding="utf-8")


def render_release_gate_html(gate: dict[str, Any]) -> str:
    summary = _dict(gate.get("summary"))
    stats = [
        ("Gate", summary.get("gate_status")),
        ("Decision", summary.get("decision")),
        ("Release", summary.get("release_status")),
        ("Audit", summary.get("audit_status")),
        ("Score", _score_label(summary.get("audit_score_percent"))),
        ("Ready", summary.get("ready_runs")),
        ("Missing", summary.get("missing_artifacts")),
        ("Generated", gate.get("generated_at")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(gate.get('title', 'MiniGPT release gate'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(gate.get('title', 'MiniGPT release gate'))}</h1><p>{_e(gate.get('release_name'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _key_value_section("Policy", _dict(gate.get("policy"))),
            _check_section(_list_of_dicts(gate.get("checks"))),
            _list_section("Recommendations", gate.get("recommendations")),
            _list_section("Bundle Recommendations", gate.get("bundle_recommendations"), hide_empty=True),
            _list_section("Bundle Warnings", gate.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT release gate.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_release_gate_html(gate: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_release_gate_html(gate), encoding="utf-8")


def write_release_gate_outputs(gate: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "gate_report.json",
        "markdown": root / "gate_report.md",
        "html": root / "gate_report.html",
    }
    write_release_gate_json(gate, paths["json"])
    write_release_gate_markdown(gate, paths["markdown"])
    write_release_gate_html(gate, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def exit_code_for_gate(gate: dict[str, Any], *, fail_on_warn: bool = False) -> int:
    status = _dict(gate.get("summary")).get("gate_status")
    if status == "fail":
        return 1
    if status == "warn" and fail_on_warn:
        return 1
    return 0


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release gate input must be a JSON object: {path}")
    return payload


def _build_checks(
    bundle: dict[str, Any],
    *,
    minimum_audit_score: float,
    minimum_ready_runs: int,
    require_generation_quality: bool,
) -> list[dict[str, Any]]:
    summary = _dict(bundle.get("summary"))
    release_status = summary.get("release_status")
    audit_status = summary.get("audit_status")
    audit_score = _number(summary.get("audit_score_percent"))
    ready_runs = _integer(summary.get("ready_runs"))
    missing_artifacts = _integer(summary.get("missing_artifacts"))
    top_runs = _list_of_dicts(bundle.get("top_runs"))
    audit_checks = _list_of_dicts(bundle.get("audit_checks"))
    bundle_warnings = _string_list(bundle.get("warnings"))
    schema_version = bundle.get("schema_version")

    checks = [
        _check(
            "bundle_schema",
            "Release bundle schema is present",
            "pass" if schema_version is not None else "warn",
            f"schema_version={schema_version if schema_version is not None else 'missing'}",
        ),
        _check(
            "release_status",
            "Release status is ready",
            "pass" if release_status == "release-ready" else "fail",
            f"release_status={release_status or 'missing'}; required=release-ready.",
        ),
        _check(
            "audit_status",
            "Audit status passed",
            _audit_status_result(audit_status),
            f"audit_status={audit_status or 'missing'}; required=pass.",
        ),
        _check(
            "audit_score",
            "Audit score meets threshold",
            "pass" if audit_score is not None and audit_score >= minimum_audit_score else "fail",
            f"audit_score={_score_label(audit_score)}; minimum={minimum_audit_score:g}%.",
        ),
        _check(
            "ready_runs",
            "Ready run count meets threshold",
            "pass" if ready_runs >= minimum_ready_runs else "fail",
            f"ready_runs={ready_runs}; minimum={minimum_ready_runs}.",
        ),
        _check(
            "best_run",
            "Best run is identified",
            "pass" if summary.get("best_run_name") else "fail",
            f"best_run={summary.get('best_run_name') or 'missing'}.",
        ),
        _check(
            "evidence_artifacts",
            "Evidence artifacts are complete",
            "pass" if missing_artifacts == 0 else "fail",
            f"missing_artifacts={missing_artifacts}; all evidence artifacts should exist.",
        ),
        _check(
            "top_runs",
            "Top runs are listed",
            "pass" if top_runs else "fail",
            f"top_runs={len(top_runs)}.",
        ),
        _check(
            "audit_checks",
            "Audit checks are clean",
            _audit_checks_result(audit_checks),
            _audit_checks_detail(audit_checks),
        ),
        _check(
            "generation_quality_audit_checks",
            "Generation quality audit checks passed",
            _generation_quality_audit_result(audit_checks, require_generation_quality),
            _generation_quality_audit_detail(audit_checks, require_generation_quality),
        ),
        _check(
            "bundle_warnings",
            "Bundle has no warnings",
            "pass" if not bundle_warnings else "warn",
            f"warnings={len(bundle_warnings)}.",
        ),
    ]
    return checks


def _build_summary(bundle: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    bundle_summary = _dict(bundle.get("summary"))
    pass_count = sum(1 for check in checks if check.get("status") == "pass")
    warn_count = sum(1 for check in checks if check.get("status") == "warn")
    fail_count = sum(1 for check in checks if check.get("status") == "fail")
    if fail_count:
        gate_status = "fail"
        decision = "blocked"
    elif warn_count:
        gate_status = "warn"
        decision = "needs-review"
    else:
        gate_status = "pass"
        decision = "approved"
    return {
        "gate_status": gate_status,
        "decision": decision,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "release_status": bundle_summary.get("release_status"),
        "audit_status": bundle_summary.get("audit_status"),
        "audit_score_percent": bundle_summary.get("audit_score_percent"),
        "run_count": bundle_summary.get("run_count"),
        "best_run_name": bundle_summary.get("best_run_name"),
        "best_val_loss": bundle_summary.get("best_val_loss"),
        "ready_runs": bundle_summary.get("ready_runs"),
        "available_artifacts": bundle_summary.get("available_artifacts"),
        "missing_artifacts": bundle_summary.get("missing_artifacts"),
    }


def _audit_status_result(audit_status: Any) -> str:
    if audit_status == "pass":
        return "pass"
    if audit_status == "warn":
        return "warn"
    return "fail"


def _audit_checks_result(audit_checks: list[dict[str, Any]]) -> str:
    if not audit_checks:
        return "fail"
    statuses = [str(check.get("status") or "missing") for check in audit_checks]
    if "fail" in statuses or "missing" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


def _audit_checks_detail(audit_checks: list[dict[str, Any]]) -> str:
    if not audit_checks:
        return "no audit checks found."
    status_counts: dict[str, int] = {}
    for check in audit_checks:
        status = str(check.get("status") or "missing")
        status_counts[status] = status_counts.get(status, 0) + 1
    ordered = [f"{key}={status_counts[key]}" for key in sorted(status_counts)]
    return ", ".join(ordered) + "."


def _generation_quality_audit_result(audit_checks: list[dict[str, Any]], require_generation_quality: bool) -> str:
    if not require_generation_quality:
        return "pass"
    by_id = _audit_checks_by_id(audit_checks)
    required = ["generation_quality", "non_pass_generation_quality"]
    statuses = [str(_dict(by_id.get(check_id)).get("status") or "missing") for check_id in required]
    if "missing" in statuses or "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


def _generation_quality_audit_detail(audit_checks: list[dict[str, Any]], require_generation_quality: bool) -> str:
    if not require_generation_quality:
        return "generation quality audit checks are not required by policy."
    by_id = _audit_checks_by_id(audit_checks)
    required = ["generation_quality", "non_pass_generation_quality"]
    missing = [check_id for check_id in required if check_id not in by_id]
    if missing:
        return "missing required audit check(s): " + ", ".join(missing) + "."
    details = []
    for check_id in required:
        check = _dict(by_id.get(check_id))
        details.append(f"{check_id}={check.get('status') or 'missing'}")
    return ", ".join(details) + "."


def _audit_checks_by_id(audit_checks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(check.get("id")): check for check in audit_checks if check.get("id")}


def _recommendations(summary: dict[str, Any], checks: list[dict[str, Any]], bundle: dict[str, Any]) -> list[str]:
    status = summary.get("gate_status")
    if status == "pass":
        return ["Release gate passed; keep gate_report outputs with the tagged version."]
    if status == "warn":
        return ["Release gate needs manual review before sharing this release externally."] + _failed_or_warned_checks(checks)
    recommendations = ["Release gate failed; fix failed checks before treating this version as releasable."]
    recommendations.extend(_failed_or_warned_checks(checks, only_fail=True))
    if _dict(bundle.get("summary")).get("release_status") == "needs-audit":
        recommendations.append("Generate a project audit and rebuild the release bundle, then rerun the release gate.")
    return recommendations


def _failed_or_warned_checks(checks: list[dict[str, Any]], *, only_fail: bool = False) -> list[str]:
    statuses = {"fail"} if only_fail else {"fail", "warn"}
    items = []
    for check in checks:
        if check.get("status") in statuses:
            items.append(f"{check.get('title')}: {check.get('detail')}")
    return items


def _check(check_id: str, title: str, status: str, detail: str) -> dict[str, str]:
    return {"id": check_id, "title": title, "status": status, "detail": detail}


def _key_value_section(title: str, payload: dict[str, Any]) -> str:
    rows = "".join(f"<tr><th>{_e(key)}</th><td>{_e(_fmt_any(value))}</td></tr>" for key, value in payload.items())
    return f'<section class="panel"><h2>{_e(title)}</h2><table>{rows}</table></section>'


def _check_section(checks: list[dict[str, Any]]) -> str:
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
    return '<section class="panel"><h2>Checks</h2><table><thead><tr><th>Status</th><th>Check</th><th>Detail</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _list_section(title: str, values: Any, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt_any(value))}</div>' + "</div>"


def _style() -> str:
    return """<style>
:root { --ink:#101828; --muted:#4b5563; --line:#d7dce5; --page:#f6f8fb; --panel:#fff; --blue:#1d4ed8; --green:#047857; --amber:#b45309; --red:#b91c1c; }
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
table { width:100%; border-collapse:collapse; min-width:820px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
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


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _integer(value: Any) -> int:
    try:
        if value is None or value == "":
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _score_label(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "missing"
    return f"{number:g}%"


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


def _md(value: Any) -> str:
    return _fmt_any(value).replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
