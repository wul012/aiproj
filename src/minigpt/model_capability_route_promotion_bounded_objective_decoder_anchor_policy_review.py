from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay import (
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review.json"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review.csv"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review.txt"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review.md"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review.html"


def locate_decoder_anchor_policy_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective decoder anchor policy review input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review(
    policy_replay: dict[str, Any],
    *,
    policy_replay_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective decoder anchor policy review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(policy_replay.get("summary"))
    replay_rows = list_of_dicts(policy_replay.get("replay_rows"))
    signals = _signals(policy_replay, replay_summary, replay_rows)
    recommendations = _recommendations(signals)
    checks = _checks(policy_replay, replay_summary, replay_rows, signals)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, signals, recommendations)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, review, signals),
        "failed_count": len(issues),
        "issues": issues,
        "source_policy_replay": str(policy_replay_path or ""),
        "replay_summary": replay_summary,
        "signals": signals,
        "recommendations": recommendations,
        "review": review,
        "check_rows": checks,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(report: dict[str, Any], *, require_review_ready: bool, require_branch_closed: bool = False) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and report.get("status") != "pass":
        return 1
    if require_branch_closed and summary.get("assisted_anchor_path_closed") is not True:
        return 1
    return 0


def _signals(policy_replay: dict[str, Any], replay_summary: dict[str, Any], replay_rows: list[dict[str, Any]]) -> dict[str, Any]:
    new_text_pass_count = int(replay_summary.get("new_text_pass_count") or 0)
    policy_pass_count = int(replay_summary.get("policy_applied_pass_count") or 0)
    case_count = int(replay_summary.get("case_count") or len(replay_rows) or 0)
    return {
        "policy_replay_status": policy_replay.get("status"),
        "policy_replay_ready": replay_summary.get("bounded_objective_decoder_anchor_policy_replay_ready") is True,
        "policy_replay_success": replay_summary.get("policy_replay_success") is True,
        "case_count": case_count,
        "policy_applied_case_count": int(replay_summary.get("policy_applied_case_count") or 0),
        "policy_applied_pass_count": policy_pass_count,
        "new_text_pass_count": new_text_pass_count,
        "promotion_ready": replay_summary.get("promotion_ready") is True,
        "all_policy_cases_reproduced": case_count > 0 and policy_pass_count == case_count,
        "unassisted_recovery_present": new_text_pass_count > 0,
        "assisted_only_recovery": policy_pass_count > 0 and new_text_pass_count == 0,
        "sample_continuations": [str(row.get("continuation") or "")[:80] for row in replay_rows[:3]],
    }


def _recommendations(signals: dict[str, Any]) -> list[dict[str, Any]]:
    if signals.get("unassisted_recovery_present"):
        return [
            {"id": "review_unassisted_recovery", "priority": "high", "action": "run_unassisted_holdout_before_any_promotion"},
            {"id": "keep_anchor_policy_as_diagnostic", "priority": "medium", "action": "do_not_use_anchor_policy_as_primary_route"},
        ]
    return [
        {"id": "close_assisted_anchor_path", "priority": "high", "action": "stop_treating_decoder_anchor_policy_as_capability_path"},
        {"id": "design_unassisted_objective_repair", "priority": "high", "action": "move_to_unassisted_objective_repair_plan"},
        {"id": "preserve_anchor_policy_as_diagnostic", "priority": "medium", "action": "keep_policy_artifacts_for_decoder_diagnostics_only"},
    ]


def _checks(policy_replay: dict[str, Any], replay_summary: dict[str, Any], replay_rows: list[dict[str, Any]], signals: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("policy_replay_passed", policy_replay.get("status") == "pass", policy_replay.get("status"), "policy replay must pass"),
        _check("policy_replay_ready", replay_summary.get("bounded_objective_decoder_anchor_policy_replay_ready") is True, replay_summary.get("bounded_objective_decoder_anchor_policy_replay_ready"), "policy replay must be ready"),
        _check("replay_rows_present", bool(replay_rows), len(replay_rows), "review must have replay rows"),
        _check("promotion_still_blocked", signals.get("promotion_ready") is False, signals.get("promotion_ready"), "policy replay must not already allow promotion"),
        _check("policy_signal_present", int(signals.get("policy_applied_pass_count") or 0) > 0, signals.get("policy_applied_pass_count"), "review expects a reproduced assisted signal"),
    ]


def _review(status: str, signals: dict[str, Any], recommendations: list[dict[str, Any]]) -> dict[str, Any]:
    close_path = status == "pass" and signals.get("assisted_only_recovery") is True
    return {
        "ready": status == "pass",
        "assisted_anchor_path_closed": close_path,
        "selected_track": "unassisted_objective_repair" if close_path else "unassisted_holdout_review",
        "promotion_ready": False,
        "new_training_allowed": False,
        "recommendation_count": len(recommendations),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_plan" if close_path else "model_capability_route_promotion_bounded_objective_unassisted_holdout_review",
        "next_step": "design_bounded_objective_unassisted_repair_plan" if close_path else "review_unassisted_recovery_before_promotion",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_decoder_anchor_policy_review_ready": status == "pass" and review.get("ready") is True,
        "assisted_anchor_path_closed": review.get("assisted_anchor_path_closed"),
        "selected_track": review.get("selected_track"),
        "promotion_ready": review.get("promotion_ready"),
        "new_training_allowed": review.get("new_training_allowed"),
        "recommendation_count": review.get("recommendation_count"),
        "proposed_next_artifact": review.get("proposed_next_artifact"),
        "next_step": review.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, review: dict[str, Any], signals: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review"
    if signals.get("unassisted_recovery_present"):
        return "review_bounded_objective_unassisted_recovery_before_promotion"
    if review.get("assisted_anchor_path_closed") is True:
        return "close_bounded_objective_decoder_anchor_policy_as_capability_path"
    return "manual_review_bounded_objective_decoder_anchor_policy"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Policy replay review inputs are incomplete.", "next_action": "repair policy replay review inputs"}
    return {
        "model_quality_claim": "review_only",
        "reason": "Decoder anchor policy replay is assisted-only evidence; it should guide diagnostics but not serve as a capability route.",
        "next_action": review.get("next_step"),
    }


__all__ = [
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review",
    "locate_decoder_anchor_policy_replay",
    "read_json_report",
    "resolve_exit_code",
]
