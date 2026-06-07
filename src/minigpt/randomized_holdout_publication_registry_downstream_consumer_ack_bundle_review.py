from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import downstream_lookup_use, is_downstream_lookup_only, sha256_file
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.html"

REVIEW_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review-v948"
EXPECTED_EVIDENCE_KINDS = ["downstream_consumer_ack", "downstream_consumer_ack_contract_check"]


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review(
    ack_bundle_report: dict[str, Any],
    *,
    ack_bundle_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    bundle_summary = as_dict(ack_bundle_report.get("summary"))
    bundle = as_dict(ack_bundle_report.get("bundle"))
    evidence_rows = list_of_dicts(ack_bundle_report.get("evidence_rows"))
    checks = _checks(ack_bundle_report, bundle_summary, bundle, evidence_rows, ack_bundle_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, bundle_summary, bundle, evidence_rows, ack_bundle_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "ack_bundle_path": str(ack_bundle_path or ""),
        "source_ack_bundle_summary": bundle_summary,
        "source_ack_bundle": bundle,
        "evidence_rows": evidence_rows,
        "check_rows": checks,
        "review": review,
        "summary": _summary(status, checks, review),
        "interpretation": _interpretation(status, review),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_review_ready: bool,
    require_publish_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready") is not True:
        return 1
    if require_publish_ready and summary.get("publish_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    bundle_report: dict[str, Any],
    bundle_summary: dict[str, Any],
    bundle: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    bundle_path: str | Path | None,
) -> list[dict[str, Any]]:
    evidence_kinds = [str(row.get("kind")) for row in evidence_rows]
    return [
        _check("ack_bundle_file_exists", _path_exists(bundle_path), str(bundle_path or ""), "ack bundle file must exist"),
        _check("ack_bundle_passed", bundle_report.get("status") == "pass", bundle_report.get("status"), "ack bundle must pass"),
        _check("ack_bundle_decision_ready", bundle_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready", bundle_report.get("decision"), "ack bundle decision must be ready"),
        _check("ack_bundle_summary_ready", bundle_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready") is True and bundle.get("bundle_ready") is True, {"summary": bundle_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready"), "bundle": bundle.get("bundle_ready")}, "ack bundle summary and body must be ready"),
        _check("bundle_status_ready", bundle_summary.get("bundle_status") == "ready_for_downstream_consumer_ack_review" and bundle.get("bundle_status") == "ready_for_downstream_consumer_ack_review", {"summary": bundle_summary.get("bundle_status"), "bundle": bundle.get("bundle_status")}, "bundle status must route to review"),
        _check("evidence_count", int(bundle_summary.get("evidence_count") or 0) == 2 and len(evidence_rows) == 2, {"summary": bundle_summary.get("evidence_count"), "rows": len(evidence_rows)}, "review requires ack and contract-check evidence"),
        _check("evidence_kinds", evidence_kinds == EXPECTED_EVIDENCE_KINDS, evidence_kinds, "evidence kinds must remain ordered and complete"),
        _check("evidence_files_exist", all(_path_exists(row.get("path")) for row in evidence_rows), [row.get("path") for row in evidence_rows], "evidence files must exist"),
        _check("evidence_digests_match", all(_digest_matches(row) for row in evidence_rows), [row.get("sha256") for row in evidence_rows], "evidence SHA-256 values must match current files"),
        _check("evidence_statuses_pass", all(row.get("status") == "pass" for row in evidence_rows), [row.get("status") for row in evidence_rows], "all evidence rows must pass"),
        _check("evidence_failed_counts_zero", all(int(row.get("failed_count") or 0) == 0 for row in evidence_rows), [row.get("failed_count") for row in evidence_rows], "all evidence failed counts must be zero"),
        _check("acked_use_lookup_only", is_downstream_lookup_only(bundle_summary.get("acked_use")) and is_downstream_lookup_only(bundle.get("acked_use")), {"summary": bundle_summary.get("acked_use"), "bundle": bundle.get("acked_use")}, "acked use must remain downstream lookup only"),
        _check("lookup_ready", bundle_summary.get("lookup_ready") is True and bundle.get("lookup_ready") is True, {"summary": bundle_summary.get("lookup_ready"), "bundle": bundle.get("lookup_ready")}, "bundle review requires lookup-ready bundle"),
        _check("contract_check_ready", bundle_summary.get("contract_check_ready") is True and bundle.get("contract_check_ready") is True, {"summary": bundle_summary.get("contract_check_ready"), "bundle": bundle.get("contract_check_ready")}, "bundle review requires contract-ready bundle"),
        _check("consumer_boundary_governance", bundle_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and bundle.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": bundle_summary.get("consumer_boundary"), "bundle": bundle.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", bundle_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and bundle.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": bundle_summary.get("model_quality_claim"), "bundle": bundle.get("model_quality_claim")}, "model quality claim must remain bounded"),
        _check("promotion_still_false", bundle_summary.get("promotion_ready") is False and bundle.get("promotion_ready") is False and bundle.get("approved_for_promotion") is False, {"summary": bundle_summary.get("promotion_ready"), "bundle": bundle.get("promotion_ready"), "approved": bundle.get("approved_for_promotion")}, "bundle review must not enable promotion"),
        _check("source_checks_clean", int(bundle_summary.get("failed_check_count") or 0) == 0, bundle_summary.get("failed_check_count"), "source bundle checks must be clean"),
        _check("source_next_step_matches", bundle_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_NEXT_STEP, bundle_summary.get("next_step"), "source bundle must route to review"),
    ]


def _review(
    status: str,
    bundle_summary: dict[str, Any],
    bundle: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    bundle_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_downstream_consumer_ack_bundle_publication" if ready else "blocked",
        "ack_bundle_path": str(bundle_path or ""),
        "consumer_name": bundle_summary.get("consumer_name") if ready else "",
        "publish_ready": ready,
        "lookup_ready": bool(ready and bundle_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and bundle_summary.get("contract_check_ready") is True),
        "acked_use": downstream_lookup_use() if ready else "none",
        "evidence_count": len(evidence_rows) if ready else 0,
        "evidence_kinds": [row.get("kind") for row in evidence_rows] if ready else [],
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review",
    }


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(str(path)).exists()


def _digest_matches(row: dict[str, Any]) -> bool:
    path = row.get("path")
    expected = row.get("sha256")
    if not path or not expected:
        return False
    source = Path(str(path))
    return source.exists() and sha256_file(source) == expected


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "consumer_name": review.get("consumer_name"),
        "publish_ready": review.get("publish_ready"),
        "lookup_ready": review.get("lookup_ready"),
        "contract_check_ready": review.get("contract_check_ready"),
        "acked_use": review.get("acked_use"),
        "evidence_count": review.get("evidence_count"),
        "evidence_kinds": review.get("evidence_kinds"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": review.get("consumer_boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream consumer ack bundle is not ready for publication review.",
            "next_action": "repair downstream consumer ack bundle before publication",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream consumer ack bundle is approved for lookup-only publication; promotion remains blocked.",
        "next_action": str(review.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle",
    "read_json_report",
    "resolve_exit_code",
]
