from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic import (
    PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.json"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.csv"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.txt"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.md"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.html"
)


def locate_fixed_preserving_transfer_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("fixed-preserving transfer plan input must be a JSON object")
    return dict(payload)


def build_fixed_preserving_transfer_plan(
    regression_diagnostic: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(regression_diagnostic.get("summary"))
    checks = _checks(regression_diagnostic, summary)
    issues = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not issues else "fail"
    plan = _plan(summary)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness fixed-preserving transfer plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_regression_diagnostic_path": str(source_path or ""),
        "source_regression_diagnostic": {
            "status": regression_diagnostic.get("status"),
            "decision": regression_diagnostic.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(status, plan, issues),
        "interpretation": _interpretation(status),
    }


def _checks(regression_diagnostic: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("diagnostic_passed", regression_diagnostic.get("status") == "pass", regression_diagnostic.get("status"), "regression diagnostic must pass"),
        _check(
            "diagnostic_decision",
            regression_diagnostic.get("decision") == "pair_readiness_pair_prompt_transfer_regressed_stop_route",
            regression_diagnostic.get("decision"),
            "plan follows only the regressed transfer route closeout",
        ),
        _check("transfer_route_closed", bool(summary.get("transfer_route_closed")), summary.get("transfer_route_closed"), "full surrogate transfer route must already be closed"),
        _check("fixed_regressed", bool(summary.get("fixed_regressed")), summary.get("fixed_regressed"), "plan is specific to fixed-side regression"),
        _check(
            "direct_hit_regressed",
            int(summary.get("transfer_hit_delta_from_direct") or 0) < 0,
            summary.get("transfer_hit_delta_from_direct"),
            "transfer hits must be lower than direct-completion hits",
        ),
        _check(
            "pair_probe_still_not_ready",
            not bool(summary.get("pair_probe_exact_heldout_pair_full")),
            summary.get("pair_probe_exact_heldout_pair_full"),
            "direct-completion pair probe must still be not ready",
        ),
    ]


def _plan(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": True,
        "closed_route": str(summary.get("closed_route") or "pair_prompt_transfer_full_surrogate_patch"),
        "proposed_next_artifact": "pair_readiness_fixed_preserving_transfer_contract_patch",
        "base_contract_artifact": "pair_readiness_direct_completion_surface_contract",
        "transfer_row_budget": 4,
        "direct_completion_rows_to_preserve": ["fixed=fixed", "loss=loss"],
        "heldout_pair_prompt_must_remain_absent": "fixed=|loss=",
        "objective": "restore fixed direct retention while keeping loss direct retention and adding only a small non-heldout transfer bridge",
        "patch_strategy": [
            "preserve exact direct-completion rows before adding transfer rows",
            "replace the broad eight-row surrogate transfer patch with at most four fixed-preserving bridge rows",
            "include explicit fixed-before-loss guard text so fixed= does not drift to loss",
            "do not add the exact heldout pair prompt or direct echo of fixed=|loss=",
        ],
        "success_guard": "next training must recover fixed and loss direct hits before any pair prompt replay promotion",
    }


def _summary(status: str, plan: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "plan_ready": status == "pass",
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "closed_route": plan.get("closed_route"),
        "transfer_row_budget": plan.get("transfer_row_budget"),
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_fixed_preserving_transfer_plan_ready"
    return "fix_pair_readiness_fixed_preserving_transfer_plan"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The regression diagnostic does not justify a fixed-preserving transfer plan yet.",
            "next_action": "repair or rerun the regression diagnostic before patching the contract",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "The full surrogate transfer patch regressed fixed retention, so the next route should be smaller and fixed-preserving.",
        "next_action": "build a checked fixed-preserving transfer contract patch from the direct-completion base contract",
    }


__all__ = [
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_CSV_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_HTML_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_JSON_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_TEXT_FILENAME",
    "build_fixed_preserving_transfer_plan",
    "locate_fixed_preserving_transfer_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
