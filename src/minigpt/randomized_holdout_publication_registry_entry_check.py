from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_registry_entry import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME,
    build_randomized_holdout_publication_registry_entry,
    read_json_report as read_registry_source_json,
)
from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_ENTRY_ID,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_JSON_FILENAME = "randomized_holdout_publication_registry_entry_check.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_CSV_FILENAME = "randomized_holdout_publication_registry_entry_check.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_TEXT_FILENAME = "randomized_holdout_publication_registry_entry_check.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_entry_check.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_HTML_FILENAME = "randomized_holdout_publication_registry_entry_check.html"

CHECKED_SUMMARY_FIELDS = (
    "randomized_holdout_publication_registry_entry_ready",
    "entry_id",
    "registry_status",
    "entry_type",
    "bounded_publication_accepted",
    "promotion_ready",
    "approved_for_promotion",
    "accepted_claim_count",
    "blocked_claim_count",
    "candidate_case_count",
    "random_seed",
    "pass_rate",
    "allowed_use",
    "model_quality_claim",
    "decision_scope",
    "source_count",
    "source_kinds",
    "consumer_boundary",
    "next_step",
)
CHECKED_ENTRY_FIELDS = (
    "entry_ready",
    "entry_id",
    "registry_status",
    "entry_type",
    "source_index_decision",
    "bounded_publication_accepted",
    "promotion_ready",
    "approved_for_promotion",
    "accepted_claim_count",
    "blocked_claim_count",
    "candidate_case_count",
    "random_seed",
    "pass_rate",
    "allowed_use",
    "model_quality_claim",
    "decision_scope",
    "source_count",
    "source_kinds",
    "consumer_boundary",
    "next_step",
)


def locate_randomized_holdout_publication_registry_entry(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry entry check input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_entry_check(
    registry_entry_report: dict[str, Any],
    *,
    registry_entry_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry entry contract check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_index = _resolve_source_index(registry_entry_report, registry_entry_path)
    rebuilt = _rebuild_entry(source_index, registry_entry_report)
    check_rows = _check_rows(registry_entry_report, rebuilt, source_index)
    issues = [row for row in check_rows if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_registry_entry": str(registry_entry_path or ""),
        "source_publication_decision_index": "" if source_index is None else str(source_index),
        "source_summary": as_dict(registry_entry_report.get("summary")),
        "rebuilt_summary": as_dict(rebuilt.get("summary")),
        "source_registry_entry_body": as_dict(registry_entry_report.get("registry_entry")),
        "rebuilt_registry_entry_body": as_dict(rebuilt.get("registry_entry")),
        "check_rows": check_rows,
        "summary": _summary(status, check_rows, registry_entry_report, rebuilt, source_index),
        "interpretation": _interpretation(status),
    }


def _resolve_source_index(registry_entry_report: dict[str, Any], registry_entry_path: str | Path | None) -> Path | None:
    entry = as_dict(registry_entry_report.get("registry_entry"))
    candidates = [registry_entry_report.get("publication_decision_index_path"), entry.get("source_index_path")]
    for value in candidates:
        text = str(value or "")
        if not text:
            continue
        direct = Path(text)
        if direct.is_file():
            return direct
        if registry_entry_path:
            sibling = Path(registry_entry_path).parent / text
            if sibling.is_file():
                return sibling
        return direct
    return None


def _rebuild_entry(source_index: Path | None, original: dict[str, Any]) -> dict[str, Any]:
    if source_index is None or not source_index.is_file():
        return {
            "status": "fail",
            "decision": "fix_randomized_holdout_publication_registry_entry",
            "failed_count": 1,
            "registry_entry": {"entry_ready": False, "entry_id": "not_registered", "registry_status": "blocked"},
            "summary": {
                "randomized_holdout_publication_registry_entry_ready": False,
                "bounded_publication_accepted": False,
                "promotion_ready": False,
                "failed_check_count": 1,
            },
        }
    return build_randomized_holdout_publication_registry_entry(
        read_registry_source_json(source_index),
        publication_decision_index_path=source_index,
        entry_id=str(as_dict(original.get("summary")).get("entry_id") or RANDOMIZED_HOLDOUT_PUBLICATION_ENTRY_ID),
    )


def _check_rows(original: dict[str, Any], rebuilt: dict[str, Any], source_index: Path | None) -> list[dict[str, Any]]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    original_entry = as_dict(original.get("registry_entry"))
    rebuilt_entry = as_dict(rebuilt.get("registry_entry"))
    rows = [
        _check("source_publication_decision_index_present", source_index is not None, str(source_index or ""), "registry entry must record a source publication decision index"),
        _check("source_publication_decision_index_exists", bool(source_index and source_index.is_file()), str(source_index or ""), "source publication decision index must exist"),
        _compare("status", original.get("status"), rebuilt.get("status")),
        _compare("decision", original.get("decision"), rebuilt.get("decision")),
        _compare("failed_count", original.get("failed_count"), rebuilt.get("failed_count")),
    ]
    rows.extend(_compare(f"summary.{field}", original_summary.get(field), rebuilt_summary.get(field)) for field in CHECKED_SUMMARY_FIELDS)
    rows.extend(_compare(f"registry_entry.{field}", original_entry.get(field), rebuilt_entry.get(field)) for field in CHECKED_ENTRY_FIELDS)
    return rows


def _compare(check_id: str, original: Any, rebuilt: Any) -> dict[str, Any]:
    return _check(check_id, original == rebuilt, {"source": original, "rebuilt": rebuilt}, f"{check_id} must match the rebuilt registry entry")


def _summary(
    status: str,
    check_rows: list[dict[str, Any]],
    original: dict[str, Any],
    rebuilt: dict[str, Any],
    source_index: Path | None,
) -> dict[str, Any]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    return {
        "contract_check_ready": status == "pass",
        "source_publication_decision_index": "" if source_index is None else str(source_index),
        "original_decision": original.get("decision"),
        "rebuilt_decision": rebuilt.get("decision"),
        "original_entry_id": original_summary.get("entry_id"),
        "rebuilt_entry_id": rebuilt_summary.get("entry_id"),
        "original_registry_status": original_summary.get("registry_status"),
        "rebuilt_registry_status": rebuilt_summary.get("registry_status"),
        "original_bounded_publication_accepted": original_summary.get("bounded_publication_accepted"),
        "rebuilt_bounded_publication_accepted": rebuilt_summary.get("bounded_publication_accepted"),
        "original_consumer_boundary": original_summary.get("consumer_boundary"),
        "rebuilt_consumer_boundary": rebuilt_summary.get("consumer_boundary"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_entry_contract_check_passed"
    return "fix_randomized_holdout_publication_registry_entry_contract"


def _interpretation(status: str) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The registry entry does not match the entry rebuilt from the source publication decision index.",
            "next_action": "repair randomized holdout publication registry entry",
        }
    return {
            "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The registry entry can be rebuilt from the source publication decision index with stable bounded fields.",
        "next_action": "package_randomized_holdout_publication_registry_entry",
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_entry_check",
    "locate_randomized_holdout_publication_registry_entry",
    "read_json_report",
    "resolve_exit_code",
]
