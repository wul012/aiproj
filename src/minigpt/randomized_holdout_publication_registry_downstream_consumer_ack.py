from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import blocked_uses, blocked_uses_complete, downstream_lookup_use, is_downstream_lookup_only
from minigpt.randomized_holdout_publication_registry_downstream_consumer_index_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack.html"

ACK_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-v945"


def locate_randomized_holdout_publication_registry_downstream_consumer_index_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack(
    consumer_index_review_report: dict[str, Any],
    *,
    consumer_index_review_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(consumer_index_review_report.get("summary"))
    review = as_dict(consumer_index_review_report.get("review"))
    lookup_rows = list_of_dicts(consumer_index_review_report.get("lookup_rows"))
    checks = _checks(consumer_index_review_report, review_summary, review, lookup_rows, consumer_index_review_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    ack = _ack(status, review_summary, review, lookup_rows, consumer_index_review_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "consumer_index_review_path": str(consumer_index_review_path or ""),
        "source_consumer_index_review_summary": review_summary,
        "source_consumer_index_review": review,
        "lookup_rows": lookup_rows,
        "check_rows": checks,
        "ack": ack,
        "summary": _summary(status, checks, ack),
        "interpretation": _interpretation(status, ack),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_ack_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_ack_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    review_report: dict[str, Any],
    review_summary: dict[str, Any],
    review: dict[str, Any],
    lookup_rows: list[dict[str, Any]],
    review_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = list(review.get("lookup_keys") or [])
    consumer_index_path = review.get("consumer_index_path")
    return [
        _check("consumer_index_review_file_exists", _path_exists(review_path), str(review_path or ""), "consumer index review file must exist"),
        _check("consumer_index_review_passed", review_report.get("status") == "pass", review_report.get("status"), "consumer index review must pass"),
        _check("consumer_index_review_decision_ready", review_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_index_review_ready", review_report.get("decision"), "consumer index review decision must be ready"),
        _check("consumer_index_review_summary_ready", review_summary.get("randomized_holdout_publication_registry_downstream_consumer_index_review_ready") is True and review.get("review_ready") is True, {"summary": review_summary.get("randomized_holdout_publication_registry_downstream_consumer_index_review_ready"), "review": review.get("review_ready")}, "consumer index review summary and body must be ready"),
        _check("consumer_index_file_exists", _path_exists(consumer_index_path), consumer_index_path, "reviewed consumer index must still exist"),
        _check("review_status_lookup_only", review_summary.get("review_status") == "approved_for_downstream_consumer_lookup_only" and review.get("review_status") == "approved_for_downstream_consumer_lookup_only", {"summary": review_summary.get("review_status"), "review": review.get("review_status")}, "review must approve lookup-only consumption"),
        _check("lookup_ready", review_summary.get("lookup_ready") is True and review.get("lookup_ready") is True, {"summary": review_summary.get("lookup_ready"), "review": review.get("lookup_ready")}, "ack requires lookup-ready review"),
        _check("downstream_ready", review_summary.get("downstream_ready") is True and review.get("downstream_ready") is True, {"summary": review_summary.get("downstream_ready"), "review": review.get("downstream_ready")}, "ack requires downstream-ready review"),
        _check("contract_check_ready", review_summary.get("contract_check_ready") is True and review.get("contract_check_ready") is True, {"summary": review_summary.get("contract_check_ready"), "review": review.get("contract_check_ready")}, "ack requires ready contract check"),
        _check("allowed_use_lookup_only", is_downstream_lookup_only(review_summary.get("allowed_use")) and is_downstream_lookup_only(review.get("allowed_use")), {"summary": review_summary.get("allowed_use"), "review": review.get("allowed_use")}, "allowed use must stay downstream lookup only"),
        _check("blocked_uses_complete", blocked_uses_complete(review_summary.get("blocked_uses")) and blocked_uses_complete(review.get("blocked_uses")), {"summary": review_summary.get("blocked_uses"), "review": review.get("blocked_uses")}, "blocked uses must remain complete"),
        _check("lookup_rows_present", len(lookup_rows) == int(review_summary.get("entry_count") or 0) and len(lookup_rows) > 0, {"lookup_rows": len(lookup_rows), "entry_count": review_summary.get("entry_count")}, "ack requires lookup rows"),
        _check("lookup_keys_present", len(lookup_keys) == len(lookup_rows) and all(str(key).startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must use publication namespace"),
        _check("lookup_rows_not_promoted", all(row.get("promotion_ready") is False for row in lookup_rows), [row.get("promotion_ready") for row in lookup_rows], "ack must not promote lookup rows"),
        _check("consumer_boundary_governance", review_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and review.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": review_summary.get("consumer_boundary"), "review": review.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", review_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and review.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": review_summary.get("model_quality_claim"), "review": review.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and review.get("promotion_ready") is False and review.get("approved_for_promotion") is False, {"summary": review_summary.get("promotion_ready"), "review": review.get("promotion_ready"), "approved": review.get("approved_for_promotion")}, "ack must not enable promotion"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source review checks must be clean"),
        _check("source_next_step_matches", review_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_NEXT_STEP, review_summary.get("next_step"), "source review must route to ack"),
    ]


def _ack(
    status: str,
    review_summary: dict[str, Any],
    review: dict[str, Any],
    lookup_rows: list[dict[str, Any]],
    review_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "ack_ready": ready,
        "ack_id": ACK_ID if ready else "not_ready",
        "ack_status": "downstream_consumer_acknowledged" if ready else "blocked",
        "consumer_index_review_path": str(review_path or ""),
        "consumer_index_path": review.get("consumer_index_path") if ready else "",
        "consumer_name": review_summary.get("consumer_name") if ready else "",
        "entry_count": len(lookup_rows) if ready else 0,
        "lookup_keys": list(review.get("lookup_keys") or []) if ready else [],
        "lookup_ready": bool(ready and review_summary.get("lookup_ready") is True),
        "downstream_ready": bool(ready and review_summary.get("downstream_ready") is True),
        "contract_check_ready": bool(ready and review_summary.get("contract_check_ready") is True),
        "acked_use": downstream_lookup_use() if ready else "none",
        "blocked_uses": blocked_uses(),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack",
    }


def _summary(status: str, checks: list[dict[str, Any]], ack: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_ready": status == "pass" and ack.get("ack_ready") is True,
        "ack_id": ack.get("ack_id"),
        "ack_status": ack.get("ack_status"),
        "consumer_name": ack.get("consumer_name"),
        "entry_count": ack.get("entry_count"),
        "lookup_key_count": len(list(ack.get("lookup_keys") or [])),
        "lookup_ready": ack.get("lookup_ready"),
        "downstream_ready": ack.get("downstream_ready"),
        "contract_check_ready": ack.get("contract_check_ready"),
        "acked_use": ack.get("acked_use"),
        "blocked_uses": ack.get("blocked_uses"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": ack.get("consumer_boundary"),
        "model_quality_claim": ack.get("model_quality_claim"),
        "next_step": ack.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack"


def _interpretation(status: str, ack: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream consumer review is not ready for acknowledgement.",
            "next_action": "repair downstream consumer review before ack",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream consumer has acknowledged lookup-only consumption while promotion remains blocked.",
        "next_action": str(ack.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack",
    "locate_randomized_holdout_publication_registry_downstream_consumer_index_review",
    "read_json_report",
    "resolve_exit_code",
]
