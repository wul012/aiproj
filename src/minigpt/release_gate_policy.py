from __future__ import annotations

from typing import Any

DEFAULT_RELEASE_GATE_POLICY_PROFILE = "standard"

RELEASE_GATE_POLICY_PROFILES: dict[str, dict[str, Any]] = {
    "standard": {
        "description": "Default tagged-release policy that preserves the v30 gate behavior.",
        "minimum_audit_score": 90.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
        "require_request_history_summary": True,
        "require_benchmark_history": True,
        "require_test_coverage": True,
    },
    "review": {
        "description": "Internal review policy with a lower audit-score bar while keeping generation-quality evidence required.",
        "minimum_audit_score": 80.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
        "require_request_history_summary": True,
        "require_benchmark_history": True,
        "require_test_coverage": True,
    },
    "strict": {
        "description": "Stricter release policy for external handoff or final review.",
        "minimum_audit_score": 95.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
        "require_request_history_summary": True,
        "require_benchmark_history": True,
        "require_test_coverage": True,
    },
    "legacy": {
        "description": "Compatibility policy for release bundles created before generation-quality, request-history, and coverage audit checks existed.",
        "minimum_audit_score": 80.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": False,
        "require_request_history_summary": False,
        "require_benchmark_history": False,
        "require_test_coverage": False,
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
    require_benchmark_history: bool | None = None,
    require_test_coverage: bool | None = None,
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
        "require_benchmark_history": require_benchmark_history is not None,
        "require_test_coverage": require_test_coverage is not None,
    }
    if minimum_audit_score is not None:
        profile["minimum_audit_score"] = float(minimum_audit_score)
    if minimum_ready_runs is not None:
        profile["minimum_ready_runs"] = int(minimum_ready_runs)
    if require_generation_quality is not None:
        profile["require_generation_quality"] = bool(require_generation_quality)
    if require_request_history_summary is not None:
        profile["require_request_history_summary"] = bool(require_request_history_summary)
    if require_benchmark_history is not None:
        profile["require_benchmark_history"] = bool(require_benchmark_history)
    if require_test_coverage is not None:
        profile["require_test_coverage"] = bool(require_test_coverage)
    return {
        "policy_profile": policy_profile,
        "profile_description": profile["description"],
        "minimum_audit_score": float(profile["minimum_audit_score"]),
        "minimum_ready_runs": int(profile["minimum_ready_runs"]),
        "require_generation_quality": bool(profile["require_generation_quality"]),
        "require_request_history_summary": bool(profile["require_request_history_summary"]),
        "require_benchmark_history": bool(profile["require_benchmark_history"]),
        "require_test_coverage": bool(profile["require_test_coverage"]),
        "overrides": overrides,
    }


__all__ = [
    "DEFAULT_RELEASE_GATE_POLICY_PROFILE",
    "RELEASE_GATE_POLICY_PROFILES",
    "release_gate_policy_profiles",
    "resolve_release_gate_policy",
]
