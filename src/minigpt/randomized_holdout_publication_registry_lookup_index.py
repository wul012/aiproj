from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_lookup_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME,
)
from minigpt.randomized_holdout_publication_registry_lookup_packet_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_JSON_FILENAME = "randomized_holdout_publication_registry_lookup_index.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_CSV_FILENAME = "randomized_holdout_publication_registry_lookup_index.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_TEXT_FILENAME = "randomized_holdout_publication_registry_lookup_index.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_lookup_index.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_HTML_FILENAME = "randomized_holdout_publication_registry_lookup_index.html"

LOOKUP_INDEX_ID = "randomized-holdout-publication-registry-lookup-index-v936"


def locate_randomized_holdout_publication_registry_lookup_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME
    return source


def locate_randomized_holdout_publication_registry_lookup_packet_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry lookup index input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_lookup_index(
    lookup_packet_report: dict[str, Any],
    lookup_packet_check_report: dict[str, Any],
    *,
    lookup_packet_path: str | Path | None = None,
    lookup_packet_check_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry lookup index",
    generated_at: str | None = None,
) -> dict[str, Any]:
    packet_summary = as_dict(lookup_packet_report.get("summary"))
    packet = as_dict(lookup_packet_report.get("lookup_packet"))
    check_summary = as_dict(lookup_packet_check_report.get("summary"))
    check_rows = _checks(lookup_packet_report, lookup_packet_check_report, packet_summary, packet, check_summary, lookup_packet_path, lookup_packet_check_path)
    issues = [row for row in check_rows if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    index = _index(status, packet_summary, packet, check_summary, lookup_packet_path, lookup_packet_check_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "lookup_packet_path": str(lookup_packet_path or ""),
        "lookup_packet_check_path": str(lookup_packet_check_path or ""),
        "source_lookup_packet_summary": packet_summary,
        "source_lookup_packet_check_summary": check_summary,
        "lookup_entries": list_of_dicts(packet.get("lookup_entries")),
        "check_rows": check_rows,
        "lookup_index": index,
        "summary": _summary(status, check_rows, index),
        "interpretation": _interpretation(status, index),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_index_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_index_ready and summary.get("randomized_holdout_publication_registry_lookup_index_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    lookup_packet_report: dict[str, Any],
    lookup_packet_check_report: dict[str, Any],
    packet_summary: dict[str, Any],
    packet: dict[str, Any],
    check_summary: dict[str, Any],
    lookup_packet_path: str | Path | None,
    lookup_packet_check_path: str | Path | None,
) -> list[dict[str, Any]]:
    entries = list_of_dicts(packet.get("lookup_entries"))
    packet_keys = list(packet.get("lookup_keys") or [])
    return [
        _check("lookup_packet_file_exists", _path_exists(lookup_packet_path), str(lookup_packet_path or ""), "lookup packet file must exist"),
        _check("lookup_packet_check_file_exists", _path_exists(lookup_packet_check_path), str(lookup_packet_check_path or ""), "lookup packet check file must exist"),
        _check("lookup_packet_passed", lookup_packet_report.get("status") == "pass", lookup_packet_report.get("status"), "lookup packet must pass"),
        _check("lookup_packet_decision_ready", lookup_packet_report.get("decision") == "randomized_holdout_publication_registry_lookup_packet_ready", lookup_packet_report.get("decision"), "lookup packet decision must be ready"),
        _check("lookup_packet_summary_ready", packet_summary.get("randomized_holdout_publication_registry_lookup_packet_ready") is True and packet.get("packet_ready") is True, {"summary": packet_summary.get("randomized_holdout_publication_registry_lookup_packet_ready"), "packet": packet.get("packet_ready")}, "lookup packet summary and body must be ready"),
        _check("lookup_packet_check_passed", lookup_packet_check_report.get("status") == "pass", lookup_packet_check_report.get("status"), "lookup packet check must pass"),
        _check("lookup_packet_check_decision_ready", lookup_packet_check_report.get("decision") == "randomized_holdout_publication_registry_lookup_packet_contract_check_passed", lookup_packet_check_report.get("decision"), "lookup packet check decision must pass"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "lookup packet contract check must be ready"),
        _check("lookup_keys_match_check", packet_keys == list(check_summary.get("original_lookup_keys") or []) == list(check_summary.get("rebuilt_lookup_keys") or []), {"packet": packet_keys, "original": check_summary.get("original_lookup_keys"), "rebuilt": check_summary.get("rebuilt_lookup_keys")}, "lookup keys must match the contract check"),
        _check("lookup_scope_governance", packet_summary.get("lookup_scope") == "governance_lookup_only" and check_summary.get("original_lookup_scope") == "governance_lookup_only" and check_summary.get("rebuilt_lookup_scope") == "governance_lookup_only", {"packet": packet_summary.get("lookup_scope"), "original": check_summary.get("original_lookup_scope"), "rebuilt": check_summary.get("rebuilt_lookup_scope")}, "lookup scope must remain governance only"),
        _check("lookup_ready", packet_summary.get("lookup_ready") is True and check_summary.get("original_lookup_ready") is True and check_summary.get("rebuilt_lookup_ready") is True, {"packet": packet_summary.get("lookup_ready"), "original": check_summary.get("original_lookup_ready"), "rebuilt": check_summary.get("rebuilt_lookup_ready")}, "lookup must be ready in packet and check"),
        _check("entries_present", int(packet_summary.get("entry_count") or 0) > 0 and len(entries) == int(packet_summary.get("entry_count") or 0), {"summary": packet_summary.get("entry_count"), "entries": len(entries)}, "lookup index requires at least one entry"),
        _check("entries_not_promoted", all(row.get("promotion_ready") is False for row in entries), [row.get("promotion_ready") for row in entries], "lookup entries must not be promoted"),
        _check("consumer_boundary_governance", packet_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, packet_summary.get("consumer_boundary"), "consumer boundary must remain governance lookup only"),
        _check("rejected_use_production_promotion", packet_summary.get("rejected_use") == "production_promotion" and check_summary.get("original_rejected_use") == "production_promotion" and check_summary.get("rebuilt_rejected_use") == "production_promotion", {"packet": packet_summary.get("rejected_use"), "original": check_summary.get("original_rejected_use"), "rebuilt": check_summary.get("rebuilt_rejected_use")}, "production promotion must stay rejected"),
        _check("promotion_still_false", packet_summary.get("promotion_ready") is False and check_summary.get("original_promotion_ready") is False and check_summary.get("rebuilt_promotion_ready") is False, {"packet": packet_summary.get("promotion_ready"), "original": check_summary.get("original_promotion_ready"), "rebuilt": check_summary.get("rebuilt_promotion_ready")}, "lookup index must not enable promotion"),
        _check("source_packet_checks_clean", int(packet_summary.get("failed_check_count") or 0) == 0, packet_summary.get("failed_check_count"), "source lookup packet checks must be clean"),
        _check("source_contract_checks_clean", int(check_summary.get("failed_check_count") or 0) == 0, check_summary.get("failed_check_count"), "source contract checks must be clean"),
    ]


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(path).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _index(
    status: str,
    packet_summary: dict[str, Any],
    packet: dict[str, Any],
    check_summary: dict[str, Any],
    lookup_packet_path: str | Path | None,
    lookup_packet_check_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    entries = list_of_dicts(packet.get("lookup_entries")) if ready else []
    return {
        "index_ready": ready,
        "lookup_index_id": LOOKUP_INDEX_ID if ready else "not_ready",
        "lookup_scope": "governance_lookup_only" if ready else "not_ready",
        "lookup_packet_path": str(lookup_packet_path or ""),
        "lookup_packet_check_path": str(lookup_packet_check_path or ""),
        "entry_count": len(entries),
        "lookup_entries": entries,
        "lookup_keys": list(packet.get("lookup_keys") or []) if ready else [],
        "lookup_ready": bool(ready and packet_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
        "bounded_publication_accepted": bool(ready and packet_summary.get("bounded_publication_accepted") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "allowed_use": "governance_lookup_only" if ready else "none",
        "rejected_use": "production_promotion",
        "evidence_count": 2 if ready else 0,
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_lookup_index",
    }


def _summary(status: str, check_rows: list[dict[str, Any]], index: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_lookup_index_ready": status == "pass" and index.get("index_ready") is True,
        "lookup_index_id": index.get("lookup_index_id"),
        "lookup_scope": index.get("lookup_scope"),
        "entry_count": index.get("entry_count"),
        "lookup_ready": index.get("lookup_ready"),
        "contract_check_ready": index.get("contract_check_ready"),
        "bounded_publication_accepted": index.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": index.get("consumer_boundary"),
        "allowed_use": index.get("allowed_use"),
        "rejected_use": index.get("rejected_use"),
        "evidence_count": index.get("evidence_count"),
        "next_step": index.get("next_step"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_lookup_index_ready"
    return "fix_randomized_holdout_publication_registry_lookup_index"


def _interpretation(status: str, index: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The lookup packet and contract check are not ready for lookup index publication.",
            "next_action": "repair lookup packet or contract check before index",
        }
    return {
        "model_quality_claim": "bounded_randomized_target_hidden_holdout_claim_only",
        "reason": "The lookup packet and its contract check are packaged into a governance lookup index while promotion remains rejected.",
        "next_action": str(index.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_lookup_index",
    "locate_randomized_holdout_publication_registry_lookup_packet",
    "locate_randomized_holdout_publication_registry_lookup_packet_check",
    "read_json_report",
    "resolve_exit_code",
]
