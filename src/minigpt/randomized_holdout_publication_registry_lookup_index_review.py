from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_lookup_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_JSON_FILENAME = "randomized_holdout_publication_registry_lookup_index_review.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_CSV_FILENAME = "randomized_holdout_publication_registry_lookup_index_review.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_TEXT_FILENAME = "randomized_holdout_publication_registry_lookup_index_review.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_lookup_index_review.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_HTML_FILENAME = "randomized_holdout_publication_registry_lookup_index_review.html"

REVIEW_ID = "randomized-holdout-publication-registry-lookup-index-review-v937"


def locate_randomized_holdout_publication_registry_lookup_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry lookup index review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_lookup_index_review(
    lookup_index_report: dict[str, Any],
    *,
    lookup_index_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry lookup index review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    index_summary = as_dict(lookup_index_report.get("summary"))
    lookup_index = as_dict(lookup_index_report.get("lookup_index"))
    entries = list_of_dicts(lookup_index.get("lookup_entries"))
    checks = _checks(lookup_index_report, index_summary, lookup_index, entries, lookup_index_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, index_summary, lookup_index, entries, lookup_index_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "lookup_index_path": str(lookup_index_path or ""),
        "source_lookup_index_summary": index_summary,
        "source_lookup_index": lookup_index,
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
    require_downstream_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("randomized_holdout_publication_registry_lookup_index_review_ready") is not True:
        return 1
    if require_downstream_ready and summary.get("downstream_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    index_report: dict[str, Any],
    index_summary: dict[str, Any],
    lookup_index: dict[str, Any],
    entries: list[dict[str, Any]],
    index_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = list(lookup_index.get("lookup_keys") or [])
    return [
        _check("lookup_index_file_exists", _path_exists(index_path), str(index_path or ""), "lookup index file must exist"),
        _check("lookup_index_passed", index_report.get("status") == "pass", index_report.get("status"), "lookup index must pass"),
        _check("lookup_index_decision_ready", index_report.get("decision") == "randomized_holdout_publication_registry_lookup_index_ready", index_report.get("decision"), "lookup index decision must be ready"),
        _check("lookup_index_summary_ready", index_summary.get("randomized_holdout_publication_registry_lookup_index_ready") is True and lookup_index.get("index_ready") is True, {"summary": index_summary.get("randomized_holdout_publication_registry_lookup_index_ready"), "index": lookup_index.get("index_ready")}, "lookup index summary and body must be ready"),
        _check("lookup_scope_governance", index_summary.get("lookup_scope") == "governance_lookup_only" and lookup_index.get("lookup_scope") == "governance_lookup_only", {"summary": index_summary.get("lookup_scope"), "index": lookup_index.get("lookup_scope")}, "lookup scope must remain governance only"),
        _check("lookup_ready", index_summary.get("lookup_ready") is True and lookup_index.get("lookup_ready") is True, {"summary": index_summary.get("lookup_ready"), "index": lookup_index.get("lookup_ready")}, "lookup index must be lookup-ready"),
        _check("contract_check_ready", index_summary.get("contract_check_ready") is True and lookup_index.get("contract_check_ready") is True, {"summary": index_summary.get("contract_check_ready"), "index": lookup_index.get("contract_check_ready")}, "lookup index must include a ready contract check"),
        _check("evidence_count", int(index_summary.get("evidence_count") or 0) >= 2 and int(lookup_index.get("evidence_count") or 0) >= 2, {"summary": index_summary.get("evidence_count"), "index": lookup_index.get("evidence_count")}, "lookup index must carry packet and check evidence"),
        _check("entries_present", int(index_summary.get("entry_count") or 0) > 0 and len(entries) == int(index_summary.get("entry_count") or 0), {"summary": index_summary.get("entry_count"), "entries": len(entries)}, "lookup index review requires entries"),
        _check("lookup_keys_present", len(lookup_keys) == len(entries) and all(str(key).startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must use the publication namespace"),
        _check("entries_not_promoted", all(row.get("promotion_ready") is False for row in entries), [row.get("promotion_ready") for row in entries], "lookup index review must not promote entries"),
        _check("consumer_boundary_governance", index_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and lookup_index.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": index_summary.get("consumer_boundary"), "index": lookup_index.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("rejected_use_production_promotion", index_summary.get("rejected_use") == "production_promotion" and lookup_index.get("rejected_use") == "production_promotion", {"summary": index_summary.get("rejected_use"), "index": lookup_index.get("rejected_use")}, "production promotion must stay rejected"),
        _check("promotion_still_false", index_summary.get("promotion_ready") is False and lookup_index.get("promotion_ready") is False, {"summary": index_summary.get("promotion_ready"), "index": lookup_index.get("promotion_ready")}, "lookup index review must not enable promotion"),
        _check("source_checks_clean", int(index_summary.get("failed_check_count") or 0) == 0, index_summary.get("failed_check_count"), "source lookup index checks must be clean"),
        _check("source_next_step_matches", index_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_NEXT_STEP, index_summary.get("next_step"), "source lookup index must route to review"),
    ]


def _review(
    status: str,
    index_summary: dict[str, Any],
    lookup_index: dict[str, Any],
    entries: list[dict[str, Any]],
    index_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_downstream_governance_lookup_only" if ready else "blocked",
        "lookup_index_path": str(index_path or ""),
        "entry_count": len(entries) if ready else 0,
        "lookup_keys": list(lookup_index.get("lookup_keys") or []) if ready else [],
        "downstream_ready": ready,
        "lookup_ready": bool(ready and index_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and index_summary.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "allowed_use": "downstream_governance_lookup_only" if ready else "none",
        "rejected_use": "production_promotion",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_lookup_index_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_lookup_index_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "entry_count": review.get("entry_count"),
        "downstream_ready": review.get("downstream_ready"),
        "lookup_ready": review.get("lookup_ready"),
        "contract_check_ready": review.get("contract_check_ready"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": review.get("consumer_boundary"),
        "allowed_use": review.get("allowed_use"),
        "rejected_use": review.get("rejected_use"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_lookup_index_review_ready"
    return "fix_randomized_holdout_publication_registry_lookup_index_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The lookup index is not ready for downstream governance lookup review.",
            "next_action": "repair lookup index before downstream review",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The lookup index is approved only for downstream governance lookup consumption; production promotion remains rejected.",
        "next_action": str(review.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_lookup_index_review",
    "locate_randomized_holdout_publication_registry_lookup_index",
    "read_json_report",
    "resolve_exit_code",
]
