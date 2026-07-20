from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import downstream_lookup_use, is_downstream_lookup_only
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.html"

PUBLICATION_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949"
EXPECTED_EVIDENCE_KINDS = ["downstream_consumer_ack", "downstream_consumer_ack_contract_check"]


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle publication input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication(
    ack_bundle_review_report: dict[str, Any],
    *,
    ack_bundle_review_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle publication",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(ack_bundle_review_report.get("summary"))
    review = as_dict(ack_bundle_review_report.get("review"))
    evidence_rows = list_of_dicts(ack_bundle_review_report.get("evidence_rows"))
    checks = _checks(ack_bundle_review_report, review_summary, review, evidence_rows, ack_bundle_review_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    publication = _publication(status, review_summary, review, evidence_rows, ack_bundle_review_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "ack_bundle_review_path": str(ack_bundle_review_path or ""),
        "source_ack_bundle_review_summary": review_summary,
        "source_ack_bundle_review": review,
        "evidence_rows": evidence_rows if status == "pass" else [],
        "check_rows": checks,
        "publication": publication,
        "summary": _summary(status, checks, publication),
        "interpretation": _interpretation(status, publication),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_publication_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_publication_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready") is not True:
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
    evidence_rows: list[dict[str, Any]],
    review_path: str | Path | None,
) -> list[dict[str, Any]]:
    evidence_kinds = [str(row.get("kind")) for row in evidence_rows]
    ack_bundle_path = review.get("ack_bundle_path")
    return [
        _check("ack_bundle_review_file_exists", _path_exists(review_path), str(review_path or ""), "ack bundle review file must exist"),
        _check("ack_bundle_review_passed", review_report.get("status") == "pass", review_report.get("status"), "ack bundle review must pass"),
        _check("ack_bundle_review_decision_ready", review_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready", review_report.get("decision"), "ack bundle review decision must be ready"),
        _check("ack_bundle_review_summary_ready", review_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready") is True and review.get("review_ready") is True, {"summary": review_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready"), "review": review.get("review_ready")}, "ack bundle review summary and body must be ready"),
        _check("ack_bundle_file_exists", _path_exists(ack_bundle_path), ack_bundle_path, "reviewed ack bundle must still exist"),
        _check("review_status_publishable", review_summary.get("review_status") == "approved_for_downstream_consumer_ack_bundle_publication" and review.get("review_status") == "approved_for_downstream_consumer_ack_bundle_publication", {"summary": review_summary.get("review_status"), "review": review.get("review_status")}, "review must approve lookup-only publication"),
        _check("publish_ready", review_summary.get("publish_ready") is True and review.get("publish_ready") is True, {"summary": review_summary.get("publish_ready"), "review": review.get("publish_ready")}, "publication requires publish-ready review"),
        _check("lookup_ready", review_summary.get("lookup_ready") is True and review.get("lookup_ready") is True, {"summary": review_summary.get("lookup_ready"), "review": review.get("lookup_ready")}, "publication requires lookup-ready review"),
        _check("contract_check_ready", review_summary.get("contract_check_ready") is True and review.get("contract_check_ready") is True, {"summary": review_summary.get("contract_check_ready"), "review": review.get("contract_check_ready")}, "publication requires contract-ready review"),
        _check("evidence_count", int(review_summary.get("evidence_count") or 0) == 2 and len(evidence_rows) == 2, {"summary": review_summary.get("evidence_count"), "rows": len(evidence_rows)}, "publication requires two evidence rows"),
        _check("evidence_kinds", evidence_kinds == EXPECTED_EVIDENCE_KINDS, evidence_kinds, "publication evidence kinds must remain ordered and complete"),
        _check("evidence_files_exist", all(_path_exists(row.get("path")) for row in evidence_rows), [row.get("path") for row in evidence_rows], "publication evidence files must exist"),
        _check("evidence_statuses_pass", all(row.get("status") == "pass" for row in evidence_rows), [row.get("status") for row in evidence_rows], "publication evidence rows must pass"),
        _check("acked_use_lookup_only", is_downstream_lookup_only(review_summary.get("acked_use")) and is_downstream_lookup_only(review.get("acked_use")), {"summary": review_summary.get("acked_use"), "review": review.get("acked_use")}, "publication must remain downstream lookup only"),
        _check("consumer_boundary_governance", review_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and review.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": review_summary.get("consumer_boundary"), "review": review.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", review_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and review.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": review_summary.get("model_quality_claim"), "review": review.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and review.get("promotion_ready") is False and review.get("approved_for_promotion") is False, {"summary": review_summary.get("promotion_ready"), "review": review.get("promotion_ready"), "approved": review.get("approved_for_promotion")}, "publication must not enable promotion"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source review checks must be clean"),
        _check("source_next_step_matches", review_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_NEXT_STEP, review_summary.get("next_step"), "source review must route to publication"),
    ]


def _publication(
    status: str,
    review_summary: dict[str, Any],
    review: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    review_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "publication_ready": ready,
        "publication_id": PUBLICATION_ID if ready else "not_ready",
        "publication_status": "published_for_downstream_consumer_lookup_only" if ready else "blocked",
        "ack_bundle_review_path": str(review_path or ""),
        "ack_bundle_path": review.get("ack_bundle_path") if ready else "",
        "consumer_name": review_summary.get("consumer_name") if ready else "",
        "published_use": downstream_lookup_use() if ready else "none",
        "publish_ready": ready,
        "lookup_ready": bool(ready and review_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and review_summary.get("contract_check_ready") is True),
        "evidence_rows": evidence_rows if ready else [],
        "evidence_count": len(evidence_rows) if ready else 0,
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication",
    }


def _summary(status: str, checks: list[dict[str, Any]], publication: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready": status == "pass" and publication.get("publication_ready") is True,
        "publication_id": publication.get("publication_id"),
        "publication_status": publication.get("publication_status"),
        "consumer_name": publication.get("consumer_name"),
        "published_use": publication.get("published_use"),
        "publish_ready": publication.get("publish_ready"),
        "lookup_ready": publication.get("lookup_ready"),
        "contract_check_ready": publication.get("contract_check_ready"),
        "evidence_count": publication.get("evidence_count"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": publication.get("consumer_boundary"),
        "model_quality_claim": publication.get("model_quality_claim"),
        "next_step": publication.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication"


def _interpretation(status: str, publication: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream consumer ack bundle review is not ready for publication.",
            "next_action": "repair downstream consumer ack bundle review before publication",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream consumer ack bundle is published for lookup-only consumption while promotion remains blocked.",
        "next_action": str(publication.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review",
    "read_json_report",
    "resolve_exit_code",
]
