from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt import (
    BLOCKED_USES,
    GRANTED_SCOPE,
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_JSON_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_CSV_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_TEXT_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_MARKDOWN_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_HTML_FILENAME = "model_capability_route_promotion_release_readiness_receipt_index.html"

READY_RECEIPT_DECISION = "model_capability_route_promotion_release_readiness_downstream_receipt_granted"
RECEIPT_NEXT_STEP = "index_checked_route_promotion_release_readiness_receipt"
INDEX_ID = "route-promotion-release-readiness-receipt-index-v1258"
LOOKUP_SCOPE = "bounded_route_promotion_release_readiness_receipt_lookup_only"
INDEX_NEXT_STEP = "review_indexed_route_promotion_release_readiness_receipt"


def locate_route_promotion_release_readiness_downstream_receipt(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion release readiness receipt index input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_release_readiness_receipt_index(
    downstream_receipt_report: dict[str, Any],
    *,
    downstream_receipt_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion release readiness receipt index",
    generated_at: str | None = None,
) -> dict[str, Any]:
    receipt_summary = as_dict(downstream_receipt_report.get("summary"))
    receipt = as_dict(downstream_receipt_report.get("receipt"))
    source_digest_rows = list_of_dicts(receipt.get("source_digest_rows"))
    check_rows = _check_rows(downstream_receipt_report, receipt_summary, receipt, source_digest_rows, downstream_receipt_path, required_boundary)
    issues = [row for row in check_rows if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    index = _index(status, receipt, source_digest_rows, downstream_receipt_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "downstream_receipt_path": str(downstream_receipt_path or ""),
        "downstream_receipt_digest": _sha256_or_empty(downstream_receipt_path),
        "source_downstream_receipt_summary": receipt_summary,
        "source_downstream_receipt": receipt,
        "source_digest_rows": source_digest_rows,
        "check_rows": check_rows,
        "receipt_index": index,
        "summary": _summary(status, check_rows, index),
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
    if require_index_ready and summary.get("receipt_index_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _check_rows(
    downstream_receipt_report: dict[str, Any],
    receipt_summary: dict[str, Any],
    receipt: dict[str, Any],
    source_digest_rows: list[dict[str, Any]],
    receipt_path: str | Path | None,
    required_boundary: str,
) -> list[dict[str, Any]]:
    source_check_rows = list_of_dicts(downstream_receipt_report.get("check_rows"))
    blocked_uses = list(receipt.get("blocked_uses") or [])
    return [
        _check("downstream_receipt_file_exists", _path_exists(receipt_path), str(receipt_path or ""), "downstream receipt file must exist"),
        _check("downstream_receipt_passed", downstream_receipt_report.get("status") == "pass", downstream_receipt_report.get("status"), "downstream receipt report must pass"),
        _check("downstream_receipt_decision_granted", downstream_receipt_report.get("decision") == READY_RECEIPT_DECISION, downstream_receipt_report.get("decision"), "downstream receipt decision must be granted"),
        _check("downstream_receipt_ready", receipt_summary.get("downstream_receipt_ready") is True, receipt_summary.get("downstream_receipt_ready"), "downstream receipt summary must be ready"),
        _check("receipt_status_granted", receipt.get("receipt_status") == "granted", receipt.get("receipt_status"), "receipt body must be granted"),
        _check("consumer_name_present", bool(str(receipt.get("consumer_name") or "").strip()), receipt.get("consumer_name"), "receipt index requires a consumer name"),
        _check("route_id_present", bool(str(receipt.get("route_id") or "").strip()), receipt.get("route_id"), "receipt index requires a route id"),
        _check("granted_scope_bounded", receipt.get("granted_scope") == GRANTED_SCOPE, receipt.get("granted_scope"), "receipt granted scope must remain bounded route-promotion release governance only"),
        _check("boundary_required", receipt.get("boundary") == required_boundary, receipt.get("boundary"), "receipt boundary must match the required boundary"),
        _check("claim_bounded", str(receipt.get("model_quality_claim") or "").startswith("seed_stable_pair_probe_route"), receipt.get("model_quality_claim"), "receipt model quality claim must remain pair-probe scoped"),
        _check("source_check_digest_present", bool(receipt.get("source_check_digest")), receipt.get("source_check_digest"), "receipt must carry the checked-summary digest"),
        _check("downstream_receipt_digest_present", bool(_sha256_or_empty(receipt_path)), _sha256_or_empty(receipt_path), "receipt index must digest the downstream receipt file"),
        _check("source_digest_count_matches", int(receipt.get("source_digest_count") or 0) == len(source_digest_rows), {"receipt": receipt.get("source_digest_count"), "actual": len(source_digest_rows)}, "source digest count must match digest rows"),
        _check("source_digests_present", all(row.get("sha256") for row in source_digest_rows), source_digest_rows, "all upstream source digest rows must carry SHA-256"),
        _check("blocked_uses_complete", set(blocked_uses) == set(BLOCKED_USES), blocked_uses, "receipt index must preserve the complete blocked-use list"),
        _check("source_receipt_checks_clean", int(downstream_receipt_report.get("failed_count") or 0) == 0 and all(row.get("status") == "pass" for row in source_check_rows), {"failed_count": downstream_receipt_report.get("failed_count"), "row_failures": _failed_ids(source_check_rows)}, "source downstream receipt checks must be clean"),
        _check("source_next_step_matches", receipt.get("next_step") == RECEIPT_NEXT_STEP and receipt_summary.get("next_step") == RECEIPT_NEXT_STEP, {"receipt": receipt.get("next_step"), "summary": receipt_summary.get("next_step")}, "source receipt must route to receipt indexing"),
    ]


def _index(
    status: str,
    receipt: dict[str, Any],
    source_digest_rows: list[dict[str, Any]],
    receipt_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    lookup_key = f"route-promotion-release-readiness:{receipt.get('route_id', '')}"
    row = {
        "lookup_key": lookup_key,
        "entry_id": receipt.get("receipt_id"),
        "consumer_name": receipt.get("consumer_name"),
        "route_id": receipt.get("route_id"),
        "granted_scope": receipt.get("granted_scope"),
        "boundary": receipt.get("boundary"),
        "model_quality_claim": receipt.get("model_quality_claim"),
        "source_check_digest": receipt.get("source_check_digest"),
        "downstream_receipt_digest": _sha256_or_empty(receipt_path),
        "source_digest_count": receipt.get("source_digest_count"),
        "blocked_uses": receipt.get("blocked_uses"),
        "promotion_ready": False,
        "lookup_ready": ready,
    }
    rows = [row] if ready else []
    return {
        "index_ready": ready,
        "index_id": INDEX_ID if ready else "not_ready",
        "lookup_scope": LOOKUP_SCOPE if ready else "not_ready",
        "downstream_receipt_path": str(receipt_path or ""),
        "downstream_receipt_digest": _sha256_or_empty(receipt_path),
        "entry_count": len(rows),
        "index_rows": rows,
        "lookup_keys": [lookup_key] if ready else [],
        "lookup_ready": ready,
        "consumer_name": receipt.get("consumer_name") if ready else "",
        "route_id": receipt.get("route_id") if ready else "",
        "granted_scope": receipt.get("granted_scope") if ready else "none",
        "boundary": receipt.get("boundary") if ready else "",
        "model_quality_claim": receipt.get("model_quality_claim") if ready else "not_claimed",
        "source_check_digest": receipt.get("source_check_digest") if ready else "",
        "source_digest_count": receipt.get("source_digest_count") if ready else 0,
        "source_digest_rows": source_digest_rows if ready else [],
        "blocked_uses": list(receipt.get("blocked_uses") or BLOCKED_USES),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "evidence_count": 2 if ready else 0,
        "next_step": INDEX_NEXT_STEP if ready else "repair_route_promotion_release_readiness_receipt_index",
    }


def _summary(status: str, check_rows: list[dict[str, Any]], index: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_index_ready": status == "pass" and index.get("index_ready") is True,
        "index_id": index.get("index_id"),
        "lookup_scope": index.get("lookup_scope"),
        "entry_count": index.get("entry_count"),
        "lookup_key_count": len(list(index.get("lookup_keys") or [])),
        "lookup_ready": index.get("lookup_ready"),
        "consumer_name": index.get("consumer_name"),
        "route_id": index.get("route_id"),
        "granted_scope": index.get("granted_scope"),
        "boundary": index.get("boundary"),
        "model_quality_claim": index.get("model_quality_claim"),
        "source_digest_count": index.get("source_digest_count"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "blocked_uses": index.get("blocked_uses"),
        "evidence_count": index.get("evidence_count"),
        "next_step": index.get("next_step"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _interpretation(status: str, index: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream receipt cannot be indexed for bounded route-promotion release readiness lookup.",
            "next_action": "repair the downstream receipt before index publication",
        }
    return {
        "model_quality_claim": index.get("model_quality_claim"),
        "reason": "The granted downstream receipt is indexed for bounded route-promotion release readiness lookup only.",
        "next_action": index.get("next_step"),
    }


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(path).exists()


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


def _failed_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("id")) for row in rows if row.get("status") != "pass"]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_release_readiness_receipt_index_ready"
    return "fix_model_capability_route_promotion_release_readiness_receipt_index"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_RECEIPT_INDEX_TEXT_FILENAME",
    "build_model_capability_route_promotion_release_readiness_receipt_index",
    "locate_route_promotion_release_readiness_downstream_receipt",
    "read_json_report",
    "resolve_exit_code",
]
