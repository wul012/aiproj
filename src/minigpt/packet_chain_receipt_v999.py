from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_REVIEW_V998_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import (
    blocked_uses,
    blocked_uses_complete,
    downstream_lookup_use,
    sha256_file,
)
from minigpt.packet_chain_review_v998 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_REVIEW_V998_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_JSON_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_CSV_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_TEXT_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_MARKDOWN_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.md"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_HTML_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.html"

RECEIPT_ID = "randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999"
RECEIPT_TYPE = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index"


def locate_receipt_index_review_v999(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_REVIEW_V998_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication index receipt index receipt v999 input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999(
    review_report: dict[str, Any],
    *,
    receipt_index_review_path: str | Path | None = None,
    consumer_name: str = "publication_index_receipt_index_governance_lookup_reader",
    requested_use: str = "downstream_governance_lookup_only",
    title: str = "MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index receipt index receipt v999",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(review_report.get("summary"))
    review = as_dict(review_report.get("review"))
    index_rows = list_of_dicts(review_report.get("receipt_index_rows"))
    source_evidence_rows = list_of_dicts(review_report.get("source_evidence_rows"))
    checks = _checks(
        review_report,
        review_summary,
        review,
        index_rows,
        source_evidence_rows,
        receipt_index_review_path,
        requested_use,
    )
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    receipt = _receipt(
        status,
        review_summary,
        review,
        index_rows,
        source_evidence_rows,
        receipt_index_review_path,
        consumer_name,
        requested_use,
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_index_review_path": str(receipt_index_review_path or ""),
        "receipt_index_review_sha256": sha256_file(receipt_index_review_path),
        "source_receipt_index_review_summary": review_summary,
        "source_receipt_index_review": review,
        "receipt_index_rows": index_rows if status == "pass" else [],
        "source_evidence_rows": source_evidence_rows if status == "pass" else [],
        "consumer_receipts": _consumer_receipts(receipt, index_rows),
        "check_rows": checks,
        "receipt": receipt,
        "summary": _summary(status, checks, receipt),
        "interpretation": _interpretation(status, receipt),
    }


def resolve_exit_code(report: dict[str, Any], *, require_receipt_ready: bool, require_promotion_ready: bool = False) -> int:
    summary = as_dict(report.get("summary"))
    if require_receipt_ready and summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    review_report: dict[str, Any],
    review_summary: dict[str, Any],
    review: dict[str, Any],
    index_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    review_path: str | Path | None,
    requested_use: str,
) -> list[dict[str, Any]]:
    lookup_keys = list(review.get("lookup_keys") or [])
    blocked = list(review_summary.get("blocked_uses") or [])
    return [
        _check("receipt_index_review_file_exists", _path_exists(review_path), str(review_path or ""), "receipt index review file must exist"),
        _check("receipt_index_review_passed", review_report.get("status") == "pass", review_report.get("status"), "receipt index review must pass"),
        _check("receipt_index_review_decision_ready", review_report.get("decision") == "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_ready", review_report.get("decision"), "receipt index review decision must be ready"),
        _check("receipt_index_review_summary_ready", review_summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_ready") is True and review.get("review_ready") is True, {"summary": review_summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_ready"), "review": review.get("review_ready")}, "receipt index review summary and body must be ready"),
        _check("review_status_allowed", review_summary.get("review_status") == "approved_for_publication_index_receipt_index_receipt_lookup_only" and review.get("review_status") == "approved_for_publication_index_receipt_index_receipt_lookup_only", {"summary": review_summary.get("review_status"), "review": review.get("review_status")}, "review must approve lookup-only receipt recording"),
        _check("requested_use_allowed", requested_use == downstream_lookup_use(), requested_use, "requested use must stay downstream governance lookup only"),
        _check("blocked_uses_complete", blocked_uses_complete(blocked), blocked, "receipt must preserve all blocked uses"),
        _check("receipt_index_lookup_ready", review_summary.get("receipt_index_ready") is True and review_summary.get("lookup_ready") is True, {"receipt_index": review_summary.get("receipt_index_ready"), "lookup": review_summary.get("lookup_ready")}, "receipt index lookup must be ready"),
        _check("contract_check_ready", review_summary.get("contract_check_ready") is True, review_summary.get("contract_check_ready"), "source contract check must be ready"),
        _check("index_rows_present", len(index_rows) == int(review_summary.get("receipt_index_row_count") or 0) == 1, {"rows": len(index_rows), "summary": review_summary.get("receipt_index_row_count")}, "receipt must cover one receipt index row"),
        _check("source_evidence_count", len(source_evidence_rows) == int(review_summary.get("source_evidence_count") or 0) == 2, {"rows": len(source_evidence_rows), "summary": review_summary.get("source_evidence_count")}, "receipt must preserve two source evidence rows"),
        _check("lookup_keys_publication_index_receipt_namespace", len(lookup_keys) == len(index_rows) and all(str(key).startswith("publication-index-receipt:") for key in lookup_keys), lookup_keys, "lookup keys must use publication-index-receipt namespace"),
        _check("index_rows_not_promoted", all(row.get("promotion_ready") is False for row in index_rows), [row.get("promotion_ready") for row in index_rows], "receipt index rows must not be promoted"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and review.get("promotion_ready") is False and review.get("approved_for_promotion") is False, {"summary": review_summary.get("promotion_ready"), "review": review.get("promotion_ready"), "approved": review.get("approved_for_promotion")}, "receipt must not enable promotion"),
        _check("consumer_boundary_governance", review_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and review.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": review_summary.get("consumer_boundary"), "review": review.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", review_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and review.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": review_summary.get("model_quality_claim"), "review": review.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("source_receipt_index_file_exists", _path_exists(review.get("receipt_index_path")), review.get("receipt_index_path"), "source receipt index must still exist"),
        _check("source_receipt_file_exists", _path_exists(review.get("source_receipt_path")), review.get("source_receipt_path"), "source receipt must still exist"),
        _check("source_receipt_check_file_exists", _path_exists(review.get("source_receipt_check_path")), review.get("source_receipt_check_path"), "source receipt contract check must still exist"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source receipt index review checks must be clean"),
        _check("source_next_step_matches", review_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_REVIEW_V998_NEXT_STEP, review_summary.get("next_step"), "source receipt index review must route to receipt"),
    ]


def _receipt(
    status: str,
    review_summary: dict[str, Any],
    review: dict[str, Any],
    index_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    review_path: str | Path | None,
    consumer_name: str,
    requested_use: str,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "receipt_ready": ready,
        "receipt_id": RECEIPT_ID if ready else "not_ready",
        "receipt_type": RECEIPT_TYPE,
        "receipt_status": "publication_index_receipt_index_lookup_receipted" if ready else "blocked",
        "consumer_name": consumer_name,
        "requested_use": requested_use,
        "granted_use": downstream_lookup_use() if ready else "none",
        "receipt_index_review_path": str(review_path or ""),
        "receipt_index_row_count": len(index_rows) if ready else 0,
        "source_evidence_count": len(source_evidence_rows) if ready else 0,
        "lookup_keys": list(review.get("lookup_keys") or []) if ready else [],
        "review_id": review_summary.get("review_id") if ready else "not_ready",
        "review_status": review_summary.get("review_status") if ready else "not_ready",
        "blocked_uses": list(review_summary.get("blocked_uses") or blocked_uses()),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "source_receipt_index_path": review.get("receipt_index_path") if ready else "",
        "source_receipt_path": review.get("source_receipt_path") if ready else "",
        "source_receipt_check_path": review.get("source_receipt_check_path") if ready else "",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_NEXT_STEP if ready else "repair_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999",
    }


def _consumer_receipts(receipt: dict[str, Any], index_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "consumer_name": receipt.get("consumer_name"),
            "lookup_key": row.get("lookup_key"),
            "receipt_index_id": row.get("receipt_index_id"),
            "source_receipt_id": row.get("receipt_id"),
            "receipt_id": receipt.get("receipt_id"),
            "granted_use": receipt.get("granted_use"),
            "blocked_uses": receipt.get("blocked_uses"),
            "promotion_ready": False,
            "receipt_status": receipt.get("receipt_status"),
        }
        for row in index_rows
    ]


def _summary(status: str, checks: list[dict[str, Any]], receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999_ready": status == "pass" and receipt.get("receipt_ready") is True,
        "receipt_id": receipt.get("receipt_id"),
        "receipt_type": receipt.get("receipt_type"),
        "receipt_status": receipt.get("receipt_status"),
        "consumer_name": receipt.get("consumer_name"),
        "granted_use": receipt.get("granted_use"),
        "receipt_index_row_count": receipt.get("receipt_index_row_count"),
        "source_evidence_count": receipt.get("source_evidence_count"),
        "lookup_key_count": len(list(receipt.get("lookup_keys") or [])),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": receipt.get("consumer_boundary"),
        "blocked_uses": receipt.get("blocked_uses"),
        "next_step": receipt.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999_ready"
    return "fix_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999"


def _interpretation(status: str, receipt: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "The publication index receipt index review is not ready to be receipted.", "next_action": "repair receipt index review before recording receipt"}
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The reviewed publication index receipt index is receipted for downstream lookup only; production promotion remains blocked.",
        "next_action": str(receipt.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_V999_TEXT_FILENAME",
    "build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999",
    "locate_receipt_index_review_v999",
    "read_json_report",
    "resolve_exit_code",
]
