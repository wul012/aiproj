from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_packet import MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_JSON_FILENAME = "model_capability_route_promotion_release_packet_review.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_CSV_FILENAME = "model_capability_route_promotion_release_packet_review.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_TEXT_FILENAME = "model_capability_route_promotion_release_packet_review.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_MARKDOWN_FILENAME = "model_capability_route_promotion_release_packet_review.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_HTML_FILENAME = "model_capability_route_promotion_release_packet_review.html"


def locate_route_promotion_release_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion release packet review input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_release_packet_review(
    release_packet: dict[str, Any],
    *,
    release_packet_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion release packet review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    packet = as_dict(release_packet.get("packet"))
    summary = as_dict(release_packet.get("summary"))
    evidence_rows = list_of_dicts(release_packet.get("evidence_rows"))
    checks = _checks(release_packet, packet, summary, evidence_rows, required_boundary)
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
        "release_packet_path": str(release_packet_path or ""),
        "source_packet_summary": summary,
        "source_packet": packet,
        "evidence_rows": evidence_rows,
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def _checks(
    release_packet: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    required_boundary: str,
) -> list[dict[str, Any]]:
    active_routes = list(packet.get("active_routes") or [])
    claim = str(packet.get("model_quality_claim") or summary.get("model_quality_claim") or "")
    return [
        _check("release_packet_passed", release_packet.get("status") == "pass", release_packet.get("status"), "release packet must pass"),
        _check(
            "release_packet_decision_ready",
            release_packet.get("decision") == "model_capability_route_promotion_release_packet_ready",
            release_packet.get("decision"),
            "release packet decision must be ready",
        ),
        _check("packet_ready", packet.get("packet_ready") is True, packet.get("packet_ready"), "packet must be ready"),
        _check(
            "handoff_ready",
            packet.get("handoff_status") == "ready_for_route_promotion_review",
            packet.get("handoff_status"),
            "packet must be ready for route promotion review",
        ),
        _check("active_routes_present", bool(active_routes), active_routes, "review requires active route evidence"),
        _check("boundary_scoped", packet.get("boundary") == required_boundary, packet.get("boundary"), "review boundary must remain tiny pair-probe scoped"),
        _check("claim_bounded", claim.startswith("seed_stable_pair_probe_route"), claim, "review claim must remain pair-probe scoped"),
        _check("evidence_count", len(evidence_rows) >= 3, len(evidence_rows), "review requires portfolio, regression, and gate evidence"),
        _check("evidence_files_exist", all(row.get("exists") is True for row in evidence_rows), evidence_rows, "all packet evidence rows must exist"),
        _check("packet_checks_clean", int(summary.get("failed_check_count") or 0) == 0, summary.get("failed_check_count"), "packet source checks must be clean"),
    ]


def _review(status: str, packet: dict[str, Any], summary: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "review_ready": status == "pass",
        "review_decision": "accept_route_promotion_packet_for_bounded_review" if status == "pass" else "repair_route_promotion_packet_before_review",
        "active_routes": packet.get("active_routes") or summary.get("active_routes") or [],
        "active_route_count": packet.get("active_route_count") or summary.get("active_route_count"),
        "boundary": packet.get("boundary") or summary.get("boundary"),
        "model_quality_claim": packet.get("model_quality_claim") or summary.get("model_quality_claim"),
        "handoff_status": packet.get("handoff_status") or summary.get("handoff_status"),
        "evidence_count": len(evidence_rows),
        "review_scope": "bounded_route_promotion_review_only",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "release_packet_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_decision": review.get("review_decision"),
        "active_route_count": review.get("active_route_count"),
        "active_routes": review.get("active_routes"),
        "boundary": review.get("boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "review_scope": review.get("review_scope"),
        "evidence_count": review.get("evidence_count"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_release_packet_review_ready"
    return "fix_model_capability_route_promotion_release_packet_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The release packet is not ready for bounded route promotion review.",
            "next_action": "repair packet evidence, boundary, or claim scope before review",
        }
    return {
        "model_quality_claim": review.get("model_quality_claim"),
        "reason": "The release packet is complete enough for bounded route promotion review.",
        "next_action": "record a final route review decision without widening the tiny pair-probe claim",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_TEXT_FILENAME",
    "build_model_capability_route_promotion_release_packet_review",
    "locate_route_promotion_release_packet",
    "read_json_report",
    "resolve_exit_code",
]
