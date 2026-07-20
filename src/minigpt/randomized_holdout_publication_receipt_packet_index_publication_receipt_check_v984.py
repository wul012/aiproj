from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_v983 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_V983_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983,
    read_json_report as read_review_json,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_JSON_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.json"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_CSV_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_TEXT_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_MARKDOWN_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.md"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_HTML_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.html"

SUMMARY_FIELDS = [
    "receipt_id",
    "receipt_type",
    "receipt_status",
    "consumer_name",
    "granted_use",
    "publication_index_row_count",
    "source_evidence_count",
    "lookup_key_count",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "blocked_uses",
    "next_step",
]

RECEIPT_FIELDS = [
    "receipt_ready",
    "receipt_id",
    "receipt_type",
    "receipt_status",
    "consumer_name",
    "requested_use",
    "granted_use",
    "index_review_path",
    "publication_index_row_count",
    "source_evidence_count",
    "lookup_keys",
    "review_id",
    "review_status",
    "blocked_uses",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "model_quality_claim",
    "source_publication_path",
    "source_publication_check_path",
    "next_step",
]


def locate_receipt_v984(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_V983_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication receipt packet index publication receipt check v984 input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984(
    receipt_report: dict[str, Any],
    *,
    receipt_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication receipt packet index publication receipt check v984",
    generated_at: str | None = None,
) -> dict[str, Any]:
    original_summary = as_dict(receipt_report.get("summary"))
    original_receipt = as_dict(receipt_report.get("receipt"))
    source_review = _resolve_source_review_path(receipt_report, original_receipt, receipt_path)
    rebuilt = _rebuild_receipt(source_review)
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    rebuilt_receipt = as_dict(rebuilt.get("receipt"))
    checks = _checks(receipt_report, rebuilt, original_summary, rebuilt_summary, original_receipt, rebuilt_receipt, source_review)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_path": str(receipt_path or ""),
        "source_index_review": str(source_review or ""),
        "original_summary": original_summary,
        "rebuilt_summary": rebuilt_summary,
        "original_receipt": original_receipt,
        "rebuilt_receipt": rebuilt_receipt,
        "check_rows": checks,
        "summary": _summary(status, checks, source_review, original_summary, rebuilt_summary),
        "interpretation": _interpretation(status),
    }


def _checks(
    original: dict[str, Any],
    rebuilt: dict[str, Any],
    original_summary: dict[str, Any],
    rebuilt_summary: dict[str, Any],
    original_receipt: dict[str, Any],
    rebuilt_receipt: dict[str, Any],
    source_review: Path | None,
) -> list[dict[str, Any]]:
    checks = [
        _check("source_index_review_exists", source_review is not None and source_review.exists(), str(source_review or ""), "source index review must exist"),
        _check("status", original.get("status") == rebuilt.get("status"), {"original": original.get("status"), "rebuilt": rebuilt.get("status")}, "status must rebuild exactly"),
        _check("decision", original.get("decision") == rebuilt.get("decision"), {"original": original.get("decision"), "rebuilt": rebuilt.get("decision")}, "decision must rebuild exactly"),
        _check("failed_count", int(original.get("failed_count") or 0) == int(rebuilt.get("failed_count") or 0), {"original": original.get("failed_count"), "rebuilt": rebuilt.get("failed_count")}, "failed count must rebuild exactly"),
        _check("consumer_receipts", list_of_dicts(original.get("consumer_receipts")) == list_of_dicts(rebuilt.get("consumer_receipts")), "consumer_receipts", "consumer receipts must rebuild exactly"),
    ]
    checks.extend(_field_checks("summary", SUMMARY_FIELDS, original_summary, rebuilt_summary))
    checks.extend(_field_checks("receipt", RECEIPT_FIELDS, original_receipt, rebuilt_receipt))
    return checks


def _field_checks(prefix: str, fields: list[str], original: dict[str, Any], rebuilt: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check(
            f"{prefix}.{field}",
            original.get(field) == rebuilt.get(field),
            {"original": original.get(field), "rebuilt": rebuilt.get(field)},
            f"{prefix}.{field} must rebuild exactly",
        )
        for field in fields
    ]


def _resolve_source_review_path(report: dict[str, Any], receipt: dict[str, Any], receipt_path: str | Path | None) -> Path | None:
    raw = report.get("index_review_path") or receipt.get("index_review_path")
    if not raw:
        return None
    source = Path(str(raw))
    if source.is_absolute() or source.exists():
        return source
    if receipt_path:
        candidate = Path(receipt_path).parent / source
        if candidate.exists():
            return candidate
    return source


def _rebuild_receipt(source_review: Path | None) -> dict[str, Any]:
    if source_review is None or not source_review.exists():
        return {}
    return build_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983(
        read_review_json(source_review),
        index_review_path=source_review,
    )


def _summary(
    status: str,
    checks: list[dict[str, Any]],
    source_review: Path | None,
    original_summary: dict[str, Any],
    rebuilt_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_check_ready": status == "pass",
        "source_index_review": str(source_review or ""),
        "original_receipt_status": original_summary.get("receipt_status"),
        "rebuilt_receipt_status": rebuilt_summary.get("receipt_status"),
        "original_granted_use": original_summary.get("granted_use"),
        "rebuilt_granted_use": rebuilt_summary.get("granted_use"),
        "original_lookup_key_count": original_summary.get("lookup_key_count"),
        "rebuilt_lookup_key_count": rebuilt_summary.get("lookup_key_count"),
        "original_promotion_ready": original_summary.get("promotion_ready"),
        "rebuilt_promotion_ready": rebuilt_summary.get("promotion_ready"),
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_NEXT_STEP if status == "pass" else "repair_randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984",
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_receipt_packet_index_publication_receipt_contract_check_v984_passed"
    return "fix_randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984"


def _interpretation(status: str) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The receipt does not rebuild from its source index review.",
            "next_action": "repair or regenerate publication receipt",
        }
    return {
        "model_quality_claim": "bounded_randomized_target_hidden_holdout_claim_only",
        "reason": "The receipt rebuilds from the source index review and remains lookup-only.",
        "next_action": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_NEXT_STEP,
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_CHECK_V984_TEXT_FILENAME",
    "build_randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984",
    "locate_receipt_v984",
    "read_json_report",
    "resolve_exit_code",
]
