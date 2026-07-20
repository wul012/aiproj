from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import downstream_lookup_use, is_downstream_lookup_only
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_JSON_FILENAME,
)
from minigpt.registry_ack_pub_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.html"

PUBLICATION_INDEX_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-index-v971"


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_JSON_FILENAME
    return source


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index(
    publication_report: dict[str, Any],
    publication_check_report: dict[str, Any],
    *,
    publication_path: str | Path | None = None,
    publication_check_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index",
    generated_at: str | None = None,
) -> dict[str, Any]:
    publication_summary = as_dict(publication_report.get("summary"))
    publication = as_dict(publication_report.get("publication"))
    check_summary = as_dict(publication_check_report.get("summary"))
    checks = _checks(publication_report, publication_check_report, publication_summary, publication, check_summary, publication_path, publication_check_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    index = _index(status, publication_summary, publication, check_summary, publication_path, publication_check_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "publication_path": str(publication_path or ""),
        "publication_check_path": str(publication_check_path or ""),
        "source_publication_summary": publication_summary,
        "source_publication_check_summary": check_summary,
        "publication_index_rows": index.get("publication_index_rows", []),
        "check_rows": checks,
        "publication_index": index,
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
    if require_index_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    publication_report: dict[str, Any],
    check_report: dict[str, Any],
    publication_summary: dict[str, Any],
    publication: dict[str, Any],
    check_summary: dict[str, Any],
    publication_path: str | Path | None,
    check_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("publication_file_exists", _path_exists(publication_path), str(publication_path or ""), "publication file must exist"),
        _check("publication_check_file_exists", _path_exists(check_path), str(check_path or ""), "publication contract check file must exist"),
        _check("publication_passed", publication_report.get("status") == "pass", publication_report.get("status"), "publication must pass"),
        _check("publication_decision_ready", publication_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready", publication_report.get("decision"), "publication decision must be ready"),
        _check("publication_summary_ready", publication_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready") is True and publication.get("publication_ready") is True, {"summary": publication_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready"), "publication": publication.get("publication_ready")}, "publication summary and body must be ready"),
        _check("publication_check_passed", check_report.get("status") == "pass", check_report.get("status"), "publication contract check must pass"),
        _check("publication_check_decision_ready", check_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_contract_check_passed", check_report.get("decision"), "publication contract check decision must pass"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "publication contract check must be ready"),
        _check("publication_status_matches_check", publication_summary.get("publication_status") == check_summary.get("original_publication_status") == check_summary.get("rebuilt_publication_status"), {"publication": publication_summary.get("publication_status"), "original": check_summary.get("original_publication_status"), "rebuilt": check_summary.get("rebuilt_publication_status")}, "publication status must match check"),
        _check("published_use_lookup_only", is_downstream_lookup_only(publication_summary.get("published_use")) and is_downstream_lookup_only(check_summary.get("original_published_use")) and is_downstream_lookup_only(check_summary.get("rebuilt_published_use")), {"publication": publication_summary.get("published_use"), "original": check_summary.get("original_published_use"), "rebuilt": check_summary.get("rebuilt_published_use")}, "published use must stay downstream lookup only"),
        _check("lookup_ready", publication_summary.get("lookup_ready") is True, publication_summary.get("lookup_ready"), "publication index requires lookup-ready publication"),
        _check("receipt_packet_index_row_count", int(publication_summary.get("receipt_packet_index_row_count") or 0) == int(check_summary.get("original_receipt_packet_index_row_count") or 0) == int(check_summary.get("rebuilt_receipt_packet_index_row_count") or 0) == 1, {"publication": publication_summary.get("receipt_packet_index_row_count"), "original": check_summary.get("original_receipt_packet_index_row_count"), "rebuilt": check_summary.get("rebuilt_receipt_packet_index_row_count")}, "publication index requires one receipt packet index row"),
        _check("source_packet_row_count", int(publication_summary.get("source_packet_row_count") or 0) == int(check_summary.get("original_source_packet_row_count") or 0) == int(check_summary.get("rebuilt_source_packet_row_count") or 0) == 1, {"publication": publication_summary.get("source_packet_row_count"), "original": check_summary.get("original_source_packet_row_count"), "rebuilt": check_summary.get("rebuilt_source_packet_row_count")}, "publication index requires one source packet row"),
        _check("source_evidence_count", int(publication_summary.get("source_evidence_count") or 0) == 2, publication_summary.get("source_evidence_count"), "publication index requires two source evidence rows"),
        _check("source_review_file_exists", _path_exists(publication.get("receipt_packet_index_review_path")), publication.get("receipt_packet_index_review_path"), "source review must still exist"),
        _check("source_index_file_exists", _path_exists(publication.get("receipt_packet_index_path")), publication.get("receipt_packet_index_path"), "source receipt packet index must still exist"),
        _check("source_packet_file_exists", _path_exists(publication.get("source_packet_path")), publication.get("source_packet_path"), "source receipt packet must still exist"),
        _check("source_packet_check_file_exists", _path_exists(publication.get("source_packet_check_path")), publication.get("source_packet_check_path"), "source receipt packet check must still exist"),
        _check("consumer_boundary_governance", publication_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, publication_summary.get("consumer_boundary"), "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", publication_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, publication_summary.get("model_quality_claim"), "model quality claim must remain bounded"),
        _check("promotion_still_false", publication_summary.get("promotion_ready") is False and check_summary.get("original_promotion_ready") is False and check_summary.get("rebuilt_promotion_ready") is False, {"publication": publication_summary.get("promotion_ready"), "original": check_summary.get("original_promotion_ready"), "rebuilt": check_summary.get("rebuilt_promotion_ready")}, "publication index must not enable promotion"),
        _check("source_publication_checks_clean", int(publication_summary.get("failed_check_count") or 0) == 0, publication_summary.get("failed_check_count"), "source publication checks must be clean"),
        _check("source_contract_checks_clean", int(check_summary.get("failed_check_count") or 0) == 0, check_summary.get("failed_check_count"), "source contract checks must be clean"),
        _check("source_next_steps_match", publication_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_NEXT_STEP and check_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_NEXT_STEP, {"publication": publication_summary.get("next_step"), "check": check_summary.get("next_step")}, "source next steps must route to check then index"),
    ]


def _index(
    status: str,
    publication_summary: dict[str, Any],
    publication: dict[str, Any],
    check_summary: dict[str, Any],
    publication_path: str | Path | None,
    check_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    publication_id = publication_summary.get("publication_id")
    rows = [
        {
            "publication_index_id": PUBLICATION_INDEX_ID if ready else "not_ready",
            "lookup_key": f"publication:{publication_id}",
            "publication_id": publication_id,
            "publication_status": publication_summary.get("publication_status"),
            "consumer_name": publication_summary.get("consumer_name"),
            "published_use": downstream_lookup_use() if ready else "none",
            "source_publication_path": str(publication_path or ""),
            "source_publication_check_path": str(check_path or ""),
            "receipt_packet_index_row_count": publication_summary.get("receipt_packet_index_row_count"),
            "source_packet_row_count": publication_summary.get("source_packet_row_count"),
            "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
            "promotion_ready": False,
        }
    ]
    return {
        "index_ready": ready,
        "publication_index_id": PUBLICATION_INDEX_ID if ready else "not_ready",
        "lookup_scope": downstream_lookup_use() if ready else "not_ready",
        "publication_index_rows": rows if ready else [],
        "publication_path": str(publication_path or ""),
        "publication_check_path": str(check_path or ""),
        "source_review_path": publication.get("receipt_packet_index_review_path") if ready else "",
        "source_index_path": publication.get("receipt_packet_index_path") if ready else "",
        "consumer_name": publication_summary.get("consumer_name") if ready else "",
        "published_use": downstream_lookup_use() if ready else "none",
        "lookup_ready": bool(ready and publication_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index",
    }


def _summary(status: str, checks: list[dict[str, Any]], index: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_ready": status == "pass" and index.get("index_ready") is True,
        "publication_index_id": index.get("publication_index_id"),
        "lookup_scope": index.get("lookup_scope"),
        "consumer_name": index.get("consumer_name"),
        "published_use": index.get("published_use"),
        "publication_index_row_count": len(list(index.get("publication_index_rows") or [])),
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
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index"


def _interpretation(status: str, index: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream publication receipt packet index publication and contract check are not ready for indexing.",
            "next_action": "repair publication or contract check before index",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream publication receipt packet index publication and contract check are packaged into a lookup-only index while promotion remains blocked.",
        "next_action": str(index.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check",
    "read_json_report",
    "resolve_exit_code",
]
