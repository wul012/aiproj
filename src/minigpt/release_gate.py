from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    utc_now,
)
from minigpt.release_gate_artifacts import (
    render_release_gate_html,
    render_release_gate_markdown,
    write_release_gate_html,
    write_release_gate_json,
    write_release_gate_markdown,
    write_release_gate_outputs,
)

DEFAULT_RELEASE_GATE_POLICY_PROFILE = "standard"

RELEASE_GATE_POLICY_PROFILES: dict[str, dict[str, Any]] = {
    "standard": {
        "description": "Default tagged-release policy that preserves the v30 gate behavior.",
        "minimum_audit_score": 90.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
        "require_request_history_summary": True,
    },
    "review": {
        "description": "Internal review policy with a lower audit-score bar while keeping generation-quality evidence required.",
        "minimum_audit_score": 80.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
        "require_request_history_summary": True,
    },
    "strict": {
        "description": "Stricter release policy for external handoff or final review.",
        "minimum_audit_score": 95.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
        "require_request_history_summary": True,
    },
    "legacy": {
        "description": "Compatibility policy for release bundles created before generation-quality and request-history audit checks existed.",
        "minimum_audit_score": 80.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": False,
        "require_request_history_summary": False,
    },
}

def release_gate_policy_profiles() -> dict[str, dict[str, Any]]:
    return {name: dict(profile) for name, profile in RELEASE_GATE_POLICY_PROFILES.items()}


def resolve_release_gate_policy(
    policy_profile: str = DEFAULT_RELEASE_GATE_POLICY_PROFILE,
    *,
    minimum_audit_score: float | None = None,
    minimum_ready_runs: int | None = None,
    require_generation_quality: bool | None = None,
    require_request_history_summary: bool | None = None,
) -> dict[str, Any]:
    if policy_profile not in RELEASE_GATE_POLICY_PROFILES:
        choices = ", ".join(sorted(RELEASE_GATE_POLICY_PROFILES))
        raise ValueError(f"unknown release gate policy profile: {policy_profile!r}; choices: {choices}")
    profile = dict(RELEASE_GATE_POLICY_PROFILES[policy_profile])
    overrides = {
        "minimum_audit_score": minimum_audit_score is not None,
        "minimum_ready_runs": minimum_ready_runs is not None,
        "require_generation_quality": require_generation_quality is not None,
        "require_request_history_summary": require_request_history_summary is not None,
    }
    if minimum_audit_score is not None:
        profile["minimum_audit_score"] = float(minimum_audit_score)
    if minimum_ready_runs is not None:
        profile["minimum_ready_runs"] = int(minimum_ready_runs)
    if require_generation_quality is not None:
        profile["require_generation_quality"] = bool(require_generation_quality)
    if require_request_history_summary is not None:
        profile["require_request_history_summary"] = bool(require_request_history_summary)
    return {
        "policy_profile": policy_profile,
        "profile_description": profile["description"],
        "minimum_audit_score": float(profile["minimum_audit_score"]),
        "minimum_ready_runs": int(profile["minimum_ready_runs"]),
        "require_generation_quality": bool(profile["require_generation_quality"]),
        "require_request_history_summary": bool(profile["require_request_history_summary"]),
        "overrides": overrides,
    }


def build_release_gate(
    bundle_path: str | Path,
    *,
    policy_profile: str = DEFAULT_RELEASE_GATE_POLICY_PROFILE,
    minimum_audit_score: float | None = None,
    minimum_ready_runs: int | None = None,
    require_generation_quality: bool | None = None,
    require_request_history_summary: bool | None = None,
    title: str = "MiniGPT release gate",
    generated_at: str | None = None,
) -> dict[str, Any]:
    bundle_file = Path(bundle_path)
    bundle = _read_required_json(bundle_file)
    policy = resolve_release_gate_policy(
        policy_profile,
        minimum_audit_score=minimum_audit_score,
        minimum_ready_runs=minimum_ready_runs,
        require_generation_quality=require_generation_quality,
        require_request_history_summary=require_request_history_summary,
    )
    checks = _build_checks(
        bundle,
        minimum_audit_score=policy["minimum_audit_score"],
        minimum_ready_runs=policy["minimum_ready_runs"],
        require_generation_quality=policy["require_generation_quality"],
        require_request_history_summary=policy["require_request_history_summary"],
    )
    summary = _build_summary(bundle, checks)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "bundle_path": str(bundle_file),
        "release_name": bundle.get("release_name"),
        "policy": {
            "policy_profile": policy["policy_profile"],
            "profile_description": policy["profile_description"],
            "required_release_status": "release-ready",
            "required_audit_status": "pass",
            "minimum_audit_score": policy["minimum_audit_score"],
            "minimum_ready_runs": policy["minimum_ready_runs"],
            "require_all_evidence_artifacts": True,
            "require_generation_quality_audit_checks": policy["require_generation_quality"],
            "require_request_history_summary_audit_check": policy["require_request_history_summary"],
            "overrides": policy["overrides"],
        },
        "summary": summary,
        "checks": checks,
        "recommendations": _recommendations(summary, checks, bundle),
        "bundle_recommendations": _string_list(bundle.get("recommendations")),
        "warnings": _string_list(bundle.get("warnings")),
    }


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
    require_request_history_summary: bool,
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
            "request_history_summary_audit_check",
            "Request history summary audit check passed",
            _request_history_summary_audit_result(audit_checks, require_request_history_summary),
            _request_history_summary_audit_detail(audit_checks, require_request_history_summary),
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


def _request_history_summary_audit_result(audit_checks: list[dict[str, Any]], require_request_history_summary: bool) -> str:
    if not require_request_history_summary:
        return "pass"
    by_id = _audit_checks_by_id(audit_checks)
    status = str(_dict(by_id.get("request_history_summary")).get("status") or "missing")
    if status in {"missing", "fail"}:
        return "fail"
    if status == "warn":
        return "warn"
    return "pass"


def _request_history_summary_audit_detail(audit_checks: list[dict[str, Any]], require_request_history_summary: bool) -> str:
    if not require_request_history_summary:
        return "request history summary audit check is not required by policy."
    by_id = _audit_checks_by_id(audit_checks)
    check = _dict(by_id.get("request_history_summary"))
    if not check:
        return "missing required audit check: request_history_summary."
    return f"request_history_summary={check.get('status') or 'missing'}."


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


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


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
