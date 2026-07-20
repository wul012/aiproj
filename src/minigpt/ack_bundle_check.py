from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication,
    read_json_report as read_review_json,
)
from minigpt.report_utils import as_dict, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.html"

SUMMARY_FIELDS = [
    "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_ready",
    "publication_id",
    "publication_status",
    "consumer_name",
    "published_use",
    "publish_ready",
    "lookup_ready",
    "contract_check_ready",
    "packet_index_row_count",
    "source_packet_row_count",
    "source_evidence_count",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "model_quality_claim",
]

PUBLICATION_FIELDS = [
    "publication_ready",
    "publication_id",
    "publication_status",
    "receipt_packet_index_review_path",
    "receipt_packet_index_path",
    "source_packet_path",
    "source_packet_check_path",
    "consumer_name",
    "published_use",
    "publish_ready",
    "lookup_ready",
    "contract_check_ready",
    "packet_index_row_count",
    "source_packet_row_count",
    "source_evidence_count",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "model_quality_claim",
    "next_step",
]


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication check input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check(
    publication_report: dict[str, Any],
    *,
    publication_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication contract check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    original_summary = as_dict(publication_report.get("summary"))
    original_publication = as_dict(publication_report.get("publication"))
    source_review = _resolve_source_review_path(publication_report, original_publication, publication_path)
    rebuilt = _rebuild_publication(source_review)
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    rebuilt_publication = as_dict(rebuilt.get("publication"))
    checks = _checks(publication_report, rebuilt, original_summary, rebuilt_summary, original_publication, rebuilt_publication, source_review)
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
        "publication_path": str(publication_path or ""),
        "source_receipt_packet_index_review": str(source_review or ""),
        "original_summary": original_summary,
        "rebuilt_summary": rebuilt_summary,
        "original_publication": original_publication,
        "rebuilt_publication": rebuilt_publication,
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
    original_publication: dict[str, Any],
    rebuilt_publication: dict[str, Any],
    source_review: Path | None,
) -> list[dict[str, Any]]:
    checks = [
        _check("source_receipt_packet_index_review_exists", source_review is not None and source_review.exists(), str(source_review or ""), "source receipt packet index review must exist"),
        _check("status", original.get("status") == rebuilt.get("status"), {"original": original.get("status"), "rebuilt": rebuilt.get("status")}, "status must rebuild exactly"),
        _check("decision", original.get("decision") == rebuilt.get("decision"), {"original": original.get("decision"), "rebuilt": rebuilt.get("decision")}, "decision must rebuild exactly"),
        _check("failed_count", int(original.get("failed_count") or 0) == int(rebuilt.get("failed_count") or 0), {"original": original.get("failed_count"), "rebuilt": rebuilt.get("failed_count")}, "failed count must rebuild exactly"),
        _check("check_rows", list(original.get("check_rows") or []) == list(rebuilt.get("check_rows") or []), "check_rows", "publication check rows must rebuild exactly"),
    ]
    checks.extend(_field_checks("summary", SUMMARY_FIELDS, original_summary, rebuilt_summary))
    checks.extend(_field_checks("publication", PUBLICATION_FIELDS, original_publication, rebuilt_publication))
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


def _resolve_source_review_path(report: dict[str, Any], publication: dict[str, Any], publication_path: str | Path | None) -> Path | None:
    raw = report.get("receipt_packet_index_review_path") or publication.get("receipt_packet_index_review_path")
    if not raw:
        return None
    source = Path(str(raw))
    if source.is_absolute() or source.exists():
        return source
    if publication_path:
        candidate = Path(publication_path).parent / source
        if candidate.exists():
            return candidate
    return source


def _rebuild_publication(source_review: Path | None) -> dict[str, Any]:
    if source_review is None or not source_review.exists():
        return {}
    return build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication(
        read_review_json(source_review),
        receipt_packet_index_review_path=source_review,
    )


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(
    status: str,
    checks: list[dict[str, Any]],
    source_review: Path | None,
    original_summary: dict[str, Any],
    rebuilt_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_check_ready": status == "pass",
        "source_receipt_packet_index_review": str(source_review or ""),
        "original_publication_status": original_summary.get("publication_status"),
        "rebuilt_publication_status": rebuilt_summary.get("publication_status"),
        "original_published_use": original_summary.get("published_use"),
        "rebuilt_published_use": rebuilt_summary.get("published_use"),
        "original_packet_index_row_count": original_summary.get("packet_index_row_count"),
        "rebuilt_packet_index_row_count": rebuilt_summary.get("packet_index_row_count"),
        "original_source_packet_row_count": original_summary.get("source_packet_row_count"),
        "rebuilt_source_packet_row_count": rebuilt_summary.get("source_packet_row_count"),
        "original_promotion_ready": original_summary.get("promotion_ready"),
        "rebuilt_promotion_ready": rebuilt_summary.get("promotion_ready"),
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_NEXT_STEP if status == "pass" else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication",
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_contract_check_passed"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication"


def _interpretation(status: str) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt packet index publication does not rebuild from its source review.",
            "next_action": "repair or regenerate publication receipt packet index publication",
        }
    return {
        "model_quality_claim": "bounded_randomized_target_hidden_holdout_claim_only",
        "reason": "The downstream publication receipt packet index publication rebuilds from the source review and remains lookup-only.",
        "next_action": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_NEXT_STEP,
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication",
    "read_json_report",
    "resolve_exit_code",
]
