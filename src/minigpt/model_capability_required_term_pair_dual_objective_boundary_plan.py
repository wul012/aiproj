from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_constrained_decode_miss_diagnostic import (
    PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_generation_internal_batch_closeout import (
    PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_strs, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_JSON_FILENAME = "model_capability_required_term_pair_dual_objective_boundary_plan.json"
PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_CSV_FILENAME = "model_capability_required_term_pair_dual_objective_boundary_plan.csv"
PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_dual_objective_boundary_plan.txt"
PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_dual_objective_boundary_plan.md"
PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_HTML_FILENAME = "model_capability_required_term_pair_dual_objective_boundary_plan.html"

DUAL_OBJECTIVE_BOUNDARY_CORPUS_MODE = "equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair"


def locate_dual_objective_boundary_closeout(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_GENERATION_INTERNAL_BATCH_CLOSEOUT_JSON_FILENAME
    return source


def locate_dual_objective_boundary_miss_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_JSON_FILENAME
    return source


def read_dual_objective_boundary_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("dual objective boundary input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_dual_objective_boundary_plan(
    closeout_report: dict[str, Any],
    miss_diagnostic: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    closeout_summary = as_dict(closeout_report.get("summary"))
    miss_summary = as_dict(miss_diagnostic.get("summary"))
    issues = _issues(closeout_report, miss_diagnostic, closeout_summary, miss_summary)
    constraints = _constraints(closeout_summary, miss_summary)
    summary = _summary(closeout_summary, miss_summary, constraints)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair dual-objective boundary plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_closeout": {
            "status": closeout_report.get("status"),
            "decision": closeout_report.get("decision"),
            "summary": closeout_summary,
        },
        "source_miss_diagnostic": {
            "status": miss_diagnostic.get("status"),
            "decision": miss_diagnostic.get("decision"),
            "summary": miss_summary,
        },
        "proposed_corpus_mode": DUAL_OBJECTIVE_BOUNDARY_CORPUS_MODE,
        "constraints": constraints,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _issues(
    closeout_report: dict[str, Any],
    miss_diagnostic: dict[str, Any],
    closeout_summary: dict[str, Any],
    miss_summary: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    if closeout_report.get("status") != "pass":
        issues.append("closeout status is not pass")
    if miss_diagnostic.get("status") != "pass":
        issues.append("miss diagnostic status is not pass")
    if int(closeout_summary.get("aligned_pair_full_count") or 0) != 0:
        issues.append("closeout already has aligned pair-full evidence")
    if "fixed" not in list_of_strs(miss_summary.get("remaining_missed_terms")):
        issues.append("miss diagnostic does not identify fixed as remaining missed term")
    if not miss_summary.get("loss_constrained_hit"):
        issues.append("miss diagnostic does not preserve loss-side constrained hit")
    if not closeout_summary.get("selected_generation_route"):
        issues.append("closeout has no selected generation route")
    if not closeout_summary.get("internal_anchor_route"):
        issues.append("closeout has no internal anchor route")
    return issues


def _constraints(closeout_summary: dict[str, Any], miss_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "preserve_generation_anchor",
            "source": str(closeout_summary.get("selected_generation_route") or ""),
            "required": True,
            "detail": "Keep the generation pair-full surface route visible before adding new internal rows.",
        },
        {
            "id": "preserve_internal_anchor",
            "source": str(closeout_summary.get("internal_anchor_route") or ""),
            "required": True,
            "detail": "Keep the internal forced-choice pair match visible as anchor evidence.",
        },
        {
            "id": "repair_fixed_after_constrained_decode",
            "source": str(miss_summary.get("fixed_miss_class") or ""),
            "required": True,
            "detail": "Add explicit fixed retention rows because constrained decode still misses fixed.",
        },
        {
            "id": "retain_loss_after_constrained_decode",
            "source": "loss_constrained_hit",
            "required": True,
            "detail": "Do not erase the loss-side hit recovered by constrained decoding.",
        },
        {
            "id": "avoid_naive_resume",
            "source": str(closeout_summary.get("next_route") or ""),
            "required": True,
            "detail": "Do not continue lower-rate or light-merge checkpoint continuation variants.",
        },
    ]


def _summary(
    closeout_summary: dict[str, Any],
    miss_summary: dict[str, Any],
    constraints: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "constraint_count": len(constraints),
        "required_constraint_count": sum(1 for row in constraints if row.get("required")),
        "selected_generation_route": closeout_summary.get("selected_generation_route"),
        "internal_anchor_route": closeout_summary.get("internal_anchor_route"),
        "fixed_miss_class": miss_summary.get("fixed_miss_class"),
        "remaining_missed_terms": list_of_strs(miss_summary.get("remaining_missed_terms")),
        "loss_constrained_hit": bool(miss_summary.get("loss_constrained_hit")),
        "proposed_corpus_mode": DUAL_OBJECTIVE_BOUNDARY_CORPUS_MODE,
        "ready_to_add_corpus_mode": True,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_dual_objective_boundary_plan"
    if summary.get("ready_to_add_corpus_mode"):
        return "explicit_dual_objective_boundary_plan_ready"
    return "explicit_dual_objective_boundary_plan_in_review"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The boundary plan inputs are incomplete.",
            "next_action": "repair closeout and miss diagnostic inputs",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "The evidence points to fixed-side repair while preserving loss and the existing split anchors.",
        "next_action": f"add corpus mode {summary.get('proposed_corpus_mode')}",
    }


__all__ = [
    "DUAL_OBJECTIVE_BOUNDARY_CORPUS_MODE",
    "PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_CSV_FILENAME",
    "PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_HTML_FILENAME",
    "PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_JSON_FILENAME",
    "PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_MARKDOWN_FILENAME",
    "PAIR_DUAL_OBJECTIVE_BOUNDARY_PLAN_TEXT_FILENAME",
    "build_model_capability_required_term_pair_dual_objective_boundary_plan",
    "locate_dual_objective_boundary_closeout",
    "locate_dual_objective_boundary_miss_diagnostic",
    "read_dual_objective_boundary_input",
    "resolve_exit_code",
]
