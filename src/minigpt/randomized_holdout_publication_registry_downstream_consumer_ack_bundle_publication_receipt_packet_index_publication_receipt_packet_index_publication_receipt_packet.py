from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import (
    blocked_uses,
    blocked_uses_complete,
    downstream_lookup_use,
    is_downstream_lookup_only,
    is_sha256,
    sha256_file,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.html"

PACKET_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-v975"


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication receipt packet input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet(
    receipt_review_report: dict[str, Any],
    *,
    receipt_review_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication receipt packet",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(receipt_review_report.get("summary"))
    review = as_dict(receipt_review_report.get("review"))
    consumer_receipts = list_of_dicts(receipt_review_report.get("consumer_receipts"))
    publication_index_rows = list_of_dicts(receipt_review_report.get("publication_index_rows"))
    checks = _checks(receipt_review_report, review_summary, review, consumer_receipts, publication_index_rows, receipt_review_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    packet = _packet(status, review_summary, review, consumer_receipts, publication_index_rows, receipt_review_path)
    source_evidence_rows = _source_evidence_rows(status, receipt_review_path, review)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_review_path": str(receipt_review_path or ""),
        "receipt_review_sha256": sha256_file(receipt_review_path),
        "source_receipt_review_summary": review_summary,
        "source_receipt_review": review,
        "consumer_receipts": consumer_receipts if status == "pass" else [],
        "publication_index_rows": publication_index_rows if status == "pass" else [],
        "source_evidence_rows": source_evidence_rows,
        "packet_rows": _packet_rows(packet, consumer_receipts),
        "check_rows": checks,
        "packet": packet,
        "summary": _summary(status, checks, packet, source_evidence_rows),
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
    if require_packet_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_ready") is not True:
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
    consumer_receipts: list[dict[str, Any]],
    publication_index_rows: list[dict[str, Any]],
    review_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = list(review.get("lookup_keys") or [])
    return [
        _check("receipt_review_file_exists", _path_exists(review_path), str(review_path or ""), "receipt review file must exist"),
        _check("receipt_review_passed", review_report.get("status") == "pass", review_report.get("status"), "receipt review must pass"),
        _check("receipt_review_decision_ready", review_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready", review_report.get("decision"), "receipt review decision must be ready"),
        _check("review_summary_ready", review_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready") is True and review.get("review_ready") is True, {"summary": review_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready"), "review": review.get("review_ready")}, "receipt review summary and body must be ready"),
        _check("review_status_packet_ready", review_summary.get("review_status") == "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet" and review.get("review_status") == "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet", {"summary": review_summary.get("review_status"), "review": review.get("review_status")}, "review must approve receipt packet construction"),
        _check("packet_ready", review_summary.get("packet_ready") is True and review.get("packet_ready") is True, {"summary": review_summary.get("packet_ready"), "review": review.get("packet_ready")}, "receipt review must be packet ready"),
        _check("receipt_status_ready", review_summary.get("receipt_status") == "downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted" and review.get("receipt_status") == "downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted", {"summary": review_summary.get("receipt_status"), "review": review.get("receipt_status")}, "source receipt must stay lookup receipted"),
        _check("granted_use_lookup_only", is_downstream_lookup_only(review_summary.get("granted_use")) and is_downstream_lookup_only(review.get("granted_use")), {"summary": review_summary.get("granted_use"), "review": review.get("granted_use")}, "granted use must stay downstream lookup only"),
        _check("blocked_uses_complete", blocked_uses_complete(review_summary.get("blocked_uses")) and blocked_uses_complete(review.get("blocked_uses")), {"summary": review_summary.get("blocked_uses"), "review": review.get("blocked_uses")}, "packet must preserve all blocked uses"),
        _check("publication_index_rows_present", len(publication_index_rows) == int(review_summary.get("publication_index_row_count") or 0) == 1, {"rows": len(publication_index_rows), "summary": review_summary.get("publication_index_row_count")}, "packet must include one publication index row"),
        _check("consumer_receipts_present", len(consumer_receipts) == int(review_summary.get("consumer_receipt_count") or 0) == 1, {"rows": len(consumer_receipts), "summary": review_summary.get("consumer_receipt_count")}, "packet must include one consumer receipt row"),
        _check("lookup_keys_publication_namespace", len(lookup_keys) == len(consumer_receipts) and all(str(key).startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must use publication namespace"),
        _check("consumer_receipts_lookup_only", all(is_downstream_lookup_only(row.get("granted_use")) for row in consumer_receipts), [row.get("granted_use") for row in consumer_receipts], "consumer rows must stay lookup-only"),
        _check("consumer_receipts_not_promoted", all(row.get("promotion_ready") is False for row in consumer_receipts), [row.get("promotion_ready") for row in consumer_receipts], "consumer rows must not be promoted"),
        _check("publication_rows_not_promoted", all(row.get("promotion_ready") is False for row in publication_index_rows), [row.get("promotion_ready") for row in publication_index_rows], "publication index rows must not be promoted"),
        _check("receipt_review_digest_shape", is_sha256(sha256_file(review_path)), sha256_file(review_path), "receipt review digest must be a lowercase sha256"),
        _check("publication_receipt_digest_shape", is_sha256(review.get("publication_receipt_sha256")), review.get("publication_receipt_sha256"), "source publication receipt digest must be a lowercase sha256"),
        _check("source_index_review_file_exists", _path_exists(review.get("source_index_review_path")), review.get("source_index_review_path"), "source index review must still exist"),
        _check("source_publication_file_exists", _path_exists(review.get("source_publication_path")), review.get("source_publication_path"), "source publication must still exist"),
        _check("source_publication_check_file_exists", _path_exists(review.get("source_publication_check_path")), review.get("source_publication_check_path"), "source publication contract check must still exist"),
        _check("source_review_file_exists", _path_exists(review.get("source_review_path")), review.get("source_review_path"), "source publication review must still exist"),
        _check("source_index_file_exists", _path_exists(review.get("source_index_path")), review.get("source_index_path"), "source publication index must still exist"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and review.get("promotion_ready") is False and review.get("approved_for_promotion") is False, {"summary": review_summary.get("promotion_ready"), "review": review.get("promotion_ready"), "approved": review.get("approved_for_promotion")}, "packet must not enable promotion"),
        _check("approved_for_promotion_false", review_summary.get("approved_for_promotion") is False and review.get("approved_for_promotion") is False, {"summary": review_summary.get("approved_for_promotion"), "review": review.get("approved_for_promotion")}, "packet must not approve promotion"),
        _check("consumer_boundary_governance", review_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and review.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": review_summary.get("consumer_boundary"), "review": review.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", review_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and review.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": review_summary.get("model_quality_claim"), "review": review.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source review checks must be clean"),
        _check("source_next_step_matches", review_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_NEXT_STEP, review_summary.get("next_step"), "source review must route to receipt packet"),
    ]


def _packet(
    status: str,
    review_summary: dict[str, Any],
    review: dict[str, Any],
    consumer_receipts: list[dict[str, Any]],
    publication_index_rows: list[dict[str, Any]],
    review_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "packet_ready": ready,
        "packet_id": PACKET_ID if ready else "not_ready",
        "packet_status": "downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_ready" if ready else "blocked",
        "receipt_review_path": str(review_path or ""),
        "receipt_review_sha256": sha256_file(review_path) if ready else "",
        "publication_receipt_path": review.get("publication_receipt_path") if ready else "",
        "publication_receipt_sha256": review.get("publication_receipt_sha256") if ready else "",
        "consumer_name": review_summary.get("consumer_name") if ready else "",
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "granted_use": downstream_lookup_use() if ready else "none",
        "blocked_uses": blocked_uses(),
        "publication_index_row_count": len(publication_index_rows) if ready else 0,
        "source_evidence_count": 2 if ready else 0,
        "consumer_receipt_count": len(consumer_receipts) if ready else 0,
        "lookup_keys": list(review.get("lookup_keys") or []) if ready else [],
        "source_index_review_path": review.get("source_index_review_path") if ready else "",
        "source_publication_path": review.get("source_publication_path") if ready else "",
        "source_publication_check_path": review.get("source_publication_check_path") if ready else "",
        "source_review_path": review.get("source_review_path") if ready else "",
        "source_index_path": review.get("source_index_path") if ready else "",
        "promotion_ready": False,
        "approved_for_promotion": False,
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet",
    }


def _packet_rows(packet: dict[str, Any], consumer_receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "packet_id": packet.get("packet_id"),
            "consumer_name": packet.get("consumer_name"),
            "lookup_key": row.get("lookup_key"),
            "publication_id": row.get("publication_id"),
            "granted_use": packet.get("granted_use"),
            "blocked_uses": packet.get("blocked_uses"),
            "promotion_ready": False,
            "receipt_status": row.get("receipt_status"),
            "packet_status": packet.get("packet_status"),
        }
        for row in consumer_receipts
    ]


def _source_evidence_rows(status: str, review_path: str | Path | None, review: dict[str, Any]) -> list[dict[str, Any]]:
    if status != "pass":
        return []
    return [
        {"kind": "receipt_review", "path": str(review_path or ""), "sha256": sha256_file(review_path), "status": "pass"},
        {"kind": "publication_receipt", "path": str(review.get("publication_receipt_path") or ""), "sha256": str(review.get("publication_receipt_sha256") or ""), "status": "pass"},
    ]


def _summary(status: str, checks: list[dict[str, Any]], packet: dict[str, Any], source_evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_ready": status == "pass" and packet.get("packet_ready") is True,
        "packet_id": packet.get("packet_id"),
        "packet_status": packet.get("packet_status"),
        "consumer_name": packet.get("consumer_name"),
        "lookup_ready": packet.get("packet_ready") is True,
        "granted_use": packet.get("granted_use"),
        "blocked_uses": packet.get("blocked_uses"),
        "publication_index_row_count": packet.get("publication_index_row_count"),
        "source_evidence_count": len(source_evidence_rows),
        "consumer_receipt_count": packet.get("consumer_receipt_count"),
        "lookup_key_count": len(list(packet.get("lookup_keys") or [])),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": packet.get("consumer_boundary"),
        "model_quality_claim": packet.get("model_quality_claim"),
        "next_step": packet.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(str(path)).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet"


def _interpretation(status: str, packet: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt review is not ready to become a receipt packet.",
            "next_action": "repair receipt review before receipt packet",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream publication receipt packet index publication receipt packet is ready for contract checking while promotion remains blocked.",
        "next_action": str(packet.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review",
    "read_json_report",
    "resolve_exit_code",
]
