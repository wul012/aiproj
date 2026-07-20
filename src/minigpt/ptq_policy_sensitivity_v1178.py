from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from minigpt.ptq_candidate_v1177 import (
    PtqCandidatePolicy,
    build_ptq_candidate_report,
    locate_ptq_report,
    read_json_report,
)
from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import resolve_exit_code

PTQ_POLICY_SENSITIVITY_STEM = "ptq_policy_sensitivity_v1178"


@dataclass(frozen=True)
class PtqPolicyProfile:
    profile_id: str
    label: str
    policy: PtqCandidatePolicy

    def as_row(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            **self.policy.as_dict(),
        }


DEFAULT_POLICY_PROFILES = (
    PtqPolicyProfile(
        "strict_quality",
        "Strict quality budget; favors lower visible degradation over compression.",
        PtqCandidatePolicy(max_dce_nats=0.02, max_exact_match_drop=0.04, max_kl_nats=0.04),
    ),
    PtqPolicyProfile(
        "balanced_default",
        "Default v1177 budget; accepts modest quality cost for lower effective bits.",
        PtqCandidatePolicy(max_dce_nats=0.08, max_exact_match_drop=0.10, max_kl_nats=0.10),
    ),
    PtqPolicyProfile(
        "aggressive_compression",
        "Aggressive compression budget; useful only when visible accuracy loss is tolerated.",
        PtqCandidatePolicy(max_dce_nats=0.10, max_exact_match_drop=0.14, max_kl_nats=0.11),
    ),
)


def build_ptq_policy_sensitivity_report(
    ptq_report_or_path: dict[str, Any] | str | Path,
    *,
    profiles: tuple[PtqPolicyProfile, ...] = DEFAULT_POLICY_PROFILES,
    source_ptq_report: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_path: Path | None = None
    if isinstance(ptq_report_or_path, (str, Path)):
        source_path = locate_ptq_report(ptq_report_or_path)
        ptq_report = read_json_report(source_path)
    else:
        ptq_report = dict(ptq_report_or_path)
        if source_ptq_report is not None:
            source_path = locate_ptq_report(source_ptq_report)

    profile_reports = [
        build_ptq_candidate_report(
            ptq_report,
            policy=profile.policy,
            source_ptq_report=source_path,
            generated_at=generated_at,
        )
        for profile in profiles
    ]
    rows = [_profile_row(profile, report) for profile, report in zip(profiles, profile_reports)]
    failures = [row for row in rows if row["status"] != "pass"]
    selected_ids = [row["selected_candidate_id"] for row in rows if row["selected_candidate_id"]]
    unique_selected = sorted(set(selected_ids))
    stable = len(unique_selected) <= 1 and bool(unique_selected)
    status = "pass" if not failures else "fail"
    decision = "ptq_policy_sensitivity_measured" if status == "pass" else "repair_ptq_policy_sensitivity_inputs"
    source_summary = as_dict(ptq_report.get("summary"))
    default_row = _row_by_profile(rows, "balanced_default")

    return {
        "schema_version": 1,
        "title": "MiniGPT PTQ policy sensitivity v1178",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "summary": {
            "policy_sensitivity_ready": status == "pass",
            "source_status": ptq_report.get("status"),
            "source_verdict": source_summary.get("verdict"),
            "source_ptq_report": str(source_path) if source_path is not None else "",
            "profile_count": len(profiles),
            "passing_profile_count": len(rows) - len(failures),
            "unique_selected_candidate_count": len(unique_selected),
            "selected_candidate_ids": unique_selected,
            "selection_stable_across_profiles": stable,
            "default_profile_candidate": default_row.get("selected_candidate_id", ""),
            "default_profile_eff_bits": default_row.get("selected_eff_bits", ""),
            "default_profile_dce_mean": default_row.get("selected_dce_mean", ""),
            "default_profile_em_drop": default_row.get("selected_em_drop", ""),
            "sensitivity_verdict": "candidate_choice_changes_with_quality_budget" if not stable else "candidate_choice_stable_across_profiles",
            "boundary": "policy_sensitivity_only_reuses_v1175_quality_cost_evidence",
            "next_step": "use_balanced_default_unless_product_tolerance_explicitly_prefers_strict_or_aggressive",
        },
        "rows": rows,
        "profile_reports": profile_reports,
        "recommendations": _recommendations(rows, stable),
        "csv_fieldnames": [
            "profile_id",
            "status",
            "selected_candidate_id",
            "selected_eff_bits",
            "selected_dce_mean",
            "selected_kl_mean",
            "selected_em_drop",
            "viable_candidate_count",
            "max_dce_nats",
            "max_exact_match_drop",
            "max_kl_nats",
        ],
    }


def write_ptq_policy_sensitivity_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=PTQ_POLICY_SENSITIVITY_STEM, row_title="PTQ Policy Profiles")


def _profile_row(profile: PtqPolicyProfile, report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    return {
        **profile.as_row(),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "selected_candidate_id": summary.get("selected_candidate_id") or "",
        "selected_eff_bits": summary.get("selected_eff_bits") or "",
        "selected_dce_mean": summary.get("selected_dce_mean") or "",
        "selected_kl_mean": summary.get("selected_kl_mean") or "",
        "selected_em_drop": summary.get("selected_em_drop") or "",
        "viable_candidate_count": summary.get("viable_candidate_count") or 0,
    }


def _row_by_profile(rows: list[dict[str, Any]], profile_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("profile_id") == profile_id:
            return row
    return {}


def _recommendations(rows: list[dict[str, Any]], stable: bool) -> list[str]:
    if stable:
        candidate = rows[0].get("selected_candidate_id", "") if rows else ""
        return [
            f"All policy profiles select {candidate}; the candidate is robust to the tested quality budgets.",
            "A real quantized runtime is still required before speed or memory claims.",
        ]
    return [
        "Candidate choice changes across strict/default/aggressive budgets; do not present any single candidate as policy-invariant.",
        "Use the balanced_default profile as the project default because it keeps dCE, KL, and exact-match drop bounded without overstating runtime benefits.",
        "Choose strict_quality when visible accuracy is more important than compression; choose aggressive_compression only with an explicit tolerance for larger exact-match loss.",
    ]


__all__ = [
    "DEFAULT_POLICY_PROFILES",
    "PTQ_POLICY_SENSITIVITY_STEM",
    "PtqPolicyProfile",
    "build_ptq_policy_sensitivity_report",
    "resolve_exit_code",
    "write_ptq_policy_sensitivity_outputs",
]
