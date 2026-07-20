from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_target_hidden_holdout_dry_run import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME
from minigpt.randomized_target_hidden_holdout_real_replay import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME
from minigpt.randomized_target_hidden_holdout_replay_review import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
from minigpt.randomized_target_hidden_holdout_suite import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME = "randomized_holdout_candidate_promotion_packet.json"
RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_CSV_FILENAME = "randomized_holdout_candidate_promotion_packet.csv"
RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_TEXT_FILENAME = "randomized_holdout_candidate_promotion_packet.txt"
RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_MARKDOWN_FILENAME = "randomized_holdout_candidate_promotion_packet.md"
RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_HTML_FILENAME = "randomized_holdout_candidate_promotion_packet.html"


def locate_randomized_holdout_replay_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
    return source


def locate_randomized_holdout_real_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME
    return source


def locate_randomized_holdout_dry_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME
    return source


def locate_randomized_holdout_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout candidate promotion packet input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_candidate_promotion_packet(
    replay_review_report: dict[str, Any],
    real_replay_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    holdout_suite_report: dict[str, Any],
    *,
    replay_review_path: str | Path | None = None,
    real_replay_path: str | Path | None = None,
    dry_run_path: str | Path | None = None,
    holdout_suite_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout candidate promotion packet",
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_summary = as_dict(replay_review_report.get("summary"))
    real_summary = as_dict(real_replay_report.get("summary"))
    dry_summary = as_dict(dry_run_report.get("summary"))
    suite_summary = as_dict(holdout_suite_report.get("summary"))
    suite_cases = list_of_dicts(as_dict(holdout_suite_report.get("benchmark_suite")).get("cases"))
    evidence_rows = _evidence_rows(
        replay_review_report,
        real_replay_report,
        dry_run_report,
        holdout_suite_report,
        replay_review_path,
        real_replay_path,
        dry_run_path,
        holdout_suite_path,
    )
    checks = _checks(
        replay_review_report,
        real_replay_report,
        dry_run_report,
        holdout_suite_report,
        review_summary,
        real_summary,
        dry_summary,
        suite_summary,
        suite_cases,
        evidence_rows,
    )
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    packet = _packet(status, review_summary, real_summary, dry_summary, suite_summary, suite_cases, evidence_rows)
    summary = _summary(status, checks, packet)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_review": str(replay_review_path or ""),
        "source_real_replay": str(real_replay_path or ""),
        "source_dry_run": str(dry_run_path or ""),
        "source_holdout_suite": str(holdout_suite_path or ""),
        "replay_review_summary": review_summary,
        "real_replay_summary": real_summary,
        "dry_run_summary": dry_summary,
        "holdout_suite_summary": suite_summary,
        "evidence_rows": evidence_rows,
        "check_rows": checks,
        "packet": packet,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_packet_ready: bool,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_packet_ready and summary.get("randomized_holdout_candidate_promotion_packet_ready") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _evidence_rows(
    replay_review_report: dict[str, Any],
    real_replay_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    holdout_suite_report: dict[str, Any],
    replay_review_path: str | Path | None,
    real_replay_path: str | Path | None,
    dry_run_path: str | Path | None,
    holdout_suite_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _evidence(
            "randomized_replay_review",
            replay_review_path,
            replay_review_report,
            "randomized_target_hidden_holdout_replay_review_ready",
            "authorizes candidate packet while blocking direct promotion",
        ),
        _evidence(
            "randomized_real_replay",
            real_replay_path,
            real_replay_report,
            "randomized_target_hidden_holdout_real_replay_ready",
            "proves the real checkpoint passes randomized target-hidden prompts",
        ),
        _evidence(
            "randomized_dry_run",
            dry_run_path,
            dry_run_report,
            "randomized_target_hidden_holdout_dry_run_ready",
            "proves the scoring contract rejects the fixed-only negative control",
        ),
        _evidence(
            "randomized_suite",
            holdout_suite_path,
            holdout_suite_report,
            "randomized_target_hidden_holdout_suite_ready",
            "defines the 20 target-hidden randomized prompts",
        ),
    ]


def _evidence(kind: str, path: str | Path | None, report: dict[str, Any], ready_key: str, role: str) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    text = str(path or "")
    return {
        "kind": kind,
        "path": text,
        "exists": Path(text).exists() if text else False,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "ready_key": ready_key,
        "ready_value": summary.get(ready_key),
        "promotion_ready": summary.get("promotion_ready"),
        "role": role,
    }


def _checks(
    review: dict[str, Any],
    real: dict[str, Any],
    dry: dict[str, Any],
    suite: dict[str, Any],
    review_summary: dict[str, Any],
    real_summary: dict[str, Any],
    dry_summary: dict[str, Any],
    suite_summary: dict[str, Any],
    suite_cases: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seeds = _seed_values(review_summary, real_summary, dry_summary, suite_summary)
    case_counts = _case_counts(review_summary, real_summary, dry_summary, suite_summary, suite_cases)
    return [
        _check("replay_review_passed", review.get("status") == "pass", review.get("status"), "replay review must pass"),
        _check("replay_review_ready", review_summary.get("randomized_target_hidden_holdout_replay_review_ready") is True, review_summary.get("randomized_target_hidden_holdout_replay_review_ready"), "review summary must be ready"),
        _check("candidate_packet_authorized", review_summary.get("approved_for_candidate_promotion_packet") is True, review_summary.get("approved_for_candidate_promotion_packet"), "review must authorize a candidate packet"),
        _check("review_blocks_direct_promotion", review_summary.get("approved_for_promotion") is False and review_summary.get("promotion_ready") is False, {"approved_for_promotion": review_summary.get("approved_for_promotion"), "promotion_ready": review_summary.get("promotion_ready")}, "review must not widen the claim into promotion"),
        _check("review_routes_to_packet", review_summary.get("next_step") == "build_randomized_holdout_candidate_promotion_packet", review_summary.get("next_step"), "review should route to this packet"),
        _check("real_replay_passed", real.get("status") == "pass", real.get("status"), "real replay must pass"),
        _check("real_replay_ready", real_summary.get("randomized_target_hidden_holdout_real_replay_ready") is True, real_summary.get("randomized_target_hidden_holdout_real_replay_ready"), "real replay summary must be ready"),
        _check("real_model_signal_ready", real_summary.get("randomized_holdout_model_quality_ready") is True, real_summary.get("randomized_holdout_model_quality_ready"), "real replay must carry the randomized model-quality signal"),
        _check("dry_run_passed", dry.get("status") == "pass", dry.get("status"), "dry-run must pass structurally"),
        _check("dry_run_ready", dry_summary.get("randomized_target_hidden_holdout_dry_run_ready") is True, dry_summary.get("randomized_target_hidden_holdout_dry_run_ready"), "dry-run summary must be ready"),
        _check("negative_control_rejected", dry_summary.get("negative_control_passed") is False, dry_summary.get("negative_control_passed"), "negative control must not pass"),
        _check("suite_passed", suite.get("status") == "pass", suite.get("status"), "randomized suite must pass"),
        _check("suite_ready", suite_summary.get("randomized_target_hidden_holdout_suite_ready") is True, suite_summary.get("randomized_target_hidden_holdout_suite_ready"), "suite summary must be ready"),
        _check("candidate_count_at_least_twenty", int(suite_summary.get("candidate_case_count") or 0) >= 20, suite_summary.get("candidate_case_count"), "packet requires at least 20 randomized cases"),
        _check("suite_cases_match_summary", len(suite_cases) == int(suite_summary.get("candidate_case_count") or 0), {"cases": len(suite_cases), "summary": suite_summary.get("candidate_case_count")}, "suite case list must match summary"),
        _check("case_counts_consistent", _all_same(case_counts), case_counts, "suite, dry-run, replay, and review must cover the same case count"),
        _check("random_seed_consistent", _all_same(seeds), seeds, "all randomized reports must carry the same source seed"),
        _check("pass_rate_complete", float(review_summary.get("pass_rate") or 0.0) == 1.0 and float(real_summary.get("pass_rate") or 0.0) == 1.0, {"review": review_summary.get("pass_rate"), "real": real_summary.get("pass_rate")}, "candidate packet expects a 1.0 randomized replay pass rate"),
        _check("clean_randomized_cases_complete", int(review_summary.get("clean_randomized_case_count") or 0) == int(suite_summary.get("candidate_case_count") or 0), review_summary.get("clean_randomized_case_count"), "review must mark every randomized case clean"),
        _check("target_hidden_complete", int(review_summary.get("target_hidden_case_count") or 0) == int(suite_summary.get("candidate_case_count") or 0), review_summary.get("target_hidden_case_count"), "review must keep every randomized case target-hidden"),
        _check("no_task_hints_or_leakage", int(review_summary.get("task_hint_case_count") or 0) == 0 and int(review_summary.get("target_leakage_case_count") or 0) == 0, {"hints": review_summary.get("task_hint_case_count"), "leakage": review_summary.get("target_leakage_case_count")}, "review must report no hints or target leakage"),
        _check("all_evidence_files_exist", all(row.get("exists") is True for row in evidence_rows), evidence_rows, "all packet source files must exist"),
        _check("all_inputs_keep_promotion_false", all(row.get("promotion_ready") is False for row in evidence_rows), [row.get("promotion_ready") for row in evidence_rows], "candidate packet must not silently become promotion"),
    ]


def _seed_values(
    review_summary: dict[str, Any],
    real_summary: dict[str, Any],
    dry_summary: dict[str, Any],
    suite_summary: dict[str, Any],
) -> list[Any]:
    return [
        suite_summary.get("random_seed"),
        dry_summary.get("source_random_seed"),
        real_summary.get("source_random_seed"),
        review_summary.get("source_random_seed"),
    ]


def _case_counts(
    review_summary: dict[str, Any],
    real_summary: dict[str, Any],
    dry_summary: dict[str, Any],
    suite_summary: dict[str, Any],
    suite_cases: list[dict[str, Any]],
) -> list[Any]:
    return [
        suite_summary.get("candidate_case_count"),
        dry_summary.get("case_count"),
        real_summary.get("case_count"),
        review_summary.get("case_count"),
        len(suite_cases),
    ]


def _all_same(values: list[Any]) -> bool:
    if not values:
        return False
    return all(value == values[0] for value in values)


def _packet(
    status: str,
    review_summary: dict[str, Any],
    real_summary: dict[str, Any],
    dry_summary: dict[str, Any],
    suite_summary: dict[str, Any],
    suite_cases: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "packet_ready": status == "pass",
        "handoff_status": "ready_for_candidate_promotion_packet_review" if status == "pass" else "blocked",
        "candidate_case_count": suite_summary.get("candidate_case_count"),
        "suite_case_count": len(suite_cases),
        "random_seed": suite_summary.get("random_seed"),
        "randomized_case_factor": suite_summary.get("randomized_case_factor"),
        "passed_case_count": real_summary.get("passed_case_count"),
        "pass_rate": real_summary.get("pass_rate"),
        "clean_randomized_case_count": review_summary.get("clean_randomized_case_count"),
        "positive_dry_run_passed_case_count": dry_summary.get("positive_passed_case_count"),
        "negative_dry_run_passed_case_count": dry_summary.get("negative_passed_case_count"),
        "candidate_packet_authorized": review_summary.get("approved_for_candidate_promotion_packet"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "model_quality_claim": "candidate_packet_only",
        "next_step": "review_randomized_holdout_candidate_promotion_packet",
        "evidence_rows": evidence_rows,
    }


def _summary(status: str, checks: list[dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_candidate_promotion_packet_ready": status == "pass" and packet.get("packet_ready") is True,
        "handoff_status": packet.get("handoff_status"),
        "candidate_case_count": packet.get("candidate_case_count"),
        "suite_case_count": packet.get("suite_case_count"),
        "random_seed": packet.get("random_seed"),
        "randomized_case_factor": packet.get("randomized_case_factor"),
        "passed_case_count": packet.get("passed_case_count"),
        "pass_rate": packet.get("pass_rate"),
        "clean_randomized_case_count": packet.get("clean_randomized_case_count"),
        "positive_dry_run_passed_case_count": packet.get("positive_dry_run_passed_case_count"),
        "negative_dry_run_passed_case_count": packet.get("negative_dry_run_passed_case_count"),
        "candidate_packet_authorized": packet.get("candidate_packet_authorized"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "model_quality_claim": packet.get("model_quality_claim"),
        "next_step": packet.get("next_step"),
        "evidence_count": len(packet.get("evidence_rows") or []),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_candidate_promotion_packet_ready"
    return "fix_randomized_holdout_candidate_promotion_packet_inputs"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout candidate packet is blocked by failed or inconsistent source evidence.",
            "next_action": "repair randomized suite, dry-run, real replay, or replay review inputs",
        }
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The randomized target-hidden holdout chain is packaged for candidate-promotion review without widening into promotion.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_TEXT_FILENAME",
    "build_randomized_holdout_candidate_promotion_packet",
    "locate_randomized_holdout_dry_run",
    "locate_randomized_holdout_real_replay",
    "locate_randomized_holdout_replay_review",
    "locate_randomized_holdout_suite",
    "read_json_report",
    "resolve_exit_code",
]
