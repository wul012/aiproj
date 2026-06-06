from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_acceptance_summary import RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME
from minigpt.randomized_holdout_acceptance_summary_check import RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_JSON_FILENAME = "randomized_holdout_acceptance_publication_packet.json"
RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_CSV_FILENAME = "randomized_holdout_acceptance_publication_packet.csv"
RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_TEXT_FILENAME = "randomized_holdout_acceptance_publication_packet.txt"
RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_MARKDOWN_FILENAME = "randomized_holdout_acceptance_publication_packet.md"
RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_HTML_FILENAME = "randomized_holdout_acceptance_publication_packet.html"


def locate_randomized_holdout_acceptance_summary(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME
    return source


def locate_randomized_holdout_acceptance_summary_check(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout acceptance publication packet input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_acceptance_publication_packet(
    acceptance_summary: dict[str, Any],
    contract_check: dict[str, Any],
    *,
    acceptance_summary_path: str | Path | None = None,
    contract_check_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout acceptance publication packet",
    generated_at: str | None = None,
) -> dict[str, Any]:
    acceptance = as_dict(acceptance_summary.get("summary"))
    check_summary = as_dict(contract_check.get("summary"))
    accepted_claims = list_of_dicts(acceptance_summary.get("accepted_claims"))
    blocked_claims = list_of_dicts(acceptance_summary.get("blocked_claims"))
    evidence_rows = _evidence_rows(acceptance_summary_path, contract_check_path)
    checks = _checks(acceptance_summary, contract_check, acceptance, check_summary, accepted_claims, blocked_claims, evidence_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    packet = _packet(status, acceptance, check_summary, accepted_claims, blocked_claims, evidence_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "acceptance_summary": acceptance,
        "contract_check_summary": check_summary,
        "accepted_claims": accepted_claims,
        "blocked_claims": blocked_claims,
        "evidence_rows": evidence_rows,
        "check_rows": checks,
        "packet": packet,
        "summary": _summary(status, checks, packet),
        "interpretation": _interpretation(status, packet),
    }


def resolve_exit_code(report: dict[str, Any], *, require_packet_ready: bool, require_promotion_ready: bool = False) -> int:
    summary = as_dict(report.get("summary"))
    if require_packet_ready and summary.get("randomized_holdout_acceptance_publication_packet_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _evidence_rows(summary_path: str | Path | None, check_path: str | Path | None) -> list[dict[str, Any]]:
    return [
        _evidence("acceptance_summary", summary_path),
        _evidence("acceptance_summary_contract_check", check_path),
    ]


def _evidence(kind: str, path: str | Path | None) -> dict[str, Any]:
    text = str(path or "")
    return {"kind": kind, "path": text, "exists": Path(text).exists() if text else False}


def _checks(
    acceptance_summary: dict[str, Any],
    contract_check: dict[str, Any],
    acceptance: dict[str, Any],
    check_summary: dict[str, Any],
    accepted_claims: list[dict[str, Any]],
    blocked_claims: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("acceptance_summary_passed", acceptance_summary.get("status") == "pass", acceptance_summary.get("status"), "acceptance summary must pass"),
        _check("acceptance_summary_ready", acceptance.get("randomized_holdout_acceptance_summary_ready") is True, acceptance.get("randomized_holdout_acceptance_summary_ready"), "acceptance summary must be ready"),
        _check("contract_check_passed", contract_check.get("status") == "pass", contract_check.get("status"), "contract check must pass"),
        _check("contract_check_ready", check_summary.get("contract_check_ready") is True, check_summary.get("contract_check_ready"), "contract check must be ready"),
        _check("contract_rebuild_matches", check_summary.get("original_decision") == check_summary.get("rebuilt_decision") == "randomized_holdout_acceptance_summary_ready", {"original": check_summary.get("original_decision"), "rebuilt": check_summary.get("rebuilt_decision")}, "contract check must rebuild the acceptance summary decision"),
        _check("bounded_acceptance_true", acceptance.get("bounded_promotion_accepted") is True, acceptance.get("bounded_promotion_accepted"), "publication packet requires bounded acceptance"),
        _check("accepted_claim_present", int(acceptance.get("accepted_claim_count") or 0) >= 1 and bool(accepted_claims), acceptance.get("accepted_claim_count"), "publication packet needs at least one accepted claim"),
        _check("blocked_claims_present", int(acceptance.get("blocked_claim_count") or 0) >= 3 and len(blocked_claims) >= 3, acceptance.get("blocked_claim_count"), "publication packet must carry blocked claim boundaries"),
        _check("allowed_use_bounded", acceptance.get("allowed_use") == "bounded_model_capability_governance_only", acceptance.get("allowed_use"), "allowed use must stay bounded governance only"),
        _check("promotion_still_false", acceptance.get("promotion_ready") is False, acceptance.get("promotion_ready"), "publication packet must not become direct promotion"),
        _check("approved_for_promotion_false", acceptance.get("approved_for_promotion") is False, acceptance.get("approved_for_promotion"), "direct promotion approval must remain false"),
        _check("evidence_files_exist", all(row.get("exists") is True for row in evidence_rows), evidence_rows, "publication evidence files must exist"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _packet(
    status: str,
    acceptance: dict[str, Any],
    check_summary: dict[str, Any],
    accepted_claims: list[dict[str, Any]],
    blocked_claims: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "packet_ready": ready,
        "handoff_status": "ready_for_bounded_acceptance_publication_review" if ready else "blocked",
        "accepted_claim_count": len(accepted_claims) if ready else 0,
        "blocked_claim_count": len(blocked_claims),
        "candidate_case_count": acceptance.get("candidate_case_count"),
        "random_seed": acceptance.get("random_seed"),
        "pass_rate": acceptance.get("pass_rate"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "allowed_use": acceptance.get("allowed_use") if ready else "none",
        "model_quality_claim": acceptance.get("model_quality_claim") if ready else "not_claimed",
        "contract_check_ready": check_summary.get("contract_check_ready"),
        "accepted_claims": accepted_claims if ready else [],
        "blocked_claims": blocked_claims,
        "evidence_rows": evidence_rows,
        "next_step": "review_randomized_holdout_acceptance_publication_packet" if ready else "repair_randomized_holdout_acceptance_publication_packet",
    }


def _summary(status: str, checks: list[dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_acceptance_publication_packet_ready": status == "pass" and packet.get("packet_ready") is True,
        "handoff_status": packet.get("handoff_status"),
        "accepted_claim_count": packet.get("accepted_claim_count"),
        "blocked_claim_count": packet.get("blocked_claim_count"),
        "candidate_case_count": packet.get("candidate_case_count"),
        "random_seed": packet.get("random_seed"),
        "pass_rate": packet.get("pass_rate"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "allowed_use": packet.get("allowed_use"),
        "model_quality_claim": packet.get("model_quality_claim"),
        "evidence_count": len(packet.get("evidence_rows") or []),
        "next_step": packet.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_acceptance_publication_packet_ready"
    return "fix_randomized_holdout_acceptance_publication_packet"


def _interpretation(status: str, packet: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout acceptance publication packet is blocked by summary, contract-check, or evidence issues.",
            "next_action": "repair acceptance summary or contract check before publication review",
        }
    return {
        "model_quality_claim": packet.get("model_quality_claim"),
        "reason": "Bounded randomized holdout acceptance is packaged for downstream review while direct production promotion remains blocked.",
        "next_action": packet.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_TEXT_FILENAME",
    "build_randomized_holdout_acceptance_publication_packet",
    "locate_randomized_holdout_acceptance_summary",
    "locate_randomized_holdout_acceptance_summary_check",
    "read_json_report",
    "resolve_exit_code",
]
