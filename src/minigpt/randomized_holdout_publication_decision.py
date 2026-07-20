from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_acceptance_publication_packet_review import RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_JSON_FILENAME
from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE,
    RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_SCOPE,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_JSON_FILENAME = "randomized_holdout_publication_decision.json"
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_CSV_FILENAME = "randomized_holdout_publication_decision.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_TEXT_FILENAME = "randomized_holdout_publication_decision.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_MARKDOWN_FILENAME = "randomized_holdout_publication_decision.md"
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_HTML_FILENAME = "randomized_holdout_publication_decision.html"


def locate_randomized_holdout_publication_packet_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication decision input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_decision(
    publication_review: dict[str, Any],
    *,
    publication_review_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review = as_dict(publication_review.get("review"))
    summary = as_dict(publication_review.get("summary"))
    checks = _checks(publication_review, review, summary, publication_review_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    final_decision = _final_decision(status, review, summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "publication_review_path": str(publication_review_path or ""),
        "source_review_summary": summary,
        "source_review": review,
        "check_rows": checks,
        "final_decision": final_decision,
        "summary": _summary(status, checks, final_decision),
        "interpretation": _interpretation(status, final_decision),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_decision_ready: bool,
    require_bounded_publication: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_decision_ready and summary.get("randomized_holdout_publication_decision_ready") is not True:
        return 1
    if require_bounded_publication and summary.get("bounded_publication_accepted") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    publication_review: dict[str, Any],
    review: dict[str, Any],
    summary: dict[str, Any],
    review_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("review_file_exists", _path_exists(review_path), str(review_path or ""), "publication review source file must exist"),
        _check("review_passed", publication_review.get("status") == "pass", publication_review.get("status"), "publication review must pass"),
        _check("review_decision_ready", publication_review.get("decision") == "randomized_holdout_acceptance_publication_packet_review_ready", publication_review.get("decision"), "publication review decision must be ready"),
        _check("review_summary_ready", summary.get("randomized_holdout_acceptance_publication_packet_review_ready") is True, summary.get("randomized_holdout_acceptance_publication_packet_review_ready"), "review summary must be ready"),
        _check("review_approves_bounded_publication", summary.get("approved_for_bounded_publication") is True and review.get("approved_for_bounded_publication") is True, {"summary": summary.get("approved_for_bounded_publication"), "review": review.get("approved_for_bounded_publication")}, "review must approve bounded publication"),
        _check("accepted_claim_count", int(summary.get("accepted_claim_count") or 0) == 1, summary.get("accepted_claim_count"), "decision expects exactly one accepted bounded claim"),
        _check("blocked_claim_count", int(summary.get("blocked_claim_count") or 0) >= 3, summary.get("blocked_claim_count"), "decision expects blocked claim boundaries"),
        _check("allowed_use_bounded", summary.get("allowed_use") == RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE, summary.get("allowed_use"), "allowed use must remain bounded governance only"),
        _check("promotion_still_false", summary.get("promotion_ready") is False and review.get("promotion_ready") is False, {"summary": summary.get("promotion_ready"), "review": review.get("promotion_ready")}, "final decision must keep direct promotion blocked"),
        _check("approved_for_promotion_false", summary.get("approved_for_promotion") is False and review.get("approved_for_promotion") is False, {"summary": summary.get("approved_for_promotion"), "review": review.get("approved_for_promotion")}, "direct promotion approval must remain false"),
        _check("review_scope_bounded", summary.get("review_scope") == "bounded_randomized_holdout_publication_review_only", summary.get("review_scope"), "review scope must stay bounded"),
        _check("source_checks_clean", int(summary.get("failed_check_count") or 0) == 0, summary.get("failed_check_count"), "source review checks must be clean"),
    ]


def _final_decision(status: str, review: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    accepted = status == "pass"
    return {
        "accepted": accepted,
        "decision": "accept_bounded_randomized_holdout_publication" if accepted else "reject_or_repair_bounded_randomized_holdout_publication",
        "bounded_publication_accepted": accepted,
        "promotion_ready": False,
        "approved_for_promotion": False,
        "approved_for_bounded_publication": accepted,
        "accepted_claim_count": summary.get("accepted_claim_count"),
        "blocked_claim_count": summary.get("blocked_claim_count"),
        "candidate_case_count": summary.get("candidate_case_count") or review.get("candidate_case_count"),
        "random_seed": summary.get("random_seed") or review.get("random_seed"),
        "pass_rate": summary.get("pass_rate") or review.get("pass_rate"),
        "allowed_use": summary.get("allowed_use") if accepted else "none",
        "model_quality_claim": summary.get("model_quality_claim") if accepted else "not_claimed",
        "decision_scope": RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_SCOPE if accepted else "not_claimed",
        "next_step": "index_randomized_holdout_publication_decision" if accepted else "repair_randomized_holdout_publication_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], final_decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_decision_ready": status == "pass" and final_decision.get("accepted") is True,
        "final_decision": final_decision.get("decision"),
        "bounded_publication_accepted": final_decision.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "approved_for_bounded_publication": final_decision.get("approved_for_bounded_publication"),
        "accepted_claim_count": final_decision.get("accepted_claim_count"),
        "blocked_claim_count": final_decision.get("blocked_claim_count"),
        "candidate_case_count": final_decision.get("candidate_case_count"),
        "random_seed": final_decision.get("random_seed"),
        "pass_rate": final_decision.get("pass_rate"),
        "allowed_use": final_decision.get("allowed_use"),
        "model_quality_claim": final_decision.get("model_quality_claim"),
        "decision_scope": final_decision.get("decision_scope"),
        "next_step": final_decision.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_decision_accepted"
    return "fix_randomized_holdout_publication_decision"


def _interpretation(status: str, final_decision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout publication decision is blocked by a failed or widened publication review.",
            "next_action": "repair randomized holdout publication review before decision",
        }
    return {
        "model_quality_claim": final_decision.get("model_quality_claim"),
        "reason": "The bounded randomized holdout publication is accepted for governance use only while direct promotion remains blocked.",
        "next_action": final_decision.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_TEXT_FILENAME",
    "build_randomized_holdout_publication_decision",
    "locate_randomized_holdout_publication_packet_review",
    "read_json_report",
    "resolve_exit_code",
]
