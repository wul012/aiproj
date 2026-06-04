from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_probe import (
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy.json"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy.csv"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy.txt"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy.md"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy.html"


def locate_decoder_anchor_probe(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective decoder anchor policy input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy(
    decoder_anchor_probe: dict[str, Any],
    *,
    probe_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective decoder anchor policy",
    generated_at: str | None = None,
) -> dict[str, Any]:
    probe_summary = as_dict(decoder_anchor_probe.get("summary"))
    probe_rows = list_of_dicts(decoder_anchor_probe.get("probe_rows"))
    policy_rows = _policy_rows(probe_rows)
    uncovered_cases = _uncovered_cases(probe_rows, policy_rows)
    guardrails = _guardrails(policy_rows, uncovered_cases)
    checks = _checks(decoder_anchor_probe, probe_summary, probe_rows, policy_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    policy = _policy(status, policy_rows, uncovered_cases, guardrails)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, policy),
        "failed_count": len(issues),
        "issues": issues,
        "source_decoder_anchor_probe": str(probe_path or ""),
        "probe_summary": probe_summary,
        "policy_rows": policy_rows,
        "uncovered_cases": uncovered_cases,
        "guardrails": guardrails,
        "check_rows": checks,
        "policy": policy,
        "summary": _summary(status, checks, policy),
        "interpretation": _interpretation(status, policy),
    }


def resolve_exit_code(report: dict[str, Any], *, require_policy_ready: bool) -> int:
    return 1 if require_policy_ready and report.get("status") != "pass" else 0


def _policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    winners: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("completion_pass") is not True:
            continue
        case_id = str(row.get("case_id") or "")
        current = winners.get(case_id)
        if current is None or _rank(row) < _rank(current):
            winners[case_id] = row
    return [_policy_row(row) for _, row in sorted(winners.items())]


def _policy_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row.get("case_id"),
        "profile_id": row.get("profile_id"),
        "anchor": row.get("anchor"),
        "anchor_length": len(str(row.get("anchor") or "")),
        "completion_hit_terms": row.get("completion_hit_terms", []),
        "new_text_hit_terms": row.get("new_text_hit_terms", []),
        "combined_preview": str(row.get("combined") or "")[:120],
        "policy_type": "case_specific_bounded_objective_decoder_anchor",
        "claim_boundary": "decoder_anchor_signal_only",
        "recommended_use": "controlled_policy_replay_only",
    }


def _rank(row: dict[str, Any]) -> tuple[int, int, str]:
    new_text_bonus = 0 if row.get("new_text_pass") is True else 1
    return (new_text_bonus, len(str(row.get("anchor") or "")), str(row.get("profile_id") or ""))


def _uncovered_cases(rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    covered = {str(row.get("case_id")) for row in policy_rows}
    case_ids = sorted({str(row.get("case_id")) for row in rows if row.get("case_id")})
    return [{"case_id": case_id, "reason": "no_completion_pass_profile"} for case_id in case_ids if case_id not in covered]


def _guardrails(policy_rows: list[dict[str, Any]], uncovered_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"id": "not_unassisted_model_capability", "severity": "blocker", "detail": "Injected anchors must not be counted as unassisted bounded objective replay success."},
        {"id": "requires_policy_replay", "severity": "blocker", "detail": "The selected anchors must be replayed before any downstream use."},
        {"id": "substring_scoring_not_final_exactness", "severity": "warning", "detail": "Policy is based on required-term completion hits; replay must still check final generated text and exact contract behavior."},
        {"id": "policy_coverage", "severity": "warning" if uncovered_cases else "info", "detail": f"Policy covers {len(policy_rows)} cases and leaves {len(uncovered_cases)} uncovered."},
    ]


def _checks(probe: dict[str, Any], probe_summary: dict[str, Any], rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("decoder_anchor_probe_passed", probe.get("status") == "pass", probe.get("status"), "decoder anchor probe must pass"),
        _check("bounded_objective_decoder_anchor_probe_ready", probe_summary.get("bounded_objective_decoder_anchor_probe_ready") is True, probe_summary.get("bounded_objective_decoder_anchor_probe_ready"), "bounded objective probe summary must be ready"),
        _check("probe_rows_present", bool(rows), len(rows), "policy must read probe rows"),
        _check("completion_signal_present", bool(policy_rows), len(policy_rows), "policy requires at least one completion-pass probe row"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _policy(status: str, policy_rows: list[dict[str, Any]], uncovered_cases: list[dict[str, Any]], guardrails: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "policy_case_count": len(policy_rows),
        "uncovered_case_count": len(uncovered_cases),
        "guardrail_count": len(guardrails),
        "coverage_is_partial": bool(uncovered_cases),
        "promotion_ready": False,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay",
        "next_step": "run_bounded_objective_decoder_anchor_policy_replay" if status == "pass" else "repair_bounded_objective_decoder_anchor_policy_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_decoder_anchor_policy_ready": status == "pass" and policy.get("ready") is True,
        "policy_case_count": policy.get("policy_case_count"),
        "uncovered_case_count": policy.get("uncovered_case_count"),
        "guardrail_count": policy.get("guardrail_count"),
        "coverage_is_partial": policy.get("coverage_is_partial"),
        "promotion_ready": policy.get("promotion_ready"),
        "proposed_next_artifact": policy.get("proposed_next_artifact"),
        "next_step": policy.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, policy: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_objective_decoder_anchor_policy"
    if policy.get("coverage_is_partial") is True:
        return "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_ready_with_partial_coverage"
    return "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_ready"


def _interpretation(status: str, policy: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Bounded objective decoder anchor policy inputs are incomplete.", "next_action": "repair decoder anchor policy inputs"}
    return {
        "model_quality_claim": "decoder_anchor_policy_only",
        "reason": "Policy is based on assisted decoder anchors and must be replayed before any capability claim.",
        "next_action": policy.get("next_step"),
    }


__all__ = [
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy",
    "locate_decoder_anchor_probe",
    "read_json_report",
    "resolve_exit_code",
]
