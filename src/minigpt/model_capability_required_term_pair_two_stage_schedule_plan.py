from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison import (
    build_model_capability_required_term_pair_generation_internal_alignment_comparison,
    locate_generation_internal_alignment_forced_choice_report,
    locate_generation_internal_alignment_refresh_report,
    make_generation_internal_alignment_source,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_TWO_STAGE_SCHEDULE_PLAN_JSON_FILENAME = (
    "model_capability_required_term_pair_two_stage_schedule_plan.json"
)
PAIR_TWO_STAGE_SCHEDULE_PLAN_CSV_FILENAME = (
    "model_capability_required_term_pair_two_stage_schedule_plan.csv"
)
PAIR_TWO_STAGE_SCHEDULE_PLAN_TEXT_FILENAME = (
    "model_capability_required_term_pair_two_stage_schedule_plan.txt"
)
PAIR_TWO_STAGE_SCHEDULE_PLAN_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_two_stage_schedule_plan.md"
)
PAIR_TWO_STAGE_SCHEDULE_PLAN_HTML_FILENAME = (
    "model_capability_required_term_pair_two_stage_schedule_plan.html"
)


def read_two_stage_schedule_plan_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("two-stage schedule plan input must be a JSON object")
    return dict(payload)


def make_two_stage_schedule_plan_source(
    *,
    label: str,
    refresh_report: dict[str, Any],
    forced_choice_report: dict[str, Any],
    refresh_path: str | Path = "",
    forced_choice_path: str | Path = "",
) -> dict[str, Any]:
    return make_generation_internal_alignment_source(
        label=label,
        refresh_report=refresh_report,
        forced_choice_report=forced_choice_report,
        refresh_path=refresh_path,
        forced_choice_path=forced_choice_path,
    )


def locate_two_stage_schedule_refresh_report(path: str | Path) -> Path:
    return locate_generation_internal_alignment_refresh_report(path)


def locate_two_stage_schedule_forced_choice_report(path: str | Path) -> Path:
    return locate_generation_internal_alignment_forced_choice_report(path)


def build_model_capability_required_term_pair_two_stage_schedule_plan(
    *,
    surface_source: dict[str, Any],
    internal_source: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    comparison = build_model_capability_required_term_pair_generation_internal_alignment_comparison(
        [surface_source, internal_source],
        generated_at=generated_at,
    )
    source_rows = list_of_dicts(comparison.get("source_rows"))
    surface_row = _row_by_label(source_rows, str(surface_source.get("label") or ""))
    internal_row = _row_by_label(source_rows, str(internal_source.get("label") or ""))
    stage_rows = _stage_rows(surface_row, internal_row)
    guardrails = _guardrails(comparison, surface_row, internal_row)
    issues = _issues(comparison, surface_row, internal_row, guardrails)
    status = "pass" if not issues else "fail"
    summary = _summary(comparison, stage_rows, guardrails)
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair two-stage schedule plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "schedule_boundary": {
            "training_semantics": "not_checkpoint_resume",
            "reason": "The current training CLI has no checkpoint-continuation flag; this plan is an auditable schedule contract.",
        },
        "source_comparison": {
            "status": comparison.get("status"),
            "decision": comparison.get("decision"),
            "summary": as_dict(comparison.get("summary")),
        },
        "stage_rows": stage_rows,
        "guardrails": guardrails,
        "summary": summary,
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _row_by_label(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    for row in rows:
        if str(row.get("source_label") or "") == label:
            return row
    return {}


def _stage_rows(surface_row: dict[str, Any], internal_row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "stage": "surface_generation_stage",
            "source_label": surface_row.get("source_label"),
            "goal": "preserve_generation_pair_full",
            "gate": "generation_pair_full",
            "gate_passed": bool(surface_row.get("generation_pair_full")),
            "checkpoint_exists": bool(surface_row.get("checkpoint_exists")),
            "generation_hit_terms": surface_row.get("generation_hit_terms", []),
            "internal_expected_best_terms": surface_row.get("internal_expected_best_terms", []),
            "alignment_class": surface_row.get("alignment_class"),
        },
        {
            "stage": "internal_repair_stage",
            "source_label": internal_row.get("source_label"),
            "goal": "repair_internal_preference_without_claiming_generation_alignment",
            "gate": "internal_pair_full",
            "gate_passed": bool(internal_row.get("internal_pair_full")),
            "checkpoint_exists": bool(internal_row.get("checkpoint_exists")),
            "generation_hit_terms": internal_row.get("generation_hit_terms", []),
            "internal_expected_best_terms": internal_row.get("internal_expected_best_terms", []),
            "alignment_class": internal_row.get("alignment_class"),
        },
    ]


def _guardrails(
    comparison: dict[str, Any],
    surface_row: dict[str, Any],
    internal_row: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = as_dict(comparison.get("summary"))
    aligned_count = int(summary.get("aligned_pair_full_count") or 0)
    return [
        {
            "id": "not_checkpoint_resume",
            "status": "active",
            "detail": "The plan does not claim checkpoint continuation; it only schedules a runnable corpus approximation.",
        },
        {
            "id": "no_aligned_route_claim",
            "status": "pass" if aligned_count == 0 else "fail",
            "detail": "Aligned generation/internal pair-full must remain unclaimed unless comparison proves it.",
        },
        {
            "id": "surface_generation_pair_full_required",
            "status": "pass" if surface_row.get("generation_pair_full") else "fail",
            "detail": "The first stage must start from the route that already releases both required terms.",
        },
        {
            "id": "internal_pair_full_required",
            "status": "pass" if internal_row.get("internal_pair_full") else "fail",
            "detail": "The second stage must be backed by forced-choice internal pair-full evidence.",
        },
    ]


def _issues(
    comparison: dict[str, Any],
    surface_row: dict[str, Any],
    internal_row: dict[str, Any],
    guardrails: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if comparison.get("status") != "pass":
        issues.append("source generation/internal comparison status is not pass")
    if not surface_row:
        issues.append("surface source row is missing")
    if not internal_row:
        issues.append("internal source row is missing")
    for guardrail in guardrails:
        if guardrail.get("status") == "fail":
            issues.append(str(guardrail.get("id")))
    return issues


def _summary(
    comparison: dict[str, Any],
    stage_rows: list[dict[str, Any]],
    guardrails: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "stage_count": len(stage_rows),
        "stage_gate_pass_count": sum(1 for row in stage_rows if row.get("gate_passed")),
        "guardrail_pass_count": sum(1 for row in guardrails if row.get("status") in {"active", "pass"}),
        "guardrail_fail_count": sum(1 for row in guardrails if row.get("status") == "fail"),
        "comparison_decision": comparison.get("decision"),
        "next_action": "run_surface_first_schedule_approximation",
    }


def _decision(status: str) -> str:
    if status != "pass":
        return "fix_two_stage_schedule_plan_inputs"
    return "two_stage_surface_internal_schedule_ready"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The two-stage schedule prerequisites are incomplete.",
            "next_action": "repair the surface generation or internal forced-choice evidence before running a schedule approximation",
        }
    return {
        "model_quality_claim": "schedule_plan_only",
        "reason": "Surface generation pair-full and internal forced-choice pair-full exist in separate routes.",
        "next_action": "run a surface-first single-corpus approximation while keeping the no-resume boundary visible",
    }


__all__ = [
    "PAIR_TWO_STAGE_SCHEDULE_PLAN_CSV_FILENAME",
    "PAIR_TWO_STAGE_SCHEDULE_PLAN_HTML_FILENAME",
    "PAIR_TWO_STAGE_SCHEDULE_PLAN_JSON_FILENAME",
    "PAIR_TWO_STAGE_SCHEDULE_PLAN_MARKDOWN_FILENAME",
    "PAIR_TWO_STAGE_SCHEDULE_PLAN_TEXT_FILENAME",
    "build_model_capability_required_term_pair_two_stage_schedule_plan",
    "locate_two_stage_schedule_forced_choice_report",
    "locate_two_stage_schedule_refresh_report",
    "make_two_stage_schedule_plan_source",
    "read_two_stage_schedule_plan_input",
    "resolve_exit_code",
]
