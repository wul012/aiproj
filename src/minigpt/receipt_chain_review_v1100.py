from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1097_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import is_downstream_lookup_only
from minigpt.receipt_chain_v1097 import (
    LOOKUP_KEY_PREFIX,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1097_JSON_FILENAME,
    READY_KEY as SOURCE_INDEX_READY_KEY,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_JSON_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100.json"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_CSV_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_TEXT_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_MARKDOWN_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100.md"
RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_HTML_FILENAME = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100.html"

READY_KEY = "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100_ready"
REVIEW_ID = "randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-review-v1100"
REVIEW_STATUS = "approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only"


def locate_receipt_index_v1100(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1097_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index review v1100 input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100(
    index_report: dict[str, Any],
    *,
    receipt_index_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index review v1100",
    generated_at: str | None = None,
) -> dict[str, Any]:
    index_summary = as_dict(index_report.get("summary"))
    receipt_index = as_dict(index_report.get("receipt_index"))
    index_rows = list_of_dicts(index_report.get("receipt_index_rows"))
    source_evidence_rows = list_of_dicts(index_report.get("source_evidence_rows"))
    checks = _checks(index_report, index_summary, receipt_index, index_rows, source_evidence_rows, receipt_index_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, index_summary, receipt_index, index_rows, source_evidence_rows, receipt_index_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "receipt_index_path": str(receipt_index_path or ""),
        "source_receipt_index_summary": index_summary,
        "source_receipt_index": receipt_index,
        "receipt_index_rows": index_rows if status == "pass" else [],
        "source_evidence_rows": source_evidence_rows if status == "pass" else [],
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get(READY_KEY) is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    index_report: dict[str, Any],
    index_summary: dict[str, Any],
    receipt_index: dict[str, Any],
    index_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = [str(row.get("lookup_key")) for row in index_rows]
    row_receipt_paths = [row.get("source_receipt_path") for row in index_rows]
    row_check_paths = [row.get("source_receipt_check_path") for row in index_rows]
    row_review_paths = [row.get("source_review_path") for row in index_rows]
    row_index_paths = [row.get("source_receipt_index_path") for row in index_rows]
    return [
        _check("receipt_index_file_exists", _path_exists(index_path), str(index_path or ""), "receipt index file must exist"),
        _check("receipt_index_passed", index_report.get("status") == "pass", index_report.get("status"), "receipt index must pass"),
        _check("receipt_index_decision_ready", index_report.get("decision") == "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_ready", index_report.get("decision"), "receipt index decision must be ready"),
        _check("receipt_index_summary_ready", index_summary.get(SOURCE_INDEX_READY_KEY) is True and receipt_index.get("index_ready") is True, {"summary": index_summary.get(SOURCE_INDEX_READY_KEY), "index": receipt_index.get("index_ready")}, "receipt index summary and body must be ready"),
        _check("lookup_scope_downstream", is_downstream_lookup_only(index_summary.get("lookup_scope")) and is_downstream_lookup_only(receipt_index.get("lookup_scope")), {"summary": index_summary.get("lookup_scope"), "index": receipt_index.get("lookup_scope")}, "lookup scope must remain downstream governance lookup only"),
        _check("granted_use_lookup_only", is_downstream_lookup_only(index_summary.get("granted_use")) and is_downstream_lookup_only(receipt_index.get("granted_use")), {"summary": index_summary.get("granted_use"), "index": receipt_index.get("granted_use")}, "granted use must stay downstream lookup only"),
        _check("lookup_ready", index_summary.get("lookup_ready") is True and receipt_index.get("lookup_ready") is True, {"summary": index_summary.get("lookup_ready"), "index": receipt_index.get("lookup_ready")}, "receipt index must be lookup-ready"),
        _check("contract_check_ready", index_summary.get("contract_check_ready") is True and receipt_index.get("contract_check_ready") is True, {"summary": index_summary.get("contract_check_ready"), "index": receipt_index.get("contract_check_ready")}, "receipt index must include a ready contract check"),
        _check("receipt_index_rows_present", len(index_rows) == int(index_summary.get("lookup_key_count") or 0) == 1, {"rows": len(index_rows), "summary": index_summary.get("lookup_key_count")}, "review requires one receipt index row"),
        _check("lookup_keys_present", len(lookup_keys) == 1 and all(key.startswith(LOOKUP_KEY_PREFIX) for key in lookup_keys), lookup_keys, "lookup keys must use the v1097 receipt-index namespace"),
        _check("source_evidence_count", int(index_summary.get("source_evidence_count") or 0) == 2 and len(source_evidence_rows) == 2, {"summary": index_summary.get("source_evidence_count"), "rows": len(source_evidence_rows)}, "review requires two source evidence rows"),
        _check("source_evidence_digests_present", all(row.get("sha256") for row in source_evidence_rows), [row.get("sha256") for row in source_evidence_rows], "source evidence digests must be present"),
        _check("source_evidence_status_pass", all(row.get("status") == "pass" for row in source_evidence_rows), [row.get("status") for row in source_evidence_rows], "source evidence rows must pass"),
        _check("source_receipt_file_exists", _path_exists(receipt_index.get("receipt_path")) and all(_path_exists(path) for path in row_receipt_paths), {"index": receipt_index.get("receipt_path"), "rows": row_receipt_paths}, "source receipt must still exist"),
        _check("source_receipt_check_file_exists", _path_exists(receipt_index.get("receipt_check_path")) and all(_path_exists(path) for path in row_check_paths), {"index": receipt_index.get("receipt_check_path"), "rows": row_check_paths}, "source receipt contract check must still exist"),
        _check("source_review_file_exists", all(_path_exists(path) for path in row_review_paths), row_review_paths, "source review must still exist"),
        _check("source_receipt_index_file_exists", all(_path_exists(path) for path in row_index_paths), row_index_paths, "source receipt index must still exist"),
        _check("consumer_boundary_governance", index_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and receipt_index.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": index_summary.get("consumer_boundary"), "index": receipt_index.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", index_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and receipt_index.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": index_summary.get("model_quality_claim"), "index": receipt_index.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("promotion_still_false", index_summary.get("promotion_ready") is False and receipt_index.get("promotion_ready") is False and receipt_index.get("approved_for_promotion") is False, {"summary": index_summary.get("promotion_ready"), "index": receipt_index.get("promotion_ready"), "approved": receipt_index.get("approved_for_promotion")}, "receipt index review must not enable promotion"),
        _check("source_checks_clean", int(index_summary.get("failed_check_count") or 0) == 0, index_summary.get("failed_check_count"), "source receipt index checks must be clean"),
        _check("source_next_step_matches", index_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1097_NEXT_STEP, index_summary.get("next_step"), "source receipt index must route to review"),
    ]


def _review(
    status: str,
    index_summary: dict[str, Any],
    receipt_index: dict[str, Any],
    index_rows: list[dict[str, Any]],
    source_evidence_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": REVIEW_STATUS if ready else "blocked",
        "receipt_index_path": str(index_path or ""),
        "receipt_index_id": index_summary.get("receipt_index_id") if ready else "",
        "receipt_index_row_count": len(index_rows) if ready else 0,
        "lookup_keys": [row.get("lookup_key") for row in index_rows] if ready else [],
        "source_evidence_count": len(source_evidence_rows) if ready else 0,
        "lookup_ready": bool(ready and index_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and index_summary.get("contract_check_ready") is True),
        "granted_use": index_summary.get("granted_use") if ready else "none",
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "source_receipt_path": receipt_index.get("receipt_path") if ready else "",
        "source_receipt_check_path": receipt_index.get("receipt_check_path") if ready else "",
        "source_review_path": index_rows[0].get("source_review_path") if ready and index_rows else "",
        "source_receipt_index_path": index_rows[0].get("source_receipt_index_path") if ready and index_rows else "",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_NEXT_STEP if ready else "repair_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        READY_KEY: status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "receipt_index_ready": review.get("review_ready"),
        "receipt_index_row_count": review.get("receipt_index_row_count"),
        "lookup_key_count": len(list(review.get("lookup_keys") or [])),
        "source_evidence_count": review.get("source_evidence_count"),
        "lookup_ready": review.get("lookup_ready"),
        "contract_check_ready": review.get("contract_check_ready"),
        "granted_use": review.get("granted_use"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": review.get("consumer_boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(str(path)).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100_ready"
    return "fix_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "The receipt index is not ready for lookup-only receipt recording.", "next_action": "repair receipt index before recording receipt"}
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The receipt index is approved only for lookup-only receipt recording; production promotion remains blocked.",
        "next_action": str(review.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1100_TEXT_FILENAME",
    "READY_KEY",
    "REVIEW_STATUS",
    "build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100",
    "locate_receipt_index_v1100",
    "read_json_report",
    "resolve_exit_code",
]
