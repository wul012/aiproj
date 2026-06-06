from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_acceptance_publication_packet import RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_JSON_FILENAME
from minigpt.randomized_holdout_acceptance_publication_packet_review import RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_JSON_FILENAME
from minigpt.randomized_holdout_publication_decision import RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_JSON_FILENAME
from minigpt.report_utils import as_dict, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_JSON_FILENAME = "randomized_holdout_publication_decision_index.json"
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_CSV_FILENAME = "randomized_holdout_publication_decision_index.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_TEXT_FILENAME = "randomized_holdout_publication_decision_index.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_MARKDOWN_FILENAME = "randomized_holdout_publication_decision_index.md"
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_HTML_FILENAME = "randomized_holdout_publication_decision_index.html"

EXPECTED_ALLOWED_USE = "bounded_model_capability_governance_only"
EXPECTED_MODEL_QUALITY_CLAIM = "bounded_randomized_target_hidden_holdout_claim_only"
NEXT_STEP = "build_randomized_holdout_publication_registry_entry"


def locate_randomized_holdout_publication_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_JSON_FILENAME
    return source


def locate_randomized_holdout_publication_packet_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_REVIEW_JSON_FILENAME
    return source


def locate_randomized_holdout_acceptance_publication_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication decision index input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_decision_index(
    publication_decision: dict[str, Any],
    publication_review: dict[str, Any],
    publication_packet: dict[str, Any],
    *,
    publication_decision_path: str | Path | None = None,
    publication_review_path: str | Path | None = None,
    publication_packet_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout publication decision index",
    generated_at: str | None = None,
) -> dict[str, Any]:
    decision_summary = as_dict(publication_decision.get("summary"))
    review_summary = as_dict(publication_review.get("summary"))
    packet_summary = as_dict(publication_packet.get("summary"))
    source_rows = _source_rows(
        publication_decision,
        publication_review,
        publication_packet,
        decision_summary,
        review_summary,
        packet_summary,
        publication_decision_path,
        publication_review_path,
        publication_packet_path,
    )
    checks = _checks(publication_decision, publication_review, publication_packet, decision_summary, review_summary, packet_summary, source_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    index = _index(status, decision_summary, review_summary, packet_summary, source_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_rows": source_rows,
        "check_rows": checks,
        "index": index,
        "summary": _summary(status, checks, index, source_rows),
        "interpretation": _interpretation(status, index),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_index_ready: bool,
    require_bounded_publication: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_index_ready and summary.get("randomized_holdout_publication_decision_index_ready") is not True:
        return 1
    if require_bounded_publication and summary.get("bounded_publication_accepted") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _source_rows(
    decision: dict[str, Any],
    review: dict[str, Any],
    packet: dict[str, Any],
    decision_summary: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    decision_path: str | Path | None,
    review_path: str | Path | None,
    packet_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _source_row(
            "publication_decision",
            decision_path,
            decision,
            decision_summary,
            "randomized_holdout_publication_decision_ready",
            "records final bounded-publication acceptance while keeping direct promotion blocked",
        ),
        _source_row(
            "publication_review",
            review_path,
            review,
            review_summary,
            "randomized_holdout_acceptance_publication_packet_review_ready",
            "approves the packet for bounded downstream governance publication only",
        ),
        _source_row(
            "publication_packet",
            packet_path,
            packet,
            packet_summary,
            "randomized_holdout_acceptance_publication_packet_ready",
            "packages accepted and blocked randomized holdout claims for review",
        ),
    ]


def _source_row(
    kind: str,
    path: str | Path | None,
    report: dict[str, Any],
    summary: dict[str, Any],
    ready_key: str,
    role: str,
) -> dict[str, Any]:
    text = str(path or "")
    return {
        "kind": kind,
        "path": text,
        "exists": Path(text).exists() if text else False,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "ready_key": ready_key,
        "ready_value": summary.get(ready_key),
        "accepted_claim_count": summary.get("accepted_claim_count"),
        "blocked_claim_count": summary.get("blocked_claim_count"),
        "candidate_case_count": summary.get("candidate_case_count"),
        "random_seed": summary.get("random_seed"),
        "pass_rate": summary.get("pass_rate"),
        "bounded_publication_accepted": summary.get("bounded_publication_accepted"),
        "approved_for_bounded_publication": summary.get("approved_for_bounded_publication"),
        "promotion_ready": summary.get("promotion_ready"),
        "approved_for_promotion": summary.get("approved_for_promotion"),
        "allowed_use": summary.get("allowed_use"),
        "model_quality_claim": summary.get("model_quality_claim"),
        "scope": summary.get("decision_scope") or summary.get("review_scope") or summary.get("handoff_status"),
        "next_step": summary.get("next_step"),
        "failed_check_count": summary.get("failed_check_count"),
        "role": role,
    }


def _checks(
    decision: dict[str, Any],
    review: dict[str, Any],
    packet: dict[str, Any],
    decision_summary: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    accepted_counts = [row.get("accepted_claim_count") for row in source_rows]
    blocked_counts = [row.get("blocked_claim_count") for row in source_rows]
    candidate_counts = [row.get("candidate_case_count") for row in source_rows]
    seeds = [row.get("random_seed") for row in source_rows]
    pass_rates = [row.get("pass_rate") for row in source_rows]
    return [
        _check("source_files_exist", all(row.get("exists") is True for row in source_rows), [row.get("exists") for row in source_rows], "all indexed publication-chain source files must exist"),
        _check("decision_passed", decision.get("status") == "pass", decision.get("status"), "publication decision must pass"),
        _check("decision_accepted", decision.get("decision") == "randomized_holdout_publication_decision_accepted", decision.get("decision"), "publication decision must be accepted"),
        _check("decision_ready", decision_summary.get("randomized_holdout_publication_decision_ready") is True, decision_summary.get("randomized_holdout_publication_decision_ready"), "publication decision summary must be ready"),
        _check("decision_accepts_bounded_publication", decision_summary.get("bounded_publication_accepted") is True, decision_summary.get("bounded_publication_accepted"), "publication decision must accept only bounded publication"),
        _check("review_passed", review.get("status") == "pass", review.get("status"), "publication review must pass"),
        _check("review_ready", review_summary.get("randomized_holdout_acceptance_publication_packet_review_ready") is True, review_summary.get("randomized_holdout_acceptance_publication_packet_review_ready"), "publication review summary must be ready"),
        _check("review_approved_publication", review_summary.get("approved_for_bounded_publication") is True, review_summary.get("approved_for_bounded_publication"), "publication review must approve bounded publication"),
        _check("packet_passed", packet.get("status") == "pass", packet.get("status"), "publication packet must pass"),
        _check("packet_ready", packet_summary.get("randomized_holdout_acceptance_publication_packet_ready") is True, packet_summary.get("randomized_holdout_acceptance_publication_packet_ready"), "publication packet summary must be ready"),
        _check("accepted_counts_match", _same_non_null(accepted_counts) and int(accepted_counts[0] or 0) == 1, accepted_counts, "accepted claim counts must match exactly one"),
        _check("blocked_counts_match", _same_non_null(blocked_counts) and int(blocked_counts[0] or 0) >= 3, blocked_counts, "blocked claim counts must match and preserve at least three boundaries"),
        _check("candidate_counts_match", _same_non_null(candidate_counts) and int(candidate_counts[0] or 0) >= 20, candidate_counts, "candidate case counts must match the randomized holdout floor"),
        _check("random_seed_matches", _same_non_null(seeds), seeds, "all sources must preserve the same randomized seed"),
        _check("pass_rate_complete", _same_non_null(pass_rates) and float(pass_rates[0] or 0.0) == 1.0, pass_rates, "all sources must preserve complete randomized replay pass rate"),
        _check("allowed_use_bounded", all(row.get("allowed_use") == EXPECTED_ALLOWED_USE for row in source_rows), [row.get("allowed_use") for row in source_rows], "all sources must keep bounded governance allowed use"),
        _check("model_quality_claim_bounded", all(row.get("model_quality_claim") == EXPECTED_MODEL_QUALITY_CLAIM for row in source_rows), [row.get("model_quality_claim") for row in source_rows], "all sources must keep the bounded randomized holdout claim"),
        _check("promotion_still_false", all(row.get("promotion_ready") is False for row in source_rows), [row.get("promotion_ready") for row in source_rows], "publication index must not widen into direct promotion"),
        _check("approved_for_promotion_false", all(row.get("approved_for_promotion") is False for row in source_rows), [row.get("approved_for_promotion") for row in source_rows], "direct promotion approval must remain false"),
        _check("source_checks_clean", all(int(row.get("failed_check_count") or 0) == 0 for row in source_rows), [row.get("failed_check_count") for row in source_rows], "all indexed source summaries must have clean checks"),
        _check(
            "next_steps_aligned",
            decision_summary.get("next_step") == "index_randomized_holdout_publication_decision"
            and review_summary.get("next_step") == "record_randomized_holdout_publication_decision"
            and packet_summary.get("next_step") == "review_randomized_holdout_acceptance_publication_packet",
            [row.get("next_step") for row in source_rows],
            "source next-step routing must match packet -> review -> decision -> index",
        ),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _index(status: str, decision_summary: dict[str, Any], review_summary: dict[str, Any], packet_summary: dict[str, Any], source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "index_ready": ready,
        "indexed_decision": decision_summary.get("final_decision") if ready else "not_indexed",
        "bounded_publication_accepted": bool(ready and decision_summary.get("bounded_publication_accepted") is True and review_summary.get("approved_for_bounded_publication") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "accepted_claim_count": decision_summary.get("accepted_claim_count") or review_summary.get("accepted_claim_count") or packet_summary.get("accepted_claim_count"),
        "blocked_claim_count": decision_summary.get("blocked_claim_count") or review_summary.get("blocked_claim_count") or packet_summary.get("blocked_claim_count"),
        "candidate_case_count": decision_summary.get("candidate_case_count") or review_summary.get("candidate_case_count") or packet_summary.get("candidate_case_count"),
        "random_seed": decision_summary.get("random_seed") or review_summary.get("random_seed") or packet_summary.get("random_seed"),
        "pass_rate": decision_summary.get("pass_rate") or review_summary.get("pass_rate") or packet_summary.get("pass_rate"),
        "allowed_use": EXPECTED_ALLOWED_USE if ready else "none",
        "model_quality_claim": EXPECTED_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "decision_scope": "bounded_randomized_holdout_publication_only" if ready else "not_claimed",
        "source_count": len(source_rows),
        "source_kinds": [str(row.get("kind")) for row in source_rows],
        "next_step": NEXT_STEP if ready else "repair_randomized_holdout_publication_decision_chain",
    }


def _summary(status: str, checks: list[dict[str, Any]], index: dict[str, Any], source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_decision_index_ready": status == "pass" and index.get("index_ready") is True,
        "indexed_decision": index.get("indexed_decision"),
        "bounded_publication_accepted": index.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "accepted_claim_count": index.get("accepted_claim_count"),
        "blocked_claim_count": index.get("blocked_claim_count"),
        "candidate_case_count": index.get("candidate_case_count"),
        "random_seed": index.get("random_seed"),
        "pass_rate": index.get("pass_rate"),
        "allowed_use": index.get("allowed_use"),
        "model_quality_claim": index.get("model_quality_claim"),
        "decision_scope": index.get("decision_scope"),
        "source_count": len(source_rows),
        "source_kinds": index.get("source_kinds"),
        "next_step": index.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_decision_index_ready"
    return "fix_randomized_holdout_publication_decision_index"


def _interpretation(status: str, index: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout publication decision chain is not indexable until packet, review, and decision evidence align.",
            "next_action": "repair randomized holdout publication decision-chain source artifacts",
        }
    return {
        "model_quality_claim": index.get("model_quality_claim"),
        "reason": "The bounded randomized holdout publication decision is indexed for downstream lookup while direct promotion remains blocked.",
        "next_action": index.get("next_step"),
    }


def _same_non_null(values: list[Any]) -> bool:
    if not values or any(value is None for value in values):
        return False
    return all(value == values[0] for value in values)


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_TEXT_FILENAME",
    "build_randomized_holdout_publication_decision_index",
    "locate_randomized_holdout_acceptance_publication_packet",
    "locate_randomized_holdout_publication_decision",
    "locate_randomized_holdout_publication_packet_review",
    "read_json_report",
    "resolve_exit_code",
]
