from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review import read_json_report as read_receipt_review_json
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.html"

CHECKED_SUMMARY_FIELDS = (
    "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_ready",
    "packet_id",
    "packet_status",
    "consumer_name",
    "lookup_ready",
    "granted_use",
    "blocked_uses",
    "publication_index_row_count",
    "source_evidence_count",
    "consumer_receipt_count",
    "lookup_key_count",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "model_quality_claim",
    "next_step",
)

CHECKED_PACKET_FIELDS = (
    "packet_ready",
    "packet_id",
    "packet_status",
    "receipt_review_path",
    "receipt_review_sha256",
    "publication_receipt_path",
    "publication_receipt_sha256",
    "consumer_name",
    "consumer_boundary",
    "granted_use",
    "blocked_uses",
    "publication_index_row_count",
    "source_evidence_count",
    "consumer_receipt_count",
    "lookup_keys",
    "source_index_review_path",
    "source_publication_path",
    "source_publication_check_path",
    "source_review_path",
    "source_index_path",
    "promotion_ready",
    "approved_for_promotion",
    "model_quality_claim",
    "next_step",
)


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet check input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(
    receipt_packet_report: dict[str, Any],
    *,
    receipt_packet_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet contract check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_review = _resolve_source_review(receipt_packet_report, receipt_packet_path)
    rebuilt = _rebuild_receipt_packet(source_review)
    checks = _check_rows(receipt_packet_report, rebuilt, source_review)
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
        "source_receipt_packet": str(receipt_packet_path or ""),
        "source_receipt_review": "" if source_review is None else str(source_review),
        "source_summary": as_dict(receipt_packet_report.get("summary")),
        "rebuilt_summary": as_dict(rebuilt.get("summary")),
        "source_packet": as_dict(receipt_packet_report.get("packet")),
        "rebuilt_packet": as_dict(rebuilt.get("packet")),
        "source_packet_rows": list_of_dicts(receipt_packet_report.get("packet_rows")),
        "rebuilt_packet_rows": list_of_dicts(rebuilt.get("packet_rows")),
        "source_evidence_rows": list_of_dicts(receipt_packet_report.get("source_evidence_rows")),
        "rebuilt_evidence_rows": list_of_dicts(rebuilt.get("source_evidence_rows")),
        "check_rows": checks,
        "summary": _summary(status, checks, receipt_packet_report, rebuilt, source_review),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool, require_promotion_ready: bool = False) -> int:
    summary = as_dict(report.get("summary"))
    if require_pass and report.get("status") != "pass":
        return 1
    if require_promotion_ready and summary.get("original_promotion_ready") is not True:
        return 1
    return 0


def _resolve_source_review(packet_report: dict[str, Any], packet_path: str | Path | None) -> Path | None:
    packet = as_dict(packet_report.get("packet"))
    candidates = [packet_report.get("receipt_review_path"), packet.get("receipt_review_path")]
    for value in candidates:
        text = str(value or "")
        if not text:
            continue
        direct = Path(text)
        if direct.is_file():
            return direct
        if packet_path:
            sibling = Path(packet_path).parent / text
            if sibling.is_file():
                return sibling
        return direct
    return None


def _rebuild_receipt_packet(source_review: Path | None) -> dict[str, Any]:
    if source_review is None or not source_review.is_file():
        return {
            "status": "fail",
            "decision": "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet",
            "failed_count": 1,
            "packet": {"packet_ready": False, "packet_id": "not_ready", "packet_status": "blocked"},
            "packet_rows": [],
            "source_evidence_rows": [],
            "check_rows": [],
            "summary": {
                "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_ready": False,
                "lookup_ready": False,
                "promotion_ready": False,
                "failed_check_count": 1,
            },
        }
    return build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet(
        read_receipt_review_json(source_review),
        receipt_review_path=source_review,
    )


def _check_rows(original: dict[str, Any], rebuilt: dict[str, Any], source_review: Path | None) -> list[dict[str, Any]]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    original_packet = as_dict(original.get("packet"))
    rebuilt_packet = as_dict(rebuilt.get("packet"))
    rows = [
        _check("source_receipt_review_present", source_review is not None, str(source_review or ""), "receipt packet must record a source publication receipt review"),
        _check("source_receipt_review_exists", bool(source_review and source_review.is_file()), str(source_review or ""), "source publication receipt review must exist"),
        _compare("status", original.get("status"), rebuilt.get("status")),
        _compare("decision", original.get("decision"), rebuilt.get("decision")),
        _compare("failed_count", original.get("failed_count"), rebuilt.get("failed_count")),
    ]
    rows.extend(_compare(f"summary.{field}", original_summary.get(field), rebuilt_summary.get(field)) for field in CHECKED_SUMMARY_FIELDS)
    rows.extend(_compare(f"packet.{field}", original_packet.get(field), rebuilt_packet.get(field)) for field in CHECKED_PACKET_FIELDS)
    rows.append(_compare("packet_rows", list_of_dicts(original.get("packet_rows")), list_of_dicts(rebuilt.get("packet_rows"))))
    rows.append(_compare("source_evidence_rows", list_of_dicts(original.get("source_evidence_rows")), list_of_dicts(rebuilt.get("source_evidence_rows"))))
    rows.append(_compare("check_rows", list_of_dicts(original.get("check_rows")), list_of_dicts(rebuilt.get("check_rows"))))
    return rows


def _compare(check_id: str, original: Any, rebuilt: Any) -> dict[str, Any]:
    return _check(check_id, original == rebuilt, {"source": original, "rebuilt": rebuilt}, f"{check_id} must match the rebuilt publication receipt packet")


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, checks: list[dict[str, Any]], original: dict[str, Any], rebuilt: dict[str, Any], source_review: Path | None) -> dict[str, Any]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    original_packet = as_dict(original.get("packet"))
    rebuilt_packet = as_dict(rebuilt.get("packet"))
    return {
        "contract_check_ready": status == "pass",
        "source_receipt_review": "" if source_review is None else str(source_review),
        "original_decision": original.get("decision"),
        "rebuilt_decision": rebuilt.get("decision"),
        "original_packet_status": original_summary.get("packet_status"),
        "rebuilt_packet_status": rebuilt_summary.get("packet_status"),
        "original_granted_use": original_summary.get("granted_use"),
        "rebuilt_granted_use": rebuilt_summary.get("granted_use"),
        "original_source_evidence_count": original_summary.get("source_evidence_count"),
        "rebuilt_source_evidence_count": rebuilt_summary.get("source_evidence_count"),
        "original_consumer_receipt_count": original_summary.get("consumer_receipt_count"),
        "rebuilt_consumer_receipt_count": rebuilt_summary.get("consumer_receipt_count"),
        "original_lookup_keys": original_packet.get("lookup_keys"),
        "rebuilt_lookup_keys": rebuilt_packet.get("lookup_keys"),
        "original_promotion_ready": original_summary.get("promotion_ready"),
        "rebuilt_promotion_ready": rebuilt_summary.get("promotion_ready"),
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_NEXT_STEP if status == "pass" else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check",
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_contract_check_passed"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_contract"


def _interpretation(status: str) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt packet index publication receipt packet does not match the packet rebuilt from its source receipt review.",
            "next_action": "repair randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream publication receipt packet index publication receipt packet can be rebuilt from the source receipt review with stable lookup-only fields.",
        "next_action": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_NEXT_STEP,
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet",
    "read_json_report",
    "resolve_exit_code",
]
