from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
)

from .release_gate import build_release_gate, release_gate_policy_profiles, utc_now
from .release_gate_comparison_artifacts import (
    render_release_gate_profile_comparison_html,
    render_release_gate_profile_comparison_markdown,
    write_release_gate_profile_comparison_csv,
    write_release_gate_profile_comparison_html,
    write_release_gate_profile_comparison_json,
    write_release_gate_profile_comparison_markdown,
    write_release_gate_profile_comparison_outputs,
    write_release_gate_profile_delta_csv,
)

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


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
