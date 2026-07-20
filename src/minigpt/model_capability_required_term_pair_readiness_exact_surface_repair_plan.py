from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_JSON_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_plan.json"
PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_CSV_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_plan.csv"
PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_plan.txt"
PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_plan.md"
PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_HTML_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_plan.html"


def locate_exact_surface_repair_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PROMPT_SURFACE_SENSITIVITY_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("exact-surface repair plan input must be a JSON object")
    return dict(payload)


def build_exact_surface_repair_plan(
    sensitivity_diagnostic: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(sensitivity_diagnostic.get("summary"))
    checks = _checks(sensitivity_diagnostic, summary)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    plan = _plan(summary)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness exact-surface repair plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_sensitivity_diagnostic_path": str(source_path or ""),
        "source_sensitivity_diagnostic": {
            "status": sensitivity_diagnostic.get("status"),
            "decision": sensitivity_diagnostic.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(status, plan, issues),
        "interpretation": _interpretation(status),
    }


def _checks(diagnostic: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "sensitivity diagnostic must pass"),
        _check(
            "diagnostic_decision",
            diagnostic.get("decision") == "pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found",
            diagnostic.get("decision"),
            "plan follows only the prompt-surface sensitivity route",
        ),
        _check("promotion_blocked", bool(summary.get("promotion_blocked")), summary.get("promotion_blocked"), "promotion must be blocked before repair"),
        _check(
            "exact_surface_missed",
            "exact-heldout-pair" in {str(item) for item in summary.get("required_missed_surface_ids", [])},
            summary.get("required_missed_surface_ids"),
            "exact heldout pair surface must be the missed required surface",
        ),
        _check(
            "optional_surface_signal_present",
            bool(summary.get("optional_pair_full_surface_ids")),
            summary.get("optional_pair_full_surface_ids"),
            "at least one optional surface should show pair-full signal before minimal repair",
        ),
    ]


def _plan(summary: dict[str, Any]) -> dict[str, Any]:
    missed = list(summary.get("required_missed_surface_ids", []))
    passed = list(summary.get("optional_pair_full_surface_ids", []))
    return {
        "ready": True,
        "proposed_next_artifact": "pair_readiness_exact_surface_repair_contract_patch",
        "base_contract_artifact": "pair_readiness_fixed_preserving_transfer_contract_patch",
        "repair_row_budget": 4,
        "missed_required_surfaces": missed,
        "observed_pair_full_surfaces": passed,
        "heldout_pair_prompt_must_remain_absent": HELDOUT_PAIR_PROBE,
        "objective": "transfer the arrow-surface pair-full behavior toward the exact heldout pipe surface without training on the exact heldout prompt",
        "patch_strategy": [
            "preserve exact direct rows fixed=fixed and loss=loss",
            "preserve the four fixed-preserving transfer rows from v747",
            "add at most four near-exact surface bridge rows that mention pipe/equals structure without using fixed=|loss=",
            "avoid adding the exact heldout prompt as a training row",
            "rerun materialization, training, and independent pair-probe replay before any promotion",
        ],
        "success_guard": "exact-heldout-pair must replay pair-full independently before promotion guard",
    }


def _summary(status: str, plan: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "plan_ready": status == "pass",
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "base_contract_artifact": plan.get("base_contract_artifact"),
        "repair_row_budget": plan.get("repair_row_budget"),
        "missed_required_surfaces": plan.get("missed_required_surfaces"),
        "observed_pair_full_surfaces": plan.get("observed_pair_full_surfaces"),
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_exact_surface_repair_plan_ready"
    return "fix_pair_readiness_exact_surface_repair_plan"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The sensitivity diagnostic does not justify an exact-surface repair plan yet.",
            "next_action": "repair or rerun prompt-surface sensitivity diagnostic",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "The checkpoint shows pair-full on an optional surface while missing the exact required pair surface.",
        "next_action": "build a checked exact-surface repair contract patch without leaking the heldout prompt",
    }


__all__ = [
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_CSV_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_HTML_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_JSON_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_TEXT_FILENAME",
    "build_exact_surface_repair_plan",
    "locate_exact_surface_repair_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
