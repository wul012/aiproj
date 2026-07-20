from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import downstream_lookup_use, is_downstream_lookup_only
from minigpt.ack_bundle_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_JSON_FILENAME,
)
from minigpt.ack_bundle_packet_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.html"

RECEIPT_PACKET_INDEX_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-v967"


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_JSON_FILENAME
    return source


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index(
    receipt_packet_report: dict[str, Any],
    receipt_packet_check_report: dict[str, Any],
    *,
    receipt_packet_path: str | Path | None = None,
    receipt_packet_check_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index",
    generated_at: str | None = None,
) -> dict[str, Any]:
    packet_summary = as_dict(receipt_packet_report.get("summary"))
    packet = as_dict(receipt_packet_report.get("packet"))
    check_summary = as_dict(receipt_packet_check_report.get("summary"))
    packet_rows = list_of_dicts(receipt_packet_report.get("packet_rows"))
    source_evidence_rows = list_of_dicts(receipt_packet_report.get("source_evidence_rows"))
    checks = _checks(receipt_packet_report, receipt_packet_check_report, packet_summary, packet, check_summary, packet_rows, source_evidence_rows, receipt_packet_path, receipt_packet_check_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    index = _index(status, packet_summary, packet, check_summary, packet_rows, source_evidence_rows, receipt_packet_path, receipt_packet_check_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_packet_path": str(receipt_packet_path or ""),
        "receipt_packet_check_path": str(receipt_packet_check_path or ""),
        "source_receipt_packet_summary": packet_summary,
        "source_receipt_packet_check_summary": check_summary,
        "receipt_packet_index_rows": index.get("receipt_packet_index_rows", []),
        "source_packet_rows": packet_rows if status == "pass" else [],
        "source_evidence_rows": source_evidence_rows if status == "pass" else [],
        "check_rows": checks,
        "receipt_packet_index": index,
        "summary": _summary(status, checks, index),
        "interpretation": _interpretation(status, index),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_index_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_index_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    packet_report: dict[str, Any],
    check_report: dict[str, Any],
    packet_summary: dict[str, Any],
    packet: dict[str, Any],
    check_summary: dict[str, Any],
    packet_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    packet_path: str | Path | None,
    check_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("receipt_packet_file_exists", _path_exists(packet_path), str(packet_path or ""), "receipt packet file must exist"),
        _check("receipt_packet_check_file_exists", _path_exists(check_path), str(check_path or ""), "receipt packet contract check file must exist"),
        _check("receipt_packet_passed", packet_report.get("status") == "pass", packet_report.get("status"), "receipt packet must pass"),
        _check("receipt_packet_decision_ready", packet_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_ready", packet_report.get("decision"), "receipt packet decision must be ready"),
        _check("receipt_packet_summary_ready", packet_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_ready") is True and packet.get("packet_ready") is True, {"summary": packet_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_ready"), "packet": packet.get("packet_ready")}, "packet summary and body must be ready"),
        _check("receipt_packet_check_passed", check_report.get("status") == "pass", check_report.get("status"), "receipt packet contract check must pass"),
        _check("receipt_packet_check_decision_ready", check_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_contract_check_passed", check_report.get("decision"), "receipt packet contract check decision must pass"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "receipt packet contract check must be ready"),
        _check("packet_status_matches_check", packet_summary.get("packet_status") == check_summary.get("original_packet_status") == check_summary.get("rebuilt_packet_status"), {"packet": packet_summary.get("packet_status"), "original": check_summary.get("original_packet_status"), "rebuilt": check_summary.get("rebuilt_packet_status")}, "packet status must match the contract check"),
        _check("granted_use_lookup_only", is_downstream_lookup_only(packet_summary.get("granted_use")) and is_downstream_lookup_only(check_summary.get("original_granted_use")) and is_downstream_lookup_only(check_summary.get("rebuilt_granted_use")), {"packet": packet_summary.get("granted_use"), "original": check_summary.get("original_granted_use"), "rebuilt": check_summary.get("rebuilt_granted_use")}, "granted use must stay downstream lookup only"),
        _check("lookup_ready", packet_summary.get("lookup_ready") is True, packet_summary.get("lookup_ready"), "receipt packet index requires lookup-ready packet"),
        _check("packet_rows_present", len(packet_rows) == int(packet_summary.get("consumer_receipt_count") or 0) == 1, {"rows": len(packet_rows), "summary": packet_summary.get("consumer_receipt_count")}, "receipt packet index requires one packet row"),
        _check("source_evidence_rows_present", len(source_evidence_rows) == int(packet_summary.get("source_evidence_count") or 0) == 2, {"rows": len(source_evidence_rows), "summary": packet_summary.get("source_evidence_count")}, "receipt packet index requires two source evidence rows"),
        _check("source_evidence_passed", all(row.get("status") == "pass" for row in source_evidence_rows), [row.get("status") for row in source_evidence_rows], "source evidence rows must pass"),
        _check("source_evidence_files_exist", all(_path_exists(row.get("path")) for row in source_evidence_rows), [row.get("path") for row in source_evidence_rows], "source evidence files must exist"),
        _check("lookup_key_namespace", all(str(row.get("lookup_key")).startswith("publication:") for row in packet_rows), [row.get("lookup_key") for row in packet_rows], "packet lookup keys must use publication namespace"),
        _check("source_receipt_review_file_exists", _path_exists(packet.get("receipt_review_path")), packet.get("receipt_review_path"), "source receipt review must still exist"),
        _check("source_publication_receipt_file_exists", _path_exists(packet.get("publication_receipt_path")), packet.get("publication_receipt_path"), "source publication receipt must still exist"),
        _check("source_index_review_file_exists", _path_exists(packet.get("source_index_review_path")), packet.get("source_index_review_path"), "source index review must still exist"),
        _check("source_publication_file_exists", _path_exists(packet.get("source_publication_path")), packet.get("source_publication_path"), "source publication must still exist"),
        _check("source_publication_check_file_exists", _path_exists(packet.get("source_publication_check_path")), packet.get("source_publication_check_path"), "source publication contract check must still exist"),
        _check("source_review_file_exists", _path_exists(packet.get("source_review_path")), packet.get("source_review_path"), "source publication review must still exist"),
        _check("source_index_file_exists", _path_exists(packet.get("source_index_path")), packet.get("source_index_path"), "source publication index must still exist"),
        _check("consumer_boundary_governance", packet_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, packet_summary.get("consumer_boundary"), "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", packet_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, packet_summary.get("model_quality_claim"), "model quality claim must remain bounded"),
        _check("promotion_still_false", packet_summary.get("promotion_ready") is False and check_summary.get("original_promotion_ready") is False and check_summary.get("rebuilt_promotion_ready") is False, {"packet": packet_summary.get("promotion_ready"), "original": check_summary.get("original_promotion_ready"), "rebuilt": check_summary.get("rebuilt_promotion_ready")}, "receipt packet index must not enable promotion"),
        _check("source_packet_checks_clean", int(packet_summary.get("failed_check_count") or 0) == 0, packet_summary.get("failed_check_count"), "source receipt packet checks must be clean"),
        _check("source_contract_checks_clean", int(check_summary.get("failed_check_count") or 0) == 0, check_summary.get("failed_check_count"), "source contract checks must be clean"),
        _check("source_next_steps_match", packet_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_NEXT_STEP and check_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_NEXT_STEP, {"packet": packet_summary.get("next_step"), "check": check_summary.get("next_step")}, "source next steps must route to check then index"),
    ]


def _index(
    status: str,
    packet_summary: dict[str, Any],
    packet: dict[str, Any],
    check_summary: dict[str, Any],
    packet_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    packet_path: str | Path | None,
    check_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    index_rows = [
        {
            "receipt_packet_index_id": RECEIPT_PACKET_INDEX_ID if ready else "not_ready",
            "lookup_key": row.get("lookup_key"),
            "packet_id": packet_summary.get("packet_id"),
            "packet_status": packet_summary.get("packet_status"),
            "consumer_name": packet_summary.get("consumer_name"),
            "granted_use": downstream_lookup_use() if ready else "none",
            "source_packet_path": str(packet_path or ""),
            "source_packet_check_path": str(check_path or ""),
            "source_evidence_count": len(source_evidence_rows) if ready else 0,
            "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
            "promotion_ready": False,
        }
        for row in packet_rows
    ]
    return {
        "index_ready": ready,
        "receipt_packet_index_id": RECEIPT_PACKET_INDEX_ID if ready else "not_ready",
        "lookup_scope": downstream_lookup_use() if ready else "not_ready",
        "receipt_packet_index_rows": index_rows if ready else [],
        "source_packet_rows": packet_rows if ready else [],
        "source_evidence_rows": source_evidence_rows if ready else [],
        "source_evidence_count": len(source_evidence_rows) if ready else 0,
        "receipt_packet_path": str(packet_path or ""),
        "receipt_packet_check_path": str(check_path or ""),
        "consumer_name": packet_summary.get("consumer_name") if ready else "",
        "granted_use": downstream_lookup_use() if ready else "none",
        "lookup_ready": bool(ready and packet_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "source_next_step": check_summary.get("next_step") if ready else "not_ready",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index",
    }


def _summary(status: str, checks: list[dict[str, Any]], index: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_ready": status == "pass" and index.get("index_ready") is True,
        "receipt_packet_index_id": index.get("receipt_packet_index_id"),
        "lookup_scope": index.get("lookup_scope"),
        "consumer_name": index.get("consumer_name"),
        "granted_use": index.get("granted_use"),
        "receipt_packet_index_row_count": len(list(index.get("receipt_packet_index_rows") or [])),
        "source_evidence_count": index.get("source_evidence_count"),
        "lookup_ready": index.get("lookup_ready"),
        "contract_check_ready": index.get("contract_check_ready"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": index.get("consumer_boundary"),
        "model_quality_claim": index.get("model_quality_claim"),
        "next_step": index.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(str(path)).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index"


def _interpretation(status: str, index: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt packet and contract check are not ready for indexing.",
            "next_action": "repair receipt packet or contract check before index",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream publication receipt packet and contract check are packaged into a lookup-only index while promotion remains blocked.",
        "next_action": str(index.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check",
    "read_json_report",
    "resolve_exit_code",
]
