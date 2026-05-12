from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any

from .release_gate import build_release_gate, release_gate_policy_profiles, utc_now

DEFAULT_COMPARISON_PROFILES = ("standard", "review", "strict", "legacy")


def build_release_gate_profile_comparison(
    bundle_paths: list[str | Path],
    *,
    policy_profiles: list[str] | None = None,
    minimum_audit_score: float | None = None,
    minimum_ready_runs: int | None = None,
    require_generation_quality: bool | None = None,
    title: str = "MiniGPT release gate profile comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    bundles = [Path(path) for path in bundle_paths]
    if not bundles:
        raise ValueError("at least one release bundle is required")

    profiles = policy_profiles or list(DEFAULT_COMPARISON_PROFILES)
    _validate_profiles(profiles)
    timestamp = generated_at or utc_now()

    rows: list[dict[str, Any]] = []
    for bundle_path in bundles:
        for profile in profiles:
            gate = build_release_gate(
                bundle_path,
                policy_profile=profile,
                minimum_audit_score=minimum_audit_score,
                minimum_ready_runs=minimum_ready_runs,
                require_generation_quality=require_generation_quality,
                title=f"{title}: {profile}",
                generated_at=timestamp,
            )
            rows.append(_row_from_gate(gate))

    summary = _build_comparison_summary(rows, bundles, profiles)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": timestamp,
        "bundle_paths": [str(path) for path in bundles],
        "policy_profiles": list(profiles),
        "summary": summary,
        "rows": rows,
        "recommendations": _comparison_recommendations(summary, rows),
    }


def write_release_gate_profile_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


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


def render_release_gate_profile_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT release gate profile comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Bundles: `{summary.get('bundle_count', 0)}`",
        f"- Profiles: `{', '.join(_string_list(report.get('policy_profiles')))}`",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Total rows | {_md(summary.get('row_count'))} |",
        f"| Approved | {_md(summary.get('approved_count'))} |",
        f"| Needs review | {_md(summary.get('needs_review_count'))} |",
        f"| Blocked | {_md(summary.get('blocked_count'))} |",
        "",
        "## Profile Matrix",
        "",
        "| Bundle | Profile | Decision | Gate | Audit score | Min score | Generation quality required | Failed checks | Warned checks |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
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
                    _md(", ".join(_string_list(row.get("failed_checks")))),
                    _md(", ".join(_string_list(row.get("warned_checks")))),
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
        ("Generated", report.get("generated_at")),
    ]
    rows = "".join(_html_row(row) for row in _list_of_dicts(report.get("rows")))
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
            f"<header><h1>{_e(report.get('title', 'MiniGPT release gate profile comparison'))}</h1><p>{_e(', '.join(_string_list(report.get('policy_profiles'))))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Profile Matrix</h2><table><thead><tr>'
            "<th>Bundle</th><th>Profile</th><th>Decision</th><th>Gate</th><th>Audit</th><th>Min</th><th>Generation</th><th>Failed</th><th>Warned</th>"
            "</tr></thead><tbody>"
            + rows
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
        "markdown": root / "release_gate_profile_comparison.md",
        "html": root / "release_gate_profile_comparison.html",
    }
    write_release_gate_profile_comparison_json(report, paths["json"])
    write_release_gate_profile_comparison_csv(report, paths["csv"])
    write_release_gate_profile_comparison_markdown(report, paths["markdown"])
    write_release_gate_profile_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _validate_profiles(profiles: list[str]) -> None:
    available = release_gate_policy_profiles()
    unknown = [profile for profile in profiles if profile not in available]
    if unknown:
        choices = ", ".join(sorted(available))
        raise ValueError(f"unknown release gate policy profile(s): {', '.join(unknown)}; choices: {choices}")


def _row_from_gate(gate: dict[str, Any]) -> dict[str, Any]:
    policy = _dict(gate.get("policy"))
    summary = _dict(gate.get("summary"))
    checks = _list_of_dicts(gate.get("checks"))
    return {
        "bundle_path": gate.get("bundle_path"),
        "release_name": gate.get("release_name"),
        "policy_profile": policy.get("policy_profile"),
        "profile_description": policy.get("profile_description"),
        "gate_status": summary.get("gate_status"),
        "decision": summary.get("decision"),
        "audit_score_percent": summary.get("audit_score_percent"),
        "minimum_audit_score": policy.get("minimum_audit_score"),
        "ready_runs": summary.get("ready_runs"),
        "minimum_ready_runs": policy.get("minimum_ready_runs"),
        "require_generation_quality_audit_checks": policy.get("require_generation_quality_audit_checks"),
        "pass_count": summary.get("pass_count"),
        "warn_count": summary.get("warn_count"),
        "fail_count": summary.get("fail_count"),
        "failed_checks": _check_ids(checks, "fail"),
        "warned_checks": _check_ids(checks, "warn"),
    }


def _build_comparison_summary(rows: list[dict[str, Any]], bundles: list[Path], profiles: list[str]) -> dict[str, Any]:
    approved = sum(1 for row in rows if row.get("decision") == "approved")
    needs_review = sum(1 for row in rows if row.get("decision") == "needs-review")
    blocked = sum(1 for row in rows if row.get("decision") == "blocked")
    return {
        "bundle_count": len(bundles),
        "profile_count": len(profiles),
        "row_count": len(rows),
        "approved_count": approved,
        "needs_review_count": needs_review,
        "blocked_count": blocked,
    }


def _comparison_recommendations(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    blocked = int(summary.get("blocked_count") or 0)
    needs_review = int(summary.get("needs_review_count") or 0)
    if blocked:
        blocked_profiles = sorted({str(row.get("policy_profile")) for row in rows if row.get("decision") == "blocked"})
        return [
            "At least one profile blocks the release; inspect failed_checks before choosing a release policy.",
            "Blocked profile(s): " + ", ".join(blocked_profiles) + ".",
        ]
    if needs_review:
        return ["No profile blocks the release, but warning profiles need manual review before external sharing."]
    return ["All compared policy profiles approved the release bundle(s)."]


def _check_ids(checks: list[dict[str, Any]], status: str) -> list[str]:
    return [str(check.get("id")) for check in checks if check.get("status") == status and check.get("id")]


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
        f"<td>{_e(', '.join(_string_list(row.get('failed_checks'))))}</td>"
        f"<td>{_e(', '.join(_string_list(row.get('warned_checks'))))}</td>"
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


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _csv_value(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(_string_list(value))
    return "" if value is None else str(value)


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


def _md(value: Any) -> str:
    return _fmt_any(value).replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
