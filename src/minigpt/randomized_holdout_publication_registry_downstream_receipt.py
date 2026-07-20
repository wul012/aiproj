from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_registry_downstream_guard import (
    BLOCKED_USES,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_utils import path_exists as _path_exists


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_receipt.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_receipt.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_receipt.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_receipt.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_receipt.html"

RECEIPT_ID = "randomized-holdout-publication-registry-downstream-receipt-v939"
RECEIPT_TYPE = "randomized_holdout_publication_registry_downstream"


def locate_randomized_holdout_publication_registry_downstream_guard(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream receipt input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_receipt(
    downstream_guard_report: dict[str, Any],
    *,
    downstream_guard_path: str | Path | None = None,
    consumer_name: str = "publication_registry_governance_lookup_reader",
    requested_use: str = "downstream_governance_lookup_only",
    title: str = "MiniGPT randomized holdout publication registry downstream receipt",
    generated_at: str | None = None,
) -> dict[str, Any]:
    guard_summary = as_dict(downstream_guard_report.get("summary"))
    guard = as_dict(downstream_guard_report.get("guard"))
    entries = list_of_dicts(downstream_guard_report.get("entry_rows"))
    checks = _checks(downstream_guard_report, guard_summary, guard, entries, downstream_guard_path, requested_use)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    receipt = _receipt(status, guard_summary, guard, entries, downstream_guard_path, consumer_name, requested_use)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "downstream_guard_path": str(downstream_guard_path or ""),
        "downstream_guard_sha256": _sha256_file(downstream_guard_path),
        "source_downstream_guard_summary": guard_summary,
        "source_downstream_guard": guard,
        "entry_rows": entries,
        "consumer_receipts": _consumer_receipts(receipt, entries),
        "check_rows": checks,
        "receipt": receipt,
        "summary": _summary(status, checks, receipt),
        "interpretation": _interpretation(status, receipt),
    }


def resolve_exit_code(report: dict[str, Any], *, require_receipt_ready: bool, require_promotion_ready: bool = False) -> int:
    summary = as_dict(report.get("summary"))
    if require_receipt_ready and summary.get("randomized_holdout_publication_registry_downstream_receipt_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    guard_report: dict[str, Any],
    guard_summary: dict[str, Any],
    guard: dict[str, Any],
    entries: list[dict[str, Any]],
    guard_path: str | Path | None,
    requested_use: str,
) -> list[dict[str, Any]]:
    blocked_uses = list(guard_summary.get("blocked_uses") or [])
    lookup_keys = list(guard.get("lookup_keys") or [])
    return [
        _check("downstream_guard_file_exists", _path_exists(guard_path), str(guard_path or ""), "downstream guard file must exist"),
        _check("downstream_guard_passed", guard_report.get("status") == "pass", guard_report.get("status"), "downstream guard must pass"),
        _check("downstream_guard_decision_ready", guard_report.get("decision") == "randomized_holdout_publication_registry_downstream_guard_ready", guard_report.get("decision"), "downstream guard decision must be ready"),
        _check("guard_summary_ready", guard_summary.get("randomized_holdout_publication_registry_downstream_guard_ready") is True and guard.get("guard_ready") is True, {"summary": guard_summary.get("randomized_holdout_publication_registry_downstream_guard_ready"), "guard": guard.get("guard_ready")}, "guard summary and body must be ready"),
        _check("guard_status_allowed", guard_summary.get("guard_status") == "downstream_governance_lookup_allowed" and guard.get("guard_status") == "downstream_governance_lookup_allowed", {"summary": guard_summary.get("guard_status"), "guard": guard.get("guard_status")}, "guard must allow downstream governance lookup"),
        _check("requested_use_allowed", requested_use == "downstream_governance_lookup_only", requested_use, "requested use must stay downstream governance lookup only"),
        _check("blocked_uses_complete", all(use in blocked_uses for use in BLOCKED_USES), blocked_uses, "receipt must preserve all blocked uses"),
        _check("promotion_still_false", guard_summary.get("promotion_ready") is False and guard.get("promotion_ready") is False, {"summary": guard_summary.get("promotion_ready"), "guard": guard.get("promotion_ready")}, "receipt must not enable promotion"),
        _check("approved_for_promotion_false", guard_summary.get("approved_for_promotion") is False and guard.get("approved_for_promotion") is False, {"summary": guard_summary.get("approved_for_promotion"), "guard": guard.get("approved_for_promotion")}, "receipt must not approve production promotion"),
        _check("downstream_lookup_ready", guard_summary.get("downstream_ready") is True and guard_summary.get("lookup_ready") is True, {"downstream": guard_summary.get("downstream_ready"), "lookup": guard_summary.get("lookup_ready")}, "downstream lookup must be ready"),
        _check("contract_check_ready", guard_summary.get("contract_check_ready") is True, guard_summary.get("contract_check_ready"), "source contract check must be ready"),
        _check("consumer_boundary_governance", guard_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY and guard.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, {"summary": guard_summary.get("consumer_boundary"), "guard": guard.get("consumer_boundary")}, "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", guard.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, guard.get("model_quality_claim"), "model quality claim must remain bounded"),
        _check("entries_present", len(entries) == int(guard_summary.get("entry_count") or 0) and len(entries) > 0, {"entries": len(entries), "summary_entry_count": guard_summary.get("entry_count")}, "receipt must cover all source entries"),
        _check("lookup_keys_publication_namespace", len(lookup_keys) == len(entries) and all(str(key).startswith("publication:") for key in lookup_keys), lookup_keys, "lookup keys must use publication namespace"),
        _check("entries_not_promoted", all(row.get("promotion_ready") is False for row in entries), [row.get("promotion_ready") for row in entries], "entries must not be promoted"),
        _check("source_checks_clean", int(guard_summary.get("failed_check_count") or 0) == 0, guard_summary.get("failed_check_count"), "source guard checks must be clean"),
        _check("source_next_step_matches", guard_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_NEXT_STEP, guard_summary.get("next_step"), "source guard must route to downstream receipt"),
    ]


def _receipt(
    status: str,
    guard_summary: dict[str, Any],
    guard: dict[str, Any],
    entries: list[dict[str, Any]],
    guard_path: str | Path | None,
    consumer_name: str,
    requested_use: str,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "receipt_ready": ready,
        "receipt_id": RECEIPT_ID if ready else "not_ready",
        "receipt_type": RECEIPT_TYPE,
        "receipt_status": "downstream_governance_lookup_receipted" if ready else "blocked",
        "consumer_name": consumer_name,
        "requested_use": requested_use,
        "granted_use": "downstream_governance_lookup_only" if ready else "none",
        "downstream_guard_path": str(guard_path or ""),
        "entry_count": len(entries) if ready else 0,
        "lookup_keys": list(guard.get("lookup_keys") or []) if ready else [],
        "guard_id": guard_summary.get("guard_id") if ready else "not_ready",
        "guard_status": guard_summary.get("guard_status") if ready else "not_ready",
        "blocked_uses": list(guard_summary.get("blocked_uses") or BLOCKED_USES),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_receipt",
    }


def _consumer_receipts(receipt: dict[str, Any], entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "consumer_name": receipt.get("consumer_name"),
            "lookup_key": row.get("lookup_key"),
            "entry_id": row.get("entry_id"),
            "granted_use": receipt.get("granted_use"),
            "blocked_uses": receipt.get("blocked_uses"),
            "promotion_ready": False,
            "receipt_status": receipt.get("receipt_status"),
        }
        for row in entries
    ]


def _summary(status: str, checks: list[dict[str, Any]], receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_receipt_ready": status == "pass" and receipt.get("receipt_ready") is True,
        "receipt_id": receipt.get("receipt_id"),
        "receipt_type": receipt.get("receipt_type"),
        "receipt_status": receipt.get("receipt_status"),
        "consumer_name": receipt.get("consumer_name"),
        "granted_use": receipt.get("granted_use"),
        "entry_count": receipt.get("entry_count"),
        "lookup_key_count": len(list(receipt.get("lookup_keys") or [])),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": receipt.get("consumer_boundary"),
        "blocked_uses": receipt.get("blocked_uses"),
        "next_step": receipt.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_receipt_ready"
    return "fix_randomized_holdout_publication_registry_downstream_receipt"


def _interpretation(status: str, receipt: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream guard is not ready to be receipted.",
            "next_action": "repair downstream guard before recording receipt",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream consumer receipt grants governance lookup only and keeps promotion and claim expansion blocked.",
        "next_action": str(receipt.get("next_step")),
    }


def _sha256_file(path: str | Path | None) -> str:
    if not path or not Path(path).is_file():
        return ""
    return sha256(Path(path).read_bytes()).hexdigest()


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_receipt",
    "locate_randomized_holdout_publication_registry_downstream_guard",
    "read_json_report",
    "resolve_exit_code",
]
