from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_decision_index import MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME
from minigpt.model_capability_route_promotion_decision_index_check import MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_JSON_FILENAME = "model_capability_route_promotion_governance_snapshot.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_CSV_FILENAME = "model_capability_route_promotion_governance_snapshot.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_TEXT_FILENAME = "model_capability_route_promotion_governance_snapshot.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_MARKDOWN_FILENAME = "model_capability_route_promotion_governance_snapshot.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_HTML_FILENAME = "model_capability_route_promotion_governance_snapshot.html"


def locate_route_promotion_decision_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME
    return source


def locate_route_promotion_decision_index_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion governance snapshot input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_governance_snapshot(
    decision_index: dict[str, Any],
    index_contract_check: dict[str, Any],
    *,
    decision_index_path: str | Path | None = None,
    index_contract_check_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion governance snapshot",
    generated_at: str | None = None,
) -> dict[str, Any]:
    index_summary = as_dict(decision_index.get("summary"))
    check_summary = as_dict(index_contract_check.get("summary"))
    route_cards = [_route_card(entry, required_boundary) for entry in list_of_dicts(decision_index.get("entries"))]
    check_rows = _checks(decision_index, index_contract_check, index_summary, check_summary, route_cards, required_boundary)
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
        "source_decision_index": str(decision_index_path or ""),
        "source_index_contract_check": str(index_contract_check_path or ""),
        "index_summary": index_summary,
        "contract_check_summary": check_summary,
        "route_cards": route_cards,
        "check_rows": check_rows,
        "summary": _summary(status, route_cards, check_rows, required_boundary),
        "downstream_policy": _downstream_policy(status, route_cards),
    }


def resolve_exit_code(report: dict[str, Any], *, require_ready_snapshot: bool) -> int:
    return 1 if require_ready_snapshot and report.get("status") != "pass" else 0


def _route_card(entry: dict[str, Any], required_boundary: str) -> dict[str, Any]:
    accepted = entry.get("entry_status") == "accepted"
    bounded = entry.get("review_scope") == "bounded_route_promotion_review_only" and entry.get("boundary") == required_boundary
    verified = accepted and bounded
    return {
        "route_id": entry.get("route_id"),
        "route_status": entry.get("entry_status"),
        "verification_status": "contract_verified" if verified else "blocked",
        "governance_status": "available_for_downstream_bounded_governance" if verified else "not_available",
        "review_scope": entry.get("review_scope"),
        "boundary": entry.get("boundary"),
        "model_quality_claim": entry.get("model_quality_claim") if verified else "not_claimed",
        "source_decision_path": entry.get("source_decision_path"),
        "allowed_downstream_use": "bounded_model_capability_governance_only" if verified else "none",
        "required_boundary": required_boundary,
    }


def _checks(
    decision_index: dict[str, Any],
    index_contract_check: dict[str, Any],
    index_summary: dict[str, Any],
    check_summary: dict[str, Any],
    route_cards: list[dict[str, Any]],
    required_boundary: str,
) -> list[dict[str, Any]]:
    verified_cards = [card for card in route_cards if card.get("verification_status") == "contract_verified"]
    boundary_mismatches = [card for card in route_cards if card.get("boundary") != required_boundary]
    return [
        _check("decision_index_passed", decision_index.get("status") == "pass", decision_index.get("status"), "decision index must pass"),
        _check(
            "decision_index_ready",
            decision_index.get("decision") == "model_capability_route_promotion_decision_index_ready",
            decision_index.get("decision"),
            "decision index must be ready",
        ),
        _check("contract_check_passed", index_contract_check.get("status") == "pass", index_contract_check.get("status"), "contract check must pass"),
        _check(
            "contract_check_ready",
            check_summary.get("contract_check_ready") is True,
            check_summary.get("contract_check_ready"),
            "contract check must be ready",
        ),
        _check("route_cards_present", bool(route_cards), len(route_cards), "snapshot must include route cards"),
        _check("verified_route_cards", len(verified_cards) == len(route_cards), len(verified_cards), "all route cards must be contract verified"),
        _check("accepted_route_count_matches", index_summary.get("accepted_route_count") == check_summary.get("rebuilt_accepted_route_count"), {"index": index_summary.get("accepted_route_count"), "rebuilt": check_summary.get("rebuilt_accepted_route_count")}, "index and rebuilt accepted route count must match"),
        _check("boundary_scoped", not boundary_mismatches, len(boundary_mismatches), "all route cards must keep the required boundary"),
    ]


def _summary(status: str, route_cards: list[dict[str, Any]], check_rows: list[dict[str, Any]], required_boundary: str) -> dict[str, Any]:
    verified = [card for card in route_cards if card.get("verification_status") == "contract_verified"]
    route_ids = sorted({str(card.get("route_id")) for card in verified if card.get("route_id")})
    claims = sorted({str(card.get("model_quality_claim")) for card in verified if card.get("model_quality_claim")})
    return {
        "governance_snapshot_ready": status == "pass",
        "route_card_count": len(route_cards),
        "verified_route_count": len(verified),
        "route_ids": route_ids,
        "route_id_count": len(route_ids),
        "required_boundary": required_boundary,
        "boundary": required_boundary if status == "pass" else "mixed_or_blocked",
        "model_quality_claims": claims,
        "model_quality_claim": claims[0] if len(claims) == 1 else "mixed_or_not_claimed",
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
        "next_step": "publish_bounded_route_promotion_governance_snapshot" if status == "pass" else "repair_route_promotion_governance_inputs",
    }


def _downstream_policy(status: str, route_cards: list[dict[str, Any]]) -> dict[str, Any]:
    if status != "pass":
        return {"allowed": False, "allowed_scope": "none", "reason": "governance snapshot inputs are not fully verified"}
    return {
        "allowed": True,
        "allowed_scope": "bounded_model_capability_governance_only",
        "route_ids": [card.get("route_id") for card in route_cards],
        "reason": "all accepted route cards are contract verified and boundary scoped",
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_governance_snapshot_ready"
    return "fix_model_capability_route_promotion_governance_snapshot"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_TEXT_FILENAME",
    "build_model_capability_route_promotion_governance_snapshot",
    "locate_route_promotion_decision_index",
    "locate_route_promotion_decision_index_check",
    "read_json_report",
    "resolve_exit_code",
]
