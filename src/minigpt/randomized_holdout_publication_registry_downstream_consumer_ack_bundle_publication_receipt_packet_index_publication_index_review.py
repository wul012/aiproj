from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import blocked_uses, downstream_lookup_use, is_downstream_lookup_only
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.html"

REVIEW_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-index-review-v962"


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review(
    index_report: dict[str, Any],
    *,
    publication_index_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    index_summary = as_dict(index_report.get("summary"))
    publication_index = as_dict(index_report.get("publication_index"))
    publication_index_rows = list_of_dicts(publication_index.get("publication_index_rows"))
    checks = _checks(index_report, index_summary, publication_index, publication_index_rows, publication_index_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, index_summary, publication_index, publication_index_rows, publication_index_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "publication_index_path": str(publication_index_path or ""),
        "source_publication_index_summary": index_summary,
        "source_publication_index": publication_index,
        "publication_index_rows": publication_index_rows,
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_downstream_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_ready") is not True:
        return 1
    if require_downstream_ready and summary.get("downstream_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    index_report: dict[str, Any],
    index_summary: dict[str, Any],
    publication_index: dict[str, Any],
    publication_index_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = [str(row.get("lookup_key")) for row in publication_index_rows]
    return [
        _check("publication_index_file_exists", _path_exists(index_path), str(index_path or ""), "publication index file must exist"),
        _check("publication_index_passed", index_report.get("status") == "pass", index_report.get("status"), "publication index must pass"),
        _check("publication_index_decision_ready", index_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_ready", index_report.get("decision"), "publication index decision must be ready"),
        _check("publication_index_summary_ready", index_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_ready") is True and publication_index.get("index_ready") is True, {"summary": index_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_ready"), "index": publication_index.get("index_ready")}, "publication index summary and body must be ready"),
        _check("lookup_scope_downstream", is_downstream_lookup_only(index_summary.get("lookup_scope")) and is_downstream_lookup_only(publication_index.get("lookup_scope")), {"summary": index_summary.get("lookup_scope"), "index": publication_index.get("lookup_scope")}, "lookup scope must remain downstream governance lookup only"),
        _check("published_use_lookup_only", is_downstream_lookup_only(index_summary.get("published_use")) and is_downstream_lookup_only(publication_index.get("published_use")), {"summary": index_summary.get("published_use"), "index": publication_index.get("published_use")}, "published use must stay downstream lookup only"),
        _check("lookup_ready", index_summary.get("lookup_ready") is True and publication_index.get("lookup_ready") is True, {"summary": index_summary.get("lookup_ready"), "index": publication_index.get("lookup_ready")}, "publication index review requires lookup-ready source"),
        _check("contract_check_ready", index_summary.get("contract_check_ready") is True and publication_index.get("contract_check_ready") is True, {"summary": index_summary.get("contract_check_ready"), "index": publication_index.get("contract_check_ready")}, "publication index review requires ready source contract check"),
        _check("publication_index_rows_present", len(publication_index_rows) == int(index_summary.get("publication_index_row_count") or 0) == 1, {"rows": len(publication_index_rows), "summary": index_summary.get("publication_index_row_count")}, "publication index review requires one publication index row"),
        _check("lookup_keys_present", len(lookup_keys) == 1 and all(key.startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must use the publication namespace"),
        _check("publication_index_rows_not_promoted", all(row.get("promotion_ready") is False for row in publication_index_rows), [row.get("promotion_ready") for row in publication_index_rows], "publication index review must not promote rows"),
        _check("source_publication_file_exists", _path_exists(publication_index.get("publication_path")), publication_index.get("publication_path"), "source publication must still exist"),
        _check("source_publication_check_file_exists", _path_exists(publication_index.get("publication_check_path")), publication_index.get("publication_check_path"), "source publication contract check must still exist"),
        _check("source_review_file_exists", _path_exists(publication_index.get("source_review_path")), publication_index.get("source_review_path"), "source publication review must still exist"),
        _check("source_index_file_exists", _path_exists(publication_index.get("source_index_path")), publication_index.get("source_index_path"), "source publication index must still exist"),
        _check("consumer_boundary_governance", index_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and publication_index.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": index_summary.get("consumer_boundary"), "index": publication_index.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", index_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and publication_index.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": index_summary.get("model_quality_claim"), "index": publication_index.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("promotion_still_false", index_summary.get("promotion_ready") is False and publication_index.get("promotion_ready") is False and publication_index.get("approved_for_promotion") is False, {"summary": index_summary.get("promotion_ready"), "index": publication_index.get("promotion_ready"), "approved": publication_index.get("approved_for_promotion")}, "publication index review must not enable promotion"),
        _check("source_checks_clean", int(index_summary.get("failed_check_count") or 0) == 0, index_summary.get("failed_check_count"), "source publication index checks must be clean"),
        _check("source_next_step_matches", index_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_NEXT_STEP, index_summary.get("next_step"), "source publication index must route to review"),
    ]


def _review(
    status: str,
    index_summary: dict[str, Any],
    publication_index: dict[str, Any],
    publication_index_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_downstream_receipt_packet_index_publication_receipt" if ready else "blocked",
        "publication_index_path": str(index_path or ""),
        "consumer_name": index_summary.get("consumer_name") if ready else "",
        "publication_index_row_count": len(publication_index_rows) if ready else 0,
        "lookup_keys": [row.get("lookup_key") for row in publication_index_rows] if ready else [],
        "downstream_ready": ready,
        "lookup_ready": bool(ready and index_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and index_summary.get("contract_check_ready") is True),
        "receipt_ready": ready,
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "allowed_use": downstream_lookup_use() if ready else "none",
        "blocked_uses": blocked_uses(),
        "source_publication_path": publication_index.get("publication_path") if ready else "",
        "source_publication_check_path": publication_index.get("publication_check_path") if ready else "",
        "source_review_path": publication_index.get("source_review_path") if ready else "",
        "source_index_path": publication_index.get("source_index_path") if ready else "",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "consumer_name": review.get("consumer_name"),
        "publication_index_row_count": review.get("publication_index_row_count"),
        "lookup_key_count": len(list(review.get("lookup_keys") or [])),
        "downstream_ready": review.get("downstream_ready"),
        "lookup_ready": review.get("lookup_ready"),
        "contract_check_ready": review.get("contract_check_ready"),
        "receipt_ready": review.get("receipt_ready"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": review.get("consumer_boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "allowed_use": review.get("allowed_use"),
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
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt packet index publication index is not ready for receipt recording.",
            "next_action": "repair publication index before recording its receipt",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream publication receipt packet index publication index is approved only for lookup-only receipt recording; production promotion remains blocked.",
        "next_action": str(review.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index",
    "read_json_report",
    "resolve_exit_code",
]
