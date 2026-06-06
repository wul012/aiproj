from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_lookup_index_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_guard.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_guard.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_guard.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_guard.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_guard.html"

GUARD_ID = "randomized-holdout-publication-registry-downstream-guard-v938"
BLOCKED_USES = ["production_promotion", "model_quality_expansion", "training_data_claim_expansion"]


def locate_randomized_holdout_publication_registry_lookup_index_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream guard input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_guard(
    lookup_index_review_report: dict[str, Any],
    *,
    lookup_index_review_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream guard",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(lookup_index_review_report.get("summary"))
    review = as_dict(lookup_index_review_report.get("review"))
    entries = list_of_dicts(lookup_index_review_report.get("entry_rows"))
    checks = _checks(lookup_index_review_report, review_summary, review, entries, lookup_index_review_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    guard = _guard(status, review_summary, review, entries, lookup_index_review_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "lookup_index_review_path": str(lookup_index_review_path or ""),
        "source_lookup_index_review_summary": review_summary,
        "source_lookup_index_review": review,
        "entry_rows": entries,
        "check_rows": checks,
        "guard": guard,
        "summary": _summary(status, checks, guard),
        "interpretation": _interpretation(status, guard),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_guard_ready: bool,
    require_downstream_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_guard_ready and summary.get("randomized_holdout_publication_registry_downstream_guard_ready") is not True:
        return 1
    if require_downstream_ready and summary.get("downstream_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    review_report: dict[str, Any],
    review_summary: dict[str, Any],
    review: dict[str, Any],
    entries: list[dict[str, Any]],
    review_path: str | Path | None,
) -> list[dict[str, Any]]:
    lookup_keys = list(review.get("lookup_keys") or [])
    return [
        _check("lookup_index_review_file_exists", _path_exists(review_path), str(review_path or ""), "lookup index review file must exist"),
        _check("lookup_index_review_passed", review_report.get("status") == "pass", review_report.get("status"), "lookup index review must pass"),
        _check("lookup_index_review_decision_ready", review_report.get("decision") == "randomized_holdout_publication_registry_lookup_index_review_ready", review_report.get("decision"), "lookup index review decision must be ready"),
        _check("review_summary_ready", review_summary.get("randomized_holdout_publication_registry_lookup_index_review_ready") is True and review.get("review_ready") is True, {"summary": review_summary.get("randomized_holdout_publication_registry_lookup_index_review_ready"), "review": review.get("review_ready")}, "review summary and body must be ready"),
        _check("review_status_downstream_only", review_summary.get("review_status") == "approved_for_downstream_governance_lookup_only" and review.get("review_status") == "approved_for_downstream_governance_lookup_only", {"summary": review_summary.get("review_status"), "review": review.get("review_status")}, "review must be downstream governance lookup only"),
        _check("downstream_ready", review_summary.get("downstream_ready") is True and review.get("downstream_ready") is True, {"summary": review_summary.get("downstream_ready"), "review": review.get("downstream_ready")}, "downstream lookup must be ready"),
        _check("lookup_ready", review_summary.get("lookup_ready") is True and review.get("lookup_ready") is True, {"summary": review_summary.get("lookup_ready"), "review": review.get("lookup_ready")}, "lookup must be ready"),
        _check("contract_check_ready", review_summary.get("contract_check_ready") is True and review.get("contract_check_ready") is True, {"summary": review_summary.get("contract_check_ready"), "review": review.get("contract_check_ready")}, "contract check must be ready"),
        _check("consumer_boundary_governance", review_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and review.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": review_summary.get("consumer_boundary"), "review": review.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("allowed_use_downstream_only", review_summary.get("allowed_use") == "downstream_governance_lookup_only" and review.get("allowed_use") == "downstream_governance_lookup_only", {"summary": review_summary.get("allowed_use"), "review": review.get("allowed_use")}, "allowed use must stay downstream lookup only"),
        _check("rejected_use_production_promotion", review_summary.get("rejected_use") == "production_promotion" and review.get("rejected_use") == "production_promotion", {"summary": review_summary.get("rejected_use"), "review": review.get("rejected_use")}, "production promotion must stay rejected"),
        _check("promotion_still_false", review_summary.get("promotion_ready") is False and review.get("promotion_ready") is False, {"summary": review_summary.get("promotion_ready"), "review": review.get("promotion_ready")}, "downstream guard must not enable promotion"),
        _check("lookup_keys_publication_namespace", len(lookup_keys) == int(review_summary.get("entry_count") or 0) and all(str(key).startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must use publication namespace"),
        _check("entries_not_promoted", all(row.get("promotion_ready") is False for row in entries), [row.get("promotion_ready") for row in entries], "entries must not be promoted"),
        _check("source_checks_clean", int(review_summary.get("failed_check_count") or 0) == 0, review_summary.get("failed_check_count"), "source review checks must be clean"),
        _check("source_next_step_matches", review_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_NEXT_STEP, review_summary.get("next_step"), "source review must route to downstream guard"),
    ]


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(path).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _guard(
    status: str,
    review_summary: dict[str, Any],
    review: dict[str, Any],
    entries: list[dict[str, Any]],
    review_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "guard_ready": ready,
        "guard_id": GUARD_ID if ready else "not_ready",
        "guard_status": "downstream_governance_lookup_allowed" if ready else "blocked",
        "lookup_index_review_path": str(review_path or ""),
        "entry_count": len(entries) if ready else 0,
        "lookup_keys": list(review.get("lookup_keys") or []) if ready else [],
        "downstream_ready": bool(ready and review_summary.get("downstream_ready") is True),
        "lookup_ready": bool(ready and review_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and review_summary.get("contract_check_ready") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "allowed_use": "downstream_governance_lookup_only" if ready else "none",
        "blocked_uses": BLOCKED_USES,
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_guard",
    }


def _summary(status: str, checks: list[dict[str, Any]], guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_guard_ready": status == "pass" and guard.get("guard_ready") is True,
        "guard_id": guard.get("guard_id"),
        "guard_status": guard.get("guard_status"),
        "entry_count": guard.get("entry_count"),
        "downstream_ready": guard.get("downstream_ready"),
        "lookup_ready": guard.get("lookup_ready"),
        "contract_check_ready": guard.get("contract_check_ready"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": guard.get("consumer_boundary"),
        "allowed_use": guard.get("allowed_use"),
        "blocked_uses": guard.get("blocked_uses"),
        "next_step": guard.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_guard_ready"
    return "fix_randomized_holdout_publication_registry_downstream_guard"


def _interpretation(status: str, guard: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The lookup index review is not ready for downstream guard.",
            "next_action": "repair lookup index review before downstream guard",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "Downstream governance lookup is allowed while production promotion and claim expansion remain blocked.",
        "next_action": str(guard.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_guard",
    "locate_randomized_holdout_publication_registry_lookup_index_review",
    "read_json_report",
    "resolve_exit_code",
]
