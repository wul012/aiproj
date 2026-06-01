from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison import (
    PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_generation_internal_alignment_route_decision import (
    PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_refresh_forced_choice_diagnostic import (
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


SURFACE_FIRST_FAILURE_ANALYSIS_JSON_FILENAME = (
    "model_capability_required_term_pair_surface_first_failure_analysis.json"
)
SURFACE_FIRST_FAILURE_ANALYSIS_CSV_FILENAME = (
    "model_capability_required_term_pair_surface_first_failure_analysis.csv"
)
SURFACE_FIRST_FAILURE_ANALYSIS_TEXT_FILENAME = (
    "model_capability_required_term_pair_surface_first_failure_analysis.txt"
)
SURFACE_FIRST_FAILURE_ANALYSIS_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_surface_first_failure_analysis.md"
)
SURFACE_FIRST_FAILURE_ANALYSIS_HTML_FILENAME = (
    "model_capability_required_term_pair_surface_first_failure_analysis.html"
)


def locate_surface_first_refresh_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def locate_surface_first_forced_choice_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME
    return source


def locate_surface_first_alignment_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME
    return source


def locate_surface_first_route_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_GENERATION_INTERNAL_ALIGNMENT_ROUTE_DECISION_JSON_FILENAME
    return source


def read_surface_first_analysis_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface-first failure analysis input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_surface_first_failure_analysis(
    *,
    refresh_report: dict[str, Any],
    forced_choice_report: dict[str, Any],
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
    source_label: str = "surface-first-schedule",
    generated_at: str | None = None,
) -> dict[str, Any]:
    evidence_rows = _evidence_rows(refresh_report, forced_choice_report, comparison_report, route_decision_report, source_label)
    issues = _issues(refresh_report, forced_choice_report, comparison_report, route_decision_report, evidence_rows)
    summary = _summary(evidence_rows, route_decision_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface-first failure analysis",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_label": source_label,
        "evidence_rows": evidence_rows,
        "summary": summary,
        "recommendations": _recommendations(status, summary),
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _evidence_rows(
    refresh_report: dict[str, Any],
    forced_choice_report: dict[str, Any],
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
    source_label: str,
) -> list[dict[str, Any]]:
    refresh_hits = _generation_hits(refresh_report)
    forced_terms = _forced_expected_terms(forced_choice_report, source_label)
    comparison_row = _comparison_row(comparison_report, source_label)
    route_summary = as_dict(route_decision_report.get("summary"))
    return [
        {
            "id": "generation_replay",
            "status": "observed",
            "value": sorted(refresh_hits),
            "detail": "Surface-first generation replay hit terms.",
        },
        {
            "id": "forced_choice",
            "status": "observed",
            "value": sorted(forced_terms),
            "detail": "Surface-first expected-best forced-choice terms.",
        },
        {
            "id": "alignment_class",
            "status": str(comparison_row.get("alignment_class") or "missing"),
            "value": comparison_row.get("alignment_class"),
            "detail": "How the full comparison classifies the surface-first route.",
        },
        {
            "id": "route_selection",
            "status": "not_selected" if route_summary.get("selected_generation_route_label") != source_label else "selected",
            "value": route_summary.get("selected_generation_route_label"),
            "detail": "The route decision selected a different generation route when surface-first was added.",
        },
    ]


def _generation_hits(refresh_report: dict[str, Any]) -> set[str]:
    replay = as_dict(refresh_report.get("replay_report"))
    return {
        str(row.get("term"))
        for row in list_of_dicts(replay.get("case_rows"))
        if row.get("continuation_hit") and str(row.get("term")) in {"fixed", "loss"}
    }


def _forced_expected_terms(forced_choice_report: dict[str, Any], source_label: str) -> set[str]:
    return {
        str(row.get("prompt_term"))
        for row in list_of_dicts(forced_choice_report.get("prompt_summaries"))
        if str(row.get("source_label") or "") == source_label
        and row.get("expected_best")
        and str(row.get("prompt_term")) in {"fixed", "loss"}
    }


def _comparison_row(comparison_report: dict[str, Any], source_label: str) -> dict[str, Any]:
    for row in list_of_dicts(comparison_report.get("source_rows")):
        if str(row.get("source_label") or "") == source_label:
            return row
    return {}


def _issues(
    refresh_report: dict[str, Any],
    forced_choice_report: dict[str, Any],
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if refresh_report.get("status") != "pass":
        issues.append("surface-first refresh status is not pass")
    if forced_choice_report.get("status") != "pass":
        issues.append("surface-first forced-choice status is not pass")
    if comparison_report.get("status") != "pass":
        issues.append("surface-first comparison status is not pass")
    if route_decision_report.get("status") != "pass":
        issues.append("surface-first route decision status is not pass")
    if any(row.get("value") in (None, "missing") for row in evidence_rows):
        issues.append("surface-first evidence row is missing")
    return issues


def _summary(evidence_rows: list[dict[str, Any]], route_decision_report: dict[str, Any]) -> dict[str, Any]:
    generation_terms = set(_row_value(evidence_rows, "generation_replay"))
    forced_terms = set(_row_value(evidence_rows, "forced_choice"))
    alignment_class = str(_row_value(evidence_rows, "alignment_class") or "")
    route_summary = as_dict(route_decision_report.get("summary"))
    fixed_only_generation = generation_terms == {"fixed"}
    fixed_only_internal = forced_terms == {"fixed"}
    return {
        "generation_hit_terms": sorted(generation_terms),
        "forced_choice_expected_terms": sorted(forced_terms),
        "alignment_class": alignment_class,
        "fixed_collapse_confirmed": fixed_only_generation and fixed_only_internal,
        "selected_generation_route": route_summary.get("selected_generation_route_label"),
        "internal_anchor_route": route_summary.get("internal_anchor_route_label"),
        "next_objective": "loss_guarded_surface_schedule_repair",
    }


def _row_value(evidence_rows: list[dict[str, Any]], row_id: str) -> Any:
    for row in evidence_rows:
        if row.get("id") == row_id:
            return row.get("value")
    return None


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_surface_first_failure_analysis_inputs"
    if summary.get("fixed_collapse_confirmed"):
        return "surface_first_schedule_fixed_collapse_confirmed"
    return "surface_first_schedule_failure_inconclusive"


def _recommendations(status: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    if status != "pass":
        return [{"id": "repair_inputs", "action": "repair input artifacts before designing a follow-up corpus"}]
    return [
        {
            "id": "stop_surface_first_repeat",
            "action": "do not repeat the same surface-first schedule without a loss guard",
        },
        {
            "id": "keep_generation_baseline",
            "action": f"keep {summary.get('selected_generation_route')} as the generation baseline",
        },
        {
            "id": "try_loss_guard",
            "action": "add loss-guarded rows before running the next tiny training seed",
        },
    ]


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The failure analysis inputs are incomplete.",
            "next_action": "repair input artifacts",
        }
    return {
        "model_quality_claim": "negative_route_diagnosis",
        "reason": "Surface-first schedule collapsed to fixed-only generation and fixed-only internal preference.",
        "next_action": "try a loss-guarded schedule approximation or stop this branch",
    }


__all__ = [
    "SURFACE_FIRST_FAILURE_ANALYSIS_CSV_FILENAME",
    "SURFACE_FIRST_FAILURE_ANALYSIS_HTML_FILENAME",
    "SURFACE_FIRST_FAILURE_ANALYSIS_JSON_FILENAME",
    "SURFACE_FIRST_FAILURE_ANALYSIS_MARKDOWN_FILENAME",
    "SURFACE_FIRST_FAILURE_ANALYSIS_TEXT_FILENAME",
    "build_model_capability_required_term_pair_surface_first_failure_analysis",
    "locate_surface_first_alignment_comparison",
    "locate_surface_first_forced_choice_report",
    "locate_surface_first_refresh_report",
    "locate_surface_first_route_decision",
    "read_surface_first_analysis_input",
    "resolve_exit_code",
]
