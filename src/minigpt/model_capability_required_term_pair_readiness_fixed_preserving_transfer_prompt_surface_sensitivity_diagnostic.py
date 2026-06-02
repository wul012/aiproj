from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_training_run import PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.json"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.csv"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.txt"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.md"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.html"
)


def locate_prompt_surface_sensitivity_training_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def locate_prompt_surface_sensitivity_replay_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("prompt-surface sensitivity diagnostic input must be a JSON object")
    return dict(payload)


def build_prompt_surface_sensitivity_diagnostic(
    training_report: dict[str, Any],
    replay_report: dict[str, Any],
    *,
    training_source_path: str | Path | None = None,
    replay_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = _surface_rows(replay_report)
    checks = _checks(training_report, replay_report, rows)
    issues = [row for row in checks if row["status"] != "pass"]
    summary = _summary(training_report, replay_report, rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness fixed-preserving transfer prompt-surface sensitivity diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_training_run": "" if training_source_path is None else str(training_source_path),
        "source_pair_probe_replay": "" if replay_source_path is None else str(replay_source_path),
        "surface_rows": rows,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _surface_rows(replay_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(replay_report.get("replay_rows")):
        rows.append(
            {
                "spec_id": row.get("spec_id"),
                "prompt": row.get("prompt"),
                "required_for_ready": bool(row.get("required_for_ready")),
                "replay_pair_full": bool(row.get("replay_pair_full")),
                "default_continuation_hit_count": int(row.get("default_continuation_hit_count") or 0),
                "suppression_continuation_hit_count": int(row.get("suppression_continuation_hit_count") or 0),
                "diagnosis": _row_diagnosis(row),
            }
        )
    return rows


def _row_diagnosis(row: dict[str, Any]) -> str:
    if row.get("replay_pair_full"):
        return "pair_full_surface"
    if row.get("required_for_ready"):
        return "required_surface_missed"
    return "optional_surface_missed"


def _checks(training_report: dict[str, Any], replay_report: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("training_passed", training_report.get("status") == "pass", training_report.get("status"), "training run must pass"),
        _check(
            "training_pair_full_observed",
            training_report.get("decision") == "pair_readiness_training_pair_full_observed",
            training_report.get("decision"),
            "diagnostic expects the v749 pair-full training observation",
        ),
        _check("replay_passed", replay_report.get("status") == "pass", replay_report.get("status"), "pair-probe replay must execute cleanly"),
        _check("surface_rows_present", bool(rows), len(rows), "replay report must contain surface rows"),
        _check(
            "required_surface_present",
            any(row.get("required_for_ready") for row in rows),
            [row.get("spec_id") for row in rows if row.get("required_for_ready")],
            "at least one required surface must be checked",
        ),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(training_report: dict[str, Any], replay_report: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    training_summary = as_dict(training_report.get("summary"))
    replay_summary = as_dict(replay_report.get("summary"))
    required_rows = [row for row in rows if row.get("required_for_ready")]
    required_missed = [row.get("spec_id") for row in required_rows if not row.get("replay_pair_full")]
    optional_passed = [row.get("spec_id") for row in rows if not row.get("required_for_ready") and row.get("replay_pair_full")]
    return {
        "training_pair_full_observed": training_summary.get("pair_full_observed") is True,
        "training_default_hit_count": training_summary.get("default_continuation_hit_count"),
        "replay_decision": replay_report.get("decision"),
        "exact_heldout_pair_full": replay_summary.get("exact_heldout_pair_full") is True,
        "required_all_pair_full": replay_summary.get("required_all_pair_full") is True,
        "pair_full_count": replay_summary.get("pair_full_count", 0),
        "surface_count": len(rows),
        "required_missed_surface_ids": required_missed,
        "optional_pair_full_surface_ids": optional_passed,
        "surface_sensitivity_observed": bool(required_missed and optional_passed),
        "promotion_blocked": bool(required_missed),
        "recommended_next_artifact": "exact_surface_repair_plan" if required_missed else "promotion_guard",
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic"
    if summary.get("surface_sensitivity_observed"):
        return "pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found"
    if summary.get("required_all_pair_full"):
        return "pair_readiness_fixed_preserving_transfer_prompt_surface_ready_for_promotion_guard"
    return "pair_readiness_fixed_preserving_transfer_prompt_surface_not_ready"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The training/replay inputs are not clean enough to diagnose prompt-surface behavior.",
            "next_action": "repair diagnostic inputs",
        }
    if summary.get("surface_sensitivity_observed"):
        return {
            "model_quality_claim": "prompt_surface_sensitive_pair_probe",
            "reason": "An optional pair surface is pair-full while the required exact heldout pair surface is missed.",
            "next_action": "plan a minimal exact-surface repair before any checkpoint promotion",
        }
    if summary.get("required_all_pair_full"):
        return {
            "model_quality_claim": "pair_probe_replay_ready",
            "reason": "All required pair surfaces replayed pair-full.",
            "next_action": "run promotion guard and seed-stability checks",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "No required prompt-surface replay readiness was observed.",
        "next_action": "repair corpus or decoding surface before promotion",
    }


__all__ = [
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_TEXT_FILENAME",
    "build_prompt_surface_sensitivity_diagnostic",
    "locate_prompt_surface_sensitivity_replay_source",
    "locate_prompt_surface_sensitivity_training_source",
    "read_json_report",
    "resolve_exit_code",
]
