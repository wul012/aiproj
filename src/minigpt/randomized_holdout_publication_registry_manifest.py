from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE,
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_packet import RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_JSON_FILENAME
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_JSON_FILENAME = "randomized_holdout_publication_registry_manifest.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_CSV_FILENAME = "randomized_holdout_publication_registry_manifest.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_TEXT_FILENAME = "randomized_holdout_publication_registry_manifest.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_manifest.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_HTML_FILENAME = "randomized_holdout_publication_registry_manifest.html"

MANIFEST_ID = "randomized-holdout-publication-registry-manifest-v932"
NEXT_STEP = "review_randomized_holdout_publication_registry_manifest"


def locate_randomized_holdout_publication_registry_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry manifest input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_manifest(
    registry_packet_report: dict[str, Any],
    *,
    registry_packet_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry manifest",
    generated_at: str | None = None,
) -> dict[str, Any]:
    packet_summary = as_dict(registry_packet_report.get("summary"))
    packet = as_dict(registry_packet_report.get("packet"))
    checks = _checks(registry_packet_report, packet_summary, packet, registry_packet_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    manifest = _manifest(status, packet_summary, packet, registry_packet_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "registry_packet_path": str(registry_packet_path or ""),
        "source_packet_summary": packet_summary,
        "source_packet": packet,
        "check_rows": checks,
        "manifest": manifest,
        "summary": _summary(status, checks, manifest),
        "interpretation": _interpretation(status, manifest),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_manifest_ready: bool,
    require_bounded_publication: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_manifest_ready and summary.get("randomized_holdout_publication_registry_manifest_ready") is not True:
        return 1
    if require_bounded_publication and summary.get("bounded_publication_accepted") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(packet_report: dict[str, Any], packet_summary: dict[str, Any], packet: dict[str, Any], packet_path: str | Path | None) -> list[dict[str, Any]]:
    return [
        _check("registry_packet_file_exists", _path_exists(packet_path), str(packet_path or ""), "registry packet file must exist"),
        _check("registry_packet_passed", packet_report.get("status") == "pass", packet_report.get("status"), "registry packet must pass"),
        _check("registry_packet_decision_ready", packet_report.get("decision") == "randomized_holdout_publication_registry_packet_ready", packet_report.get("decision"), "registry packet decision must be ready"),
        _check("packet_summary_ready", packet_summary.get("randomized_holdout_publication_registry_packet_ready") is True and packet.get("packet_ready") is True, {"summary": packet_summary.get("randomized_holdout_publication_registry_packet_ready"), "packet": packet.get("packet_ready")}, "registry packet summary and body must be ready"),
        _check("handoff_manifest_ready", packet_summary.get("handoff_status") == "ready_for_publication_registry_manifest", packet_summary.get("handoff_status"), "packet must route to registry manifest"),
        _check("registry_status_registered", packet_summary.get("registry_status") == "registered", packet_summary.get("registry_status"), "manifest only accepts registered entries"),
        _check("contract_check_ready", packet_summary.get("contract_check_ready") is True, packet_summary.get("contract_check_ready"), "packet must carry a ready contract check"),
        _check("bounded_publication_accepted", packet_summary.get("bounded_publication_accepted") is True, packet_summary.get("bounded_publication_accepted"), "manifest only accepts bounded publication entries"),
        _check("consumer_boundary_governance", packet_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, packet_summary.get("consumer_boundary"), "consumer boundary must remain governance lookup only"),
        _check("allowed_use_bounded", packet_summary.get("allowed_use") == RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE, packet_summary.get("allowed_use"), "allowed use must stay bounded governance only"),
        _check("model_quality_claim_bounded", packet_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, packet_summary.get("model_quality_claim"), "model quality claim must stay bounded"),
        _check("promotion_still_false", packet_summary.get("promotion_ready") is False, packet_summary.get("promotion_ready"), "manifest must not enable direct promotion"),
        _check("approved_for_promotion_false", packet_summary.get("approved_for_promotion") is False, packet_summary.get("approved_for_promotion"), "manifest must not approve direct promotion"),
        _check("evidence_count", int(packet_summary.get("evidence_count") or 0) >= 2, packet_summary.get("evidence_count"), "manifest expects registry entry and contract check evidence"),
        _check("source_checks_clean", int(packet_summary.get("failed_check_count") or 0) == 0, packet_summary.get("failed_check_count"), "source packet checks must be clean"),
        _check("source_next_step_matches", packet_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_NEXT_STEP, packet_summary.get("next_step"), "source packet must route to registry manifest build"),
    ]


def _manifest(status: str, packet_summary: dict[str, Any], packet: dict[str, Any], packet_path: str | Path | None) -> dict[str, Any]:
    ready = status == "pass"
    entry = {
        "entry_id": packet_summary.get("entry_id"),
        "registry_status": packet_summary.get("registry_status"),
        "bounded_publication_accepted": packet_summary.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "accepted_claim_count": packet_summary.get("accepted_claim_count"),
        "blocked_claim_count": packet_summary.get("blocked_claim_count"),
        "candidate_case_count": packet_summary.get("candidate_case_count"),
        "random_seed": packet_summary.get("random_seed"),
        "pass_rate": packet_summary.get("pass_rate"),
        "allowed_use": packet_summary.get("allowed_use"),
        "model_quality_claim": packet_summary.get("model_quality_claim"),
        "consumer_boundary": packet_summary.get("consumer_boundary"),
    }
    return {
        "manifest_ready": ready,
        "manifest_id": MANIFEST_ID if ready else "not_ready",
        "manifest_scope": "bounded_publication_registry_manifest_only" if ready else "not_ready",
        "registry_packet_path": str(packet_path or ""),
        "entry_count": 1 if ready else 0,
        "entries": [entry] if ready else [],
        "entry_id": packet_summary.get("entry_id"),
        "registry_status": packet_summary.get("registry_status"),
        "contract_check_ready": bool(ready and packet_summary.get("contract_check_ready") is True and packet.get("contract_check_ready") is True),
        "bounded_publication_accepted": bool(ready and packet_summary.get("bounded_publication_accepted") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "next_step": NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_manifest",
    }


def _summary(status: str, checks: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_manifest_ready": status == "pass" and manifest.get("manifest_ready") is True,
        "manifest_id": manifest.get("manifest_id"),
        "manifest_scope": manifest.get("manifest_scope"),
        "entry_count": manifest.get("entry_count"),
        "entry_id": manifest.get("entry_id"),
        "registry_status": manifest.get("registry_status"),
        "contract_check_ready": manifest.get("contract_check_ready"),
        "bounded_publication_accepted": manifest.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": manifest.get("consumer_boundary"),
        "next_step": manifest.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_manifest_ready"
    return "fix_randomized_holdout_publication_registry_manifest"


def _interpretation(status: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout publication registry packet is not ready for manifest build.",
            "next_action": "repair registry packet before manifest",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The verified publication registry packet is summarized into a bounded governance manifest while direct promotion remains blocked.",
        "next_action": manifest.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_manifest",
    "locate_randomized_holdout_publication_registry_packet",
    "read_json_report",
    "resolve_exit_code",
]
