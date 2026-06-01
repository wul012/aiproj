from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_aligned_candidate_seed_stability import (
    PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_refresh_forced_choice_diagnostic import (
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_JSON_FILENAME = "model_capability_required_term_pair_dual_boundary_batch_closeout.json"
PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_CSV_FILENAME = "model_capability_required_term_pair_dual_boundary_batch_closeout.csv"
PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_TEXT_FILENAME = "model_capability_required_term_pair_dual_boundary_batch_closeout.txt"
PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_MARKDOWN_FILENAME = "model_capability_required_term_pair_dual_boundary_batch_closeout.md"
PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_HTML_FILENAME = "model_capability_required_term_pair_dual_boundary_batch_closeout.html"


def locate_dual_boundary_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME
    return source


def locate_dual_boundary_forced_choice_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("dual-boundary closeout input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_dual_boundary_batch_closeout(
    stability_report: dict[str, Any],
    forced_choice_report: dict[str, Any],
    *,
    stability_source_path: str | Path | None = None,
    forced_choice_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    seed_rows = _seed_rows(stability_report, forced_choice_report)
    issues = _issues(stability_report, forced_choice_report, seed_rows)
    summary = _summary(seed_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair dual-boundary batch closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_stability_path": str(stability_source_path or ""),
        "source_forced_choice_path": str(forced_choice_source_path or ""),
        "source_stability": {
            "status": stability_report.get("status"),
            "decision": stability_report.get("decision"),
            "summary": as_dict(stability_report.get("summary")),
        },
        "source_forced_choice": {
            "status": forced_choice_report.get("status"),
            "decision": forced_choice_report.get("decision"),
            "summary": as_dict(forced_choice_report.get("summary")),
        },
        "seed_rows": seed_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _seed_rows(stability_report: dict[str, Any], forced_choice_report: dict[str, Any]) -> list[dict[str, Any]]:
    forced_by_seed = {
        _seed_from_label(str(row.get("source_label") or "")): row
        for row in list_of_dicts(forced_choice_report.get("source_summaries"))
    }
    rows = []
    for row in list_of_dicts(stability_report.get("seed_rows")):
        seed = int(row.get("seed") or 0)
        forced = as_dict(forced_by_seed.get(seed))
        generation_pair_full = bool(row.get("pair_full_observed"))
        internal_pair_full = bool(forced.get("forced_choice_full_match"))
        rows.append(
            {
                "seed": seed,
                "generation_pair_full": generation_pair_full,
                "internal_pair_full": internal_pair_full,
                "aligned_pair_full": generation_pair_full and internal_pair_full,
                "generation_decision": row.get("decision"),
                "internal_expected_best_terms": forced.get("expected_best_terms") or [],
                "classification": _classification(generation_pair_full, internal_pair_full),
            }
        )
    return rows


def _issues(stability_report: dict[str, Any], forced_choice_report: dict[str, Any], seed_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if stability_report.get("status") != "pass":
        issues.append("source seed stability report is not pass")
    if forced_choice_report.get("status") != "pass":
        issues.append("source forced-choice report is not pass")
    if not seed_rows:
        issues.append("no seed rows available for closeout")
    internal_count = sum(1 for row in seed_rows if row.get("internal_pair_full"))
    forced_summary = as_dict(forced_choice_report.get("summary"))
    if forced_summary and internal_count != forced_summary.get("forced_choice_full_match_source_count"):
        issues.append("forced-choice source count does not match joined seed rows")
    return issues


def _summary(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(seed_rows)
    generation_count = sum(1 for row in seed_rows if row.get("generation_pair_full"))
    internal_count = sum(1 for row in seed_rows if row.get("internal_pair_full"))
    aligned_count = sum(1 for row in seed_rows if row.get("aligned_pair_full"))
    internal_only_count = sum(1 for row in seed_rows if row.get("classification") == "internal_only_generation_surface_miss")
    return {
        "seed_count": seed_count,
        "generation_pair_full_seed_count": generation_count,
        "internal_pair_full_seed_count": internal_count,
        "aligned_pair_full_seed_count": aligned_count,
        "internal_only_seed_count": internal_only_count,
        "stable_generation_pair_full": bool(seed_rows) and generation_count == seed_count,
        "stable_internal_pair_full": bool(seed_rows) and internal_count == seed_count,
        "promotion_ready": bool(seed_rows) and generation_count == seed_count and internal_count == seed_count,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_dual_boundary_closeout_inputs"
    if summary.get("promotion_ready"):
        return "required_term_pair_dual_boundary_ready_for_candidate_promotion"
    if summary.get("stable_internal_pair_full") and not summary.get("stable_generation_pair_full"):
        return "required_term_pair_dual_boundary_internal_stable_generation_surface_unstable"
    if summary.get("aligned_pair_full_seed_count"):
        return "required_term_pair_dual_boundary_partial_alignment"
    return "required_term_pair_dual_boundary_not_recovered"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "Closeout inputs are incomplete or inconsistent."
        next_action = "repair closeout inputs before changing training"
        claim = "not_claimed"
    elif summary.get("promotion_ready"):
        reason = "All tested seeds align both generation pair-full and internal forced-choice pair-full."
        next_action = "promote as a candidate baseline and test held-out surfaces"
        claim = "targeted_pair_refresh_stable_signal"
    elif summary.get("stable_internal_pair_full") and not summary.get("stable_generation_pair_full"):
        reason = "Internal forced-choice is stable across seeds, but generation pair-full is not stable."
        next_action = "focus next experiments on generation surface stability or decoding policy, not internal preference repair"
        claim = "targeted_internal_preference_stable_signal_only"
    elif summary.get("aligned_pair_full_seed_count"):
        reason = "Only part of the seed set aligns both generation and internal evidence."
        next_action = "inspect aligned and missed seeds before promotion"
        claim = "targeted_pair_refresh_partial_signal"
    else:
        reason = "No seed aligns both generation and internal evidence."
        next_action = "return to corpus design"
        claim = "not_claimed"
    return {
        "model_quality_claim": claim,
        "reason": reason,
        "next_action": next_action,
    }


def _classification(generation_pair_full: bool, internal_pair_full: bool) -> str:
    if generation_pair_full and internal_pair_full:
        return "generation_internal_pair_full"
    if internal_pair_full:
        return "internal_only_generation_surface_miss"
    if generation_pair_full:
        return "generation_only_internal_miss"
    return "not_recovered"


def _seed_from_label(label: str) -> int:
    match = re.search(r"seed-(?P<seed>[0-9]+)", label)
    return int(match.group("seed")) if match else 0


__all__ = [
    "PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_CSV_FILENAME",
    "PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_HTML_FILENAME",
    "PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_JSON_FILENAME",
    "PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_DUAL_BOUNDARY_BATCH_CLOSEOUT_TEXT_FILENAME",
    "build_model_capability_required_term_pair_dual_boundary_batch_closeout",
    "locate_dual_boundary_forced_choice_source",
    "locate_dual_boundary_stability_source",
    "read_json_report",
    "resolve_exit_code",
]
