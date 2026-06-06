from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_bounded_promotion_decision import RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_JSON_FILENAME
from minigpt.randomized_holdout_bounded_promotion_gate import RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME
from minigpt.randomized_holdout_candidate_promotion_packet import RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
from minigpt.randomized_holdout_candidate_promotion_packet_review import RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME
from minigpt.report_utils import as_dict, utc_now


RANDOMIZED_HOLDOUT_DECISION_INDEX_JSON_FILENAME = "randomized_holdout_decision_index.json"
RANDOMIZED_HOLDOUT_DECISION_INDEX_CSV_FILENAME = "randomized_holdout_decision_index.csv"
RANDOMIZED_HOLDOUT_DECISION_INDEX_TEXT_FILENAME = "randomized_holdout_decision_index.txt"
RANDOMIZED_HOLDOUT_DECISION_INDEX_MARKDOWN_FILENAME = "randomized_holdout_decision_index.md"
RANDOMIZED_HOLDOUT_DECISION_INDEX_HTML_FILENAME = "randomized_holdout_decision_index.html"


def locate_randomized_holdout_bounded_promotion_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_DECISION_JSON_FILENAME
    return source


def locate_randomized_holdout_bounded_promotion_gate(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_BOUNDED_PROMOTION_GATE_JSON_FILENAME
    return source


def locate_randomized_holdout_candidate_packet_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_REVIEW_JSON_FILENAME
    return source


def locate_randomized_holdout_candidate_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout decision index input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_decision_index(
    bounded_decision_report: dict[str, Any],
    bounded_gate_report: dict[str, Any],
    candidate_packet_review_report: dict[str, Any],
    candidate_packet_report: dict[str, Any],
    *,
    bounded_decision_path: str | Path | None = None,
    bounded_gate_path: str | Path | None = None,
    candidate_packet_review_path: str | Path | None = None,
    candidate_packet_path: str | Path | None = None,
    minimum_candidate_cases: int = 20,
    title: str = "MiniGPT randomized holdout decision index",
    generated_at: str | None = None,
) -> dict[str, Any]:
    decision_summary = as_dict(bounded_decision_report.get("summary"))
    gate_summary = as_dict(bounded_gate_report.get("summary"))
    review_summary = as_dict(candidate_packet_review_report.get("summary"))
    packet_summary = as_dict(candidate_packet_report.get("summary"))
    sources = _sources(
        bounded_decision_report,
        bounded_gate_report,
        candidate_packet_review_report,
        candidate_packet_report,
        decision_summary,
        gate_summary,
        review_summary,
        packet_summary,
        bounded_decision_path,
        bounded_gate_path,
        candidate_packet_review_path,
        candidate_packet_path,
    )
    checks = _checks(
        bounded_decision_report,
        bounded_gate_report,
        candidate_packet_review_report,
        candidate_packet_report,
        decision_summary,
        gate_summary,
        review_summary,
        packet_summary,
        sources,
        minimum_candidate_cases,
    )
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    index = _index(status, decision_summary, gate_summary, review_summary, packet_summary, sources)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_rows": sources,
        "check_rows": checks,
        "index": index,
        "summary": _summary(status, checks, index, sources),
        "interpretation": _interpretation(status, index),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_index_ready: bool,
    require_bounded_acceptance: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_index_ready and summary.get("randomized_holdout_decision_index_ready") is not True:
        return 1
    if require_bounded_acceptance and summary.get("bounded_promotion_accepted") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _sources(
    decision_report: dict[str, Any],
    gate_report: dict[str, Any],
    review_report: dict[str, Any],
    packet_report: dict[str, Any],
    decision_summary: dict[str, Any],
    gate_summary: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    decision_path: str | Path | None,
    gate_path: str | Path | None,
    review_path: str | Path | None,
    packet_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _source_row(
            "bounded_decision",
            decision_path,
            decision_report,
            decision_summary,
            "randomized_holdout_bounded_promotion_decision_ready",
            "records the bounded randomized holdout acceptance without enabling direct promotion",
        ),
        _source_row(
            "bounded_gate",
            gate_path,
            gate_report,
            gate_summary,
            "randomized_holdout_bounded_promotion_gate_ready",
            "verifies packet review and packet can enter bounded decision",
        ),
        _source_row(
            "candidate_packet_review",
            review_path,
            review_report,
            review_summary,
            "randomized_holdout_candidate_promotion_packet_review_ready",
            "reviews candidate packet for bounded gate only",
        ),
        _source_row(
            "candidate_packet",
            packet_path,
            packet_report,
            packet_summary,
            "randomized_holdout_candidate_promotion_packet_ready",
            "packages randomized target-hidden evidence without direct promotion",
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
        "candidate_case_count": summary.get("candidate_case_count"),
        "random_seed": summary.get("random_seed"),
        "pass_rate": summary.get("pass_rate"),
        "promotion_ready": summary.get("promotion_ready"),
        "approved_for_promotion": summary.get("approved_for_promotion"),
        "model_quality_claim": summary.get("model_quality_claim"),
        "failed_check_count": summary.get("failed_check_count"),
        "role": role,
    }


def _checks(
    decision_report: dict[str, Any],
    gate_report: dict[str, Any],
    review_report: dict[str, Any],
    packet_report: dict[str, Any],
    decision_summary: dict[str, Any],
    gate_summary: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    sources: list[dict[str, Any]],
    minimum_candidate_cases: int,
) -> list[dict[str, Any]]:
    counts = [
        decision_summary.get("candidate_case_count"),
        gate_summary.get("candidate_case_count"),
        review_summary.get("candidate_case_count"),
        packet_summary.get("candidate_case_count"),
    ]
    clean_counts = [
        gate_summary.get("clean_randomized_case_count"),
        review_summary.get("clean_randomized_case_count"),
        packet_summary.get("clean_randomized_case_count"),
    ]
    seeds = [
        decision_summary.get("random_seed"),
        gate_summary.get("random_seed"),
        review_summary.get("random_seed"),
        packet_summary.get("random_seed"),
    ]
    pass_rates = [
        decision_summary.get("pass_rate"),
        gate_summary.get("pass_rate"),
        review_summary.get("pass_rate"),
        packet_summary.get("pass_rate"),
    ]
    return [
        _check("source_files_exist", all(row.get("exists") is True for row in sources), [row.get("exists") for row in sources], "all indexed source artifact files must exist"),
        _check("bounded_decision_passed", decision_report.get("status") == "pass", decision_report.get("status"), "bounded decision must pass"),
        _check("bounded_decision_accepted", decision_report.get("decision") == "randomized_holdout_bounded_promotion_decision_accepted", decision_report.get("decision"), "bounded decision must be accepted"),
        _check("bounded_decision_ready", decision_summary.get("randomized_holdout_bounded_promotion_decision_ready") is True, decision_summary.get("randomized_holdout_bounded_promotion_decision_ready"), "bounded decision summary must be ready"),
        _check("bounded_acceptance_true", decision_summary.get("bounded_promotion_accepted") is True, decision_summary.get("bounded_promotion_accepted"), "decision must accept bounded randomized holdout claim"),
        _check("gate_passed", gate_report.get("status") == "pass", gate_report.get("status"), "bounded gate must pass"),
        _check("gate_ready", gate_summary.get("randomized_holdout_bounded_promotion_gate_ready") is True, gate_summary.get("randomized_holdout_bounded_promotion_gate_ready"), "bounded gate summary must be ready"),
        _check("gate_approves_decision", gate_summary.get("approved_for_bounded_promotion_decision") is True, gate_summary.get("approved_for_bounded_promotion_decision"), "gate must approve bounded decision entry"),
        _check("review_passed", review_report.get("status") == "pass", review_report.get("status"), "candidate packet review must pass"),
        _check("review_ready", review_summary.get("randomized_holdout_candidate_promotion_packet_review_ready") is True, review_summary.get("randomized_holdout_candidate_promotion_packet_review_ready"), "candidate packet review summary must be ready"),
        _check("review_approves_gate", review_summary.get("approved_for_bounded_promotion_gate") is True, review_summary.get("approved_for_bounded_promotion_gate"), "review must approve bounded gate entry"),
        _check("packet_passed", packet_report.get("status") == "pass", packet_report.get("status"), "candidate packet must pass"),
        _check("packet_ready", packet_summary.get("randomized_holdout_candidate_promotion_packet_ready") is True, packet_summary.get("randomized_holdout_candidate_promotion_packet_ready"), "candidate packet summary must be ready"),
        _check("packet_authorized", packet_summary.get("candidate_packet_authorized") is True, packet_summary.get("candidate_packet_authorized"), "candidate packet must be authorized"),
        _check("candidate_count_floor", min(_ints(counts)) >= minimum_candidate_cases, counts, "all levels must keep at least the randomized 20-case floor"),
        _check("candidate_counts_match", _same_non_null(counts), counts, "decision, gate, review, and packet candidate counts must match"),
        _check("clean_counts_match_candidate_count", _same_non_null(clean_counts) and clean_counts[0] == packet_summary.get("candidate_case_count"), clean_counts, "gate, review, and packet clean randomized counts must match candidate count"),
        _check("random_seed_matches", _same_non_null(seeds), seeds, "all levels must carry the same randomized seed"),
        _check("pass_rate_complete", _same_non_null(pass_rates) and float(pass_rates[0]) == 1.0, pass_rates, "all levels must preserve the complete randomized replay pass rate"),
        _check("source_checks_clean", all(int(row.get("failed_check_count") or 0) == 0 for row in sources), [row.get("failed_check_count") for row in sources], "indexed source summaries must have no failed checks"),
        _check("promotion_still_false", all(row.get("promotion_ready") is False for row in sources), [row.get("promotion_ready") for row in sources], "decision index must not widen into direct promotion"),
        _check("approved_for_promotion_false", all(row.get("approved_for_promotion") is False for row in sources), [row.get("approved_for_promotion") for row in sources], "direct promotion approval must remain false"),
        _check(
            "claim_scopes_expected",
            decision_summary.get("model_quality_claim") == "bounded_randomized_target_hidden_holdout_claim_only"
            and gate_summary.get("model_quality_claim") == "bounded_gate_only"
            and review_summary.get("model_quality_claim") == "candidate_packet_review_only"
            and packet_summary.get("model_quality_claim") == "candidate_packet_only",
            [row.get("model_quality_claim") for row in sources],
            "each layer must keep its bounded claim scope",
        ),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _index(
    status: str,
    decision_summary: dict[str, Any],
    gate_summary: dict[str, Any],
    review_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "index_ready": ready,
        "indexed_decision": decision_summary.get("final_decision") if ready else "not_indexed",
        "bounded_promotion_accepted": bool(ready and decision_summary.get("bounded_promotion_accepted") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "candidate_case_count": decision_summary.get("candidate_case_count") or gate_summary.get("candidate_case_count") or review_summary.get("candidate_case_count") or packet_summary.get("candidate_case_count"),
        "random_seed": decision_summary.get("random_seed") or gate_summary.get("random_seed") or review_summary.get("random_seed") or packet_summary.get("random_seed"),
        "pass_rate": decision_summary.get("pass_rate") or gate_summary.get("pass_rate") or review_summary.get("pass_rate") or packet_summary.get("pass_rate"),
        "claim_scope": "randomized_target_hidden_20_case_tiny_checkpoint_only" if ready else "not_claimed",
        "model_quality_claim": "bounded_randomized_target_hidden_holdout_claim_only" if ready else "not_claimed",
        "source_count": len(sources),
        "source_kinds": [str(row.get("kind")) for row in sources],
        "next_step": "build_randomized_holdout_acceptance_summary" if ready else "repair_randomized_holdout_decision_chain",
    }


def _summary(status: str, checks: list[dict[str, Any]], index: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "randomized_holdout_decision_index_ready": status == "pass" and index.get("index_ready") is True,
        "indexed_decision": index.get("indexed_decision"),
        "bounded_promotion_accepted": index.get("bounded_promotion_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "candidate_case_count": index.get("candidate_case_count"),
        "random_seed": index.get("random_seed"),
        "pass_rate": index.get("pass_rate"),
        "claim_scope": index.get("claim_scope"),
        "model_quality_claim": index.get("model_quality_claim"),
        "source_count": len(sources),
        "source_kinds": index.get("source_kinds"),
        "next_step": index.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_decision_index_ready"
    return "fix_randomized_holdout_decision_index"


def _interpretation(status: str, index: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout decision chain is not indexable until bounded decision, gate, review, and packet evidence align.",
            "next_action": "repair randomized holdout decision-chain source artifacts",
        }
    return {
        "model_quality_claim": index.get("model_quality_claim"),
        "reason": "The bounded randomized holdout acceptance can now be consumed through a single decision index while direct promotion remains blocked.",
        "next_action": index.get("next_step"),
    }


def _ints(values: list[Any]) -> list[int]:
    return [int(value or 0) for value in values]


def _same_non_null(values: list[Any]) -> bool:
    if not values or any(value is None for value in values):
        return False
    return all(value == values[0] for value in values)


__all__ = [
    "RANDOMIZED_HOLDOUT_DECISION_INDEX_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_DECISION_INDEX_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_DECISION_INDEX_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_DECISION_INDEX_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_DECISION_INDEX_TEXT_FILENAME",
    "build_randomized_holdout_decision_index",
    "locate_randomized_holdout_bounded_promotion_decision",
    "locate_randomized_holdout_bounded_promotion_gate",
    "locate_randomized_holdout_candidate_packet",
    "locate_randomized_holdout_candidate_packet_review",
    "read_json_report",
    "resolve_exit_code",
]
