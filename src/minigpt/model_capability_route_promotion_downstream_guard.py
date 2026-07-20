from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_governance_snapshot import MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_JSON_FILENAME = "model_capability_route_promotion_downstream_guard.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_CSV_FILENAME = "model_capability_route_promotion_downstream_guard.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_TEXT_FILENAME = "model_capability_route_promotion_downstream_guard.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_MARKDOWN_FILENAME = "model_capability_route_promotion_downstream_guard.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_HTML_FILENAME = "model_capability_route_promotion_downstream_guard.html"


def locate_route_promotion_governance_snapshot(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion downstream guard input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_downstream_guard(
    governance_snapshot: dict[str, Any],
    *,
    route_id: str,
    consumer_name: str,
    requested_scope: str = "bounded_model_capability_governance_only",
    required_boundary: str = "tiny_required_term_pair_probe_only",
    governance_snapshot_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion downstream guard",
    generated_at: str | None = None,
) -> dict[str, Any]:
    policy = as_dict(governance_snapshot.get("downstream_policy"))
    route_card = _find_route_card(governance_snapshot, route_id)
    check_rows = _checks(governance_snapshot, policy, route_card, requested_scope, required_boundary)
    issues = [row for row in check_rows if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    access = _access_decision(status, route_card, requested_scope, consumer_name)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_governance_snapshot": str(governance_snapshot_path or ""),
        "request": {
            "route_id": route_id,
            "consumer_name": consumer_name,
            "requested_scope": requested_scope,
            "required_boundary": required_boundary,
        },
        "route_card": route_card,
        "downstream_policy": policy,
        "check_rows": check_rows,
        "access_decision": access,
        "summary": _summary(status, check_rows, access),
    }


def resolve_exit_code(report: dict[str, Any], *, require_allowed: bool) -> int:
    return 1 if require_allowed and report.get("status") != "pass" else 0


def _find_route_card(governance_snapshot: dict[str, Any], route_id: str) -> dict[str, Any]:
    for card in list_of_dicts(governance_snapshot.get("route_cards")):
        if str(card.get("route_id")) == route_id:
            return card
    return {}


def _checks(
    governance_snapshot: dict[str, Any],
    policy: dict[str, Any],
    route_card: dict[str, Any],
    requested_scope: str,
    required_boundary: str,
) -> list[dict[str, Any]]:
    claim = str(route_card.get("model_quality_claim") or "")
    return [
        _check("snapshot_passed", governance_snapshot.get("status") == "pass", governance_snapshot.get("status"), "governance snapshot must pass"),
        _check(
            "snapshot_ready",
            governance_snapshot.get("decision") == "model_capability_route_promotion_governance_snapshot_ready",
            governance_snapshot.get("decision"),
            "governance snapshot decision must be ready",
        ),
        _check("downstream_policy_allowed", policy.get("allowed") is True, policy.get("allowed"), "downstream policy must allow bounded use"),
        _check("route_card_present", bool(route_card), route_card.get("route_id"), "requested route must exist in route cards"),
        _check("route_contract_verified", route_card.get("verification_status") == "contract_verified", route_card.get("verification_status"), "route card must be contract verified"),
        _check("route_governance_available", route_card.get("governance_status") == "available_for_downstream_bounded_governance", route_card.get("governance_status"), "route must be available for bounded governance"),
        _check("requested_scope_allowed", requested_scope == policy.get("allowed_scope") == route_card.get("allowed_downstream_use"), {"requested": requested_scope, "policy": policy.get("allowed_scope"), "route": route_card.get("allowed_downstream_use")}, "requested scope must match allowed bounded scope"),
        _check("boundary_scoped", route_card.get("boundary") == required_boundary, route_card.get("boundary"), "route card boundary must match the required boundary"),
        _check("claim_bounded", claim.startswith("seed_stable_pair_probe_route"), claim, "route claim must remain pair-probe scoped"),
    ]


def _access_decision(status: str, route_card: dict[str, Any], requested_scope: str, consumer_name: str) -> dict[str, Any]:
    allowed = status == "pass"
    return {
        "allowed": allowed,
        "consumer_name": consumer_name,
        "route_id": route_card.get("route_id") if route_card else "",
        "allowed_scope": requested_scope if allowed else "none",
        "boundary": route_card.get("boundary") if allowed else "",
        "model_quality_claim": route_card.get("model_quality_claim") if allowed else "not_claimed",
        "next_step": "build_bounded_route_promotion_consumer_plan" if allowed else "repair_or_reject_downstream_route_request",
    }


def _summary(status: str, check_rows: list[dict[str, Any]], access: dict[str, Any]) -> dict[str, Any]:
    return {
        "downstream_guard_ready": status == "pass",
        "access_allowed": access.get("allowed"),
        "consumer_name": access.get("consumer_name"),
        "route_id": access.get("route_id"),
        "allowed_scope": access.get("allowed_scope"),
        "boundary": access.get("boundary"),
        "model_quality_claim": access.get("model_quality_claim"),
        "next_step": access.get("next_step"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_downstream_guard_allowed"
    return "fix_model_capability_route_promotion_downstream_guard"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DOWNSTREAM_GUARD_TEXT_FILENAME",
    "build_model_capability_route_promotion_downstream_guard",
    "locate_route_promotion_governance_snapshot",
    "read_json_report",
    "resolve_exit_code",
]
