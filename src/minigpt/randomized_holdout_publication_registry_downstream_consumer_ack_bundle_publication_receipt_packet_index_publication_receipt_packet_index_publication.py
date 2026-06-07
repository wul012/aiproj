from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import downstream_lookup_use, is_downstream_lookup_only
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.html"

PUBLICATION_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-v969"


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication(
    index_review_report: dict[str, Any],
    *,
    receipt_packet_index_review_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(index_review_report.get("summary"))
    review = as_dict(index_review_report.get("review"))
    checks = _checks(index_review_report, review_summary, review, receipt_packet_index_review_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    publication = _publication(status, review_summary, review, receipt_packet_index_review_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_packet_index_review_path": str(receipt_packet_index_review_path or ""),
        "source_receipt_packet_index_review_summary": review_summary,
        "source_receipt_packet_index_review": review,
        "check_rows": checks,
        "publication": publication,
        "summary": _summary(status, checks, publication),
        "interpretation": _interpretation(status, publication),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_publication_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_publication_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready") is not True:
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
    review_path: str | Path | None,
) -> list[dict[str, Any]]:
    index_path = review.get("receipt_packet_index_path")
    packet_path = review.get("source_packet_path")
    packet_check_path = review.get("source_packet_check_path")
    return [
        _check("receipt_packet_index_review_file_exists", _path_exists(review_path), str(review_path or ""), "receipt packet index review file must exist"),
        _check("receipt_packet_index_review_passed", review_report.get("status") == "pass", review_report.get("status"), "receipt packet index review must pass"),
        _check("receipt_packet_index_review_decision_ready", review_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review_ready", review_report.get("decision"), "receipt packet index review decision must be ready"),
        _check("receipt_packet_index_review_summary_ready", review_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review_ready") is True and review.get("review_ready") is True, {"summary": review_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review_ready"), "review": review.get("review_ready")}, "review summary and body must be ready"),
        _check("review_status_publishable", review_summary.get("review_status") == "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication" and review.get("review_status") == "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication", {"summary": review_summary.get("review_status"), "review": review.get("review_status")}, "review must approve lookup-only publication"),
        _check("receipt_packet_index_file_exists", _path_exists(index_path), index_path, "reviewed receipt packet index must still exist"),
        _check("source_packet_file_exists", _path_exists(packet_path), packet_path, "source receipt packet must still exist"),
        _check("source_packet_check_file_exists", _path_exists(packet_check_path), packet_check_path, "source receipt packet check must still exist"),
        _check("downstream_ready", review_summary.get("downstream_ready") is True and review.get("downstream_ready") is True, {"summary": review_summary.get("downstream_ready"), "review": review.get("downstream_ready")}, "publication requires downstream-ready review"),
        _check("publish_ready", review_summary.get("publish_ready") is True and review.get("publish_ready") is True, {"summary": review_summary.get("publish_ready"), "review": review.get("publish_ready")}, "publication requires publish-ready review"),
        _check("lookup_ready", review_summary.get("lookup_ready") is True and review.get("lookup_ready") is True, {"summary": review_summary.get("lookup_ready"), "review": review.get("lookup_ready")}, "publication requires lookup-ready review"),
        _check("contract_check_ready", review_summary.get("contract_check_ready") is True and review.get("contract_check_ready") is True, {"summary": review_summary.get("contract_check_ready"), "review": review.get("contract_check_ready")}, "publication requires contract-ready review"),
        _check("receipt_packet_index_row_count", int(review_summary.get("receipt_packet_index_row_count") or 0) == 1 and int(review.get("receipt_packet_index_row_count") or 0) == 1, {"summary": review_summary.get("receipt_packet_index_row_count"), "review": review.get("receipt_packet_index_row_count")}, "publication requires one receipt packet index row"),
        _check("source_packet_row_count", int(review_summary.get("source_packet_row_count") or 0) == 1 and int(review.get("source_packet_row_count") or 0) == 1, {"summary": review_summary.get("source_packet_row_count"), "review": review.get("source_packet_row_count")}, "publication requires one source packet row"),
        _check("source_evidence_count", int(review_summary.get("source_evidence_count") or 0) == 2 and int(review.get("source_evidence_count") or 0) == 2, {"summary": review_summary.get("source_evidence_count"), "review": review.get("source_evidence_count")}, "publication requires two source evidence rows"),
        _check("allowed_use_lookup_only", is_downstream_lookup_only(review_summary.get("allowed_use")) and is_downstream_lookup_only(review.get("allowed_use")), {"summary": review_summary.get("allowed_use"), "review": review.get("allowed_use")}, "publication must remain downstream lookup only"),
        _check("consumer_boundary_governance", review_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and review.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": review_summary.get("consumer_boundary"), "review": review.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", review_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and review.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": review_summary.get("model_quality_claim"), "review": review.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and review.get("promotion_ready") is False and review.get("approved_for_promotion") is False, {"summary": review_summary.get("promotion_ready"), "review": review.get("promotion_ready"), "approved": review.get("approved_for_promotion")}, "publication must not enable promotion"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source review checks must be clean"),
        _check("source_next_step_matches", review_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_NEXT_STEP, review_summary.get("next_step"), "source review must route to publication"),
    ]


def _publication(
    status: str,
    review_summary: dict[str, Any],
    review: dict[str, Any],
    review_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "publication_ready": ready,
        "publication_id": PUBLICATION_ID if ready else "not_ready",
        "publication_status": "published_for_downstream_receipt_packet_index_publication_receipt_packet_index_lookup_only" if ready else "blocked",
        "receipt_packet_index_review_path": str(review_path or ""),
        "receipt_packet_index_path": review.get("receipt_packet_index_path") if ready else "",
        "source_packet_path": review.get("source_packet_path") if ready else "",
        "source_packet_check_path": review.get("source_packet_check_path") if ready else "",
        "consumer_name": review_summary.get("consumer_name") if ready else "",
        "published_use": downstream_lookup_use() if ready else "none",
        "publish_ready": ready,
        "lookup_ready": bool(ready and review_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and review_summary.get("contract_check_ready") is True),
        "receipt_packet_index_row_count": int(review_summary.get("receipt_packet_index_row_count") or 0) if ready else 0,
        "source_packet_row_count": int(review_summary.get("source_packet_row_count") or 0) if ready else 0,
        "source_evidence_count": int(review_summary.get("source_evidence_count") or 0) if ready else 0,
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication",
    }


def _summary(status: str, checks: list[dict[str, Any]], publication: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready": status == "pass" and publication.get("publication_ready") is True,
        "publication_id": publication.get("publication_id"),
        "publication_status": publication.get("publication_status"),
        "consumer_name": publication.get("consumer_name"),
        "published_use": publication.get("published_use"),
        "publish_ready": publication.get("publish_ready"),
        "lookup_ready": publication.get("lookup_ready"),
        "contract_check_ready": publication.get("contract_check_ready"),
        "receipt_packet_index_row_count": publication.get("receipt_packet_index_row_count"),
        "source_packet_row_count": publication.get("source_packet_row_count"),
        "source_evidence_count": publication.get("source_evidence_count"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": publication.get("consumer_boundary"),
        "model_quality_claim": publication.get("model_quality_claim"),
        "next_step": publication.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(str(path)).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication"


def _interpretation(status: str, publication: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt packet index review is not ready for publication.",
            "next_action": "repair receipt packet index review before publication",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream publication receipt packet index is published only for lookup-only consumption; production promotion remains blocked.",
        "next_action": str(publication.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review",
    "read_json_report",
    "resolve_exit_code",
]
