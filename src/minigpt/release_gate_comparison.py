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

from .release_gate import build_release_gate, release_gate_policy_profiles, utc_now

DEFAULT_COMPARISON_PROFILES = ("standard", "review", "strict", "legacy")


def build_release_gate_profile_comparison(
    bundle_paths: list[str | Path],
    *,
    policy_profiles: list[str] | None = None,
    minimum_audit_score: float | None = None,
    minimum_ready_runs: int | None = None,
    require_generation_quality: bool | None = None,
    require_request_history_summary: bool | None = None,
    baseline_profile: str | None = None,
    title: str = "MiniGPT release gate profile comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    bundles = [Path(path) for path in bundle_paths]
    if not bundles:
        raise ValueError("at least one release bundle is required")

    profiles = policy_profiles or list(DEFAULT_COMPARISON_PROFILES)
    _validate_profiles(profiles)
    baseline = _resolve_baseline_profile(profiles, baseline_profile)
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
                require_request_history_summary=require_request_history_summary,
                title=f"{title}: {profile}",
                generated_at=timestamp,
            )
            rows.append(_row_from_gate(gate))

    deltas = _build_profile_deltas(rows, profiles, baseline)
    summary = _build_comparison_summary(rows, deltas, bundles, profiles, baseline)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": timestamp,
        "bundle_paths": [str(path) for path in bundles],
        "policy_profiles": list(profiles),
        "baseline_profile": baseline,
        "summary": summary,
        "rows": rows,
        "deltas": deltas,
        "recommendations": _comparison_recommendations(summary, rows, deltas),
    }


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


def _validate_profiles(profiles: list[str]) -> None:
    available = release_gate_policy_profiles()
    unknown = [profile for profile in profiles if profile not in available]
    if unknown:
        choices = ", ".join(sorted(available))
        raise ValueError(f"unknown release gate policy profile(s): {', '.join(unknown)}; choices: {choices}")


def _resolve_baseline_profile(profiles: list[str], baseline_profile: str | None) -> str:
    if not profiles:
        raise ValueError("at least one policy profile is required")
    baseline = baseline_profile or profiles[0]
    available = release_gate_policy_profiles()
    if baseline not in available:
        choices = ", ".join(sorted(available))
        raise ValueError(f"unknown baseline policy profile: {baseline!r}; choices: {choices}")
    if baseline not in profiles:
        raise ValueError("baseline policy profile must be included in policy_profiles")
    return baseline


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
        "require_request_history_summary_audit_check": policy.get("require_request_history_summary_audit_check"),
        "pass_count": summary.get("pass_count"),
        "warn_count": summary.get("warn_count"),
        "fail_count": summary.get("fail_count"),
        "failed_checks": _check_ids(checks, "fail"),
        "warned_checks": _check_ids(checks, "warn"),
    }


def _build_comparison_summary(
    rows: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    bundles: list[Path],
    profiles: list[str],
    baseline_profile: str,
) -> dict[str, Any]:
    approved = sum(1 for row in rows if row.get("decision") == "approved")
    needs_review = sum(1 for row in rows if row.get("decision") == "needs-review")
    blocked = sum(1 for row in rows if row.get("decision") == "blocked")
    decision_deltas = sum(1 for delta in deltas if delta.get("decision_changed"))
    check_deltas = sum(1 for delta in deltas if delta.get("added_failed_checks") or delta.get("removed_failed_checks") or delta.get("added_warned_checks") or delta.get("removed_warned_checks"))
    diverged_bundles = len({delta.get("bundle_path") for delta in deltas if delta.get("delta_status") != "same"})
    return {
        "bundle_count": len(bundles),
        "profile_count": len(profiles),
        "baseline_profile": baseline_profile,
        "row_count": len(rows),
        "approved_count": approved,
        "needs_review_count": needs_review,
        "blocked_count": blocked,
        "delta_count": len(deltas),
        "decision_delta_count": decision_deltas,
        "check_delta_count": check_deltas,
        "diverged_bundle_count": diverged_bundles,
    }


def _comparison_recommendations(summary: dict[str, Any], rows: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[str]:
    blocked = int(summary.get("blocked_count") or 0)
    needs_review = int(summary.get("needs_review_count") or 0)
    decision_deltas = int(summary.get("decision_delta_count") or 0)
    if blocked:
        blocked_profiles = sorted({str(row.get("policy_profile")) for row in rows if row.get("decision") == "blocked"})
        recommendations = [
            "At least one profile blocks the release; inspect failed_checks before choosing a release policy.",
            "Blocked profile(s): " + ", ".join(blocked_profiles) + ".",
        ]
        if decision_deltas:
            recommendations.append("Profile deltas explain why compared profiles disagree with the baseline decision.")
        return recommendations
    if needs_review:
        return ["No profile blocks the release, but warning profiles need manual review before external sharing."]
    if any(delta.get("delta_status") != "same" for delta in deltas):
        return ["All profiles approve, but profile deltas still show threshold or warning differences worth reviewing."]
    return ["All compared policy profiles approved the release bundle(s)."]


def _build_profile_deltas(rows: list[dict[str, Any]], profiles: list[str], baseline_profile: str) -> list[dict[str, Any]]:
    if len(profiles) < 2:
        return []
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = str(row.get("bundle_path") or row.get("release_name") or "")
        grouped.setdefault(key, {})[str(row.get("policy_profile"))] = row

    deltas: list[dict[str, Any]] = []
    for bundle_path in sorted(grouped):
        profile_rows = grouped[bundle_path]
        baseline = profile_rows.get(baseline_profile)
        if not baseline:
            continue
        for compared_profile in [profile for profile in profiles if profile != baseline_profile]:
            compared = profile_rows.get(compared_profile)
            if not compared:
                continue
            delta = _delta_between_rows(baseline, compared)
            deltas.append(delta)
    return deltas


def _delta_between_rows(baseline: dict[str, Any], compared: dict[str, Any]) -> dict[str, Any]:
    baseline_failed = set(_string_list(baseline.get("failed_checks")))
    compared_failed = set(_string_list(compared.get("failed_checks")))
    baseline_warned = set(_string_list(baseline.get("warned_checks")))
    compared_warned = set(_string_list(compared.get("warned_checks")))
    added_failed = sorted(compared_failed - baseline_failed)
    removed_failed = sorted(baseline_failed - compared_failed)
    added_warned = sorted(compared_warned - baseline_warned)
    removed_warned = sorted(baseline_warned - compared_warned)
    decision_changed = baseline.get("decision") != compared.get("decision")
    check_changed = bool(added_failed or removed_failed or added_warned or removed_warned)
    if decision_changed:
        delta_status = "decision-delta"
    elif check_changed:
        delta_status = "check-delta"
    else:
        delta_status = "same"
    delta = {
        "bundle_path": baseline.get("bundle_path"),
        "release_name": baseline.get("release_name"),
        "baseline_profile": baseline.get("policy_profile"),
        "compared_profile": compared.get("policy_profile"),
        "baseline_decision": baseline.get("decision"),
        "compared_decision": compared.get("decision"),
        "baseline_gate_status": baseline.get("gate_status"),
        "compared_gate_status": compared.get("gate_status"),
        "baseline_minimum_audit_score": baseline.get("minimum_audit_score"),
        "compared_minimum_audit_score": compared.get("minimum_audit_score"),
        "baseline_require_generation_quality": baseline.get("require_generation_quality_audit_checks"),
        "compared_require_generation_quality": compared.get("require_generation_quality_audit_checks"),
        "baseline_require_request_history_summary": baseline.get("require_request_history_summary_audit_check"),
        "compared_require_request_history_summary": compared.get("require_request_history_summary_audit_check"),
        "decision_changed": decision_changed,
        "delta_status": delta_status,
        "added_failed_checks": added_failed,
        "removed_failed_checks": removed_failed,
        "added_warned_checks": added_warned,
        "removed_warned_checks": removed_warned,
    }
    delta["explanation"] = _delta_explanation(delta)
    return delta


def _delta_explanation(delta: dict[str, Any]) -> str:
    baseline = delta.get("baseline_profile")
    compared = delta.get("compared_profile")
    decision = f"{delta.get('baseline_decision')} -> {delta.get('compared_decision')}"
    parts = []
    if delta.get("decision_changed"):
        parts.append(f"{compared} changes the decision from {decision}.")
    else:
        parts.append(f"{compared} keeps the same decision as {baseline}: {delta.get('compared_decision')}.")

    added_failed = _string_list(delta.get("added_failed_checks"))
    removed_failed = _string_list(delta.get("removed_failed_checks"))
    added_warned = _string_list(delta.get("added_warned_checks"))
    removed_warned = _string_list(delta.get("removed_warned_checks"))
    if added_failed:
        parts.append("It adds failed check(s): " + ", ".join(added_failed) + ".")
    if removed_failed:
        parts.append("It removes failed check(s): " + ", ".join(removed_failed) + ".")
    if added_warned:
        parts.append("It adds warning check(s): " + ", ".join(added_warned) + ".")
    if removed_warned:
        parts.append("It removes warning check(s): " + ", ".join(removed_warned) + ".")
    if not any([added_failed, removed_failed, added_warned, removed_warned]):
        parts.append("No failed or warning check delta is present.")

    if delta.get("baseline_minimum_audit_score") != delta.get("compared_minimum_audit_score"):
        parts.append(
            f"Audit-score threshold changes from {delta.get('baseline_minimum_audit_score')} to {delta.get('compared_minimum_audit_score')}."
        )
    if delta.get("baseline_require_generation_quality") != delta.get("compared_require_generation_quality"):
        parts.append(
            f"Generation-quality requirement changes from {delta.get('baseline_require_generation_quality')} to {delta.get('compared_require_generation_quality')}."
        )
    if delta.get("baseline_require_request_history_summary") != delta.get("compared_require_request_history_summary"):
        parts.append(
            "Request-history-summary requirement changes from "
            f"{delta.get('baseline_require_request_history_summary')} to {delta.get('compared_require_request_history_summary')}."
        )
    return " ".join(parts)


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
