from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic import (
    TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_plan_ready as resolve_exit_code


TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan.json"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan.csv"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan.txt"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan.md"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan.html"
)


def locate_stagnation_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("stagnation-aware suffix repair plan input must be a JSON object")
    return dict(payload)


def build_stagnation_aware_suffix_repair_plan(
    stagnation_diagnostic: dict[str, Any],
    *,
    stagnation_diagnostic_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix repair plan",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(stagnation_diagnostic.get("summary"))
    diagnostic = as_dict(stagnation_diagnostic.get("diagnostic"))
    case_rows = list_of_dicts(stagnation_diagnostic.get("case_diagnostics"))
    actions = _plan_actions(diagnostic_summary, case_rows)
    checks = _checks(stagnation_diagnostic, diagnostic_summary, diagnostic, case_rows, actions)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, diagnostic_summary, actions)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_stagnation_diagnostic": str(stagnation_diagnostic_path or ""),
        "stagnation_summary": diagnostic_summary,
        "stagnation_diagnostic": diagnostic,
        "source_case_diagnostics": case_rows,
        "plan_actions": actions,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _plan_actions(summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    case_count = len(case_rows)
    format_delta = summary.get("surface_format_changed_without_suffix_gain") is True
    return [
        _action(
            "suffix-position-bridge",
            "suffix_position",
            "required",
            "Add examples where loss immediately follows the fixed-l and fixed-lo fragments under the exact contract labels.",
            "Generate paired snippets for `fixed l -> fixed loss`, `fixed lo -> fixed loss`, and direct `fixed loss` completions.",
            case_count,
        ),
        _action(
            "surface-format-normalization",
            "surface_format",
            "required" if format_delta else "recommended",
            "Preserve both space-prefixed and newline-prefixed continuations so formatting drift does not hide suffix progress.",
            "Create parallel answer/completion examples for ` answer: fixed loss` and `answer:\\nfixed loss` surfaces.",
            int(summary.get("continuation_changed_count") or 0),
        ),
        _action(
            "replay-prompt-boundary-lock",
            "replay_prompt_boundary",
            "required",
            "Bind patch examples to the unchanged v836 prompts instead of relying on free-form sample prompts.",
            "Use the canonical/minimal/completion contract prompts as literal prefixes in the next patch corpus.",
            case_count,
        ),
        _action(
            "suffix-ratio-increase",
            "training_corpus_ratio",
            "required",
            "Raise suffix-uptake examples above surface carry-forward examples because the prior patch changed formatting without adding loss hits.",
            "Target at least 2:1 suffix-uptake to surface-carry-forward examples, while keeping decoder anchors at zero.",
            int(summary.get("loss_newly_hit_case_count") or 0),
        ),
        _action(
            "contract-gated-training-stop",
            "verification_gate",
            "required",
            "Keep training claims gated behind unchanged contract replay, since v885 sample success did not transfer.",
            "Require a replay comparison before any promotion or holdout route; do not infer recovery from sample text.",
            int(summary.get("pass_delta") or 0),
        ),
    ]


def _action(action_id: str, category: str, priority: str, purpose: str, implementation_hint: str, evidence_count: int) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "category": category,
        "priority": priority,
        "purpose": purpose,
        "implementation_hint": implementation_hint,
        "evidence_count": evidence_count,
        "next_artifact_role": "patch_requirement",
    }


def _checks(
    stagnation_diagnostic: dict[str, Any],
    summary: dict[str, Any],
    diagnostic: dict[str, Any],
    case_rows: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    categories = {str(row.get("category")) for row in actions}
    return [
        _check("diagnostic_passed", stagnation_diagnostic.get("status") == "pass", stagnation_diagnostic.get("status"), "source stagnation diagnostic must pass"),
        _check(
            "diagnostic_ready",
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic_ready") is True,
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic_ready"),
            "source stagnation diagnostic must be ready",
        ),
        _check("no_contract_gain", summary.get("no_contract_gain_confirmed") is True, summary.get("no_contract_gain_confirmed"), "repair plan applies only after no contract gain is confirmed"),
        _check("loss_not_newly_hit", int(summary.get("loss_newly_hit_case_count") or 0) == 0, summary.get("loss_newly_hit_case_count"), "repair plan should not override genuine loss recovery"),
        _check("cases_present", bool(case_rows), len(case_rows), "case diagnostics must be present"),
        _check("actions_present", len(actions) >= 5, len(actions), "repair plan needs multiple targeted actions"),
        _check("required_categories", _required_categories().issubset(categories), sorted(categories), "repair plan must cover suffix, surface, prompt boundary, ratio, and verification"),
        _check("next_step_matches", diagnostic.get("next_step") == "build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan", diagnostic.get("next_step"), "source diagnostic should route to this plan"),
    ]


def _required_categories() -> set[str]:
    return {"suffix_position", "surface_format", "replay_prompt_boundary", "training_corpus_ratio", "verification_gate"}


def _summary(status: str, diagnostic_summary: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready": status == "pass",
        "action_count": len(actions),
        "required_action_count": sum(1 for row in actions if row["priority"] == "required"),
        "suffix_position_action_count": sum(1 for row in actions if row["category"] == "suffix_position"),
        "surface_format_action_count": sum(1 for row in actions if row["category"] == "surface_format"),
        "replay_prompt_boundary_action_count": sum(1 for row in actions if row["category"] == "replay_prompt_boundary"),
        "training_corpus_ratio_action_count": sum(1 for row in actions if row["category"] == "training_corpus_ratio"),
        "verification_gate_action_count": sum(1 for row in actions if row["category"] == "verification_gate"),
        "source_no_contract_gain_confirmed": diagnostic_summary.get("no_contract_gain_confirmed"),
        "source_surface_format_changed_without_suffix_gain": diagnostic_summary.get("surface_format_changed_without_suffix_gain"),
        "model_quality_claim": "repair_plan_only",
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch" if status == "pass" else "",
        "next_step": "build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch" if status == "pass" else "repair_stagnation_aware_suffix_repair_plan_inputs",
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready"
    return "fix_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Stagnation-aware suffix repair plan inputs failed.", "next_action": "repair_stagnation_aware_suffix_repair_plan_inputs"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The plan converts no-contract-gain evidence into targeted suffix, surface, prompt-boundary, ratio, and replay-gate repair actions.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_TEXT_FILENAME",
    "build_stagnation_aware_suffix_repair_plan",
    "locate_stagnation_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
