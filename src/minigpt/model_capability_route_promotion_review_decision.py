from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_packet_review import MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_JSON_FILENAME
from minigpt.report_utils import as_dict, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_JSON_FILENAME = "model_capability_route_promotion_review_decision.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_CSV_FILENAME = "model_capability_route_promotion_review_decision.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_TEXT_FILENAME = "model_capability_route_promotion_review_decision.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_MARKDOWN_FILENAME = "model_capability_route_promotion_review_decision.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_HTML_FILENAME = "model_capability_route_promotion_review_decision.html"


def locate_route_promotion_release_packet_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion review decision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_review_decision(
    release_packet_review: dict[str, Any],
    *,
    release_packet_review_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion review decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review = as_dict(release_packet_review.get("review"))
    review_summary = as_dict(release_packet_review.get("summary"))
    checks = _checks(release_packet_review, review, review_summary, required_boundary)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    decision = _final_decision(status, review)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "release_packet_review_path": str(release_packet_review_path or ""),
        "source_review_summary": review_summary,
        "source_review": review,
        "check_rows": checks,
        "final_decision": decision,
        "summary": _summary(status, checks, decision),
        "interpretation": _interpretation(status, decision),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _checks(
    release_packet_review: dict[str, Any],
    review: dict[str, Any],
    review_summary: dict[str, Any],
    required_boundary: str,
) -> list[dict[str, Any]]:
    claim = str(review.get("model_quality_claim") or review_summary.get("model_quality_claim") or "")
    return [
        _check("review_passed", release_packet_review.get("status") == "pass", release_packet_review.get("status"), "release packet review must pass"),
        _check(
            "review_decision_ready",
            release_packet_review.get("decision") == "model_capability_route_promotion_release_packet_review_ready",
            release_packet_review.get("decision"),
            "release packet review decision must be ready",
        ),
        _check(
            "review_accepts_packet",
            review.get("review_decision") == "accept_route_promotion_packet_for_bounded_review",
            review.get("review_decision"),
            "source review must accept the packet",
        ),
        _check("review_scope_bounded", review.get("review_scope") == "bounded_route_promotion_review_only", review.get("review_scope"), "review scope must stay bounded"),
        _check("active_route_present", int(review.get("active_route_count") or 0) > 0, review.get("active_route_count"), "final decision requires active routes"),
        _check("boundary_scoped", review.get("boundary") == required_boundary, review.get("boundary"), "final decision boundary must remain tiny pair-probe scoped"),
        _check("claim_bounded", claim.startswith("seed_stable_pair_probe_route"), claim, "final decision claim must remain pair-probe scoped"),
        _check("source_review_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source review checks must be clean"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _final_decision(status: str, review: dict[str, Any]) -> dict[str, Any]:
    accepted = status == "pass"
    return {
        "accepted": accepted,
        "decision": "accept_bounded_route_promotion" if accepted else "reject_or_repair_bounded_route_promotion",
        "active_routes": review.get("active_routes") or [],
        "active_route_count": review.get("active_route_count"),
        "boundary": review.get("boundary"),
        "model_quality_claim": review.get("model_quality_claim") if accepted else "not_claimed",
        "review_scope": review.get("review_scope"),
        "next_step": "index_bounded_route_promotion_decision" if accepted else "repair_release_packet_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_promotion_review_decision_ready": status == "pass" and decision.get("accepted") is True,
        "final_decision": decision.get("decision"),
        "active_route_count": decision.get("active_route_count"),
        "active_routes": decision.get("active_routes"),
        "boundary": decision.get("boundary"),
        "model_quality_claim": decision.get("model_quality_claim"),
        "review_scope": decision.get("review_scope"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_final_review_accepted"
    return "fix_model_capability_route_promotion_review_decision"


def _interpretation(status: str, decision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The release packet review cannot be accepted as a bounded route promotion decision.",
            "next_action": "repair the release packet review before indexing the route promotion",
        }
    return {
        "model_quality_claim": decision.get("model_quality_claim"),
        "reason": "The route promotion is accepted inside the bounded tiny pair-probe review scope.",
        "next_action": "index the bounded route promotion decision for route history consumers",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_review_decision",
    "locate_route_promotion_release_packet_review",
    "read_json_report",
    "resolve_exit_code",
]
