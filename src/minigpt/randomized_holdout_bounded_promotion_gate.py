from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_candidate_promotion_packet import RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
from minigpt.randomized_holdout_candidate_promotion_packet_review import RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME = "randomized_holdout_bounded_promotion_gate.json"
RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_CSV_FILENAME = "randomized_holdout_bounded_promotion_gate.csv"
RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_TEXT_FILENAME = "randomized_holdout_bounded_promotion_gate.txt"
RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_MARKDOWN_FILENAME = "randomized_holdout_bounded_promotion_gate.md"
RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_HTML_FILENAME = "randomized_holdout_bounded_promotion_gate.html"


def locate_randomized_holdout_candidate_packet_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME
    return source


def locate_randomized_holdout_candidate_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout bounded promotion gate input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_bounded_promotion_gate(
    candidate_packet_review: dict[str, Any],
    candidate_packet: dict[str, Any],
    *,
    candidate_packet_review_path: str | Path | None = None,
    candidate_packet_path: str | Path | None = None,
    minimum_candidate_cases: int = 20,
    title: str = "MiniGPT randomized holdout bounded promotion gate",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(candidate_packet_review.get("summary"))
    packet_summary = as_dict(candidate_packet.get("summary"))
    review = as_dict(candidate_packet_review.get("review"))
    packet = as_dict(candidate_packet.get("packet"))
    checks = _checks(
        candidate_packet_review,
        candidate_packet,
        review,
        packet,
        review_summary,
        packet_summary,
        candidate_packet_review_path,
        candidate_packet_path,
        minimum_candidate_cases,
    )
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    gate = _gate(status, review, packet, review_summary, packet_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "exit_code": 0 if status == "pass" else 1,
        "failed_count": len(issues),
        "issues": issues,
        "candidate_packet_review_path": str(candidate_packet_review_path or ""),
        "candidate_packet_path": str(candidate_packet_path or ""),
        "candidate_packet_review_summary": review_summary,
        "candidate_packet_summary": packet_summary,
        "candidate_packet_review": review,
        "candidate_packet": packet,
        "check_rows": checks,
        "gate": gate,
        "summary": _summary(status, checks, gate),
        "interpretation": _interpretation(status, gate),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_gate_ready: bool,
    require_decision_approval: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_gate_ready and summary.get("randomized_holdout_bounded_promotion_gate_ready") is not True:
        return 1
    if require_decision_approval and summary.get("approved_for_bounded_promotion_decision") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    review_report: dict[str, Any],
    packet_report: dict[str, Any],
    review: dict[str, Any],
    packet: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    review_path: str | Path | None,
    packet_path: str | Path | None,
    minimum_candidate_cases: int,
) -> list[dict[str, Any]]:
    review_count = int(review_summary.get("candidate_case_count") or review.get("candidate_case_count") or 0)
    packet_count = int(packet_summary.get("candidate_case_count") or packet.get("candidate_case_count") or 0)
    review_seed = review_summary.get("random_seed") or review.get("random_seed")
    packet_seed = packet_summary.get("random_seed") or packet.get("random_seed")
    return [
        _check("review_file_exists", _path_exists(review_path), str(review_path or ""), "candidate packet review source file must exist"),
        _check("packet_file_exists", _path_exists(packet_path), str(packet_path or ""), "candidate packet source file must exist"),
        _check("review_passed", review_report.get("status") == "pass", review_report.get("status"), "candidate packet review must pass"),
        _check(
            "review_decision_ready",
            review_report.get("decision") == "randomized_holdout_candidate_promotion_packet_review_ready",
            review_report.get("decision"),
            "candidate packet review decision must be ready",
        ),
        _check("review_summary_ready", review_summary.get("randomized_holdout_candidate_promotion_packet_review_ready") is True, review_summary.get("randomized_holdout_candidate_promotion_packet_review_ready"), "review summary must be ready"),
        _check("review_approves_bounded_gate", review_summary.get("approved_for_bounded_promotion_gate") is True, review_summary.get("approved_for_bounded_promotion_gate"), "review must approve bounded gate entry"),
        _check("review_routes_to_gate", review_summary.get("next_step") == "build_randomized_holdout_bounded_promotion_gate", review_summary.get("next_step"), "review must route to this gate"),
        _check("packet_passed", packet_report.get("status") == "pass", packet_report.get("status"), "candidate packet must pass"),
        _check("packet_ready", packet_summary.get("randomized_holdout_candidate_promotion_packet_ready") is True and packet.get("packet_ready") is True, {"summary": packet_summary.get("randomized_holdout_candidate_promotion_packet_ready"), "packet": packet.get("packet_ready")}, "candidate packet must be ready"),
        _check("candidate_count_floor", review_count >= minimum_candidate_cases and packet_count >= minimum_candidate_cases, {"review": review_count, "packet": packet_count}, "gate requires the randomized 20-case floor"),
        _check("candidate_counts_match", review_count == packet_count, {"review": review_count, "packet": packet_count}, "review and packet candidate counts must match"),
        _check("random_seed_matches", review_seed == packet_seed and review_seed is not None, {"review": review_seed, "packet": packet_seed}, "review and packet must carry the same randomized seed"),
        _check("pass_rate_complete", float(review_summary.get("pass_rate") or 0.0) == 1.0 and float(packet_summary.get("pass_rate") or 0.0) == 1.0, {"review": review_summary.get("pass_rate"), "packet": packet_summary.get("pass_rate")}, "gate requires a complete randomized replay pass rate"),
        _check("clean_cases_match", int(review_summary.get("clean_randomized_case_count") or 0) == int(packet_summary.get("clean_randomized_case_count") or 0) == packet_count, {"review": review_summary.get("clean_randomized_case_count"), "packet": packet_summary.get("clean_randomized_case_count")}, "clean randomized case counts must match candidate count"),
        _check("packet_negative_control_rejected", int(packet_summary.get("negative_dry_run_passed_case_count") or 0) == 0, packet_summary.get("negative_dry_run_passed_case_count"), "gate requires the packet negative control to remain rejected"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0 and int(packet_summary.get("failed_check_count") or 0) == 0, {"review": review_summary.get("failed_check_count"), "packet": packet_summary.get("failed_check_count")}, "review and packet checks must be clean"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and packet_summary.get("promotion_ready") is False and packet.get("promotion_ready") is False, {"review": review_summary.get("promotion_ready"), "packet_summary": packet_summary.get("promotion_ready"), "packet": packet.get("promotion_ready")}, "bounded gate must not become direct promotion"),
        _check("approved_for_promotion_false", review_summary.get("approved_for_promotion") is False and packet_summary.get("approved_for_promotion") is False and packet.get("approved_for_promotion") is False, {"review": review_summary.get("approved_for_promotion"), "packet_summary": packet_summary.get("approved_for_promotion"), "packet": packet.get("approved_for_promotion")}, "direct promotion approval must stay false"),
        _check("claim_scope_bounded", review_summary.get("model_quality_claim") == "candidate_packet_review_only" and packet_summary.get("model_quality_claim") == "candidate_packet_only", {"review": review_summary.get("model_quality_claim"), "packet": packet_summary.get("model_quality_claim")}, "claims must stay at packet-review and packet-only scope"),
    ]


def _gate(
    status: str,
    review: dict[str, Any],
    packet: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
) -> dict[str, Any]:
    accepted = status == "pass"
    return {
        "gate_ready": accepted,
        "gate_decision": "allow_bounded_randomized_holdout_promotion_decision" if accepted else "stop_for_randomized_holdout_gate_repair",
        "allowed_next_steps": ["record_randomized_holdout_bounded_promotion_decision", "build_randomized_holdout_decision_index"] if accepted else [],
        "blocked_next_steps": [] if accepted else ["record_randomized_holdout_bounded_promotion_decision", "build_randomized_holdout_decision_index"],
        "candidate_case_count": review_summary.get("candidate_case_count") or packet_summary.get("candidate_case_count"),
        "random_seed": review_summary.get("random_seed") or packet_summary.get("random_seed"),
        "pass_rate": review_summary.get("pass_rate") or packet_summary.get("pass_rate"),
        "clean_randomized_case_count": review_summary.get("clean_randomized_case_count") or packet_summary.get("clean_randomized_case_count"),
        "review_scope": review_summary.get("review_scope") or review.get("review_scope"),
        "handoff_status": packet.get("handoff_status"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "approved_for_bounded_promotion_decision": accepted,
        "model_quality_claim": "bounded_gate_only",
        "next_step": "record_randomized_holdout_bounded_promotion_decision" if accepted else "repair_randomized_holdout_bounded_promotion_gate",
    }


def _summary(status: str, checks: list[dict[str, Any]], gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_bounded_promotion_gate_ready": status == "pass" and gate.get("gate_ready") is True,
        "gate_decision": gate.get("gate_decision"),
        "candidate_case_count": gate.get("candidate_case_count"),
        "random_seed": gate.get("random_seed"),
        "pass_rate": gate.get("pass_rate"),
        "clean_randomized_case_count": gate.get("clean_randomized_case_count"),
        "review_scope": gate.get("review_scope"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "approved_for_bounded_promotion_decision": gate.get("approved_for_bounded_promotion_decision"),
        "model_quality_claim": gate.get("model_quality_claim"),
        "next_step": gate.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_bounded_promotion_gate_passed"
    return "fix_randomized_holdout_bounded_promotion_gate"


def _interpretation(status: str, gate: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout bounded promotion gate is blocked by review, packet, or boundary inconsistencies.",
            "next_action": "repair candidate packet review or packet evidence before bounded decision",
        }
    return {
        "model_quality_claim": gate.get("model_quality_claim"),
        "reason": "The randomized holdout candidate packet and review are clean enough for a bounded promotion decision while direct promotion remains blocked.",
        "next_action": gate.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_TEXT_FILENAME",
    "build_randomized_holdout_bounded_promotion_gate",
    "locate_randomized_holdout_candidate_packet",
    "locate_randomized_holdout_candidate_packet_review",
    "read_json_report",
    "resolve_exit_code",
]
