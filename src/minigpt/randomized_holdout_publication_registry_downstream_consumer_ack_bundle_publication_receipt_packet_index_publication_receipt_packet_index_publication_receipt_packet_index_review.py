from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import blocked_uses, downstream_lookup_use, is_downstream_lookup_only
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_JSON_FILENAME = "randomized_holdout_publication_receipt_packet_index_review_v978.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_CSV_FILENAME = "randomized_holdout_publication_receipt_packet_index_review_v978.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_TEXT_FILENAME = "randomized_holdout_publication_receipt_packet_index_review_v978.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_publication_receipt_packet_index_review_v978.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_HTML_FILENAME = "randomized_holdout_publication_receipt_packet_index_review_v978.html"

REVIEW_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-review-v978"


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication receipt packet index review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review(
    index_report: dict[str, Any],
    *,
    receipt_packet_index_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication receipt packet index review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    index_summary = as_dict(index_report.get("summary"))
    receipt_packet_index = as_dict(index_report.get("receipt_packet_index"))
    index_rows = list_of_dicts(receipt_packet_index.get("receipt_packet_index_rows"))
    source_packet_rows = list_of_dicts(receipt_packet_index.get("source_packet_rows"))
    source_evidence_rows = list_of_dicts(receipt_packet_index.get("source_evidence_rows"))
    checks = _checks(index_report, index_summary, receipt_packet_index, index_rows, source_packet_rows, source_evidence_rows, receipt_packet_index_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, index_summary, receipt_packet_index, index_rows, source_packet_rows, source_evidence_rows, receipt_packet_index_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_packet_index_path": str(receipt_packet_index_path or ""),
        "source_receipt_packet_index_summary": index_summary,
        "source_receipt_packet_index": receipt_packet_index,
        "receipt_packet_index_rows": index_rows,
        "source_packet_rows": source_packet_rows,
        "source_evidence_rows": source_evidence_rows,
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
    if require_review_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review_ready") is not True:
        return 1
    if require_downstream_ready and summary.get("downstream_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    index_report: dict[str, Any],
    index_summary: dict[str, Any],
    receipt_packet_index: dict[str, Any],
    index_rows: list[dict[str, Any]],
    source_packet_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = [str(row.get("lookup_key")) for row in index_rows]
    return [
        _check("receipt_packet_index_file_exists", _path_exists(index_path), str(index_path or ""), "receipt packet index file must exist"),
        _check("receipt_packet_index_passed", index_report.get("status") == "pass", index_report.get("status"), "receipt packet index must pass"),
        _check("receipt_packet_index_decision_ready", index_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_ready", index_report.get("decision"), "receipt packet index decision must be ready"),
        _check("receipt_packet_index_summary_ready", index_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_ready") is True and receipt_packet_index.get("index_ready") is True, {"summary": index_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_ready"), "index": receipt_packet_index.get("index_ready")}, "index summary and body must be ready"),
        _check("lookup_scope_downstream", is_downstream_lookup_only(index_summary.get("lookup_scope")) and is_downstream_lookup_only(receipt_packet_index.get("lookup_scope")), {"summary": index_summary.get("lookup_scope"), "index": receipt_packet_index.get("lookup_scope")}, "lookup scope must remain downstream governance lookup only"),
        _check("granted_use_lookup_only", is_downstream_lookup_only(index_summary.get("granted_use")) and is_downstream_lookup_only(receipt_packet_index.get("granted_use")), {"summary": index_summary.get("granted_use"), "index": receipt_packet_index.get("granted_use")}, "granted use must stay downstream lookup only"),
        _check("lookup_ready", index_summary.get("lookup_ready") is True and receipt_packet_index.get("lookup_ready") is True, {"summary": index_summary.get("lookup_ready"), "index": receipt_packet_index.get("lookup_ready")}, "receipt packet index must be lookup-ready"),
        _check("contract_check_ready", index_summary.get("contract_check_ready") is True and receipt_packet_index.get("contract_check_ready") is True, {"summary": index_summary.get("contract_check_ready"), "index": receipt_packet_index.get("contract_check_ready")}, "receipt packet index must include a ready contract check"),
        _check("receipt_packet_index_rows_present", len(index_rows) == int(index_summary.get("receipt_packet_index_row_count") or 0) == 1, {"rows": len(index_rows), "summary": index_summary.get("receipt_packet_index_row_count")}, "review requires one receipt packet index row"),
        _check("source_packet_rows_present", len(source_packet_rows) == 1, len(source_packet_rows), "review requires one source packet row"),
        _check("lookup_keys_present", len(lookup_keys) == 1 and all(key.startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must use the publication namespace"),
        _check("receipt_packet_index_rows_not_promoted", all(row.get("promotion_ready") is False for row in index_rows), [row.get("promotion_ready") for row in index_rows], "receipt packet index rows must not promote"),
        _check("source_packet_rows_not_promoted", all(row.get("promotion_ready") is False for row in source_packet_rows), [row.get("promotion_ready") for row in source_packet_rows], "source packet rows must not promote"),
        _check("source_evidence_count", int(index_summary.get("source_evidence_count") or 0) == 2 and len(source_evidence_rows) == 2, {"summary": index_summary.get("source_evidence_count"), "rows": len(source_evidence_rows)}, "review requires two source evidence rows"),
        _check("source_evidence_passed", all(row.get("status") == "pass" for row in source_evidence_rows), [row.get("status") for row in source_evidence_rows], "source evidence rows must pass"),
        _check("source_evidence_files_exist", all(_path_exists(row.get("path")) for row in source_evidence_rows), [row.get("path") for row in source_evidence_rows], "source evidence files must exist"),
        _check("source_packet_file_exists", _path_exists(receipt_packet_index.get("receipt_packet_path")), receipt_packet_index.get("receipt_packet_path"), "source receipt packet must still exist"),
        _check("source_packet_check_file_exists", _path_exists(receipt_packet_index.get("receipt_packet_check_path")), receipt_packet_index.get("receipt_packet_check_path"), "source receipt packet contract check must still exist"),
        _check("consumer_boundary_governance", index_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and receipt_packet_index.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": index_summary.get("consumer_boundary"), "index": receipt_packet_index.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", index_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and receipt_packet_index.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": index_summary.get("model_quality_claim"), "index": receipt_packet_index.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("promotion_still_false", index_summary.get("promotion_ready") is False and receipt_packet_index.get("promotion_ready") is False and receipt_packet_index.get("approved_for_promotion") is False, {"summary": index_summary.get("promotion_ready"), "index": receipt_packet_index.get("promotion_ready"), "approved": receipt_packet_index.get("approved_for_promotion")}, "review must not enable promotion"),
        _check("source_checks_clean", int(index_summary.get("failed_check_count") or 0) == 0, index_summary.get("failed_check_count"), "source receipt packet index checks must be clean"),
        _check("source_next_step_matches", index_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_NEXT_STEP, index_summary.get("next_step"), "source receipt packet index must route to review"),
    ]


def _review(
    status: str,
    index_summary: dict[str, Any],
    receipt_packet_index: dict[str, Any],
    index_rows: list[dict[str, Any]],
    source_packet_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication" if ready else "blocked",
        "receipt_packet_index_path": str(index_path or ""),
        "consumer_name": index_summary.get("consumer_name") if ready else "",
        "receipt_packet_index_row_count": len(index_rows) if ready else 0,
        "source_packet_row_count": len(source_packet_rows) if ready else 0,
        "source_evidence_count": len(source_evidence_rows) if ready else 0,
        "lookup_keys": [row.get("lookup_key") for row in index_rows] if ready else [],
        "downstream_ready": ready,
        "publish_ready": ready,
        "lookup_ready": bool(ready and index_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and index_summary.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "allowed_use": downstream_lookup_use() if ready else "none",
        "blocked_uses": blocked_uses(),
        "source_packet_path": receipt_packet_index.get("receipt_packet_path") if ready else "",
        "source_packet_check_path": receipt_packet_index.get("receipt_packet_check_path") if ready else "",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "consumer_name": review.get("consumer_name"),
        "receipt_packet_index_row_count": review.get("receipt_packet_index_row_count"),
        "source_packet_row_count": review.get("source_packet_row_count"),
        "source_evidence_count": review.get("source_evidence_count"),
        "lookup_key_count": len(list(review.get("lookup_keys") or [])),
        "downstream_ready": review.get("downstream_ready"),
        "publish_ready": review.get("publish_ready"),
        "lookup_ready": review.get("lookup_ready"),
        "contract_check_ready": review.get("contract_check_ready"),
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
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt packet index is not ready for lookup-only publication.",
            "next_action": "repair receipt packet index before publication",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream publication receipt packet index is approved only for lookup-only publication; production promotion remains blocked.",
        "next_action": str(review.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index",
    "read_json_report",
    "resolve_exit_code",
]
