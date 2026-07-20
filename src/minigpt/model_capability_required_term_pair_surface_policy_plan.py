from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_failure_diagnostic import (
    PAIR_SURFACE_FAILURE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SURFACE_POLICY_PLAN_JSON_FILENAME = "model_capability_required_term_pair_surface_policy_plan.json"
PAIR_SURFACE_POLICY_PLAN_CSV_FILENAME = "model_capability_required_term_pair_surface_policy_plan.csv"
PAIR_SURFACE_POLICY_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_surface_policy_plan.txt"
PAIR_SURFACE_POLICY_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_policy_plan.md"
PAIR_SURFACE_POLICY_PLAN_HTML_FILENAME = "model_capability_required_term_pair_surface_policy_plan.html"


def locate_surface_policy_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_FAILURE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface policy plan input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_surface_policy_plan(
    surface_failure_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    issues = _issues(surface_failure_report)
    failure_terms = _failure_terms(surface_failure_report)
    policy_rows = _policy_rows(failure_terms)
    summary = _summary(policy_rows, failure_terms)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface policy plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_surface_failure_path": str(source_path or ""),
        "source_surface_failure": {
            "status": surface_failure_report.get("status"),
            "decision": surface_failure_report.get("decision"),
            "summary": as_dict(surface_failure_report.get("summary")),
        },
        "policy_rows": policy_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _issues(report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if report.get("status") != "pass":
        issues.append("source surface failure diagnostic is not pass")
    if not as_dict(report.get("summary")).get("surface_failure_seed_count"):
        issues.append("source diagnostic has no surface failure to plan against")
    return issues


def _failure_terms(report: dict[str, Any]) -> list[str]:
    terms = as_dict(report.get("summary")).get("surface_failure_terms") or []
    return [str(term) for term in terms if str(term)]


def _policy_rows(failure_terms: list[str]) -> list[dict[str, Any]]:
    policies = [
        {
            "policy_id": "single_label_default",
            "prompt_template": "{term}=",
            "generation_profile": "default",
            "leakage_level": "none",
            "replay_scope": "baseline",
            "included_in_replay": True,
            "purpose": "Measure the current minimal label prompt without changing decoding.",
        },
        {
            "policy_id": "single_label_suppress_newline",
            "prompt_template": "{term}=",
            "generation_profile": "suppress_newline_tokens",
            "leakage_level": "none",
            "replay_scope": "decode_surface_hygiene",
            "included_in_replay": True,
            "purpose": "Check whether newline suppression alone repairs the missing surface term.",
        },
        {
            "policy_id": "pair_context_prefix",
            "prompt_template": "{other_term}={other_term} {term}=",
            "generation_profile": "suppress_newline_tokens",
            "leakage_level": "contextual_anchor",
            "replay_scope": "paired_surface_policy",
            "included_in_replay": True,
            "purpose": "Test whether preserving the other learned term before the target label stabilizes the missed term.",
        },
        {
            "policy_id": "dual_boundary_sentence",
            "prompt_template": "dual boundary surface {other_term}={other_term} {term}=",
            "generation_profile": "suppress_newline_tokens",
            "leakage_level": "contextual_anchor",
            "replay_scope": "boundary_surface_policy",
            "included_in_replay": True,
            "purpose": "Replay the corpus boundary wording at inference time without writing the target value.",
        },
        {
            "policy_id": "target_echo_upper_bound",
            "prompt_template": "{term}={term}",
            "generation_profile": "suppress_newline_tokens",
            "leakage_level": "target_echo",
            "replay_scope": "upper_bound_only",
            "included_in_replay": False,
            "purpose": "Keep a documented upper-bound policy out of replay because it already contains the answer.",
        },
    ]
    return [{**row, "target_failure_terms": failure_terms} for row in policies]


def _summary(policy_rows: list[dict[str, Any]], failure_terms: list[str]) -> dict[str, Any]:
    replay_rows = [row for row in policy_rows if row.get("included_in_replay")]
    contextual_rows = [row for row in replay_rows if row.get("leakage_level") == "contextual_anchor"]
    return {
        "failure_terms": failure_terms,
        "policy_count": len(policy_rows),
        "replay_policy_count": len(replay_rows),
        "non_leaking_replay_policy_count": sum(1 for row in replay_rows if row.get("leakage_level") == "none"),
        "contextual_anchor_policy_count": len(contextual_rows),
        "excluded_upper_bound_policy_count": sum(1 for row in policy_rows if not row.get("included_in_replay")),
        "recommended_replay_policy_ids": [row.get("policy_id") for row in replay_rows],
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_policy_plan_input"
    if summary.get("contextual_anchor_policy_count"):
        return "required_term_pair_surface_policy_plan_ready"
    return "required_term_pair_surface_policy_plan_needs_contextual_candidate"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The source surface failure diagnostic is not usable."
        next_action = "repair diagnostic input before policy replay"
        claim = "not_claimed"
    else:
        reason = "The plan separates non-leaking baselines from contextual-anchor replay and excludes target-echo upper bounds."
        next_action = "run surface policy replay over the dual-boundary seed reports"
        claim = "surface_policy_plan_only"
    return {"model_quality_claim": claim, "reason": reason, "next_action": next_action}


__all__ = [
    "PAIR_SURFACE_POLICY_PLAN_CSV_FILENAME",
    "PAIR_SURFACE_POLICY_PLAN_HTML_FILENAME",
    "PAIR_SURFACE_POLICY_PLAN_JSON_FILENAME",
    "PAIR_SURFACE_POLICY_PLAN_MARKDOWN_FILENAME",
    "PAIR_SURFACE_POLICY_PLAN_TEXT_FILENAME",
    "build_model_capability_required_term_pair_surface_policy_plan",
    "locate_surface_policy_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
