from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_registry_entry import RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME
from minigpt.randomized_holdout_publication_registry_entry_check import RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_JSON_FILENAME
from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE,
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_NEXT_STEP,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_JSON_FILENAME = "randomized_holdout_publication_registry_packet.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_CSV_FILENAME = "randomized_holdout_publication_registry_packet.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_TEXT_FILENAME = "randomized_holdout_publication_registry_packet.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_packet.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_HTML_FILENAME = "randomized_holdout_publication_registry_packet.html"

def locate_randomized_holdout_publication_registry_entry(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME
    return source


def locate_randomized_holdout_publication_registry_entry_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry packet input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_packet(
    registry_entry_report: dict[str, Any],
    registry_entry_check_report: dict[str, Any],
    *,
    registry_entry_path: str | Path | None = None,
    registry_entry_check_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry packet",
    generated_at: str | None = None,
) -> dict[str, Any]:
    entry_summary = as_dict(registry_entry_report.get("summary"))
    check_summary = as_dict(registry_entry_check_report.get("summary"))
    evidence_rows = _evidence_rows(registry_entry_path, registry_entry_check_path)
    checks = _checks(registry_entry_report, registry_entry_check_report, entry_summary, check_summary, evidence_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    packet = _packet(status, entry_summary, check_summary, evidence_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "registry_entry_path": str(registry_entry_path or ""),
        "registry_entry_check_path": str(registry_entry_check_path or ""),
        "source_registry_entry_summary": entry_summary,
        "source_registry_entry_check_summary": check_summary,
        "evidence_rows": evidence_rows,
        "check_rows": checks,
        "packet": packet,
        "summary": _summary(status, checks, packet),
        "interpretation": _interpretation(status, packet),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_packet_ready: bool,
    require_bounded_publication: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_packet_ready and summary.get("randomized_holdout_publication_registry_packet_ready") is not True:
        return 1
    if require_bounded_publication and summary.get("bounded_publication_accepted") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _evidence_rows(entry_path: str | Path | None, check_path: str | Path | None) -> list[dict[str, Any]]:
    return [
        _evidence("registry_entry", entry_path),
        _evidence("registry_entry_contract_check", check_path),
    ]


def _evidence(kind: str, path: str | Path | None) -> dict[str, Any]:
    text = str(path or "")
    return {"kind": kind, "path": text, "exists": Path(text).exists() if text else False}


def _checks(
    entry_report: dict[str, Any],
    check_report: dict[str, Any],
    entry_summary: dict[str, Any],
    check_summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("evidence_files_exist", all(row.get("exists") is True for row in evidence_rows), evidence_rows, "registry packet evidence files must exist"),
        _check("entry_passed", entry_report.get("status") == "pass", entry_report.get("status"), "registry entry must pass"),
        _check("entry_ready_decision", entry_report.get("decision") == "randomized_holdout_publication_registry_entry_ready", entry_report.get("decision"), "registry entry decision must be ready"),
        _check("entry_summary_ready", entry_summary.get("randomized_holdout_publication_registry_entry_ready") is True, entry_summary.get("randomized_holdout_publication_registry_entry_ready"), "registry entry summary must be ready"),
        _check("entry_registered", entry_summary.get("registry_status") == "registered", entry_summary.get("registry_status"), "registry entry must be registered"),
        _check("contract_check_passed", check_report.get("status") == "pass", check_report.get("status"), "registry entry contract check must pass"),
        _check("contract_check_decision_passed", check_report.get("decision") == "randomized_holdout_publication_registry_entry_contract_check_passed", check_report.get("decision"), "contract check decision must pass"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "contract check summary must be ready"),
        _check("entry_id_matches_check", entry_summary.get("entry_id") == check_summary.get("original_entry_id") == check_summary.get("rebuilt_entry_id"), {"entry": entry_summary.get("entry_id"), "original": check_summary.get("original_entry_id"), "rebuilt": check_summary.get("rebuilt_entry_id")}, "entry id must match original and rebuilt check values"),
        _check("bounded_publication_accepted", entry_summary.get("bounded_publication_accepted") is True and check_summary.get("original_bounded_publication_accepted") is True and check_summary.get("rebuilt_bounded_publication_accepted") is True, {"entry": entry_summary.get("bounded_publication_accepted"), "original": check_summary.get("original_bounded_publication_accepted"), "rebuilt": check_summary.get("rebuilt_bounded_publication_accepted")}, "packet only accepts bounded publication-ready entries"),
        _check("consumer_boundary_governance", entry_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and check_summary.get("original_consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and check_summary.get("rebuilt_consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"entry": entry_summary.get("consumer_boundary"), "original": check_summary.get("original_consumer_boundary"), "rebuilt": check_summary.get("rebuilt_consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("allowed_use_bounded", entry_summary.get("allowed_use") == RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE, entry_summary.get("allowed_use"), "allowed use must stay bounded governance only"),
        _check("model_quality_claim_bounded", entry_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, entry_summary.get("model_quality_claim"), "model quality claim must stay bounded"),
        _check("promotion_still_false", entry_summary.get("promotion_ready") is False, entry_summary.get("promotion_ready"), "packet must not enable direct promotion"),
        _check("approved_for_promotion_false", entry_summary.get("approved_for_promotion") is False, entry_summary.get("approved_for_promotion"), "packet must not approve direct promotion"),
        _check("source_checks_clean", int(entry_summary.get("failed_check_count") or 0) == 0 and int(check_summary.get("failed_check_count") or 0) == 0, {"entry": entry_summary.get("failed_check_count"), "check": check_summary.get("failed_check_count")}, "entry and contract check must have no failed checks"),
    ]


def _packet(status: str, entry_summary: dict[str, Any], check_summary: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "packet_ready": ready,
        "handoff_status": "ready_for_publication_registry_manifest" if ready else "repair_publication_registry_entry_or_check",
        "entry_id": entry_summary.get("entry_id"),
        "registry_status": entry_summary.get("registry_status"),
        "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
        "bounded_publication_accepted": bool(ready and entry_summary.get("bounded_publication_accepted") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "accepted_claim_count": entry_summary.get("accepted_claim_count"),
        "blocked_claim_count": entry_summary.get("blocked_claim_count"),
        "candidate_case_count": entry_summary.get("candidate_case_count"),
        "random_seed": entry_summary.get("random_seed"),
        "pass_rate": entry_summary.get("pass_rate"),
        "allowed_use": RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE if ready else "none",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "evidence_count": len(evidence_rows),
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_packet",
    }


def _summary(status: str, checks: list[dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_packet_ready": status == "pass" and packet.get("packet_ready") is True,
        "handoff_status": packet.get("handoff_status"),
        "entry_id": packet.get("entry_id"),
        "registry_status": packet.get("registry_status"),
        "contract_check_ready": packet.get("contract_check_ready"),
        "bounded_publication_accepted": packet.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "accepted_claim_count": packet.get("accepted_claim_count"),
        "blocked_claim_count": packet.get("blocked_claim_count"),
        "candidate_case_count": packet.get("candidate_case_count"),
        "random_seed": packet.get("random_seed"),
        "pass_rate": packet.get("pass_rate"),
        "allowed_use": packet.get("allowed_use"),
        "model_quality_claim": packet.get("model_quality_claim"),
        "consumer_boundary": packet.get("consumer_boundary"),
        "evidence_count": packet.get("evidence_count"),
        "next_step": packet.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_packet_ready"
    return "fix_randomized_holdout_publication_registry_packet"


def _interpretation(status: str, packet: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout publication registry entry and contract check are not ready for packet handoff.",
            "next_action": "repair registry entry or registry entry contract check",
        }
    return {
        "model_quality_claim": packet.get("model_quality_claim"),
        "reason": "The verified registry entry is packaged for publication registry manifest consumption while direct promotion remains blocked.",
        "next_action": packet.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_packet",
    "locate_randomized_holdout_publication_registry_entry",
    "locate_randomized_holdout_publication_registry_entry_check",
    "read_json_report",
    "resolve_exit_code",
]
