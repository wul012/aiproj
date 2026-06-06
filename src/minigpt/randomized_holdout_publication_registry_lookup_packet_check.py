from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM
from minigpt.randomized_holdout_publication_registry_lookup_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME,
    build_randomized_holdout_publication_registry_lookup_packet,
    read_json_report as read_lookup_packet_source_json,
)
from minigpt.randomized_holdout_publication_registry_manifest_review import read_json_report as read_manifest_review_json
from minigpt.report_utils import as_dict, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME = "randomized_holdout_publication_registry_lookup_packet_check.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_CSV_FILENAME = "randomized_holdout_publication_registry_lookup_packet_check.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_TEXT_FILENAME = "randomized_holdout_publication_registry_lookup_packet_check.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_lookup_packet_check.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_HTML_FILENAME = "randomized_holdout_publication_registry_lookup_packet_check.html"

CHECKED_SUMMARY_FIELDS = (
    "randomized_holdout_publication_registry_lookup_packet_ready",
    "lookup_packet_id",
    "lookup_scope",
    "entry_count",
    "lookup_ready",
    "bounded_publication_accepted",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "allowed_use",
    "rejected_use",
    "next_step",
)
CHECKED_PACKET_FIELDS = (
    "packet_ready",
    "lookup_packet_id",
    "lookup_scope",
    "registry_manifest_review_path",
    "entry_count",
    "lookup_entries",
    "lookup_keys",
    "lookup_ready",
    "bounded_publication_accepted",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "allowed_use",
    "rejected_use",
    "next_step",
)


def locate_randomized_holdout_publication_registry_lookup_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry lookup packet check input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_lookup_packet_check(
    lookup_packet_report: dict[str, Any],
    *,
    lookup_packet_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry lookup packet contract check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_review = _resolve_source_review(lookup_packet_report, lookup_packet_path)
    rebuilt = _rebuild_lookup_packet(source_review)
    check_rows = _check_rows(lookup_packet_report, rebuilt, source_review)
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
        "source_lookup_packet": str(lookup_packet_path or ""),
        "source_manifest_review": "" if source_review is None else str(source_review),
        "source_summary": as_dict(lookup_packet_report.get("summary")),
        "rebuilt_summary": as_dict(rebuilt.get("summary")),
        "source_lookup_packet_body": as_dict(lookup_packet_report.get("lookup_packet")),
        "rebuilt_lookup_packet_body": as_dict(rebuilt.get("lookup_packet")),
        "check_rows": check_rows,
        "summary": _summary(status, check_rows, lookup_packet_report, rebuilt, source_review),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _resolve_source_review(lookup_packet_report: dict[str, Any], lookup_packet_path: str | Path | None) -> Path | None:
    packet = as_dict(lookup_packet_report.get("lookup_packet"))
    candidates = [lookup_packet_report.get("registry_manifest_review_path"), packet.get("registry_manifest_review_path")]
    for value in candidates:
        text = str(value or "")
        if not text:
            continue
        direct = Path(text)
        if direct.is_file():
            return direct
        if lookup_packet_path:
            sibling = Path(lookup_packet_path).parent / text
            if sibling.is_file():
                return sibling
        return direct
    return None


def _rebuild_lookup_packet(source_review: Path | None) -> dict[str, Any]:
    if source_review is None or not source_review.is_file():
        return {
            "status": "fail",
            "decision": "fix_randomized_holdout_publication_registry_lookup_packet",
            "failed_count": 1,
            "lookup_packet": {"packet_ready": False, "lookup_packet_id": "not_ready", "lookup_scope": "not_ready"},
            "summary": {
                "randomized_holdout_publication_registry_lookup_packet_ready": False,
                "lookup_ready": False,
                "promotion_ready": False,
                "failed_check_count": 1,
            },
        }
    return build_randomized_holdout_publication_registry_lookup_packet(
        read_manifest_review_json(source_review),
        registry_manifest_review_path=source_review,
    )


def _check_rows(original: dict[str, Any], rebuilt: dict[str, Any], source_review: Path | None) -> list[dict[str, Any]]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    original_packet = as_dict(original.get("lookup_packet"))
    rebuilt_packet = as_dict(rebuilt.get("lookup_packet"))
    rows = [
        _check("source_manifest_review_present", source_review is not None, str(source_review or ""), "lookup packet must record a source manifest review"),
        _check("source_manifest_review_exists", bool(source_review and source_review.is_file()), str(source_review or ""), "source manifest review must exist"),
        _compare("status", original.get("status"), rebuilt.get("status")),
        _compare("decision", original.get("decision"), rebuilt.get("decision")),
        _compare("failed_count", original.get("failed_count"), rebuilt.get("failed_count")),
    ]
    rows.extend(_compare(f"summary.{field}", original_summary.get(field), rebuilt_summary.get(field)) for field in CHECKED_SUMMARY_FIELDS)
    rows.extend(_compare(f"lookup_packet.{field}", original_packet.get(field), rebuilt_packet.get(field)) for field in CHECKED_PACKET_FIELDS)
    return rows


def _compare(check_id: str, original: Any, rebuilt: Any) -> dict[str, Any]:
    return _check(check_id, original == rebuilt, {"source": original, "rebuilt": rebuilt}, f"{check_id} must match the rebuilt lookup packet")


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(
    status: str,
    check_rows: list[dict[str, Any]],
    original: dict[str, Any],
    rebuilt: dict[str, Any],
    source_review: Path | None,
) -> dict[str, Any]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    original_packet = as_dict(original.get("lookup_packet"))
    rebuilt_packet = as_dict(rebuilt.get("lookup_packet"))
    return {
        "contract_check_ready": status == "pass",
        "source_manifest_review": "" if source_review is None else str(source_review),
        "original_decision": original.get("decision"),
        "rebuilt_decision": rebuilt.get("decision"),
        "original_lookup_scope": original_summary.get("lookup_scope"),
        "rebuilt_lookup_scope": rebuilt_summary.get("lookup_scope"),
        "original_lookup_ready": original_summary.get("lookup_ready"),
        "rebuilt_lookup_ready": rebuilt_summary.get("lookup_ready"),
        "original_lookup_keys": original_packet.get("lookup_keys"),
        "rebuilt_lookup_keys": rebuilt_packet.get("lookup_keys"),
        "original_rejected_use": original_summary.get("rejected_use"),
        "rebuilt_rejected_use": rebuilt_summary.get("rejected_use"),
        "original_promotion_ready": original_summary.get("promotion_ready"),
        "rebuilt_promotion_ready": rebuilt_summary.get("promotion_ready"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_lookup_packet_contract_check_passed"
    return "fix_randomized_holdout_publication_registry_lookup_packet_contract"


def _interpretation(status: str) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The registry lookup packet does not match the packet rebuilt from the source manifest review.",
            "next_action": "repair randomized holdout publication registry lookup packet",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The registry lookup packet can be rebuilt from the source manifest review with stable lookup-only fields.",
        "next_action": "package_randomized_holdout_publication_registry_lookup_packet",
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_lookup_packet_check",
    "locate_randomized_holdout_publication_registry_lookup_packet",
    "read_json_report",
    "resolve_exit_code",
]
