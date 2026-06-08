from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V990_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import blocked_uses, downstream_lookup_use, is_downstream_lookup_only, is_sha256
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V990_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_JSON_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.json"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_CSV_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_TEXT_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_MARKDOWN_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.md"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_HTML_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.html"

PUBLICATION_ID = "randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-v991"


def locate_receipt_index_review_v991(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V990_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication receipt index receipt index publication v991 input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991(
    review_report: dict[str, Any],
    *,
    receipt_index_review_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication v991",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(review_report.get("summary"))
    review = as_dict(review_report.get("review"))
    receipt_index_rows = list_of_dicts(review_report.get("receipt_index_rows"))
    source_evidence_rows = list_of_dicts(review_report.get("source_evidence_rows"))
    checks = _checks(review_report, review_summary, review, receipt_index_rows, source_evidence_rows, receipt_index_review_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    publication = _publication(status, review_summary, review, receipt_index_rows, source_evidence_rows, receipt_index_review_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_index_review_path": str(receipt_index_review_path or ""),
        "source_receipt_index_review_summary": review_summary,
        "source_receipt_index_review": review,
        "receipt_index_rows": receipt_index_rows,
        "source_evidence_rows": source_evidence_rows,
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
    if require_publication_ready and summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_ready") is not True:
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
    receipt_index_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    review_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = [str(row.get("lookup_key")) for row in receipt_index_rows]
    return [
        _check("receipt_index_review_file_exists", _path_exists(review_path), str(review_path or ""), "receipt index review file must exist"),
        _check("receipt_index_review_passed", review_report.get("status") == "pass", review_report.get("status"), "receipt index review must pass"),
        _check("receipt_index_review_decision_ready", review_report.get("decision") == "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_ready", review_report.get("decision"), "receipt index review decision must be ready"),
        _check("receipt_index_review_summary_ready", review_summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_ready") is True and review.get("review_ready") is True, {"summary": review_summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_ready"), "review": review.get("review_ready")}, "review summary and body must be ready"),
        _check("review_status_publishable", review_summary.get("review_status") == "approved_for_publication_receipt_index_receipt_index_publication_lookup_only" and review.get("review_status") == "approved_for_publication_receipt_index_receipt_index_publication_lookup_only", {"summary": review_summary.get("review_status"), "review": review.get("review_status")}, "review must approve lookup-only publication"),
        _check("receipt_index_file_exists", _path_exists(review.get("receipt_index_path")), review.get("receipt_index_path"), "reviewed receipt index must still exist"),
        _check("source_receipt_file_exists", _path_exists(review.get("source_receipt_path")), review.get("source_receipt_path"), "source receipt must still exist"),
        _check("source_receipt_check_file_exists", _path_exists(review.get("source_receipt_check_path")), review.get("source_receipt_check_path"), "source receipt contract check must still exist"),
        _check("receipt_ready", review_summary.get("receipt_ready") is True and review.get("receipt_ready") is True, {"summary": review_summary.get("receipt_ready"), "review": review.get("receipt_ready")}, "publication requires receipt-ready review"),
        _check("lookup_ready", review_summary.get("lookup_ready") is True and review.get("lookup_ready") is True, {"summary": review_summary.get("lookup_ready"), "review": review.get("lookup_ready")}, "publication requires lookup-ready review"),
        _check("contract_check_ready", review_summary.get("contract_check_ready") is True and review.get("contract_check_ready") is True, {"summary": review_summary.get("contract_check_ready"), "review": review.get("contract_check_ready")}, "publication requires contract-ready review"),
        _check("receipt_index_row_count", int(review_summary.get("receipt_index_row_count") or 0) == 1 and int(review.get("receipt_index_row_count") or 0) == 1 and len(receipt_index_rows) == 1, {"summary": review_summary.get("receipt_index_row_count"), "review": review.get("receipt_index_row_count"), "rows": len(receipt_index_rows)}, "publication requires one receipt index row"),
        _check("lookup_keys_present", len(lookup_keys) == int(review_summary.get("lookup_key_count") or 0) == 1 and all(key.startswith("receipt-index-receipt:") for key in lookup_keys), lookup_keys, "publication requires one stable receipt-index-receipt lookup key"),
        _check("source_evidence_count", int(review_summary.get("source_evidence_count") or 0) == 2 and int(review.get("source_evidence_count") or 0) == 2 and len(source_evidence_rows) == 2, {"summary": review_summary.get("source_evidence_count"), "review": review.get("source_evidence_count"), "rows": len(source_evidence_rows)}, "publication requires two source evidence rows"),
        _check("source_evidence_passed", all(row.get("status") == "pass" for row in source_evidence_rows), [row.get("status") for row in source_evidence_rows], "source evidence rows must pass"),
        _check("source_evidence_digests", all(is_sha256(row.get("sha256")) for row in source_evidence_rows), [row.get("sha256") for row in source_evidence_rows], "source evidence rows must carry SHA-256 digests"),
        _check("source_evidence_files_exist", all(_path_exists(row.get("path")) for row in source_evidence_rows), [row.get("path") for row in source_evidence_rows], "source evidence files must exist"),
        _check("allowed_use_lookup_only", is_downstream_lookup_only(review_summary.get("allowed_use")) and is_downstream_lookup_only(review.get("allowed_use")), {"summary": review_summary.get("allowed_use"), "review": review.get("allowed_use")}, "publication must remain downstream lookup only"),
        _check("consumer_boundary_governance", review_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and review.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": review_summary.get("consumer_boundary"), "review": review.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", review_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and review.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": review_summary.get("model_quality_claim"), "review": review.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("blocked_uses_preserved", list(review_summary.get("blocked_uses") or []) == blocked_uses() and list(review.get("blocked_uses") or []) == blocked_uses(), {"summary": review_summary.get("blocked_uses"), "review": review.get("blocked_uses")}, "blocked uses must remain explicit"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and review.get("promotion_ready") is False and review.get("approved_for_promotion") is False, {"summary": review_summary.get("promotion_ready"), "review": review.get("promotion_ready"), "approved": review.get("approved_for_promotion")}, "publication must not enable promotion"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source review checks must be clean"),
        _check("source_next_step_matches", review_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V990_NEXT_STEP, review_summary.get("next_step"), "source review must route to publication"),
    ]


def _publication(
    status: str,
    review_summary: dict[str, Any],
    review: dict[str, Any],
    receipt_index_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    review_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "publication_ready": ready,
        "publication_id": PUBLICATION_ID if ready else "not_ready",
        "publication_status": "published_for_publication_receipt_index_receipt_index_lookup_only" if ready else "blocked",
        "receipt_index_review_path": str(review_path or ""),
        "receipt_index_path": review.get("receipt_index_path") if ready else "",
        "receipt_index_id": review.get("receipt_index_id") if ready else "",
        "receipt_index_row_count": len(receipt_index_rows) if ready else 0,
        "source_evidence_count": len(source_evidence_rows) if ready else 0,
        "lookup_keys": [row.get("lookup_key") for row in receipt_index_rows] if ready else [],
        "source_receipt_path": review.get("source_receipt_path") if ready else "",
        "source_receipt_check_path": review.get("source_receipt_check_path") if ready else "",
        "published_use": downstream_lookup_use() if ready else "none",
        "publish_ready": ready,
        "lookup_ready": bool(ready and review_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and review_summary.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "blocked_uses": blocked_uses(),
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_NEXT_STEP if ready else "repair_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991",
    }


def _summary(status: str, checks: list[dict[str, Any]], publication: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_ready": status == "pass" and publication.get("publication_ready") is True,
        "publication_id": publication.get("publication_id"),
        "publication_status": publication.get("publication_status"),
        "published_use": publication.get("published_use"),
        "publish_ready": publication.get("publish_ready"),
        "lookup_ready": publication.get("lookup_ready"),
        "contract_check_ready": publication.get("contract_check_ready"),
        "receipt_index_id": publication.get("receipt_index_id"),
        "receipt_index_row_count": publication.get("receipt_index_row_count"),
        "source_evidence_count": publication.get("source_evidence_count"),
        "lookup_key_count": len(list(publication.get("lookup_keys") or [])),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": publication.get("consumer_boundary"),
        "model_quality_claim": publication.get("model_quality_claim"),
        "blocked_uses": publication.get("blocked_uses"),
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
        return "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_ready"
    return "fix_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991"


def _interpretation(status: str, publication: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The receipt index receipt index review is not ready for lookup-only publication.",
            "next_action": "repair receipt index review before publication",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The receipt index receipt index is published only for lookup-only consumption; production promotion remains blocked.",
        "next_action": str(publication.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_TEXT_FILENAME",
    "build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991",
    "locate_receipt_index_review_v991",
    "read_json_report",
    "resolve_exit_code",
]
