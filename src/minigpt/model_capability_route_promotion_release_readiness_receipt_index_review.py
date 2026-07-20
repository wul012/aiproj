from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt import BLOCKED_USES, GRANTED_SCOPE
from minigpt.model_capability_route_promotion_release_readiness_receipt_index import (
    INDEX_NEXT_STEP,
    LOOKUP_SCOPE,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_JSON_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index_review.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_CSV_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index_review.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_TEXT_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index_review.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_MARKDOWN_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index_review.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_HTML_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index_review.html"

READY_INDEX_DECISION = "model_capability_route_promotion_release_readiness_receipt_index_ready"
REVIEW_ID = "route-promotion-release-readiness-receipt-index-review-v1259"
REVIEW_NEXT_STEP = "record_reviewed_route_promotion_release_readiness_receipt_index"


def locate_route_promotion_release_readiness_receipt_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion release readiness receipt index review input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_release_readiness_receipt_index_review(
    receipt_index_report: dict[str, Any],
    *,
    receipt_index_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion release readiness receipt index review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    index_summary = as_dict(receipt_index_report.get("summary"))
    receipt_index = as_dict(receipt_index_report.get("receipt_index"))
    lookup_rows = list_of_dicts(receipt_index.get("index_rows"))
    source_digest_rows = list_of_dicts(receipt_index.get("source_digest_rows"))
    check_rows = _check_rows(receipt_index_report, index_summary, receipt_index, lookup_rows, source_digest_rows, receipt_index_path, required_boundary)
    issues = [row for row in check_rows if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, index_summary, receipt_index, lookup_rows, receipt_index_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_index_path": str(receipt_index_path or ""),
        "receipt_index_digest": _sha256_or_empty(receipt_index_path),
        "source_receipt_index_summary": index_summary,
        "source_receipt_index": receipt_index,
        "lookup_rows": lookup_rows,
        "source_digest_rows": source_digest_rows,
        "check_rows": check_rows,
        "review": review,
        "summary": _summary(status, check_rows, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("receipt_index_review_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _check_rows(
    index_report: dict[str, Any],
    index_summary: dict[str, Any],
    receipt_index: dict[str, Any],
    lookup_rows: list[dict[str, Any]],
    source_digest_rows: list[dict[str, Any]],
    index_path: str | Path | None,
    required_boundary: str,
) -> list[dict[str, Any]]:
    row = lookup_rows[0] if lookup_rows else {}
    receipt_path = receipt_index.get("downstream_receipt_path")
    receipt_digest = receipt_index.get("downstream_receipt_digest")
    row_receipt_digest = row.get("downstream_receipt_digest")
    return [
        _check("receipt_index_file_exists", _path_exists(index_path), str(index_path or ""), "receipt index file must exist"),
        _check("receipt_index_digest_present", bool(_sha256_or_empty(index_path)), _sha256_or_empty(index_path), "review must digest the receipt index file"),
        _check("receipt_index_passed", index_report.get("status") == "pass", index_report.get("status"), "receipt index report must pass"),
        _check("receipt_index_decision_ready", index_report.get("decision") == READY_INDEX_DECISION, index_report.get("decision"), "receipt index decision must be ready"),
        _check("receipt_index_ready", index_summary.get("receipt_index_ready") is True and receipt_index.get("index_ready") is True, {"summary": index_summary.get("receipt_index_ready"), "index": receipt_index.get("index_ready")}, "receipt index summary and body must be ready"),
        _check("lookup_scope_bounded", index_summary.get("lookup_scope") == LOOKUP_SCOPE and receipt_index.get("lookup_scope") == LOOKUP_SCOPE, {"summary": index_summary.get("lookup_scope"), "index": receipt_index.get("lookup_scope")}, "lookup scope must remain bounded receipt lookup only"),
        _check("lookup_ready", index_summary.get("lookup_ready") is True and receipt_index.get("lookup_ready") is True, {"summary": index_summary.get("lookup_ready"), "index": receipt_index.get("lookup_ready")}, "receipt index must remain lookup-ready"),
        _check("lookup_rows_present", len(lookup_rows) == int(index_summary.get("entry_count") or 0) == int(receipt_index.get("entry_count") or 0) and len(lookup_rows) > 0, {"rows": len(lookup_rows), "summary": index_summary.get("entry_count"), "index": receipt_index.get("entry_count")}, "review requires lookup rows"),
        _check("lookup_key_count_matches", len(list(receipt_index.get("lookup_keys") or [])) == len(lookup_rows) == int(index_summary.get("lookup_key_count") or 0), {"keys": receipt_index.get("lookup_keys"), "rows": len(lookup_rows), "summary": index_summary.get("lookup_key_count")}, "lookup keys must match lookup rows"),
        _check("row_route_matches_summary", row.get("route_id") == index_summary.get("route_id") == receipt_index.get("route_id"), {"row": row.get("route_id"), "summary": index_summary.get("route_id"), "index": receipt_index.get("route_id")}, "lookup row route must match the index summary"),
        _check("granted_scope_bounded", row.get("granted_scope") == GRANTED_SCOPE and receipt_index.get("granted_scope") == GRANTED_SCOPE, {"row": row.get("granted_scope"), "index": receipt_index.get("granted_scope")}, "granted scope must remain bounded"),
        _check("boundary_required", receipt_index.get("boundary") == required_boundary and row.get("boundary") == required_boundary, {"row": row.get("boundary"), "index": receipt_index.get("boundary")}, "index boundary must match the required boundary"),
        _check("claim_bounded", str(receipt_index.get("model_quality_claim") or "").startswith("seed_stable_pair_probe_route") and str(row.get("model_quality_claim") or "").startswith("seed_stable_pair_probe_route"), {"row": row.get("model_quality_claim"), "index": receipt_index.get("model_quality_claim")}, "model quality claim must remain pair-probe scoped"),
        _check("source_check_digest_present", bool(receipt_index.get("source_check_digest")) and bool(row.get("source_check_digest")), {"row": row.get("source_check_digest"), "index": receipt_index.get("source_check_digest")}, "source check digest must remain present"),
        _check("downstream_receipt_file_exists", _path_exists(receipt_path), receipt_path, "indexed downstream receipt file must still exist"),
        _check("downstream_receipt_digest_matches", bool(receipt_digest) and receipt_digest == row_receipt_digest == _sha256_or_empty(receipt_path), {"index": receipt_digest, "row": row_receipt_digest, "actual": _sha256_or_empty(receipt_path)}, "indexed downstream receipt digest must match the receipt file"),
        _check("source_digest_count_matches", int(receipt_index.get("source_digest_count") or 0) == len(source_digest_rows) == int(row.get("source_digest_count") or 0), {"index": receipt_index.get("source_digest_count"), "row": row.get("source_digest_count"), "actual": len(source_digest_rows)}, "source digest count must match source digest rows"),
        _check("source_digests_present", all(digest_row.get("sha256") for digest_row in source_digest_rows), source_digest_rows, "all source digest rows must carry SHA-256"),
        _check("blocked_uses_complete", set(receipt_index.get("blocked_uses") or []) == set(BLOCKED_USES) and set(row.get("blocked_uses") or []) == set(BLOCKED_USES), {"index": receipt_index.get("blocked_uses"), "row": row.get("blocked_uses")}, "blocked uses must remain complete"),
        _check("promotion_still_false", index_summary.get("promotion_ready") is False and receipt_index.get("promotion_ready") is False and row.get("promotion_ready") is False and receipt_index.get("approved_for_promotion") is False, {"summary": index_summary.get("promotion_ready"), "index": receipt_index.get("promotion_ready"), "row": row.get("promotion_ready"), "approved": receipt_index.get("approved_for_promotion")}, "receipt index review must not enable promotion"),
        _check("source_index_checks_clean", int(index_report.get("failed_count") or 0) == 0 and int(index_summary.get("failed_check_count") or 0) == 0, {"failed_count": index_report.get("failed_count"), "summary_failed": index_summary.get("failed_check_count")}, "source receipt index checks must be clean"),
        _check("source_next_step_matches", index_summary.get("next_step") == INDEX_NEXT_STEP and receipt_index.get("next_step") == INDEX_NEXT_STEP, {"summary": index_summary.get("next_step"), "index": receipt_index.get("next_step")}, "source index must route to index review"),
    ]


def _review(
    status: str,
    index_summary: dict[str, Any],
    receipt_index: dict[str, Any],
    lookup_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_bounded_receipt_lookup" if ready else "blocked",
        "receipt_index_path": str(index_path or ""),
        "receipt_index_digest": _sha256_or_empty(index_path),
        "entry_count": len(lookup_rows) if ready else 0,
        "lookup_keys": list(receipt_index.get("lookup_keys") or []) if ready else [],
        "lookup_ready": bool(ready and index_summary.get("lookup_ready") is True),
        "consumer_name": receipt_index.get("consumer_name") if ready else "",
        "route_id": receipt_index.get("route_id") if ready else "",
        "allowed_use": LOOKUP_SCOPE if ready else "none",
        "granted_scope": receipt_index.get("granted_scope") if ready else "none",
        "boundary": receipt_index.get("boundary") if ready else "",
        "model_quality_claim": receipt_index.get("model_quality_claim") if ready else "not_claimed",
        "source_digest_count": receipt_index.get("source_digest_count") if ready else 0,
        "promotion_ready": False,
        "approved_for_promotion": False,
        "blocked_uses": list(receipt_index.get("blocked_uses") or BLOCKED_USES),
        "next_step": REVIEW_NEXT_STEP if ready else "repair_route_promotion_release_readiness_receipt_index_review",
    }


def _summary(status: str, check_rows: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_index_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "entry_count": review.get("entry_count"),
        "lookup_key_count": len(list(review.get("lookup_keys") or [])),
        "lookup_ready": review.get("lookup_ready"),
        "consumer_name": review.get("consumer_name"),
        "route_id": review.get("route_id"),
        "allowed_use": review.get("allowed_use"),
        "granted_scope": review.get("granted_scope"),
        "boundary": review.get("boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "source_digest_count": review.get("source_digest_count"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "blocked_uses": review.get("blocked_uses"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The receipt index is not approved for bounded lookup.",
            "next_action": "repair the receipt index before downstream lookup consumption",
        }
    return {
        "model_quality_claim": review.get("model_quality_claim"),
        "reason": "The receipt index is approved for bounded route-promotion release readiness lookup only.",
        "next_action": review.get("next_step"),
    }


def _sha256_or_empty(path: str | Path | None) -> str:
    if not path:
        return ""
    source = Path(path)
    if not source.is_file():
        return ""
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_release_readiness_receipt_index_review_ready"
    return "fix_model_capability_route_promotion_release_readiness_receipt_index_review"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_REVIEW_TEXT_FILENAME",
    "build_model_capability_route_promotion_release_readiness_receipt_index_review",
    "locate_route_promotion_release_readiness_receipt_index",
    "read_json_report",
    "resolve_exit_code",
]
