from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_manifest_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME = "randomized_holdout_publication_registry_lookup_packet.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CSV_FILENAME = "randomized_holdout_publication_registry_lookup_packet.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_TEXT_FILENAME = "randomized_holdout_publication_registry_lookup_packet.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_lookup_packet.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_HTML_FILENAME = "randomized_holdout_publication_registry_lookup_packet.html"

LOOKUP_PACKET_ID = "randomized-holdout-publication-registry-lookup-packet-v934"


def locate_randomized_holdout_publication_registry_manifest_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry lookup packet input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_lookup_packet(
    registry_manifest_review_report: dict[str, Any],
    *,
    registry_manifest_review_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry lookup packet",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(registry_manifest_review_report.get("summary"))
    review = as_dict(registry_manifest_review_report.get("review"))
    entry_rows = list_of_dicts(registry_manifest_review_report.get("entry_rows"))
    checks = _checks(registry_manifest_review_report, review_summary, review, entry_rows, registry_manifest_review_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    packet = _packet(status, review_summary, review, entry_rows, registry_manifest_review_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "registry_manifest_review_path": str(registry_manifest_review_path or ""),
        "source_review_summary": review_summary,
        "source_review": review,
        "entry_rows": entry_rows,
        "check_rows": checks,
        "lookup_packet": packet,
        "summary": _summary(status, checks, packet),
        "interpretation": _interpretation(status, packet),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_packet_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_packet_ready and summary.get("randomized_holdout_publication_registry_lookup_packet_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    review_report: dict[str, Any],
    review_summary: dict[str, Any],
    review: dict[str, Any],
    entries: list[dict[str, Any]],
    review_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("registry_manifest_review_file_exists", _path_exists(review_path), str(review_path or ""), "manifest review file must exist"),
        _check("registry_manifest_review_passed", review_report.get("status") == "pass", review_report.get("status"), "manifest review must pass"),
        _check("registry_manifest_review_decision_ready", review_report.get("decision") == "randomized_holdout_publication_registry_manifest_review_ready", review_report.get("decision"), "manifest review decision must be ready"),
        _check("review_summary_ready", review_summary.get("randomized_holdout_publication_registry_manifest_review_ready") is True and review.get("review_ready") is True, {"summary": review_summary.get("randomized_holdout_publication_registry_manifest_review_ready"), "review": review.get("review_ready")}, "review summary and body must be ready"),
        _check("review_status_lookup_only", review_summary.get("review_status") == "approved_for_governance_lookup_only" and review.get("review_status") == "approved_for_governance_lookup_only", {"summary": review_summary.get("review_status"), "review": review.get("review_status")}, "review must be lookup-only approved"),
        _check("lookup_ready", review_summary.get("lookup_ready") is True and review.get("lookup_ready") is True, {"summary": review_summary.get("lookup_ready"), "review": review.get("lookup_ready")}, "lookup must be ready"),
        _check("entry_count_positive", int(review_summary.get("entry_count") or 0) > 0 and len(entries) == int(review_summary.get("entry_count") or 0), {"summary": review_summary.get("entry_count"), "entries": len(entries)}, "lookup packet entry count must match entries"),
        _check("entries_registered", all(row.get("registry_status") == "registered" for row in entries), [row.get("registry_status") for row in entries], "all lookup entries must be registered"),
        _check("entries_bounded", all(row.get("bounded_publication_accepted") is True for row in entries), [row.get("bounded_publication_accepted") for row in entries], "all lookup entries must be bounded accepted"),
        _check("entries_not_promoted", all(row.get("promotion_ready") is False for row in entries), [row.get("promotion_ready") for row in entries], "lookup packet must not promote entries"),
        _check("consumer_boundary_governance", review_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and review.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": review_summary.get("consumer_boundary"), "review": review.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", review_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and all(row.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM for row in entries), {"summary": review_summary.get("model_quality_claim"), "entries": [row.get("model_quality_claim") for row in entries]}, "lookup packet claims must stay bounded"),
        _check("allowed_use_lookup_only", review_summary.get("allowed_use") == "governance_lookup_only" and review.get("allowed_use") == "governance_lookup_only", {"summary": review_summary.get("allowed_use"), "review": review.get("allowed_use")}, "allowed use must stay lookup-only"),
        _check("rejected_use_production_promotion", review_summary.get("rejected_use") == "production_promotion" and review.get("rejected_use") == "production_promotion", {"summary": review_summary.get("rejected_use"), "review": review.get("rejected_use")}, "production promotion must stay rejected"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and review.get("promotion_ready") is False, {"summary": review_summary.get("promotion_ready"), "review": review.get("promotion_ready")}, "lookup packet must not enable direct promotion"),
        _check("approved_for_promotion_false", review_summary.get("approved_for_promotion") is False and review.get("approved_for_promotion") is False, {"summary": review_summary.get("approved_for_promotion"), "review": review.get("approved_for_promotion")}, "lookup packet must not approve promotion"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source review checks must be clean"),
        _check("source_next_step_matches", review_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_NEXT_STEP, review_summary.get("next_step"), "source review must route to lookup packet build"),
    ]


def _packet(
    status: str,
    review_summary: dict[str, Any],
    review: dict[str, Any],
    entries: list[dict[str, Any]],
    review_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    lookup_entries = [_lookup_entry(row) for row in entries] if ready else []
    return {
        "packet_ready": ready,
        "lookup_packet_id": LOOKUP_PACKET_ID if ready else "not_ready",
        "lookup_scope": "governance_lookup_only" if ready else "not_ready",
        "registry_manifest_review_path": str(review_path or ""),
        "entry_count": len(lookup_entries),
        "lookup_entries": lookup_entries,
        "lookup_keys": [row["lookup_key"] for row in lookup_entries],
        "lookup_ready": bool(ready and review_summary.get("lookup_ready") is True and review.get("lookup_ready") is True),
        "bounded_publication_accepted": bool(ready and review_summary.get("bounded_publication_accepted") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "allowed_use": "governance_lookup_only" if ready else "none",
        "rejected_use": "production_promotion",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_lookup_packet",
    }


def _lookup_entry(row: dict[str, Any]) -> dict[str, Any]:
    entry_id = str(row.get("entry_id") or "")
    return {
        "lookup_key": f"publication:{entry_id}",
        "entry_id": entry_id,
        "registry_status": row.get("registry_status"),
        "bounded_publication_accepted": row.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "consumer_boundary": row.get("consumer_boundary"),
        "allowed_use": row.get("allowed_use") or "governance_lookup_only",
        "model_quality_claim": row.get("model_quality_claim"),
        "random_seed": row.get("random_seed"),
        "pass_rate": row.get("pass_rate"),
    }


def _summary(status: str, checks: list[dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_lookup_packet_ready": status == "pass" and packet.get("packet_ready") is True,
        "lookup_packet_id": packet.get("lookup_packet_id"),
        "lookup_scope": packet.get("lookup_scope"),
        "entry_count": packet.get("entry_count"),
        "lookup_ready": packet.get("lookup_ready"),
        "bounded_publication_accepted": packet.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": packet.get("consumer_boundary"),
        "allowed_use": packet.get("allowed_use"),
        "rejected_use": packet.get("rejected_use"),
        "next_step": packet.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_lookup_packet_ready"
    return "fix_randomized_holdout_publication_registry_lookup_packet"


def _interpretation(status: str, packet: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The publication registry manifest review is not ready for lookup packet build.",
            "next_action": "repair manifest review before lookup packet",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The reviewed publication manifest is packaged for governance lookup only; production promotion remains rejected.",
        "next_action": packet.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_lookup_packet",
    "locate_randomized_holdout_publication_registry_manifest_review",
    "read_json_report",
    "resolve_exit_code",
]
