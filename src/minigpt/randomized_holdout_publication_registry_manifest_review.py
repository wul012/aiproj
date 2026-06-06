from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_manifest import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_JSON_FILENAME = "randomized_holdout_publication_registry_manifest_review.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_CSV_FILENAME = "randomized_holdout_publication_registry_manifest_review.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_TEXT_FILENAME = "randomized_holdout_publication_registry_manifest_review.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_manifest_review.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_HTML_FILENAME = "randomized_holdout_publication_registry_manifest_review.html"

REVIEW_ID = "randomized-holdout-publication-registry-manifest-review-v933"
EXPECTED_MANIFEST_NEXT_STEP = "review_randomized_holdout_publication_registry_manifest"


def locate_randomized_holdout_publication_registry_manifest(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry manifest review input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_manifest_review(
    registry_manifest_report: dict[str, Any],
    *,
    registry_manifest_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry manifest review",
    generated_at: str | None = None,
) -> dict[str, Any]:
    manifest_summary = as_dict(registry_manifest_report.get("summary"))
    manifest = as_dict(registry_manifest_report.get("manifest"))
    entries = list_of_dicts(manifest.get("entries"))
    checks = _checks(registry_manifest_report, manifest_summary, manifest, entries, registry_manifest_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review = _review(status, manifest_summary, manifest, entries, registry_manifest_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "registry_manifest_path": str(registry_manifest_path or ""),
        "source_manifest_summary": manifest_summary,
        "source_manifest": manifest,
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
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_review_ready and summary.get("randomized_holdout_publication_registry_manifest_review_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    manifest_report: dict[str, Any],
    manifest_summary: dict[str, Any],
    manifest: dict[str, Any],
    entries: list[dict[str, Any]],
    manifest_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("registry_manifest_file_exists", _path_exists(manifest_path), str(manifest_path or ""), "registry manifest file must exist"),
        _check("registry_manifest_passed", manifest_report.get("status") == "pass", manifest_report.get("status"), "registry manifest must pass"),
        _check("registry_manifest_decision_ready", manifest_report.get("decision") == "randomized_holdout_publication_registry_manifest_ready", manifest_report.get("decision"), "registry manifest decision must be ready"),
        _check("manifest_summary_ready", manifest_summary.get("randomized_holdout_publication_registry_manifest_ready") is True and manifest.get("manifest_ready") is True, {"summary": manifest_summary.get("randomized_holdout_publication_registry_manifest_ready"), "manifest": manifest.get("manifest_ready")}, "manifest summary and body must be ready"),
        _check("manifest_scope_bounded", manifest_summary.get("manifest_scope") == "bounded_publication_registry_manifest_only", manifest_summary.get("manifest_scope"), "manifest scope must remain bounded"),
        _check("entry_count_positive", int(manifest_summary.get("entry_count") or 0) > 0 and len(entries) == int(manifest_summary.get("entry_count") or 0), {"summary": manifest_summary.get("entry_count"), "entries": len(entries)}, "manifest entry count must match entries"),
        _check("entries_registered", all(row.get("registry_status") == "registered" for row in entries), [row.get("registry_status") for row in entries], "all entries must be registered"),
        _check("entries_bounded", all(row.get("bounded_publication_accepted") is True for row in entries), [row.get("bounded_publication_accepted") for row in entries], "all entries must be bounded accepted"),
        _check("entries_not_promoted", all(row.get("promotion_ready") is False for row in entries), [row.get("promotion_ready") for row in entries], "review must not promote entries"),
        _check("contract_check_ready", manifest_summary.get("contract_check_ready") is True and manifest.get("contract_check_ready") is True, {"summary": manifest_summary.get("contract_check_ready"), "manifest": manifest.get("contract_check_ready")}, "manifest must carry a ready contract check"),
        _check("bounded_publication_accepted", manifest_summary.get("bounded_publication_accepted") is True, manifest_summary.get("bounded_publication_accepted"), "review only accepts bounded publication"),
        _check("consumer_boundary_governance", manifest_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and manifest.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": manifest_summary.get("consumer_boundary"), "manifest": manifest.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", all(row.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM for row in entries), [row.get("model_quality_claim") for row in entries], "entry claims must stay bounded"),
        _check("promotion_still_false", manifest_summary.get("promotion_ready") is False and manifest.get("promotion_ready") is False, {"summary": manifest_summary.get("promotion_ready"), "manifest": manifest.get("promotion_ready")}, "review must not enable direct promotion"),
        _check("approved_for_promotion_false", manifest_summary.get("approved_for_promotion") is False and manifest.get("approved_for_promotion") is False, {"summary": manifest_summary.get("approved_for_promotion"), "manifest": manifest.get("approved_for_promotion")}, "review must not approve promotion"),
        _check("source_checks_clean", int(manifest_summary.get("failed_check_count") or 0) == 0, manifest_summary.get("failed_check_count"), "source manifest checks must be clean"),
        _check("source_next_step_matches", manifest_summary.get("next_step") == EXPECTED_MANIFEST_NEXT_STEP, manifest_summary.get("next_step"), "source manifest must route to review"),
    ]


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(path).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _review(
    status: str,
    manifest_summary: dict[str, Any],
    manifest: dict[str, Any],
    entries: list[dict[str, Any]],
    manifest_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "review_ready": ready,
        "review_id": REVIEW_ID if ready else "not_ready",
        "review_status": "approved_for_governance_lookup_only" if ready else "blocked",
        "registry_manifest_path": str(manifest_path or ""),
        "entry_count": len(entries) if ready else 0,
        "reviewed_entry_ids": [str(row.get("entry_id")) for row in entries] if ready else [],
        "lookup_ready": ready,
        "bounded_publication_accepted": bool(ready and manifest_summary.get("bounded_publication_accepted") is True),
        "contract_check_ready": bool(ready and manifest.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "allowed_use": "governance_lookup_only" if ready else "none",
        "rejected_use": "production_promotion",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_manifest_review",
    }


def _summary(status: str, checks: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_manifest_review_ready": status == "pass" and review.get("review_ready") is True,
        "review_id": review.get("review_id"),
        "review_status": review.get("review_status"),
        "entry_count": review.get("entry_count"),
        "lookup_ready": review.get("lookup_ready"),
        "bounded_publication_accepted": review.get("bounded_publication_accepted"),
        "contract_check_ready": review.get("contract_check_ready"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": review.get("consumer_boundary"),
        "model_quality_claim": review.get("model_quality_claim"),
        "allowed_use": review.get("allowed_use"),
        "rejected_use": review.get("rejected_use"),
        "next_step": review.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_manifest_review_ready"
    return "fix_randomized_holdout_publication_registry_manifest_review"


def _interpretation(status: str, review: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The publication registry manifest is not ready for bounded governance lookup review.",
            "next_action": "repair registry manifest before review",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The publication registry manifest is approved only for governance lookup consumption; production promotion remains blocked.",
        "next_action": review.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_manifest_review",
    "locate_randomized_holdout_publication_registry_manifest",
    "read_json_report",
    "resolve_exit_code",
]
