from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import blocked_uses, blocked_uses_complete, downstream_lookup_use, is_downstream_lookup_only
from minigpt.randomized_holdout_publication_registry_downstream_consumer_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index_review.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index_review.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index_review.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index_review.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index_review.html"

REVIEW_ID = "randomized-holdout-publication-registry-downstream-consumer-index-review-v944"


def locate_randomized_holdout_publication_registry_downstream_consumer_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer index review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_index_review(
    consumer_index_report: dict[str, Any],
    *,
    consumer_index_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer index review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    index_summary = as_dict(consumer_index_report.get("summary"))
    consumer_index = as_dict(consumer_index_report.get("consumer_index"))
    lookup_rows = list_of_dicts(consumer_index.get("packet_rows"))
    checks = _checks(consumer_index_report, index_summary, consumer_index, lookup_rows, consumer_index_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, index_summary, consumer_index, lookup_rows, consumer_index_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "consumer_index_path": str(consumer_index_path or ""),
        "source_consumer_index_summary": index_summary,
        "source_consumer_index": consumer_index,
        "lookup_rows": lookup_rows,
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
    if require_review_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_index_review_ready") is not True:
        return 1
    if require_downstream_ready and summary.get("downstream_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    index_report: dict[str, Any],
    index_summary: dict[str, Any],
    consumer_index: dict[str, Any],
    lookup_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = list(consumer_index.get("lookup_keys") or [])
    source_packet = consumer_index.get("consumer_packet_path")
    source_packet_check = consumer_index.get("consumer_packet_check_path")
    return [
        _check("consumer_index_file_exists", _path_exists(index_path), str(index_path or ""), "consumer index file must exist"),
        _check("consumer_index_passed", index_report.get("status") == "pass", index_report.get("status"), "consumer index must pass"),
        _check("consumer_index_decision_ready", index_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_index_ready", index_report.get("decision"), "consumer index decision must be ready"),
        _check("consumer_index_summary_ready", index_summary.get("randomized_holdout_publication_registry_downstream_consumer_index_ready") is True and consumer_index.get("index_ready") is True, {"summary": index_summary.get("randomized_holdout_publication_registry_downstream_consumer_index_ready"), "index": consumer_index.get("index_ready")}, "consumer index summary and body must be ready"),
        _check("lookup_scope_downstream", is_downstream_lookup_only(index_summary.get("lookup_scope")) and is_downstream_lookup_only(consumer_index.get("lookup_scope")), {"summary": index_summary.get("lookup_scope"), "index": consumer_index.get("lookup_scope")}, "lookup scope must remain downstream governance lookup only"),
        _check("lookup_ready", index_summary.get("lookup_ready") is True and consumer_index.get("lookup_ready") is True, {"summary": index_summary.get("lookup_ready"), "index": consumer_index.get("lookup_ready")}, "consumer index must be lookup-ready"),
        _check("contract_check_ready", index_summary.get("contract_check_ready") is True and consumer_index.get("contract_check_ready") is True, {"summary": index_summary.get("contract_check_ready"), "index": consumer_index.get("contract_check_ready")}, "consumer index must include a ready contract check"),
        _check("evidence_count", int(index_summary.get("evidence_count") or 0) >= 2 and int(consumer_index.get("evidence_count") or 0) >= 2, {"summary": index_summary.get("evidence_count"), "index": consumer_index.get("evidence_count")}, "consumer index must carry packet and check evidence"),
        _check("lookup_rows_present", len(lookup_rows) == int(index_summary.get("entry_count") or 0) and len(lookup_rows) > 0, {"lookup_rows": len(lookup_rows), "entry_count": index_summary.get("entry_count")}, "consumer index review requires lookup rows"),
        _check("lookup_keys_present", len(lookup_keys) == len(lookup_rows) and all(str(key).startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must use the publication namespace"),
        _check("lookup_rows_not_promoted", all(row.get("promotion_ready") is False for row in lookup_rows), [row.get("promotion_ready") for row in lookup_rows], "consumer index review must not promote rows"),
        _check("granted_use_lookup_only", is_downstream_lookup_only(index_summary.get("granted_use")) and is_downstream_lookup_only(consumer_index.get("granted_use")), {"summary": index_summary.get("granted_use"), "index": consumer_index.get("granted_use")}, "granted use must stay downstream lookup only"),
        _check("blocked_uses_complete", blocked_uses_complete(index_summary.get("blocked_uses")) and blocked_uses_complete(consumer_index.get("blocked_uses")), {"summary": index_summary.get("blocked_uses"), "index": consumer_index.get("blocked_uses")}, "blocked uses must remain complete"),
        _check("consumer_boundary_governance", index_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and consumer_index.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": index_summary.get("consumer_boundary"), "index": consumer_index.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", index_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and consumer_index.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": index_summary.get("model_quality_claim"), "index": consumer_index.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("source_packet_file_exists", _path_exists(source_packet), source_packet, "source consumer packet must still exist"),
        _check("source_packet_check_file_exists", _path_exists(source_packet_check), source_packet_check, "source consumer packet check must still exist"),
        _check("promotion_still_false", index_summary.get("promotion_ready") is False and consumer_index.get("promotion_ready") is False and consumer_index.get("approved_for_promotion") is False, {"summary": index_summary.get("promotion_ready"), "index": consumer_index.get("promotion_ready"), "approved": consumer_index.get("approved_for_promotion")}, "consumer index review must not enable promotion"),
        _check("source_checks_clean", int(index_summary.get("failed_check_count") or 0) == 0, index_summary.get("failed_check_count"), "source consumer index checks must be clean"),
        _check("source_next_step_matches", index_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_NEXT_STEP, index_summary.get("next_step"), "source consumer index must route to review"),
    ]


def _review(
    status: str,
    index_summary: dict[str, Any],
    consumer_index: dict[str, Any],
    lookup_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_downstream_consumer_lookup_only" if ready else "blocked",
        "consumer_index_path": str(index_path or ""),
        "consumer_name": index_summary.get("consumer_name") if ready else "",
        "entry_count": len(lookup_rows) if ready else 0,
        "lookup_keys": list(consumer_index.get("lookup_keys") or []) if ready else [],
        "downstream_ready": ready,
        "lookup_ready": bool(ready and index_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and index_summary.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "allowed_use": downstream_lookup_use() if ready else "none",
        "blocked_uses": blocked_uses(),
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_index_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_index_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "consumer_name": review.get("consumer_name"),
        "entry_count": review.get("entry_count"),
        "lookup_key_count": len(list(review.get("lookup_keys") or [])),
        "downstream_ready": review.get("downstream_ready"),
        "lookup_ready": review.get("lookup_ready"),
        "contract_check_ready": review.get("contract_check_ready"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": review.get("consumer_boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "allowed_use": review.get("allowed_use"),
        "blocked_uses": review.get("blocked_uses"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_index_review_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_index_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream consumer index is not ready for downstream consumer review.",
            "next_action": "repair consumer index before downstream consumer review",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream consumer index is approved only for lookup-only consumption; production promotion remains blocked.",
        "next_action": str(review.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_index_review",
    "locate_randomized_holdout_publication_registry_downstream_consumer_index",
    "read_json_report",
    "resolve_exit_code",
]
