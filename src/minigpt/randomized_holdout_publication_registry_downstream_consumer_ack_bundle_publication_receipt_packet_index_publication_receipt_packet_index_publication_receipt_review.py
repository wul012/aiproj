from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import blocked_uses, blocked_uses_complete, downstream_lookup_use
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.html"

REVIEW_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-review-v974"


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication receipt review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review(
    receipt_report: dict[str, Any],
    *,
    publication_receipt_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication receipt review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    receipt_summary = as_dict(receipt_report.get("summary"))
    receipt = as_dict(receipt_report.get("receipt"))
    consumer_receipts = list_of_dicts(receipt_report.get("consumer_receipts"))
    publication_index_rows = list_of_dicts(receipt_report.get("publication_index_rows"))
    receipt_digest = _sha256_file(publication_receipt_path)
    checks = _checks(receipt_report, receipt_summary, receipt, consumer_receipts, publication_index_rows, publication_receipt_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, receipt_summary, receipt, consumer_receipts, publication_receipt_path, receipt_digest)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "publication_receipt_path": str(publication_receipt_path or ""),
        "publication_receipt_sha256": receipt_digest,
        "source_publication_receipt_summary": receipt_summary,
        "source_publication_receipt": receipt,
        "index_review_path": receipt.get("index_review_path", ""),
        "index_review_sha256": receipt_report.get("index_review_sha256", ""),
        "publication_index_rows": publication_index_rows if status == "pass" else [],
        "consumer_receipts": consumer_receipts if status == "pass" else [],
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_packet_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready") is not True:
        return 1
    if require_packet_ready and summary.get("packet_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    receipt_report: dict[str, Any],
    receipt_summary: dict[str, Any],
    receipt: dict[str, Any],
    consumer_receipts: list[dict[str, Any]],
    publication_index_rows: list[dict[str, Any]],
    receipt_path: str | Path | None,
) -> list[dict[str, Any]]:
    blocked = list(receipt_summary.get("blocked_uses") or [])
    lookup_keys = list(receipt.get("lookup_keys") or [])
    index_review_digest = str(receipt_report.get("index_review_sha256") or "")
    return [
        _check("publication_receipt_file_exists", _path_exists(receipt_path), str(receipt_path or ""), "publication receipt file must exist"),
        _check("publication_receipt_passed", receipt_report.get("status") == "pass", receipt_report.get("status"), "publication receipt must pass"),
        _check("publication_receipt_decision_ready", receipt_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_ready", receipt_report.get("decision"), "publication receipt decision must be ready"),
        _check("receipt_summary_ready", receipt_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_ready") is True and receipt.get("receipt_ready") is True, {"summary": receipt_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_ready"), "receipt": receipt.get("receipt_ready")}, "receipt summary and body must be ready"),
        _check("receipt_status_ready", receipt_summary.get("receipt_status") == "downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted" and receipt.get("receipt_status") == "downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted", {"summary": receipt_summary.get("receipt_status"), "receipt": receipt.get("receipt_status")}, "receipt must be downstream lookup receipted"),
        _check("granted_use_lookup_only", receipt_summary.get("granted_use") == downstream_lookup_use() and receipt.get("granted_use") == downstream_lookup_use(), {"summary": receipt_summary.get("granted_use"), "receipt": receipt.get("granted_use")}, "granted use must stay downstream governance lookup only"),
        _check("blocked_uses_complete", blocked_uses_complete(blocked), blocked, "review must preserve all blocked uses"),
        _check("publication_index_rows_present", len(publication_index_rows) == int(receipt_summary.get("publication_index_row_count") or 0) == 1, {"rows": len(publication_index_rows), "summary": receipt_summary.get("publication_index_row_count")}, "review must cover one publication index row"),
        _check("consumer_receipts_present", len(consumer_receipts) == int(receipt_summary.get("lookup_key_count") or 0) == 1, {"rows": len(consumer_receipts), "summary": receipt_summary.get("lookup_key_count")}, "review must cover one consumer receipt row"),
        _check("lookup_keys_publication_namespace", len(lookup_keys) == len(consumer_receipts) and all(str(key).startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must stay in the publication namespace"),
        _check("consumer_receipts_lookup_only", all(row.get("granted_use") == downstream_lookup_use() for row in consumer_receipts), [row.get("granted_use") for row in consumer_receipts], "consumer receipt rows must stay lookup only"),
        _check("publication_index_rows_not_promoted", all(row.get("promotion_ready") is False for row in publication_index_rows), [row.get("promotion_ready") for row in publication_index_rows], "publication index rows must not be promoted"),
        _check("consumer_receipts_not_promoted", all(row.get("promotion_ready") is False for row in consumer_receipts), [row.get("promotion_ready") for row in consumer_receipts], "consumer receipt rows must not be promoted"),
        _check("promotion_still_false", receipt_summary.get("promotion_ready") is False and receipt.get("promotion_ready") is False and receipt.get("approved_for_promotion") is False, {"summary": receipt_summary.get("promotion_ready"), "receipt": receipt.get("promotion_ready"), "approved": receipt.get("approved_for_promotion")}, "review must not enable promotion"),
        _check("consumer_boundary_governance", receipt_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and receipt.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": receipt_summary.get("consumer_boundary"), "receipt": receipt.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", receipt.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, receipt.get("model_quality_claim"), "model quality claim must remain bounded"),
        _check("source_index_review_file_exists", _path_exists(receipt.get("index_review_path")), receipt.get("index_review_path"), "source index review must still exist"),
        _check("source_publication_file_exists", _path_exists(receipt.get("source_publication_path")), receipt.get("source_publication_path"), "source publication must still exist"),
        _check("source_publication_check_file_exists", _path_exists(receipt.get("source_publication_check_path")), receipt.get("source_publication_check_path"), "source publication contract check must still exist"),
        _check("source_review_file_exists", _path_exists(receipt.get("source_review_path")), receipt.get("source_review_path"), "source publication review must still exist"),
        _check("source_index_file_exists", _path_exists(receipt.get("source_index_path")), receipt.get("source_index_path"), "source publication index must still exist"),
        _check("source_index_review_digest_shape", len(index_review_digest) == 64 and all(char in "0123456789abcdef" for char in index_review_digest), index_review_digest, "source index review digest must be a lowercase sha256"),
        _check("source_index_review_digest_matches", _sha256_file(receipt.get("index_review_path")) == index_review_digest, {"path": receipt.get("index_review_path"), "digest": index_review_digest}, "source index review digest must match the referenced JSON"),
        _check("source_checks_clean", int(receipt_summary.get("failed_check_count") or 0) == 0, receipt_summary.get("failed_check_count"), "source receipt checks must be clean"),
        _check("source_next_step_matches", receipt_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_NEXT_STEP, receipt_summary.get("next_step"), "source receipt must route to receipt review"),
    ]


def _review(
    status: str,
    receipt_summary: dict[str, Any],
    receipt: dict[str, Any],
    consumer_receipts: list[dict[str, Any]],
    receipt_path: str | Path | None,
    receipt_sha256: str,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet" if ready else "blocked",
        "publication_receipt_path": str(receipt_path or ""),
        "publication_receipt_sha256": receipt_sha256 if ready else "",
        "consumer_name": receipt_summary.get("consumer_name") if ready else "",
        "packet_ready": ready,
        "receipt_status": receipt_summary.get("receipt_status") if ready else "blocked",
        "granted_use": receipt_summary.get("granted_use") if ready else "none",
        "publication_index_row_count": receipt_summary.get("publication_index_row_count") if ready else 0,
        "lookup_keys": list(receipt.get("lookup_keys") or []) if ready else [],
        "consumer_receipt_count": len(consumer_receipts) if ready else 0,
        "blocked_uses": list(receipt_summary.get("blocked_uses") or blocked_uses()),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "source_index_review_path": receipt.get("index_review_path") if ready else "",
        "source_publication_path": receipt.get("source_publication_path") if ready else "",
        "source_publication_check_path": receipt.get("source_publication_check_path") if ready else "",
        "source_review_path": receipt.get("source_review_path") if ready else "",
        "source_index_path": receipt.get("source_index_path") if ready else "",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "consumer_name": review.get("consumer_name"),
        "packet_ready": review.get("packet_ready"),
        "receipt_status": review.get("receipt_status"),
        "granted_use": review.get("granted_use"),
        "publication_index_row_count": review.get("publication_index_row_count"),
        "lookup_key_count": len(list(review.get("lookup_keys") or [])),
        "consumer_receipt_count": review.get("consumer_receipt_count"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": review.get("consumer_boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "blocked_uses": review.get("blocked_uses"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(str(path)).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt is not ready for receipt-packet construction.",
            "next_action": "repair downstream publication receipt before packet construction",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream publication receipt is reviewed for packet construction while promotion remains blocked.",
        "next_action": str(review.get("next_step")),
    }


def _sha256_file(path: str | Path | None) -> str:
    if not path or not Path(str(path)).is_file():
        return ""
    return sha256(Path(str(path)).read_bytes()).hexdigest()


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt",
    "read_json_report",
    "resolve_exit_code",
]
