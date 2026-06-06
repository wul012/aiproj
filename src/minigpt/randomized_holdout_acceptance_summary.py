from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_decision_index import RANDOMIZED_HOLDOUT_DECISION_INDEX_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME = "randomized_holdout_acceptance_summary.json"
RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CSV_FILENAME = "randomized_holdout_acceptance_summary.csv"
RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_TEXT_FILENAME = "randomized_holdout_acceptance_summary.txt"
RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_MARKDOWN_FILENAME = "randomized_holdout_acceptance_summary.md"
RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_HTML_FILENAME = "randomized_holdout_acceptance_summary.html"


def locate_randomized_holdout_decision_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_DECISION_INDEX_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout acceptance summary input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_acceptance_summary(
    decision_index: dict[str, Any],
    *,
    decision_index_path: str | Path | None = None,
    minimum_candidate_cases: int = 20,
    title: str = "MiniGPT randomized holdout acceptance summary",
    generated_at: str | None = None,
) -> dict[str, Any]:
    index_summary = as_dict(decision_index.get("summary"))
    source_rows = list_of_dicts(decision_index.get("source_rows"))
    accepted_claims = _accepted_claims(index_summary)
    blocked_claims = _blocked_claims()
    checks = _checks(decision_index, index_summary, source_rows, decision_index_path, minimum_candidate_cases)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    acceptance_card = _acceptance_card(status, index_summary, accepted_claims, blocked_claims, source_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_decision_index": str(decision_index_path or ""),
        "index_summary": index_summary,
        "source_rows": source_rows,
        "accepted_claims": accepted_claims,
        "blocked_claims": blocked_claims,
        "check_rows": checks,
        "acceptance_card": acceptance_card,
        "summary": _summary(status, checks, acceptance_card),
        "interpretation": _interpretation(status, acceptance_card),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_summary_ready: bool,
    require_bounded_acceptance: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_summary_ready and summary.get("randomized_holdout_acceptance_summary_ready") is not True:
        return 1
    if require_bounded_acceptance and summary.get("bounded_promotion_accepted") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _accepted_claims(index_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "bounded_randomized_target_hidden_holdout_claim",
            "status": "accepted",
            "scope": index_summary.get("claim_scope"),
            "model_quality_claim": index_summary.get("model_quality_claim"),
            "candidate_case_count": index_summary.get("candidate_case_count"),
            "random_seed": index_summary.get("random_seed"),
            "pass_rate": index_summary.get("pass_rate"),
            "allowed_use": "bounded_model_capability_governance_only",
        }
    ]


def _blocked_claims() -> list[dict[str, Any]]:
    return [
        {"claim_id": "production_promotion", "status": "blocked", "reason": "promotion_ready remains false"},
        {"claim_id": "general_model_quality", "status": "blocked", "reason": "evidence is limited to a 20-case tiny-checkpoint randomized holdout"},
        {"claim_id": "larger_corpus_transfer", "status": "blocked", "reason": "no larger corpus or external benchmark evidence is attached"},
    ]


def _checks(
    decision_index: dict[str, Any],
    index_summary: dict[str, Any],
    source_rows: list[dict[str, Any]],
    decision_index_path: str | Path | None,
    minimum_candidate_cases: int,
) -> list[dict[str, Any]]:
    source_kinds = {str(row.get("kind")) for row in source_rows}
    expected_kinds = {"bounded_decision", "bounded_gate", "candidate_packet_review", "candidate_packet"}
    return [
        _check("decision_index_file_exists", _path_exists(decision_index_path), str(decision_index_path or ""), "source decision index file must exist"),
        _check("decision_index_passed", decision_index.get("status") == "pass", decision_index.get("status"), "decision index must pass"),
        _check("decision_index_ready", decision_index.get("decision") == "randomized_holdout_decision_index_ready", decision_index.get("decision"), "decision index must be ready"),
        _check("summary_ready", index_summary.get("randomized_holdout_decision_index_ready") is True, index_summary.get("randomized_holdout_decision_index_ready"), "index summary must be ready"),
        _check("bounded_acceptance_true", index_summary.get("bounded_promotion_accepted") is True, index_summary.get("bounded_promotion_accepted"), "bounded randomized holdout claim must be accepted"),
        _check("promotion_still_false", index_summary.get("promotion_ready") is False, index_summary.get("promotion_ready"), "acceptance summary must not become direct promotion"),
        _check("approved_for_promotion_false", index_summary.get("approved_for_promotion") is False, index_summary.get("approved_for_promotion"), "direct promotion approval must remain false"),
        _check("candidate_count_floor", int(index_summary.get("candidate_case_count") or 0) >= minimum_candidate_cases, index_summary.get("candidate_case_count"), "acceptance summary requires the randomized 20-case floor"),
        _check("seed_present", index_summary.get("random_seed") is not None, index_summary.get("random_seed"), "acceptance summary must carry the randomized seed"),
        _check("pass_rate_complete", float(index_summary.get("pass_rate") or 0.0) == 1.0, index_summary.get("pass_rate"), "acceptance summary requires complete randomized replay pass rate"),
        _check("claim_scope_bounded", index_summary.get("model_quality_claim") == "bounded_randomized_target_hidden_holdout_claim_only", index_summary.get("model_quality_claim"), "accepted claim must remain bounded"),
        _check("source_rows_present", len(source_rows) >= 4, len(source_rows), "summary must retain source rows"),
        _check("source_kinds_complete", expected_kinds.issubset(source_kinds), sorted(source_kinds), "source rows must include packet, review, gate, and decision"),
        _check("source_rows_ready", all(row.get("status") == "pass" and row.get("ready_value") is True for row in source_rows), [row.get("ready_value") for row in source_rows], "all source rows must remain passed and ready"),
        _check("source_rows_block_promotion", all(row.get("promotion_ready") is False for row in source_rows), [row.get("promotion_ready") for row in source_rows], "all source rows must keep promotion false"),
    ]


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(path).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _acceptance_card(
    status: str,
    index_summary: dict[str, Any],
    accepted_claims: list[dict[str, Any]],
    blocked_claims: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "card_ready": ready,
        "accepted": bool(ready and index_summary.get("bounded_promotion_accepted") is True),
        "accepted_claim_count": len(accepted_claims) if ready else 0,
        "blocked_claim_count": len(blocked_claims),
        "candidate_case_count": index_summary.get("candidate_case_count"),
        "random_seed": index_summary.get("random_seed"),
        "pass_rate": index_summary.get("pass_rate"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "model_quality_claim": index_summary.get("model_quality_claim") if ready else "not_claimed",
        "allowed_use": "bounded_model_capability_governance_only" if ready else "none",
        "source_count": len(source_rows),
        "next_step": "check_randomized_holdout_acceptance_summary_contract" if ready else "repair_randomized_holdout_decision_index",
    }


def _summary(status: str, checks: list[dict[str, Any]], card: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_acceptance_summary_ready": status == "pass" and card.get("card_ready") is True,
        "bounded_promotion_accepted": card.get("accepted"),
        "accepted_claim_count": card.get("accepted_claim_count"),
        "blocked_claim_count": card.get("blocked_claim_count"),
        "candidate_case_count": card.get("candidate_case_count"),
        "random_seed": card.get("random_seed"),
        "pass_rate": card.get("pass_rate"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "model_quality_claim": card.get("model_quality_claim"),
        "allowed_use": card.get("allowed_use"),
        "source_count": card.get("source_count"),
        "next_step": card.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_acceptance_summary_ready"
    return "fix_randomized_holdout_acceptance_summary"


def _interpretation(status: str, card: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout acceptance summary is blocked by an invalid or widened decision index.",
            "next_action": "repair randomized holdout decision index before publishing acceptance summary",
        }
    return {
        "model_quality_claim": card.get("model_quality_claim"),
        "reason": "The bounded randomized holdout acceptance is summarized for downstream governance while production promotion remains blocked.",
        "next_action": card.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_TEXT_FILENAME",
    "build_randomized_holdout_acceptance_summary",
    "locate_randomized_holdout_decision_index",
    "read_json_report",
    "resolve_exit_code",
]
