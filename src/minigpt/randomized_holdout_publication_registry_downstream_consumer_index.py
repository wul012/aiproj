from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import blocked_uses_complete, downstream_lookup_use, is_downstream_lookup_only
from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_JSON_FILENAME,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_CHECK_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_index.html"

CONSUMER_INDEX_ID = "randomized-holdout-publication-registry-downstream-consumer-index-v943"


def locate_randomized_holdout_publication_registry_downstream_consumer_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_JSON_FILENAME
    return source


def locate_randomized_holdout_publication_registry_downstream_consumer_packet_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer index input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_index(
    consumer_packet_report: dict[str, Any],
    consumer_packet_check_report: dict[str, Any],
    *,
    consumer_packet_path: str | Path | None = None,
    consumer_packet_check_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer index",
    generated_at: str | None = None,
) -> dict[str, Any]:
    packet_summary = as_dict(consumer_packet_report.get("summary"))
    packet = as_dict(consumer_packet_report.get("packet"))
    check_summary = as_dict(consumer_packet_check_report.get("summary"))
    packet_rows = list_of_dicts(consumer_packet_report.get("packet_rows"))
    checks = _checks(
        consumer_packet_report,
        consumer_packet_check_report,
        packet_summary,
        packet,
        packet_rows,
        check_summary,
        consumer_packet_path,
        consumer_packet_check_path,
    )
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    index = _index(status, packet_summary, packet, packet_rows, check_summary, consumer_packet_path, consumer_packet_check_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "consumer_packet_path": str(consumer_packet_path or ""),
        "consumer_packet_check_path": str(consumer_packet_check_path or ""),
        "source_consumer_packet_summary": packet_summary,
        "source_consumer_packet_check_summary": check_summary,
        "packet_rows": packet_rows,
        "check_rows": checks,
        "consumer_index": index,
        "summary": _summary(status, checks, index),
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
    if require_index_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_index_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    packet_report: dict[str, Any],
    packet_check_report: dict[str, Any],
    packet_summary: dict[str, Any],
    packet: dict[str, Any],
    packet_rows: list[dict[str, Any]],
    check_summary: dict[str, Any],
    packet_path: str | Path | None,
    check_path: str | Path | None,
) -> list[dict[str, Any]]:
    packet_keys = list(packet.get("lookup_keys") or [])
    return [
        _check("consumer_packet_file_exists", _path_exists(packet_path), str(packet_path or ""), "consumer packet file must exist"),
        _check("consumer_packet_check_file_exists", _path_exists(check_path), str(check_path or ""), "consumer packet check file must exist"),
        _check("consumer_packet_passed", packet_report.get("status") == "pass", packet_report.get("status"), "consumer packet must pass"),
        _check("consumer_packet_decision_ready", packet_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_packet_ready", packet_report.get("decision"), "consumer packet decision must be ready"),
        _check("consumer_packet_summary_ready", packet_summary.get("randomized_holdout_publication_registry_downstream_consumer_packet_ready") is True and packet.get("packet_ready") is True, {"summary": packet_summary.get("randomized_holdout_publication_registry_downstream_consumer_packet_ready"), "packet": packet.get("packet_ready")}, "consumer packet summary and body must be ready"),
        _check("consumer_packet_check_passed", packet_check_report.get("status") == "pass", packet_check_report.get("status"), "consumer packet check must pass"),
        _check("consumer_packet_check_decision_ready", packet_check_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_packet_contract_check_passed", packet_check_report.get("decision"), "consumer packet check decision must pass"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "consumer packet contract check must be ready"),
        _check("lookup_keys_match_check", packet_keys == list(check_summary.get("original_lookup_keys") or []) == list(check_summary.get("rebuilt_lookup_keys") or []), {"packet": packet_keys, "original": check_summary.get("original_lookup_keys"), "rebuilt": check_summary.get("rebuilt_lookup_keys")}, "lookup keys must match the contract check"),
        _check("lookup_ready", packet_summary.get("lookup_ready") is True, packet_summary.get("lookup_ready"), "consumer index requires lookup-ready packet"),
        _check("granted_use_lookup_only", is_downstream_lookup_only(packet_summary.get("granted_use")) and is_downstream_lookup_only(check_summary.get("original_granted_use")) and is_downstream_lookup_only(check_summary.get("rebuilt_granted_use")), {"packet": packet_summary.get("granted_use"), "original": check_summary.get("original_granted_use"), "rebuilt": check_summary.get("rebuilt_granted_use")}, "granted use must stay downstream lookup only"),
        _check("blocked_uses_complete", blocked_uses_complete(packet_summary.get("blocked_uses")), packet_summary.get("blocked_uses"), "consumer index must preserve all blocked uses"),
        _check("packet_rows_present", len(packet_rows) == int(packet_summary.get("entry_count") or 0) and len(packet_rows) > 0, {"packet_rows": len(packet_rows), "entry_count": packet_summary.get("entry_count")}, "consumer index requires packet rows"),
        _check("packet_rows_not_promoted", all(row.get("promotion_ready") is False for row in packet_rows), [row.get("promotion_ready") for row in packet_rows], "packet rows must not be promoted"),
        _check("consumer_boundary_governance", packet_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, packet_summary.get("consumer_boundary"), "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", packet_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, packet_summary.get("model_quality_claim"), "model quality claim must remain bounded"),
        _check("promotion_still_false", packet_summary.get("promotion_ready") is False and check_summary.get("original_promotion_ready") is False and check_summary.get("rebuilt_promotion_ready") is False, {"packet": packet_summary.get("promotion_ready"), "original": check_summary.get("original_promotion_ready"), "rebuilt": check_summary.get("rebuilt_promotion_ready")}, "consumer index must not enable promotion"),
        _check("source_packet_checks_clean", int(packet_summary.get("failed_check_count") or 0) == 0, packet_summary.get("failed_check_count"), "source consumer packet checks must be clean"),
        _check("source_contract_checks_clean", int(check_summary.get("failed_check_count") or 0) == 0, check_summary.get("failed_check_count"), "source contract checks must be clean"),
    ]


def _index(
    status: str,
    packet_summary: dict[str, Any],
    packet: dict[str, Any],
    packet_rows: list[dict[str, Any]],
    check_summary: dict[str, Any],
    packet_path: str | Path | None,
    check_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    rows = packet_rows if ready else []
    return {
        "index_ready": ready,
        "consumer_index_id": CONSUMER_INDEX_ID if ready else "not_ready",
        "lookup_scope": downstream_lookup_use() if ready else "not_ready",
        "consumer_packet_path": str(packet_path or ""),
        "consumer_packet_check_path": str(check_path or ""),
        "consumer_name": packet_summary.get("consumer_name") if ready else "",
        "entry_count": len(rows),
        "packet_rows": rows,
        "lookup_keys": list(packet.get("lookup_keys") or []) if ready else [],
        "lookup_ready": bool(ready and packet_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
        "granted_use": downstream_lookup_use() if ready else "none",
        "blocked_uses": list(packet_summary.get("blocked_uses") or []),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "evidence_count": 2 if ready else 0,
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_index",
    }


def _summary(status: str, check_rows: list[dict[str, Any]], index: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_index_ready": status == "pass" and index.get("index_ready") is True,
        "consumer_index_id": index.get("consumer_index_id"),
        "lookup_scope": index.get("lookup_scope"),
        "consumer_name": index.get("consumer_name"),
        "entry_count": index.get("entry_count"),
        "lookup_key_count": len(list(index.get("lookup_keys") or [])),
        "lookup_ready": index.get("lookup_ready"),
        "contract_check_ready": index.get("contract_check_ready"),
        "granted_use": index.get("granted_use"),
        "blocked_uses": index.get("blocked_uses"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": index.get("consumer_boundary"),
        "model_quality_claim": index.get("model_quality_claim"),
        "evidence_count": index.get("evidence_count"),
        "next_step": index.get("next_step"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_index_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_index"


def _interpretation(status: str, index: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream consumer packet and contract check are not ready for consumer index publication.",
            "next_action": "repair consumer packet or contract check before index",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream consumer packet and its contract check are packaged into a lookup-only consumer index while promotion remains blocked.",
        "next_action": str(index.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_index",
    "locate_randomized_holdout_publication_registry_downstream_consumer_packet",
    "locate_randomized_holdout_publication_registry_downstream_consumer_packet_check",
    "read_json_report",
    "resolve_exit_code",
]
