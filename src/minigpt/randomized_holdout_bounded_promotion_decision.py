from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_bounded_promotion_gate import RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME
from minigpt.randomized_holdout_candidate_promotion_packet import RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
from minigpt.randomized_holdout_candidate_promotion_packet_review import RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME
from minigpt.report_utils import as_dict, utc_now


RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_JSON_FILENAME = "randomized_holdout_bounded_promotion_decision.json"
RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_CSV_FILENAME = "randomized_holdout_bounded_promotion_decision.csv"
RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_TEXT_FILENAME = "randomized_holdout_bounded_promotion_decision.txt"
RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_MARKDOWN_FILENAME = "randomized_holdout_bounded_promotion_decision.md"
RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_HTML_FILENAME = "randomized_holdout_bounded_promotion_decision.html"


def locate_randomized_holdout_bounded_promotion_gate(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME
    return source


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
        raise ValueError("randomized holdout bounded promotion decision input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_bounded_promotion_decision(
    gate_report: dict[str, Any],
    candidate_packet_review: dict[str, Any],
    candidate_packet: dict[str, Any],
    *,
    gate_path: str | Path | None = None,
    candidate_packet_review_path: str | Path | None = None,
    candidate_packet_path: str | Path | None = None,
    minimum_candidate_cases: int = 20,
    title: str = "MiniGPT randomized holdout bounded promotion decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    gate = as_dict(gate_report.get("gate"))
    gate_summary = as_dict(gate_report.get("summary"))
    review_summary = as_dict(candidate_packet_review.get("summary"))
    packet_summary = as_dict(candidate_packet.get("summary"))
    checks = _checks(
        gate_report,
        candidate_packet_review,
        candidate_packet,
        gate,
        gate_summary,
        review_summary,
        packet_summary,
        gate_path,
        candidate_packet_review_path,
        candidate_packet_path,
        minimum_candidate_cases,
    )
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    final_decision = _final_decision(status, gate, gate_summary, review_summary, packet_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "gate_path": str(gate_path or ""),
        "candidate_packet_review_path": str(candidate_packet_review_path or ""),
        "candidate_packet_path": str(candidate_packet_path or ""),
        "gate_summary": gate_summary,
        "candidate_packet_review_summary": review_summary,
        "candidate_packet_summary": packet_summary,
        "gate": gate,
        "check_rows": checks,
        "final_decision": final_decision,
        "summary": _summary(status, checks, final_decision),
        "interpretation": _interpretation(status, final_decision),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_decision_ready: bool,
    require_bounded_acceptance: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_decision_ready and summary.get("randomized_holdout_bounded_promotion_decision_ready") is not True:
        return 1
    if require_bounded_acceptance and summary.get("bounded_promotion_accepted") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    gate_report: dict[str, Any],
    review_report: dict[str, Any],
    packet_report: dict[str, Any],
    gate: dict[str, Any],
    gate_summary: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    gate_path: str | Path | None,
    review_path: str | Path | None,
    packet_path: str | Path | None,
    minimum_candidate_cases: int,
) -> list[dict[str, Any]]:
    gate_count = int(gate_summary.get("candidate_case_count") or gate.get("candidate_case_count") or 0)
    review_count = int(review_summary.get("candidate_case_count") or 0)
    packet_count = int(packet_summary.get("candidate_case_count") or 0)
    return [
        _check("gate_file_exists", _path_exists(gate_path), str(gate_path or ""), "bounded gate source file must exist"),
        _check("review_file_exists", _path_exists(review_path), str(review_path or ""), "candidate packet review source file must exist"),
        _check("packet_file_exists", _path_exists(packet_path), str(packet_path or ""), "candidate packet source file must exist"),
        _check("gate_passed", gate_report.get("status") == "pass", gate_report.get("status"), "bounded gate must pass"),
        _check("gate_decision_passed", gate_report.get("decision") == "randomized_holdout_bounded_promotion_gate_passed", gate_report.get("decision"), "bounded gate decision must pass"),
        _check("gate_ready", gate_summary.get("randomized_holdout_bounded_promotion_gate_ready") is True and gate.get("gate_ready") is True, {"summary": gate_summary.get("randomized_holdout_bounded_promotion_gate_ready"), "gate": gate.get("gate_ready")}, "bounded gate must be ready"),
        _check("gate_allows_bounded_decision", gate_summary.get("approved_for_bounded_promotion_decision") is True, gate_summary.get("approved_for_bounded_promotion_decision"), "gate must approve bounded decision entry"),
        _check("gate_routes_to_decision", gate_summary.get("next_step") == "record_randomized_holdout_bounded_promotion_decision", gate_summary.get("next_step"), "gate must route to bounded decision"),
        _check("review_passed", review_report.get("status") == "pass", review_report.get("status"), "candidate packet review must pass"),
        _check("packet_passed", packet_report.get("status") == "pass", packet_report.get("status"), "candidate packet must pass"),
        _check("candidate_count_floor", min(gate_count, review_count, packet_count) >= minimum_candidate_cases, {"gate": gate_count, "review": review_count, "packet": packet_count}, "bounded decision requires the randomized 20-case floor"),
        _check("candidate_counts_match", gate_count == review_count == packet_count, {"gate": gate_count, "review": review_count, "packet": packet_count}, "gate, review, and packet candidate counts must match"),
        _check("random_seed_matches", gate_summary.get("random_seed") == review_summary.get("random_seed") == packet_summary.get("random_seed"), {"gate": gate_summary.get("random_seed"), "review": review_summary.get("random_seed"), "packet": packet_summary.get("random_seed")}, "gate, review, and packet must carry the same seed"),
        _check("pass_rate_complete", float(gate_summary.get("pass_rate") or 0.0) == float(review_summary.get("pass_rate") or 0.0) == float(packet_summary.get("pass_rate") or 0.0) == 1.0, {"gate": gate_summary.get("pass_rate"), "review": review_summary.get("pass_rate"), "packet": packet_summary.get("pass_rate")}, "bounded decision requires a complete replay pass rate"),
        _check("clean_cases_match", int(gate_summary.get("clean_randomized_case_count") or 0) == int(review_summary.get("clean_randomized_case_count") or 0) == int(packet_summary.get("clean_randomized_case_count") or 0) == packet_count, {"gate": gate_summary.get("clean_randomized_case_count"), "review": review_summary.get("clean_randomized_case_count"), "packet": packet_summary.get("clean_randomized_case_count")}, "clean randomized case counts must match"),
        _check("source_checks_clean", int(gate_summary.get("failed_check_count") or 0) == 0 and int(review_summary.get("failed_check_count") or 0) == 0 and int(packet_summary.get("failed_check_count") or 0) == 0, {"gate": gate_summary.get("failed_check_count"), "review": review_summary.get("failed_check_count"), "packet": packet_summary.get("failed_check_count")}, "all upstream checks must be clean"),
        _check("promotion_still_false", gate_summary.get("promotion_ready") is False and review_summary.get("promotion_ready") is False and packet_summary.get("promotion_ready") is False, {"gate": gate_summary.get("promotion_ready"), "review": review_summary.get("promotion_ready"), "packet": packet_summary.get("promotion_ready")}, "bounded decision must not become production promotion"),
        _check("approved_for_promotion_false", gate_summary.get("approved_for_promotion") is False and review_summary.get("approved_for_promotion") is False and packet_summary.get("approved_for_promotion") is False, {"gate": gate_summary.get("approved_for_promotion"), "review": review_summary.get("approved_for_promotion"), "packet": packet_summary.get("approved_for_promotion")}, "direct promotion approval must stay false"),
        _check("claim_scopes_expected", gate_summary.get("model_quality_claim") == "bounded_gate_only" and review_summary.get("model_quality_claim") == "candidate_packet_review_only" and packet_summary.get("model_quality_claim") == "candidate_packet_only", {"gate": gate_summary.get("model_quality_claim"), "review": review_summary.get("model_quality_claim"), "packet": packet_summary.get("model_quality_claim")}, "claim scopes must stay bounded"),
    ]


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(path).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _final_decision(
    status: str,
    gate: dict[str, Any],
    gate_summary: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
) -> dict[str, Any]:
    accepted = status == "pass"
    return {
        "accepted": accepted,
        "decision": "accept_bounded_randomized_holdout_claim" if accepted else "reject_or_repair_bounded_randomized_holdout_claim",
        "bounded_promotion_accepted": accepted,
        "promotion_ready": False,
        "approved_for_promotion": False,
        "candidate_case_count": gate_summary.get("candidate_case_count") or review_summary.get("candidate_case_count") or packet_summary.get("candidate_case_count"),
        "random_seed": gate_summary.get("random_seed") or review_summary.get("random_seed") or packet_summary.get("random_seed"),
        "pass_rate": gate_summary.get("pass_rate") or review_summary.get("pass_rate") or packet_summary.get("pass_rate"),
        "claim_scope": "randomized_target_hidden_20_case_tiny_checkpoint_only" if accepted else "not_claimed",
        "model_quality_claim": "bounded_randomized_target_hidden_holdout_claim_only" if accepted else "not_claimed",
        "review_scope": gate.get("review_scope") or gate_summary.get("review_scope"),
        "next_step": "build_randomized_holdout_decision_index" if accepted else "repair_randomized_holdout_bounded_promotion_gate",
    }


def _summary(status: str, checks: list[dict[str, Any]], final_decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_bounded_promotion_decision_ready": status == "pass" and final_decision.get("accepted") is True,
        "final_decision": final_decision.get("decision"),
        "bounded_promotion_accepted": final_decision.get("bounded_promotion_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "candidate_case_count": final_decision.get("candidate_case_count"),
        "random_seed": final_decision.get("random_seed"),
        "pass_rate": final_decision.get("pass_rate"),
        "claim_scope": final_decision.get("claim_scope"),
        "model_quality_claim": final_decision.get("model_quality_claim"),
        "review_scope": final_decision.get("review_scope"),
        "next_step": final_decision.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_bounded_promotion_decision_accepted"
    return "fix_randomized_holdout_bounded_promotion_decision"


def _interpretation(status: str, final_decision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The bounded randomized holdout claim cannot be accepted until gate, review, and packet evidence align.",
            "next_action": "repair bounded gate, packet review, or packet evidence",
        }
    return {
        "model_quality_claim": final_decision.get("model_quality_claim"),
        "reason": "The randomized target-hidden holdout signal is accepted only inside the 20-case tiny-checkpoint bounded scope.",
        "next_action": final_decision.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_TEXT_FILENAME",
    "build_randomized_holdout_bounded_promotion_decision",
    "locate_randomized_holdout_bounded_promotion_gate",
    "locate_randomized_holdout_candidate_packet",
    "locate_randomized_holdout_candidate_packet_review",
    "read_json_report",
    "resolve_exit_code",
]
