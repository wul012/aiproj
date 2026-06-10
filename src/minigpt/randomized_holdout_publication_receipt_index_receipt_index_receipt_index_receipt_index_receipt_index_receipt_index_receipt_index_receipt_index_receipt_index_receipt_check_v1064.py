from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1063 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1063_JSON_FILENAME,
    READY_KEY as SOURCE_READY_KEY,
    build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1063,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_JSON_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064.json"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_CSV_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_TEXT_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_MARKDOWN_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064.md"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_HTML_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064.html"

SUMMARY_FIELDS = [
    SOURCE_READY_KEY,
    "receipt_id",
    "receipt_type",
    "receipt_status",
    "consumer_name",
    "granted_use",
    "receipt_index_row_count",
    "source_evidence_count",
    "lookup_key_count",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "model_quality_claim",
    "next_step",
    "passed_check_count",
    "failed_check_count",
]

RECEIPT_FIELDS = [
    "receipt_ready",
    "receipt_id",
    "receipt_type",
    "receipt_status",
    "consumer_name",
    "requested_use",
    "granted_use",
    "receipt_index_review_path",
    "receipt_index_review_sha256",
    "receipt_index_row_count",
    "source_evidence_count",
    "lookup_keys",
    "review_id",
    "review_status",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "model_quality_claim",
    "source_receipt_index_path",
    "source_receipt_path",
    "source_receipt_check_path",
    "source_review_path",
    "source_receipt_index_origin_path",
    "next_step",
]


def locate_receipt_v1064(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1063_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt check v1064 input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064(
    receipt_report: dict[str, Any],
    *,
    receipt_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt check v1064",
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
        "source_receipt_index_review": str(source_review or ""),
        "original_summary": original_summary,
        "rebuilt_summary": rebuilt_summary,
        "original_receipt": original_receipt,
        "rebuilt_receipt": rebuilt_receipt,
        "check_rows": checks,
        "summary": _summary(status, checks, source_review, original_summary, rebuilt_summary),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


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
        _check("source_receipt_index_review_exists", source_review is not None and source_review.exists(), str(source_review or ""), "source receipt index review must exist"),
        _check("status", original.get("status") == rebuilt.get("status"), {"original": original.get("status"), "rebuilt": rebuilt.get("status")}, "status must rebuild exactly"),
        _check("decision", original.get("decision") == rebuilt.get("decision"), {"original": original.get("decision"), "rebuilt": rebuilt.get("decision")}, "decision must rebuild exactly"),
        _check("failed_count", int(original.get("failed_count") or 0) == int(rebuilt.get("failed_count") or 0), {"original": original.get("failed_count"), "rebuilt": rebuilt.get("failed_count")}, "failed count must rebuild exactly"),
        _check("receipt_index_review_sha256", original.get("receipt_index_review_sha256") == rebuilt.get("receipt_index_review_sha256"), {"original": original.get("receipt_index_review_sha256"), "rebuilt": rebuilt.get("receipt_index_review_sha256")}, "source review digest must rebuild exactly"),
        _check("consumer_receipts", list_of_dicts(original.get("consumer_receipts")) == list_of_dicts(rebuilt.get("consumer_receipts")), "consumer_receipts", "consumer receipts must rebuild exactly"),
    ]
    checks.extend(_field_checks("summary", SUMMARY_FIELDS, original_summary, rebuilt_summary))
    checks.extend(_field_checks("receipt", RECEIPT_FIELDS, original_receipt, rebuilt_receipt))
    return checks


def _field_checks(prefix: str, fields: list[str], original: dict[str, Any], rebuilt: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check(f"{prefix}.{field}", original.get(field) == rebuilt.get(field), {"original": original.get(field), "rebuilt": rebuilt.get(field)}, f"{prefix}.{field} must rebuild exactly")
        for field in fields
    ]


def _resolve_source_review_path(report: dict[str, Any], receipt: dict[str, Any], receipt_path: str | Path | None) -> Path | None:
    raw = report.get("receipt_index_review_path") or receipt.get("receipt_index_review_path")
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
    return build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1063(
        read_json_report(source_review),
        receipt_index_review_path=source_review,
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
        "source_receipt_index_review": str(source_review or ""),
        "original_receipt_status": original_summary.get("receipt_status"),
        "rebuilt_receipt_status": rebuilt_summary.get("receipt_status"),
        "original_granted_use": original_summary.get("granted_use"),
        "rebuilt_granted_use": rebuilt_summary.get("granted_use"),
        "original_lookup_key_count": original_summary.get("lookup_key_count"),
        "rebuilt_lookup_key_count": rebuilt_summary.get("lookup_key_count"),
        "original_promotion_ready": original_summary.get("promotion_ready"),
        "rebuilt_promotion_ready": rebuilt_summary.get("promotion_ready"),
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_NEXT_STEP if status == "pass" else "repair_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064",
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1064_passed"
    return "fix_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064"


def _interpretation(status: str) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "The v1063 receipt does not rebuild from its source review.", "next_action": "repair or regenerate v1063 receipt"}
    return {
        "model_quality_claim": "bounded_randomized_target_hidden_holdout_claim_only",
        "reason": "The v1063 receipt rebuilds from the v1062 review and remains lookup-only.",
        "next_action": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_NEXT_STEP,
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1064_TEXT_FILENAME",
    "build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064",
    "locate_receipt_v1064",
    "read_json_report",
    "resolve_exit_code",
]
