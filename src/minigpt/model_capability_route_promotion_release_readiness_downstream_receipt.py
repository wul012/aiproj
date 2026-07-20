from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_readiness_summary_check import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, string_list, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_JSON_FILENAME = "model_capability_route_promotion_release_readiness_downstream_receipt.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_CSV_FILENAME = "model_capability_route_promotion_release_readiness_downstream_receipt.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_TEXT_FILENAME = "model_capability_route_promotion_release_readiness_downstream_receipt.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_MARKDOWN_FILENAME = "model_capability_route_promotion_release_readiness_downstream_receipt.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_HTML_FILENAME = "model_capability_route_promotion_release_readiness_downstream_receipt.html"

READY_CHECK_DECISION = "model_capability_route_promotion_release_readiness_summary_contract_check_passed"
GRANTED_SCOPE = "bounded_route_promotion_release_governance_only"
SOURCE_SCOPE = "bounded_model_capability_governance_only"
BLOCKED_USES = (
    "production_model_quality_claim",
    "unbounded_release_promotion",
    "training_data_reuse_proof",
    "model_capability_claim_beyond_pair_probe_route",
)


def locate_route_promotion_release_readiness_summary_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion release readiness downstream receipt input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_release_readiness_downstream_receipt(
    release_readiness_summary_check: dict[str, Any],
    *,
    consumer_name: str,
    route_id: str,
    requested_scope: str = GRANTED_SCOPE,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    release_readiness_summary_check_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion release readiness downstream receipt",
    generated_at: str | None = None,
) -> dict[str, Any]:
    check_summary = as_dict(release_readiness_summary_check.get("summary"))
    downstream_policy = as_dict(release_readiness_summary_check.get("downstream_policy"))
    source_digest_rows = list_of_dicts(release_readiness_summary_check.get("source_digest_rows"))
    check_rows = _check_rows(
        release_readiness_summary_check,
        check_summary,
        downstream_policy,
        source_digest_rows,
        consumer_name,
        route_id,
        requested_scope,
        required_boundary,
    )
    issues = [row for row in check_rows if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    receipt = _receipt(
        status,
        check_summary,
        downstream_policy,
        source_digest_rows,
        consumer_name,
        route_id,
        requested_scope,
        release_readiness_summary_check_path,
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_release_readiness_summary_check": str(release_readiness_summary_check_path or ""),
        "source_release_readiness_summary_check_digest": _sha256_or_empty(release_readiness_summary_check_path),
        "request": {
            "consumer_name": consumer_name,
            "route_id": route_id,
            "requested_scope": requested_scope,
            "required_boundary": required_boundary,
        },
        "source_check_summary": check_summary,
        "source_downstream_policy": downstream_policy,
        "source_digest_rows": source_digest_rows,
        "check_rows": check_rows,
        "receipt": receipt,
        "summary": _summary(status, check_rows, receipt),
        "interpretation": _interpretation(status, receipt),
    }


def resolve_exit_code(report: dict[str, Any], *, require_receipt_ready: bool) -> int:
    return 1 if require_receipt_ready and report.get("status") != "pass" else 0


def _check_rows(
    release_readiness_summary_check: dict[str, Any],
    check_summary: dict[str, Any],
    downstream_policy: dict[str, Any],
    source_digest_rows: list[dict[str, Any]],
    consumer_name: str,
    route_id: str,
    requested_scope: str,
    required_boundary: str,
) -> list[dict[str, Any]]:
    source_check_rows = list_of_dicts(release_readiness_summary_check.get("check_rows"))
    active_routes = _unique_sorted(check_summary.get("active_routes"))
    claim = str(check_summary.get("model_quality_claim") or "")
    return [
        _check("consumer_name_present", bool(str(consumer_name).strip()), consumer_name, "consumer name must be recorded"),
        _check("route_id_requested", bool(str(route_id).strip()), route_id, "requested route id must be recorded"),
        _check("summary_check_passed", release_readiness_summary_check.get("status") == "pass", release_readiness_summary_check.get("status"), "source contract check must pass"),
        _check("summary_check_decision_ready", release_readiness_summary_check.get("decision") == READY_CHECK_DECISION, release_readiness_summary_check.get("decision"), "source contract check decision must be ready"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "source summary check must be ready"),
        _check("source_failed_count_zero", int(release_readiness_summary_check.get("failed_count") or 0) == 0, release_readiness_summary_check.get("failed_count"), "source check failed_count must be zero"),
        _check("source_check_rows_clean", all(row.get("status") == "pass" for row in source_check_rows), _status_counts(source_check_rows), "source check rows must all pass"),
        _check("route_id_in_checked_summary", str(route_id) in active_routes, {"requested": route_id, "active_routes": active_routes}, "requested route must be present in checked summary"),
        _check("boundary_required", check_summary.get("boundary") == required_boundary, check_summary.get("boundary"), "checked summary boundary must match required boundary"),
        _check("claim_bounded", claim.startswith("seed_stable_pair_probe_route"), claim, "checked summary claim must remain pair-probe scoped"),
        _check("source_digest_count_matches", int(check_summary.get("source_digest_count") or 0) == len(source_digest_rows), {"summary": check_summary.get("source_digest_count"), "actual": len(source_digest_rows)}, "source digest count must match digest rows"),
        _check("source_digests_present", all(row.get("sha256") for row in source_digest_rows), source_digest_rows, "all source digest rows must carry SHA-256"),
        _check("requested_scope_allowed", requested_scope == GRANTED_SCOPE, requested_scope, "requested scope must be bounded route-promotion release governance only"),
        _check("downstream_scope_matches", downstream_policy.get("allowed_scope") == GRANTED_SCOPE, downstream_policy.get("allowed_scope"), "source downstream policy scope must match requested receipt scope"),
        _check("source_scope_bounded", downstream_policy.get("source_allowed_scope") == SOURCE_SCOPE, downstream_policy.get("source_allowed_scope"), "source governance scope must remain bounded model-capability governance only"),
        _check("downstream_policy_allowed", downstream_policy.get("allowed") is True, downstream_policy.get("allowed"), "source downstream policy must allow bounded use"),
    ]


def _receipt(
    status: str,
    check_summary: dict[str, Any],
    downstream_policy: dict[str, Any],
    source_digest_rows: list[dict[str, Any]],
    consumer_name: str,
    route_id: str,
    requested_scope: str,
    source_check_path: str | Path | None,
) -> dict[str, Any]:
    allowed = status == "pass"
    return {
        "receipt_id": f"route-promotion-release-readiness:{route_id}:{consumer_name}",
        "receipt_status": "granted" if allowed else "blocked",
        "consumer_name": consumer_name,
        "route_id": route_id if allowed else "",
        "requested_scope": requested_scope,
        "granted_scope": requested_scope if allowed else "none",
        "boundary": check_summary.get("boundary") if allowed else "",
        "model_quality_claim": check_summary.get("model_quality_claim") if allowed else "not_claimed",
        "source_check_path": str(source_check_path or ""),
        "source_check_digest": _sha256_or_empty(source_check_path),
        "source_summary_ready": check_summary.get("source_summary_ready"),
        "source_digest_count": check_summary.get("source_digest_count"),
        "source_digest_rows": source_digest_rows if allowed else [],
        "blocked_uses": list(BLOCKED_USES),
        "policy_reason": downstream_policy.get("reason") if allowed else "downstream receipt is blocked",
        "next_step": "index_checked_route_promotion_release_readiness_receipt" if allowed else "repair_checked_route_promotion_release_readiness_receipt",
    }


def _summary(status: str, check_rows: list[dict[str, Any]], receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "downstream_receipt_ready": status == "pass",
        "receipt_status": receipt.get("receipt_status"),
        "consumer_name": receipt.get("consumer_name"),
        "route_id": receipt.get("route_id"),
        "granted_scope": receipt.get("granted_scope"),
        "boundary": receipt.get("boundary"),
        "model_quality_claim": receipt.get("model_quality_claim"),
        "source_digest_count": receipt.get("source_digest_count"),
        "blocked_uses": receipt.get("blocked_uses"),
        "next_step": receipt.get("next_step"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _interpretation(status: str, receipt: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The checked release readiness summary cannot be granted to the downstream consumer.",
            "next_action": "repair the checked summary, requested route, scope, or source digests before receipt indexing",
        }
    return {
        "model_quality_claim": receipt.get("model_quality_claim"),
        "reason": "A downstream consumer receipt is granted for bounded route-promotion release governance only.",
        "next_action": "index the receipt before using it as downstream governance evidence",
    }


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "pass": sum(1 for row in rows if row.get("status") == "pass"),
        "fail": sum(1 for row in rows if row.get("status") != "pass"),
    }


def _unique_sorted(value: Any) -> list[str]:
    return sorted({str(item) for item in string_list(value) if str(item)})


def _sha256_or_empty(path: str | Path | None) -> str:
    if not path:
        return ""
    source = Path(path)
    if not source.is_file():
        return ""
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_release_readiness_downstream_receipt_granted"
    return "fix_model_capability_route_promotion_release_readiness_downstream_receipt"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_DOWNSTREAM_RECEIPT_TEXT_FILENAME",
    "build_model_capability_route_promotion_release_readiness_downstream_receipt",
    "locate_route_promotion_release_readiness_summary_check",
    "read_json_report",
    "resolve_exit_code",
]
