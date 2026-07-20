from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_acceptance_publication_packet import RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_JSON_FILENAME = "randomized_holdout_acceptance_publication_packet_review.json"
RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_CSV_FILENAME = "randomized_holdout_acceptance_publication_packet_review.csv"
RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_TEXT_FILENAME = "randomized_holdout_acceptance_publication_packet_review.txt"
RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_acceptance_publication_packet_review.md"
RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_HTML_FILENAME = "randomized_holdout_acceptance_publication_packet_review.html"


def locate_randomized_holdout_acceptance_publication_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout acceptance publication packet review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_acceptance_publication_packet_review(
    publication_packet: dict[str, Any],
    *,
    publication_packet_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout acceptance publication packet review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    packet = as_dict(publication_packet.get("packet"))
    summary = as_dict(publication_packet.get("summary"))
    evidence_rows = list_of_dicts(publication_packet.get("evidence_rows"))
    accepted_claims = list_of_dicts(publication_packet.get("accepted_claims"))
    blocked_claims = list_of_dicts(publication_packet.get("blocked_claims"))
    checks = _checks(publication_packet, packet, summary, evidence_rows, accepted_claims, blocked_claims)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, packet, summary, evidence_rows, accepted_claims, blocked_claims)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "publication_packet_path": str(publication_packet_path or ""),
        "source_packet_summary": summary,
        "source_packet": packet,
        "evidence_rows": evidence_rows,
        "accepted_claims": accepted_claims,
        "blocked_claims": blocked_claims,
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_publication_approval: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("randomized_holdout_acceptance_publication_packet_review_ready") is not True:
        return 1
    if require_publication_approval and summary.get("approved_for_bounded_publication") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    publication_packet: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    accepted_claims: list[dict[str, Any]],
    blocked_claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("publication_packet_passed", publication_packet.get("status") == "pass", publication_packet.get("status"), "publication packet must pass"),
        _check("publication_packet_ready_decision", publication_packet.get("decision") == "randomized_holdout_acceptance_publication_packet_ready", publication_packet.get("decision"), "publication packet decision must be ready"),
        _check("packet_ready", packet.get("packet_ready") is True and summary.get("randomized_holdout_acceptance_publication_packet_ready") is True, {"packet": packet.get("packet_ready"), "summary": summary.get("randomized_holdout_acceptance_publication_packet_ready")}, "packet and summary must both be ready"),
        _check("handoff_ready_for_review", packet.get("handoff_status") == "ready_for_bounded_acceptance_publication_review", packet.get("handoff_status"), "packet must route to bounded publication review"),
        _check("accepted_claim_count", int(summary.get("accepted_claim_count") or 0) == len(accepted_claims) == 1, {"summary": summary.get("accepted_claim_count"), "claims": len(accepted_claims)}, "review expects exactly one bounded accepted claim"),
        _check("blocked_claim_count", int(summary.get("blocked_claim_count") or 0) == len(blocked_claims) >= 3, {"summary": summary.get("blocked_claim_count"), "claims": len(blocked_claims)}, "review expects blocked claim boundaries"),
        _check("allowed_use_bounded", summary.get("allowed_use") == "bounded_model_capability_governance_only" and packet.get("allowed_use") == "bounded_model_capability_governance_only", {"summary": summary.get("allowed_use"), "packet": packet.get("allowed_use")}, "allowed use must stay bounded governance only"),
        _check("promotion_still_false", summary.get("promotion_ready") is False and packet.get("promotion_ready") is False, {"summary": summary.get("promotion_ready"), "packet": packet.get("promotion_ready")}, "review must keep direct promotion blocked"),
        _check("approved_for_promotion_false", summary.get("approved_for_promotion") is False and packet.get("approved_for_promotion") is False, {"summary": summary.get("approved_for_promotion"), "packet": packet.get("approved_for_promotion")}, "direct promotion approval must remain false"),
        _check("contract_check_ready", packet.get("contract_check_ready") is True, packet.get("contract_check_ready"), "packet must include a passing contract check"),
        _check("evidence_count", len(evidence_rows) >= 2 and int(summary.get("evidence_count") or 0) >= 2, {"summary": summary.get("evidence_count"), "rows": len(evidence_rows)}, "review requires summary and contract-check evidence"),
        _check("evidence_files_exist", all(row.get("exists") is True for row in evidence_rows), evidence_rows, "all publication packet evidence rows must exist"),
        _check("packet_checks_clean", int(summary.get("failed_check_count") or 0) == 0, summary.get("failed_check_count"), "publication packet checks must be clean"),
    ]


def _review(
    status: str,
    packet: dict[str, Any],
    summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    accepted_claims: list[dict[str, Any]],
    blocked_claims: list[dict[str, Any]],
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_decision": "accept_publication_packet_for_bounded_downstream_review" if ready else "repair_publication_packet_before_review",
        "approved_for_bounded_publication": ready,
        "approved_for_promotion": False,
        "promotion_ready": False,
        "accepted_claim_count": len(accepted_claims) if ready else 0,
        "blocked_claim_count": len(blocked_claims),
        "candidate_case_count": packet.get("candidate_case_count") or summary.get("candidate_case_count"),
        "random_seed": packet.get("random_seed") or summary.get("random_seed"),
        "pass_rate": packet.get("pass_rate") or summary.get("pass_rate"),
        "allowed_use": packet.get("allowed_use") if ready else "none",
        "model_quality_claim": packet.get("model_quality_claim") if ready else "not_claimed",
        "review_scope": "bounded_randomized_holdout_publication_review_only",
        "evidence_count": len(evidence_rows),
        "next_step": "record_randomized_holdout_publication_decision" if ready else "repair_randomized_holdout_acceptance_publication_packet",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_acceptance_publication_packet_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_decision": review.get("review_decision"),
        "approved_for_bounded_publication": review.get("approved_for_bounded_publication"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "accepted_claim_count": review.get("accepted_claim_count"),
        "blocked_claim_count": review.get("blocked_claim_count"),
        "candidate_case_count": review.get("candidate_case_count"),
        "random_seed": review.get("random_seed"),
        "pass_rate": review.get("pass_rate"),
        "allowed_use": review.get("allowed_use"),
        "model_quality_claim": review.get("model_quality_claim"),
        "review_scope": review.get("review_scope"),
        "evidence_count": review.get("evidence_count"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_acceptance_publication_packet_review_ready"
    return "fix_randomized_holdout_acceptance_publication_packet_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout publication packet is not ready for bounded downstream review.",
            "next_action": "repair publication packet evidence, contract check, or boundary fields",
        }
    return {
        "model_quality_claim": review.get("model_quality_claim"),
        "reason": "The publication packet is approved only for bounded downstream governance review while direct promotion remains blocked.",
        "next_action": review.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_acceptance_publication_packet_review",
    "locate_randomized_holdout_acceptance_publication_packet",
    "read_json_report",
    "resolve_exit_code",
]
