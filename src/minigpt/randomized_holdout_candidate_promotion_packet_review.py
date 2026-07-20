from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_candidate_promotion_packet import RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME = "randomized_holdout_candidate_promotion_packet_review.json"
RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_CSV_FILENAME = "randomized_holdout_candidate_promotion_packet_review.csv"
RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_TEXT_FILENAME = "randomized_holdout_candidate_promotion_packet_review.txt"
RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_candidate_promotion_packet_review.md"
RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_HTML_FILENAME = "randomized_holdout_candidate_promotion_packet_review.html"


def locate_randomized_holdout_candidate_promotion_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout candidate promotion packet review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_candidate_promotion_packet_review(
    candidate_packet: dict[str, Any],
    *,
    candidate_packet_path: str | Path | None = None,
    minimum_candidate_cases: int = 20,
    title: str = "MiniGPT randomized holdout candidate promotion packet review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    packet = as_dict(candidate_packet.get("packet"))
    summary = as_dict(candidate_packet.get("summary"))
    evidence_rows = list_of_dicts(candidate_packet.get("evidence_rows"))
    checks = _checks(candidate_packet, packet, summary, evidence_rows, minimum_candidate_cases)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, packet, summary, evidence_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "candidate_packet_path": str(candidate_packet_path or ""),
        "source_packet_summary": summary,
        "source_packet": packet,
        "evidence_rows": evidence_rows,
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_gate_approval: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("randomized_holdout_candidate_promotion_packet_review_ready") is not True:
        return 1
    if require_gate_approval and summary.get("approved_for_bounded_promotion_gate") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    candidate_packet: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    minimum_candidate_cases: int,
) -> list[dict[str, Any]]:
    candidate_count = int(summary.get("candidate_case_count") or packet.get("candidate_case_count") or 0)
    suite_count = int(summary.get("suite_case_count") or packet.get("suite_case_count") or 0)
    clean_count = int(summary.get("clean_randomized_case_count") or packet.get("clean_randomized_case_count") or 0)
    return [
        _check("candidate_packet_passed", candidate_packet.get("status") == "pass", candidate_packet.get("status"), "candidate packet must pass"),
        _check(
            "candidate_packet_decision_ready",
            candidate_packet.get("decision") == "randomized_holdout_candidate_promotion_packet_ready",
            candidate_packet.get("decision"),
            "candidate packet decision must be ready",
        ),
        _check(
            "candidate_packet_summary_ready",
            summary.get("randomized_holdout_candidate_promotion_packet_ready") is True,
            summary.get("randomized_holdout_candidate_promotion_packet_ready"),
            "candidate packet summary must be ready",
        ),
        _check("packet_ready", packet.get("packet_ready") is True, packet.get("packet_ready"), "source packet body must be ready"),
        _check(
            "handoff_ready_for_review",
            packet.get("handoff_status") == "ready_for_candidate_promotion_packet_review",
            packet.get("handoff_status"),
            "candidate packet must route to packet review",
        ),
        _check("candidate_case_count_floor", candidate_count >= minimum_candidate_cases, candidate_count, "review requires the randomized 20-case floor"),
        _check("suite_case_count_matches", suite_count == candidate_count, {"suite": suite_count, "candidate": candidate_count}, "suite and candidate counts must match"),
        _check("clean_cases_complete", clean_count == candidate_count, clean_count, "all candidate prompts must remain clean randomized prompts"),
        _check("random_seed_present", summary.get("random_seed") is not None or packet.get("random_seed") is not None, summary.get("random_seed") or packet.get("random_seed"), "review needs the randomized source seed"),
        _check("pass_rate_complete", float(summary.get("pass_rate") or packet.get("pass_rate") or 0.0) == 1.0, summary.get("pass_rate") or packet.get("pass_rate"), "candidate packet must preserve the 1.0 randomized replay pass rate"),
        _check("negative_control_rejected", int(summary.get("negative_dry_run_passed_case_count") or packet.get("negative_dry_run_passed_case_count") or 0) == 0, summary.get("negative_dry_run_passed_case_count") or packet.get("negative_dry_run_passed_case_count"), "dry-run negative control must remain rejected"),
        _check("candidate_packet_authorized", summary.get("candidate_packet_authorized") is True or packet.get("candidate_packet_authorized") is True, summary.get("candidate_packet_authorized") or packet.get("candidate_packet_authorized"), "source review must authorize the candidate packet"),
        _check("source_checks_clean", int(summary.get("failed_check_count") or 0) == 0, summary.get("failed_check_count"), "source packet checks must be clean"),
        _check("evidence_count", len(evidence_rows) >= 4, len(evidence_rows), "review requires suite, dry-run, real replay, and replay review evidence"),
        _check("evidence_files_exist", all(row.get("exists") is True for row in evidence_rows), evidence_rows, "all evidence source paths must exist"),
        _check("evidence_ready", all(row.get("ready_value") is True for row in evidence_rows), [row.get("ready_value") for row in evidence_rows], "all evidence rows must report ready"),
        _check("evidence_keeps_promotion_false", all(row.get("promotion_ready") is False for row in evidence_rows), [row.get("promotion_ready") for row in evidence_rows], "source evidence must not claim promotion"),
        _check("packet_keeps_promotion_false", summary.get("promotion_ready") is False and packet.get("promotion_ready") is False, {"summary": summary.get("promotion_ready"), "packet": packet.get("promotion_ready")}, "candidate packet review must not widen into promotion"),
        _check("approved_for_promotion_false", summary.get("approved_for_promotion") is False and packet.get("approved_for_promotion") is False, {"summary": summary.get("approved_for_promotion"), "packet": packet.get("approved_for_promotion")}, "direct promotion must remain false"),
        _check("claim_is_candidate_packet_only", (summary.get("model_quality_claim") or packet.get("model_quality_claim")) == "candidate_packet_only", summary.get("model_quality_claim") or packet.get("model_quality_claim"), "source claim must remain candidate-packet only"),
    ]


def _review(status: str, packet: dict[str, Any], summary: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = status == "pass"
    return {
        "review_ready": accepted,
        "review_decision": "accept_randomized_holdout_candidate_packet_for_bounded_gate" if accepted else "repair_randomized_holdout_candidate_packet_before_gate",
        "candidate_case_count": summary.get("candidate_case_count") or packet.get("candidate_case_count"),
        "random_seed": summary.get("random_seed") or packet.get("random_seed"),
        "pass_rate": summary.get("pass_rate") or packet.get("pass_rate"),
        "clean_randomized_case_count": summary.get("clean_randomized_case_count") or packet.get("clean_randomized_case_count"),
        "evidence_count": len(evidence_rows),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "approved_for_bounded_promotion_gate": accepted,
        "model_quality_claim": "candidate_packet_review_only",
        "review_scope": "bounded_randomized_holdout_candidate_review_only",
        "next_step": "build_randomized_holdout_bounded_promotion_gate" if accepted else "repair_randomized_holdout_candidate_promotion_packet",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_candidate_promotion_packet_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_decision": review.get("review_decision"),
        "candidate_case_count": review.get("candidate_case_count"),
        "random_seed": review.get("random_seed"),
        "pass_rate": review.get("pass_rate"),
        "clean_randomized_case_count": review.get("clean_randomized_case_count"),
        "evidence_count": review.get("evidence_count"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "approved_for_bounded_promotion_gate": review.get("approved_for_bounded_promotion_gate"),
        "model_quality_claim": review.get("model_quality_claim"),
        "review_scope": review.get("review_scope"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_candidate_promotion_packet_review_ready"
    return "fix_randomized_holdout_candidate_promotion_packet_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout candidate packet is not ready for bounded promotion-gate review.",
            "next_action": "repair candidate packet evidence, counts, seed, or promotion-boundary fields",
        }
    return {
        "model_quality_claim": review.get("model_quality_claim"),
        "reason": "The randomized holdout candidate packet is ready for a bounded gate while direct promotion remains blocked.",
        "next_action": review.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_candidate_promotion_packet_review",
    "locate_randomized_holdout_candidate_promotion_packet",
    "read_json_report",
    "resolve_exit_code",
]
