from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_training_run import (
    PAIR_READINESS_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_JSON_FILENAME = "model_capability_required_term_pair_readiness_heldout_failure_diagnostic.json"
PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_CSV_FILENAME = "model_capability_required_term_pair_readiness_heldout_failure_diagnostic.csv"
PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_TEXT_FILENAME = "model_capability_required_term_pair_readiness_heldout_failure_diagnostic.txt"
PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_heldout_failure_diagnostic.md"
PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_HTML_FILENAME = "model_capability_required_term_pair_readiness_heldout_failure_diagnostic.html"


def locate_pair_readiness_heldout_failure_diagnostic_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair-readiness heldout failure diagnostic input must be a JSON object")
    return dict(payload)


def build_pair_readiness_heldout_failure_diagnostic(
    training_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = _case_rows(training_report)
    analysis_rows = [_analysis_row(row) for row in rows]
    summary = _summary(training_report, analysis_rows)
    issues = _issues(training_report, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness heldout failure diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_training_path": str(source_path or ""),
        "source_training": {
            "status": training_report.get("status"),
            "decision": training_report.get("decision"),
            "summary": as_dict(training_report.get("summary")),
        },
        "analysis_rows": analysis_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _case_rows(training_report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(as_dict(training_report.get("replay_report")).get("case_rows"))


def _analysis_row(row: dict[str, Any]) -> dict[str, Any]:
    term = str(row.get("term") or "")
    continuation = str(row.get("continuation") or "")
    fixed_present = "fixed" in continuation
    loss_present = "loss" in continuation
    return {
        "profile_id": row.get("profile_id"),
        "term": term,
        "prompt": row.get("prompt"),
        "generated": row.get("generated_preview") or row.get("generated"),
        "continuation": continuation,
        "continuation_hit": bool(row.get("continuation_hit")),
        "fixed_present": fixed_present,
        "loss_present": loss_present,
        "pollution_class": _pollution_class(term, fixed_present, loss_present),
    }


def _pollution_class(term: str, fixed_present: bool, loss_present: bool) -> str:
    if term == "fixed" and fixed_present:
        return "expected-fixed"
    if term == "loss" and loss_present:
        return "expected-loss"
    if term == "fixed" and loss_present:
        return "fixed-prompt-loss-pollution"
    if term == "loss" and fixed_present:
        return "loss-prompt-fixed-pollution"
    return "miss"


def _summary(training_report: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    classes = [str(row.get("pollution_class")) for row in rows if row.get("profile_id") == "default"]
    return {
        "training_status": as_dict(training_report.get("summary")).get("training_status"),
        "pair_full_observed": as_dict(training_report.get("summary")).get("pair_full_observed"),
        "default_row_count": len(classes),
        "fixed_hit_count": classes.count("expected-fixed"),
        "loss_hit_count": classes.count("expected-loss"),
        "loss_prompt_fixed_pollution_count": classes.count("loss-prompt-fixed-pollution"),
        "fixed_prompt_loss_pollution_count": classes.count("fixed-prompt-loss-pollution"),
        "miss_count": classes.count("miss"),
        "dominant_failure": _dominant_failure(classes),
    }


def _dominant_failure(classes: list[str]) -> str:
    if "loss-prompt-fixed-pollution" in classes:
        return "loss_prompt_absorbed_by_fixed"
    if "fixed-prompt-loss-pollution" in classes:
        return "fixed_prompt_absorbed_by_loss"
    if "miss" in classes:
        return "heldout_direct_miss"
    return "none"


def _issues(training_report: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if training_report.get("status") != "pass":
        issues.append({"id": "training_report_not_pass", "detail": "source training report must pass"})
    if as_dict(training_report.get("replay_report")).get("status") != "pass":
        issues.append({"id": "replay_report_not_pass", "detail": "source replay report must pass"})
    if int(summary.get("default_row_count") or 0) < 2:
        issues.append({"id": "too_few_default_rows", "detail": "need default fixed/loss rows for diagnosis"})
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_heldout_failure_diagnostic_input"
    if summary.get("dominant_failure") == "loss_prompt_absorbed_by_fixed":
        return "pair_readiness_loss_prompt_absorbed_by_fixed"
    if summary.get("dominant_failure") == "fixed_prompt_absorbed_by_loss":
        return "pair_readiness_fixed_prompt_absorbed_by_loss"
    if summary.get("pair_full_observed") is True:
        return "pair_readiness_no_heldout_failure"
    return "pair_readiness_heldout_direct_miss"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The heldout failure diagnostic could not trust the source replay.",
            "next_action": "repair source training replay before changing corpus",
        }
    return {
        "model_quality_claim": "diagnostic_only",
        "reason": f"Dominant heldout failure is {summary.get('dominant_failure')}.",
        "next_action": "plan a loss-retention repair only if loss prompt fixed-pollution is dominant",
    }


__all__ = [
    "PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_TEXT_FILENAME",
    "build_pair_readiness_heldout_failure_diagnostic",
    "locate_pair_readiness_heldout_failure_diagnostic_source",
    "read_json_report",
    "resolve_exit_code",
]
