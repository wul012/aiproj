from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CHECK_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_NEXT_STEP,
)
from minigpt.randomized_holdout_publication_downstream_common import blocked_uses_complete, downstream_lookup_use, is_downstream_lookup_only, sha256_file
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_JSON_FILENAME,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CHECK_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_JSON_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_CSV_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_TEXT_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_HTML_FILENAME = "randomized_holdout_publication_registry_downstream_consumer_ack_bundle.html"

BUNDLE_ID = "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-v947"


def locate_randomized_holdout_publication_registry_downstream_consumer_ack(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_JSON_FILENAME
    return source


def locate_randomized_holdout_publication_registry_downstream_consumer_ack_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry downstream consumer ack bundle input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(
    consumer_ack_report: dict[str, Any],
    consumer_ack_check_report: dict[str, Any],
    *,
    consumer_ack_path: str | Path | None = None,
    consumer_ack_check_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication registry downstream consumer ack bundle",
    generated_at: str | None = None,
) -> dict[str, Any]:
    ack_summary = as_dict(consumer_ack_report.get("summary"))
    ack = as_dict(consumer_ack_report.get("ack"))
    check_summary = as_dict(consumer_ack_check_report.get("summary"))
    checks = _checks(consumer_ack_report, consumer_ack_check_report, ack_summary, ack, check_summary, consumer_ack_path, consumer_ack_check_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    evidence_rows = _evidence_rows(status, consumer_ack_report, consumer_ack_check_report, consumer_ack_path, consumer_ack_check_path)
    bundle = _bundle(status, ack_summary, ack, check_summary, evidence_rows, consumer_ack_path, consumer_ack_check_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "consumer_ack_path": str(consumer_ack_path or ""),
        "consumer_ack_check_path": str(consumer_ack_check_path or ""),
        "source_consumer_ack_summary": ack_summary,
        "source_consumer_ack_check_summary": check_summary,
        "lookup_rows": list_of_dicts(consumer_ack_report.get("lookup_rows")),
        "evidence_rows": evidence_rows,
        "check_rows": checks,
        "bundle": bundle,
        "summary": _summary(status, checks, bundle),
        "interpretation": _interpretation(status, bundle),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_bundle_ready: bool,
    require_lookup_ready: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_bundle_ready and summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready") is not True:
        return 1
    if require_lookup_ready and summary.get("lookup_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    ack_report: dict[str, Any],
    ack_check_report: dict[str, Any],
    ack_summary: dict[str, Any],
    ack: dict[str, Any],
    check_summary: dict[str, Any],
    ack_path: str | Path | None,
    check_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("consumer_ack_file_exists", _path_exists(ack_path), str(ack_path or ""), "consumer ack file must exist"),
        _check("consumer_ack_check_file_exists", _path_exists(check_path), str(check_path or ""), "consumer ack check file must exist"),
        _check("consumer_ack_passed", ack_report.get("status") == "pass", ack_report.get("status"), "consumer ack must pass"),
        _check("consumer_ack_decision_ready", ack_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_ready", ack_report.get("decision"), "consumer ack decision must be ready"),
        _check("consumer_ack_summary_ready", ack_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_ready") is True and ack.get("ack_ready") is True, {"summary": ack_summary.get("randomized_holdout_publication_registry_downstream_consumer_ack_ready"), "ack": ack.get("ack_ready")}, "consumer ack summary and body must be ready"),
        _check("consumer_ack_check_passed", ack_check_report.get("status") == "pass", ack_check_report.get("status"), "consumer ack contract check must pass"),
        _check("consumer_ack_check_decision_ready", ack_check_report.get("decision") == "randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed", ack_check_report.get("decision"), "consumer ack check decision must pass"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "consumer ack check must be contract-ready"),
        _check("acked_use_lookup_only", is_downstream_lookup_only(ack_summary.get("acked_use")) and is_downstream_lookup_only(check_summary.get("original_acked_use")) and is_downstream_lookup_only(check_summary.get("rebuilt_acked_use")), {"ack": ack_summary.get("acked_use"), "original": check_summary.get("original_acked_use"), "rebuilt": check_summary.get("rebuilt_acked_use")}, "acked use must remain downstream lookup only"),
        _check("blocked_uses_complete", blocked_uses_complete(ack_summary.get("blocked_uses")), ack_summary.get("blocked_uses"), "blocked uses must remain complete"),
        _check("lookup_ready", ack_summary.get("lookup_ready") is True, ack_summary.get("lookup_ready"), "bundle requires lookup-ready ack"),
        _check("downstream_ready", ack_summary.get("downstream_ready") is True, ack_summary.get("downstream_ready"), "bundle requires downstream-ready ack"),
        _check("lookup_rows_present", int(ack_summary.get("entry_count") or 0) > 0 and int(ack_summary.get("lookup_key_count") or 0) == int(ack_summary.get("entry_count") or 0), {"entry_count": ack_summary.get("entry_count"), "lookup_key_count": ack_summary.get("lookup_key_count")}, "bundle requires lookup rows"),
        _check("consumer_boundary_governance", ack_summary.get("consumer_boundary") == RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY, ack_summary.get("consumer_boundary"), "consumer boundary must remain governance lookup only"),
        _check("model_quality_claim_bounded", ack_summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, ack_summary.get("model_quality_claim"), "model quality claim must remain bounded"),
        _check("promotion_still_false", ack_summary.get("promotion_ready") is False and check_summary.get("original_promotion_ready") is False and check_summary.get("rebuilt_promotion_ready") is False, {"ack": ack_summary.get("promotion_ready"), "original": check_summary.get("original_promotion_ready"), "rebuilt": check_summary.get("rebuilt_promotion_ready")}, "bundle must not enable promotion"),
        _check("source_ack_checks_clean", int(ack_summary.get("failed_check_count") or 0) == 0, ack_summary.get("failed_check_count"), "source ack checks must be clean"),
        _check("source_contract_checks_clean", int(check_summary.get("failed_check_count") or 0) == 0, check_summary.get("failed_check_count"), "source contract checks must be clean"),
        _check("source_ack_next_step_matches", ack_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_NEXT_STEP, ack_summary.get("next_step"), "ack must route to contract check"),
        _check("source_check_next_step_matches", check_summary.get("next_step") == RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CHECK_NEXT_STEP, check_summary.get("next_step"), "ack check must route to bundle"),
    ]


def _evidence_rows(
    status: str,
    ack_report: dict[str, Any],
    ack_check_report: dict[str, Any],
    ack_path: str | Path | None,
    check_path: str | Path | None,
) -> list[dict[str, Any]]:
    if status != "pass":
        return []
    return [
        _evidence_row("downstream_consumer_ack", ack_report, ack_path),
        _evidence_row("downstream_consumer_ack_contract_check", ack_check_report, check_path),
    ]


def _evidence_row(kind: str, report: dict[str, Any], path: str | Path | None) -> dict[str, Any]:
    source = Path(path) if path else None
    return {
        "kind": kind,
        "path": str(path or ""),
        "sha256": sha256_file(source) if source and source.exists() else "",
        "status": report.get("status"),
        "decision": report.get("decision"),
        "failed_count": report.get("failed_count"),
    }


def _bundle(
    status: str,
    ack_summary: dict[str, Any],
    ack: dict[str, Any],
    check_summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    ack_path: str | Path | None,
    check_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "bundle_ready": ready,
        "bundle_id": BUNDLE_ID if ready else "not_ready",
        "bundle_status": "ready_for_downstream_consumer_ack_review" if ready else "blocked",
        "consumer_ack_path": str(ack_path or ""),
        "consumer_ack_check_path": str(check_path or ""),
        "consumer_name": ack_summary.get("consumer_name") if ready else "",
        "entry_count": ack_summary.get("entry_count") if ready else 0,
        "lookup_key_count": ack_summary.get("lookup_key_count") if ready else 0,
        "lookup_keys": list(ack.get("lookup_keys") or []) if ready else [],
        "lookup_ready": bool(ready and ack_summary.get("lookup_ready") is True),
        "contract_check_ready": bool(ready and check_summary.get("contract_check_ready") is True),
        "acked_use": downstream_lookup_use() if ready else "none",
        "evidence_rows": evidence_rows,
        "evidence_count": len(evidence_rows),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY if ready else "not_ready",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_NEXT_STEP if ready else "repair_randomized_holdout_publication_registry_downstream_consumer_ack_bundle",
    }


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(path).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, checks: list[dict[str, Any]], bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready": status == "pass" and bundle.get("bundle_ready") is True,
        "bundle_id": bundle.get("bundle_id"),
        "bundle_status": bundle.get("bundle_status"),
        "consumer_name": bundle.get("consumer_name"),
        "entry_count": bundle.get("entry_count"),
        "lookup_key_count": bundle.get("lookup_key_count"),
        "lookup_ready": bundle.get("lookup_ready"),
        "contract_check_ready": bundle.get("contract_check_ready"),
        "acked_use": bundle.get("acked_use"),
        "evidence_count": bundle.get("evidence_count"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "consumer_boundary": bundle.get("consumer_boundary"),
        "model_quality_claim": bundle.get("model_quality_claim"),
        "next_step": bundle.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready"
    return "fix_randomized_holdout_publication_registry_downstream_consumer_ack_bundle"


def _interpretation(status: str, bundle: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The downstream consumer acknowledgement and contract check are not ready for bundling.",
            "next_action": "repair downstream consumer ack or check before bundle",
        }
    return {
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
        "reason": "The downstream consumer acknowledgement and its contract check are bundled for lookup-only review while promotion remains blocked.",
        "next_action": str(bundle.get("next_step")),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack",
    "locate_randomized_holdout_publication_registry_downstream_consumer_ack_check",
    "read_json_report",
    "resolve_exit_code",
]
