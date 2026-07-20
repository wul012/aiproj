from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_CHECK_V996_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_V995_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import downstream_lookup_use, is_downstream_lookup_only, sha256_file
from minigpt.packet_chain_check_v996 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_CHECK_V996_JSON_FILENAME,
)
from minigpt.packet_chain_receipt_v995 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_V995_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_JSON_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.json"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_CSV_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_TEXT_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_MARKDOWN_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.md"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_HTML_FILENAME = "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.html"

RECEIPT_INDEX_ID = "randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-v997"


def locate_receipt_v997(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_V995_JSON_FILENAME
    return source


def locate_receipt_check_v997(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_CHECK_V996_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication index receipt index v997 input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997(
    receipt_report: dict[str, Any],
    receipt_check_report: dict[str, Any],
    *,
    receipt_path: str | Path | None = None,
    receipt_check_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index receipt index v997",
    generated_at: str | None = None,
) -> dict[str, Any]:
    receipt_summary = as_dict(receipt_report.get("summary"))
    receipt = as_dict(receipt_report.get("receipt"))
    check_summary = as_dict(receipt_check_report.get("summary"))
    checks = _checks(receipt_report, receipt_check_report, receipt_summary, receipt, check_summary, receipt_path, receipt_check_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    index = _index(status, receipt_summary, receipt, check_summary, receipt_path, receipt_check_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_path": str(receipt_path or ""),
        "receipt_check_path": str(receipt_check_path or ""),
        "source_receipt_summary": receipt_summary,
        "source_receipt_check_summary": check_summary,
        "receipt_index_rows": index.get("receipt_index_rows", []),
        "source_evidence_rows": index.get("source_evidence_rows", []),
        "check_rows": checks,
        "receipt_index": index,
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
    if require_index_ready and summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    receipt_report: dict[str, Any],
    receipt_check_report: dict[str, Any],
    receipt_summary: dict[str, Any],
    receipt: dict[str, Any],
    check_summary: dict[str, Any],
    receipt_path: str | Path | None,
    receipt_check_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("receipt_file_exists", _path_exists(receipt_path), str(receipt_path or ""), "receipt file must exist"),
        _check("receipt_check_file_exists", _path_exists(receipt_check_path), str(receipt_check_path or ""), "receipt contract check file must exist"),
        _check("receipt_passed", receipt_report.get("status") == "pass", receipt_report.get("status"), "receipt must pass"),
        _check("receipt_decision_ready", receipt_report.get("decision") == "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995_ready", receipt_report.get("decision"), "receipt decision must be ready"),
        _check("receipt_summary_ready", receipt_summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995_ready") is True and receipt.get("receipt_ready") is True, {"summary": receipt_summary.get("randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995_ready"), "receipt": receipt.get("receipt_ready")}, "receipt summary and body must be ready"),
        _check("receipt_status_ready", receipt_summary.get("receipt_status") == "publication_index_lookup_receipted" and receipt.get("receipt_status") == "publication_index_lookup_receipted", {"summary": receipt_summary.get("receipt_status"), "receipt": receipt.get("receipt_status")}, "receipt must be lookup receipted"),
        _check("receipt_check_passed", receipt_check_report.get("status") == "pass", receipt_check_report.get("status"), "receipt contract check must pass"),
        _check("receipt_check_decision_ready", receipt_check_report.get("decision") == "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_contract_check_v996_passed", receipt_check_report.get("decision"), "receipt contract check decision must pass"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "receipt contract check must be ready"),
        _check("receipt_status_matches_check", receipt_summary.get("receipt_status") == check_summary.get("original_receipt_status") == check_summary.get("rebuilt_receipt_status"), {"receipt": receipt_summary.get("receipt_status"), "original": check_summary.get("original_receipt_status"), "rebuilt": check_summary.get("rebuilt_receipt_status")}, "receipt status must match contract check"),
        _check("granted_use_lookup_only", is_downstream_lookup_only(receipt_summary.get("granted_use")) and is_downstream_lookup_only(receipt.get("granted_use")) and is_downstream_lookup_only(check_summary.get("original_granted_use")) and is_downstream_lookup_only(check_summary.get("rebuilt_granted_use")), {"summary": receipt_summary.get("granted_use"), "receipt": receipt.get("granted_use"), "original": check_summary.get("original_granted_use"), "rebuilt": check_summary.get("rebuilt_granted_use")}, "granted use must stay downstream lookup only"),
        _check("lookup_key_count", int(receipt_summary.get("lookup_key_count") or 0) == int(check_summary.get("original_lookup_key_count") or 0) == int(check_summary.get("rebuilt_lookup_key_count") or 0) == len(list(receipt.get("lookup_keys") or [])) == 1, {"summary": receipt_summary.get("lookup_key_count"), "original": check_summary.get("original_lookup_key_count"), "rebuilt": check_summary.get("rebuilt_lookup_key_count"), "receipt": len(list(receipt.get("lookup_keys") or []))}, "receipt index requires one lookup key"),
        _check("source_evidence_count", int(receipt_summary.get("source_evidence_count") or 0) == int(receipt.get("source_evidence_count") or 0) == 2, {"summary": receipt_summary.get("source_evidence_count"), "receipt": receipt.get("source_evidence_count")}, "receipt index requires two source evidence rows"),
        _check("source_review_file_exists", _path_exists(receipt.get("publication_index_review_path")), receipt.get("publication_index_review_path"), "source review must still exist"),
        _check("source_publication_file_exists", _path_exists(receipt.get("source_publication_path")), receipt.get("source_publication_path"), "source publication must still exist"),
        _check("source_publication_check_file_exists", _path_exists(receipt.get("source_publication_check_path")), receipt.get("source_publication_check_path"), "source publication check must still exist"),
        _check("consumer_boundary_governance", receipt_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and receipt.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": receipt_summary.get("consumer_boundary"), "receipt": receipt.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", receipt.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, receipt.get("model_quality_claim"), "model quality claim must remain bounded"),
        _check("promotion_still_false", receipt_summary.get("promotion_ready") is False and receipt_summary.get("approved_for_promotion") is False and receipt.get("promotion_ready") is False and receipt.get("approved_for_promotion") is False and check_summary.get("original_promotion_ready") is False and check_summary.get("rebuilt_promotion_ready") is False, {"summary": receipt_summary.get("promotion_ready"), "approved": receipt_summary.get("approved_for_promotion"), "receipt": receipt.get("promotion_ready"), "original": check_summary.get("original_promotion_ready"), "rebuilt": check_summary.get("rebuilt_promotion_ready")}, "receipt index must not enable promotion"),
        _check("source_receipt_checks_clean", int(receipt_summary.get("failed_check_count") or 0) == 0, receipt_summary.get("failed_check_count"), "source receipt checks must be clean"),
        _check("source_contract_checks_clean", int(check_summary.get("failed_check_count") or 0) == 0, check_summary.get("failed_check_count"), "source contract checks must be clean"),
        _check("source_next_steps_match", receipt_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_V995_NEXT_STEP and check_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_CHECK_V996_NEXT_STEP, {"receipt": receipt_summary.get("next_step"), "check": check_summary.get("next_step")}, "source next steps must route to check then index"),
    ]


def _index(
    status: str,
    receipt_summary: dict[str, Any],
    receipt: dict[str, Any],
    check_summary: dict[str, Any],
    receipt_path: str | Path | None,
    receipt_check_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    lookup_key = f"publication-index-receipt:{receipt_summary.get('receipt_id') or 'not-ready'}"
    index_rows = [
        {
            "receipt_index_id": RECEIPT_INDEX_ID,
            "lookup_key": lookup_key,
            "receipt_id": receipt_summary.get("receipt_id"),
            "receipt_status": receipt_summary.get("receipt_status"),
            "granted_use": downstream_lookup_use(),
            "source_receipt_path": str(receipt_path or ""),
            "source_receipt_check_path": str(receipt_check_path or ""),
            "source_review_path": receipt.get("publication_index_review_path"),
            "contract_check_ready": bool(check_summary.get("contract_check_ready") is True),
            "promotion_ready": False,
        }
    ] if ready else []
    evidence_rows = _source_evidence_rows(receipt_path, receipt_check_path, receipt_status=receipt_summary.get("receipt_status"), check_status=check_summary.get("contract_check_ready"))
    return {
        "index_ready": ready,
        "receipt_index_id": RECEIPT_INDEX_ID if ready else "not_ready",
        "lookup_scope": downstream_lookup_use() if ready else "not_ready",
        "lookup_key_count": len(index_rows),
        "receipt_index_rows": index_rows,
        "source_evidence_rows": evidence_rows if ready else [],
        "source_evidence_count": len(evidence_rows) if ready else 0,
        "receipt_path": str(receipt_path or ""),
        "receipt_check_path": str(receipt_check_path or ""),
        "receipt_id": receipt_summary.get("receipt_id") if ready else "",
        "receipt_status": receipt_summary.get("receipt_status") if ready else "",
        "granted_use": downstream_lookup_use() if ready else "none",
        "lookup_ready": bool(ready and receipt_summary.get("lookup_key_count") == 1),
        "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "source_next_step": check_summary.get("next_step") if ready else "not_ready",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_NEXT_STEP if ready else "repair_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997",
    }


def _source_evidence_rows(
    receipt_path: str | Path | None,
    receipt_check_path: str | Path | None,
    *,
    receipt_status: Any,
    check_status: Any,
) -> list[dict[str, Any]]:
    return [_evidence_row("receipt", receipt_path, receipt_status), _evidence_row("receipt_check", receipt_check_path, check_status)]


def _evidence_row(kind: str, path: str | Path | None, status: Any) -> dict[str, Any]:
    return {"kind": kind, "path": str(path or ""), "sha256": sha256_file(path), "status": "pass" if status else "fail"}


def _summary(status: str, checks: list[dict[str, Any]], index: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997_ready": status == "pass" and index.get("index_ready") is True,
        "receipt_index_id": index.get("receipt_index_id"),
        "lookup_scope": index.get("lookup_scope"),
        "lookup_key_count": index.get("lookup_key_count"),
        "receipt_id": index.get("receipt_id"),
        "receipt_status": index.get("receipt_status"),
        "granted_use": index.get("granted_use"),
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
        return "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997_ready"
    return "fix_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997"


def _interpretation(status: str, index: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "The lookup-only receipt and its contract check are not ready for indexing.", "next_action": "repair receipt or contract check before index"}
    return {"model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, "reason": "The lookup-only receipt and contract check are packaged into a receipt index while production promotion remains blocked.", "next_action": str(index.get("next_step"))}


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_V997_TEXT_FILENAME",
    "build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997",
    "locate_receipt_check_v997",
    "locate_receipt_v997",
    "read_json_report",
    "resolve_exit_code",
]
