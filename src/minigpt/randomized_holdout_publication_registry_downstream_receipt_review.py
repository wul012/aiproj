from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_downstream_guard import BLOCKED_USES
from minigpt.randomized_holdout_publication_registry_downstream_receipt import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_receipt_review.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_receipt_review.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_receipt_review.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_receipt_review.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_receipt_review.html"

REVIEW_ID = "randomized-holdout-publication-registry-downstream-receipt-review-v940"


def locate_randomized_holdout_publication_registry_downstream_receipt(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream receipt review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_receipt_review(
    receipt_report: dict[str, Any],
    *,
    downstream_receipt_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream receipt review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    receipt_summary = as_dict(receipt_report.get("summary"))
    receipt = as_dict(receipt_report.get("receipt"))
    consumer_receipts = list_of_dicts(receipt_report.get("consumer_receipts"))
    entries = list_of_dicts(receipt_report.get("entry_rows"))
    checks = _checks(receipt_report, receipt_summary, receipt, consumer_receipts, entries, downstream_receipt_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(
        status,
        receipt_summary,
        receipt,
        consumer_receipts,
        downstream_receipt_path,
        str(receipt_report.get("downstream_guard_sha256") or ""),
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "downstream_receipt_path": str(downstream_receipt_path or ""),
        "source_downstream_receipt_summary": receipt_summary,
        "source_downstream_receipt": receipt,
        "source_downstream_guard_sha256": receipt_report.get("downstream_guard_sha256", ""),
        "consumer_receipts": consumer_receipts,
        "entry_rows": entries,
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_consumer_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("randomized_holdout_publication_registry_downstream_receipt_review_ready") is not True:
        return 1
    if require_consumer_ready and summary.get("consumer_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    receipt_report: dict[str, Any],
    receipt_summary: dict[str, Any],
    receipt: dict[str, Any],
    consumer_receipts: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    receipt_path: str | Path | None,
) -> list[dict[str, Any]]:
    blocked_uses = list(receipt_summary.get("blocked_uses") or [])
    source_guard_path = receipt.get("downstream_guard_path")
    source_digest = str(receipt_report.get("downstream_guard_sha256") or "")
    return [
        _check("downstream_receipt_file_exists", _path_exists(receipt_path), str(receipt_path or ""), "downstream receipt file must exist"),
        _check("downstream_receipt_passed", receipt_report.get("status") == "pass", receipt_report.get("status"), "downstream receipt must pass"),
        _check("downstream_receipt_decision_ready", receipt_report.get("decision") == "randomized_holdout_publication_registry_downstream_receipt_ready", receipt_report.get("decision"), "downstream receipt decision must be ready"),
        _check("receipt_summary_ready", receipt_summary.get("randomized_holdout_publication_registry_downstream_receipt_ready") is True and receipt.get("receipt_ready") is True, {"summary": receipt_summary.get("randomized_holdout_publication_registry_downstream_receipt_ready"), "receipt": receipt.get("receipt_ready")}, "receipt summary and body must be ready"),
        _check("receipt_status_ready", receipt_summary.get("receipt_status") == "downstream_governance_lookup_receipted" and receipt.get("receipt_status") == "downstream_governance_lookup_receipted", {"summary": receipt_summary.get("receipt_status"), "receipt": receipt.get("receipt_status")}, "receipt must be governance lookup receipted"),
        _check("granted_use_lookup_only", receipt_summary.get("granted_use") == "downstream_governance_lookup_only" and receipt.get("granted_use") == "downstream_governance_lookup_only", {"summary": receipt_summary.get("granted_use"), "receipt": receipt.get("granted_use")}, "granted use must stay downstream lookup only"),
        _check("blocked_uses_complete", all(use in blocked_uses for use in BLOCKED_USES), blocked_uses, "review must preserve all blocked uses"),
        _check("promotion_still_false", receipt_summary.get("promotion_ready") is False and receipt.get("promotion_ready") is False, {"summary": receipt_summary.get("promotion_ready"), "receipt": receipt.get("promotion_ready")}, "review must not enable promotion"),
        _check("approved_for_promotion_false", receipt_summary.get("approved_for_promotion") is False and receipt.get("approved_for_promotion") is False, {"summary": receipt_summary.get("approved_for_promotion"), "receipt": receipt.get("approved_for_promotion")}, "review must not approve promotion"),
        _check("consumer_boundary_governance", receipt_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and receipt.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": receipt_summary.get("consumer_boundary"), "receipt": receipt.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", receipt.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, receipt.get("model_quality_claim"), "model quality claim must remain bounded"),
        _check("consumer_receipts_present", len(consumer_receipts) == int(receipt_summary.get("entry_count") or 0) and len(consumer_receipts) > 0, {"consumer_receipts": len(consumer_receipts), "entry_count": receipt_summary.get("entry_count")}, "review must cover all consumer receipt rows"),
        _check("consumer_receipts_lookup_only", all(row.get("granted_use") == "downstream_governance_lookup_only" for row in consumer_receipts), [row.get("granted_use") for row in consumer_receipts], "consumer rows must stay lookup-only"),
        _check("consumer_receipts_not_promoted", all(row.get("promotion_ready") is False for row in consumer_receipts), [row.get("promotion_ready") for row in consumer_receipts], "consumer rows must not be promoted"),
        _check("entries_present", len(entries) == int(receipt_summary.get("entry_count") or 0) and len(entries) > 0, {"entries": len(entries), "entry_count": receipt_summary.get("entry_count")}, "review must keep entry rows aligned"),
        _check("lookup_key_count_matches", int(receipt_summary.get("lookup_key_count") or 0) == len(consumer_receipts), {"lookup_key_count": receipt_summary.get("lookup_key_count"), "consumer_receipts": len(consumer_receipts)}, "lookup key count must match consumer rows"),
        _check("source_guard_digest_shape", len(source_digest) == 64 and all(char in "0123456789abcdef" for char in source_digest), source_digest, "source guard digest must be a lowercase sha256"),
        _check("source_guard_digest_matches", _sha256_file(source_guard_path) == source_digest, {"path": source_guard_path, "digest": source_digest}, "source guard digest must match the referenced guard JSON"),
        _check("source_checks_clean", int(receipt_summary.get("failed_check_count") or 0) == 0, receipt_summary.get("failed_check_count"), "source receipt checks must be clean"),
        _check("source_next_step_matches", receipt_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_NEXT_STEP, receipt_summary.get("next_step"), "source receipt must route to review"),
    ]


def _review(
    status: str,
    receipt_summary: dict[str, Any],
    receipt: dict[str, Any],
    consumer_receipts: list[dict[str, Any]],
    receipt_path: str | Path | None,
    source_guard_sha256: str,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_downstream_consumer_packet" if ready else "blocked",
        "downstream_receipt_path": str(receipt_path or ""),
        "consumer_name": receipt_summary.get("consumer_name") if ready else "",
        "consumer_ready": ready,
        "entry_count": len(consumer_receipts) if ready else 0,
        "granted_use": receipt_summary.get("granted_use") if ready else "none",
        "blocked_uses": list(receipt_summary.get("blocked_uses") or BLOCKED_USES),
        "source_guard_sha256": source_guard_sha256 if ready else "",
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_receipt_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_receipt_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "consumer_name": review.get("consumer_name"),
        "consumer_ready": review.get("consumer_ready"),
        "entry_count": review.get("entry_count"),
        "granted_use": review.get("granted_use"),
        "blocked_uses": review.get("blocked_uses"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": review.get("consumer_boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_receipt_review_ready"
    return "fix_randomized_holdout_publication_registry_downstream_receipt_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream receipt is not ready for consumer packet construction.",
            "next_action": "repair downstream receipt before consumer packet",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream receipt is reviewed for consumer-packet construction while promotion and claim expansion remain blocked.",
        "next_action": str(review.get("next_step")),
    }


def _sha256_file(path: Any) -> str:
    if not path or not Path(str(path)).is_file():
        return ""
    return sha256(Path(str(path)).read_bytes()).hexdigest()


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_receipt_review",
    "locate_randomized_holdout_publication_registry_downstream_receipt",
    "read_json_report",
    "resolve_exit_code",
]
