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


PAIR_SURFACE_FAILURE_DIAGNOSTIC_JSON_FILENAME = "model_capability_required_term_pair_surface_failure_diagnostic.json"
PAIR_SURFACE_FAILURE_DIAGNOSTIC_CSV_FILENAME = "model_capability_required_term_pair_surface_failure_diagnostic.csv"
PAIR_SURFACE_FAILURE_DIAGNOSTIC_TEXT_FILENAME = "model_capability_required_term_pair_surface_failure_diagnostic.txt"
PAIR_SURFACE_FAILURE_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_failure_diagnostic.md"
PAIR_SURFACE_FAILURE_DIAGNOSTIC_HTML_FILENAME = "model_capability_required_term_pair_surface_failure_diagnostic.html"


def locate_surface_failure_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME
    return source


def locate_surface_failure_forced_choice_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface failure diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_surface_failure_diagnostic(
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
        "title": "MiniGPT required-term pair surface failure diagnostic",
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
    refresh_by_seed = {
        int(as_dict(report.get("settings")).get("seed") or 0): report
        for report in list_of_dicts(stability_report.get("seed_reports"))
    }
    rows: list[dict[str, Any]] = []
    for seed_row in list_of_dicts(stability_report.get("seed_rows")):
        seed = int(seed_row.get("seed") or 0)
        refresh = as_dict(refresh_by_seed.get(seed))
        replay = as_dict(refresh.get("replay_report"))
        forced = as_dict(forced_by_seed.get(seed))
        generation_hit_terms = _generation_hit_terms(replay)
        generation_missed_terms = _generation_missed_terms(replay)
        internal_terms = [str(term) for term in forced.get("expected_best_terms") or []]
        rows.append(
            {
                "seed": seed,
                "generation_pair_full": bool(seed_row.get("pair_full_observed")),
                "generation_hit_terms": generation_hit_terms,
                "generation_missed_terms": generation_missed_terms,
                "internal_pair_full": bool(forced.get("forced_choice_full_match")),
                "internal_expected_best_terms": internal_terms,
                "surface_failure_terms": [term for term in internal_terms if term in generation_missed_terms],
                "dominant_failure_term": _dominant_failure_term(generation_missed_terms, internal_terms),
                "best_generation_preview": _best_generation_preview(replay, generation_missed_terms),
                "classification": _classification(bool(seed_row.get("pair_full_observed")), bool(forced.get("forced_choice_full_match"))),
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
        issues.append("no seed rows available for surface failure diagnostic")
    return issues


def _summary(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(seed_rows)
    surface_failure_rows = [row for row in seed_rows if row.get("classification") == "internal_stable_surface_failure"]
    failed_terms = sorted({term for row in surface_failure_rows for term in row.get("surface_failure_terms", [])})
    return {
        "seed_count": seed_count,
        "generation_pair_full_seed_count": sum(1 for row in seed_rows if row.get("generation_pair_full")),
        "internal_pair_full_seed_count": sum(1 for row in seed_rows if row.get("internal_pair_full")),
        "surface_failure_seed_count": len(surface_failure_rows),
        "surface_failure_seeds": [row.get("seed") for row in surface_failure_rows],
        "surface_failure_terms": failed_terms,
        "single_surface_failure_term": failed_terms[0] if len(failed_terms) == 1 else "",
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_failure_inputs"
    if summary.get("surface_failure_seed_count"):
        if summary.get("single_surface_failure_term"):
            return "required_term_pair_single_term_surface_failure_isolated"
        return "required_term_pair_surface_failure_isolated"
    return "required_term_pair_surface_failure_not_observed"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "Input reports are incomplete or inconsistent."
        next_action = "repair diagnostic inputs before changing generation policy"
        claim = "not_claimed"
    elif summary.get("surface_failure_seed_count"):
        term = summary.get("single_surface_failure_term")
        if term:
            reason = f"Internal preference is stable, but generation misses `{term}` on at least one seed."
        else:
            reason = "Internal preference is stable, but generation misses required terms on at least one seed."
        next_action = "design a generation-surface policy replay before retraining"
        claim = "targeted_surface_failure_diagnostic"
    else:
        reason = "No internal-stable/free-generation surface failure was found."
        next_action = "proceed to broader held-out prompt checks"
        claim = "not_claimed"
    return {"model_quality_claim": claim, "reason": reason, "next_action": next_action}


def _generation_hit_terms(replay: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for row in list_of_dicts(replay.get("variant_rows")):
        for term in row.get("hit_terms") or []:
            text = str(term)
            if text not in terms:
                terms.append(text)
    return terms


def _generation_missed_terms(replay: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for row in list_of_dicts(replay.get("variant_rows")):
        for term in row.get("missed_terms") or []:
            text = str(term)
            if text not in terms:
                terms.append(text)
    return terms


def _best_generation_preview(replay: dict[str, Any], missed_terms: list[str]) -> str:
    if not missed_terms:
        return ""
    target = missed_terms[0]
    for row in list_of_dicts(replay.get("case_rows")):
        if str(row.get("term")) == target:
            return str(row.get("continuation_preview") or row.get("generated_preview") or "")
    return ""


def _dominant_failure_term(missed_terms: list[str], internal_terms: list[str]) -> str:
    for term in missed_terms:
        if term in internal_terms:
            return term
    return missed_terms[0] if missed_terms else ""


def _classification(generation_pair_full: bool, internal_pair_full: bool) -> str:
    if generation_pair_full and internal_pair_full:
        return "aligned_pair_full"
    if internal_pair_full:
        return "internal_stable_surface_failure"
    if generation_pair_full:
        return "generation_only_internal_failure"
    return "not_recovered"


def _seed_from_label(label: str) -> int:
    match = re.search(r"seed-(?P<seed>[0-9]+)", label)
    return int(match.group("seed")) if match else 0


__all__ = [
    "PAIR_SURFACE_FAILURE_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_SURFACE_FAILURE_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_SURFACE_FAILURE_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_SURFACE_FAILURE_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_SURFACE_FAILURE_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_required_term_pair_surface_failure_diagnostic",
    "locate_surface_failure_forced_choice_source",
    "locate_surface_failure_stability_source",
    "read_json_report",
    "resolve_exit_code",
]
