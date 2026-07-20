from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison import (
    TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison import (
    TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic.json"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic.csv"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic.txt"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic.md"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic.html"
)


def locate_completion_surface_stabilization_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_REPLAY_COMPARISON_JSON_FILENAME
    return source


def locate_stabilized_loss_suffix_uptake_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_REPLAY_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("stabilized loss-suffix uptake stagnation diagnostic input must be a JSON object")
    return dict(payload)


def build_stabilized_loss_suffix_uptake_stagnation_diagnostic(
    baseline_replay_comparison: dict[str, Any],
    current_replay_comparison: dict[str, Any],
    *,
    baseline_replay_comparison_path: str | Path | None = None,
    current_replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory stabilized loss-suffix uptake stagnation diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    baseline_summary = as_dict(baseline_replay_comparison.get("summary"))
    current_summary = as_dict(current_replay_comparison.get("summary"))
    case_rows = _case_diagnostics(
        list_of_dicts(baseline_replay_comparison.get("replay_rows")),
        list_of_dicts(current_replay_comparison.get("replay_rows")),
    )
    diagnostic = _diagnostic(baseline_summary, current_summary, case_rows)
    checks = _checks(baseline_replay_comparison, baseline_summary, current_replay_comparison, current_summary, case_rows, diagnostic)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, baseline_summary, current_summary, case_rows, diagnostic)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, diagnostic),
        "failed_count": len(issues),
        "issues": issues,
        "source_baseline_replay_comparison": str(baseline_replay_comparison_path or ""),
        "source_current_replay_comparison": str(current_replay_comparison_path or ""),
        "baseline_summary": baseline_summary,
        "current_summary": current_summary,
        "case_diagnostics": case_rows,
        "diagnostic": diagnostic,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, diagnostic),
    }


def _case_diagnostics(baseline_rows: list[dict[str, Any]], current_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline_by_id = {str(row.get("case_id")): row for row in baseline_rows}
    current_by_id = {str(row.get("case_id")): row for row in current_rows}
    rows: list[dict[str, Any]] = []
    for case_id in sorted(set(baseline_by_id) | set(current_by_id)):
        baseline = baseline_by_id.get(case_id, {})
        current = current_by_id.get(case_id, {})
        baseline_hits = _terms(baseline.get("hit_terms"))
        current_hits = _terms(current.get("hit_terms"))
        baseline_continuation = str(baseline.get("continuation") or "")
        current_continuation = str(current.get("continuation") or "")
        current_fixed_l_partial = "fixed" in current_hits and "loss" not in current_hits and "fixed l" in current_continuation.lower().strip()
        rows.append({
            "case_id": case_id,
            "baseline_present": bool(baseline),
            "current_present": bool(current),
            "baseline_continuation": baseline_continuation,
            "current_continuation": current_continuation,
            "continuation_changed": baseline_continuation != current_continuation,
            "baseline_hit_terms": baseline_hits,
            "current_hit_terms": current_hits,
            "hit_terms_changed": baseline_hits != current_hits,
            "baseline_case_pass": baseline.get("case_pass") is True,
            "current_case_pass": current.get("case_pass") is True,
            "loss_newly_hit": "loss" not in baseline_hits and "loss" in current_hits,
            "current_fixed_l_partial": current_fixed_l_partial,
            "state_label": _state_label(baseline_continuation, current_continuation, baseline_hits, current_hits, current_fixed_l_partial),
        })
    return rows


def _terms(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _state_label(
    baseline_continuation: str,
    current_continuation: str,
    baseline_hits: list[str],
    current_hits: list[str],
    current_fixed_l_partial: bool,
) -> str:
    if "loss" in current_hits:
        return "loss_recovered"
    if not current_hits:
        return "zero_hit_regression"
    if current_fixed_l_partial and baseline_continuation == current_continuation and baseline_hits == current_hits:
        return "unchanged_fixed_l_partial"
    if current_fixed_l_partial:
        return "changed_fixed_l_partial"
    return "other_partial"


def _diagnostic(baseline_summary: dict[str, Any], current_summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pass_delta = int(current_summary.get("passed_case_count") or 0) - int(baseline_summary.get("passed_case_count") or 0)
    any_hit_delta = int(current_summary.get("any_hit_case_count") or 0) - int(baseline_summary.get("any_hit_case_count") or 0)
    zero_hit_delta = int(current_summary.get("zero_hit_case_count") or 0) - int(baseline_summary.get("zero_hit_case_count") or 0)
    continuation_changed_count = sum(1 for row in case_rows if row["continuation_changed"])
    loss_newly_hit_count = sum(1 for row in case_rows if row["loss_newly_hit"])
    unchanged_fixed_l_count = sum(1 for row in case_rows if row["state_label"] == "unchanged_fixed_l_partial")
    current_fixed_l_count = sum(1 for row in case_rows if row["current_fixed_l_partial"])
    no_contract_gain_confirmed = (
        bool(case_rows)
        and current_fixed_l_count == len(case_rows)
        and pass_delta == 0
        and any_hit_delta == 0
        and zero_hit_delta == 0
        and loss_newly_hit_count == 0
        and current_summary.get("objective_contract_recovered") is False
    )
    return {
        "ready": no_contract_gain_confirmed,
        "pass_delta": pass_delta,
        "any_hit_delta": any_hit_delta,
        "zero_hit_delta": zero_hit_delta,
        "continuation_changed_count": continuation_changed_count,
        "loss_newly_hit_case_count": loss_newly_hit_count,
        "unchanged_fixed_l_partial_case_count": unchanged_fixed_l_count,
        "current_fixed_l_partial_case_count": current_fixed_l_count,
        "stagnation_confirmed": no_contract_gain_confirmed and unchanged_fixed_l_count == len(case_rows),
        "surface_format_changed_without_suffix_gain": no_contract_gain_confirmed and continuation_changed_count > 0,
        "no_contract_gain_confirmed": no_contract_gain_confirmed,
        "next_step": (
            "build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan"
            if no_contract_gain_confirmed
            else "review_stabilized_loss_suffix_uptake_replay_delta"
        ),
    }


def _checks(
    baseline_replay: dict[str, Any],
    baseline_summary: dict[str, Any],
    current_replay: dict[str, Any],
    current_summary: dict[str, Any],
    case_rows: list[dict[str, Any]],
    diagnostic: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _check("baseline_replay_passed", baseline_replay.get("status") == "pass", baseline_replay.get("status"), "baseline replay must pass structurally"),
        _check("current_replay_passed", current_replay.get("status") == "pass", current_replay.get("status"), "current replay must pass structurally"),
        _check(
            "baseline_replay_ready",
            baseline_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison_ready") is True,
            baseline_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison_ready"),
            "baseline completion-surface replay must be ready",
        ),
        _check(
            "current_replay_ready",
            current_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison_ready") is True,
            current_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison_ready"),
            "current stabilized loss-suffix replay must be ready",
        ),
        _check("matching_case_set", bool(case_rows) and all(row["baseline_present"] and row["current_present"] for row in case_rows), len(case_rows), "baseline and current replay cases must match"),
        _check("contract_still_unrecovered", current_summary.get("objective_contract_recovered") is False, current_summary.get("objective_contract_recovered"), "diagnostic only applies while contract is unrecovered"),
        _check("no_pass_delta", diagnostic.get("pass_delta") == 0, diagnostic.get("pass_delta"), "stagnation requires no pass-count gain"),
        _check("no_required_term_delta", diagnostic.get("any_hit_delta") == 0 and diagnostic.get("zero_hit_delta") == 0, {"any": diagnostic.get("any_hit_delta"), "zero": diagnostic.get("zero_hit_delta")}, "required-term hit counts should not change"),
        _check("no_loss_newly_hit", diagnostic.get("loss_newly_hit_case_count") == 0, diagnostic.get("loss_newly_hit_case_count"), "loss suffix must not be newly hit"),
        _check("all_current_fixed_l_partial", diagnostic.get("current_fixed_l_partial_case_count") == len(case_rows), diagnostic.get("current_fixed_l_partial_case_count"), "all current cases should remain fixed-l partial"),
    ]


def _summary(
    status: str,
    baseline_summary: dict[str, Any],
    current_summary: dict[str, Any],
    case_rows: list[dict[str, Any]],
    diagnostic: dict[str, Any],
) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic_ready": status == "pass",
        "case_count": len(case_rows),
        "baseline_passed_case_count": baseline_summary.get("passed_case_count"),
        "current_passed_case_count": current_summary.get("passed_case_count"),
        "pass_delta": diagnostic.get("pass_delta"),
        "any_hit_delta": diagnostic.get("any_hit_delta"),
        "zero_hit_delta": diagnostic.get("zero_hit_delta"),
        "continuation_changed_count": diagnostic.get("continuation_changed_count"),
        "loss_newly_hit_case_count": diagnostic.get("loss_newly_hit_case_count"),
        "unchanged_fixed_l_partial_case_count": diagnostic.get("unchanged_fixed_l_partial_case_count"),
        "stagnation_confirmed": diagnostic.get("stagnation_confirmed"),
        "surface_format_changed_without_suffix_gain": diagnostic.get("surface_format_changed_without_suffix_gain"),
        "no_contract_gain_confirmed": diagnostic.get("no_contract_gain_confirmed"),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic"
    if diagnostic.get("stagnation_confirmed") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_stagnated_at_fixed_l"
    if diagnostic.get("surface_format_changed_without_suffix_gain") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_surface_format_changed_without_suffix_gain"
    return "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_changed_review_required"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Stagnation diagnostic inputs did not match the expected unchanged fixed-l partial state.", "next_action": "review_stabilized_loss_suffix_uptake_replay_delta"}
    return {
        "model_quality_claim": "stabilized_loss_suffix_uptake_no_contract_gain",
        "reason": "The stabilized loss-suffix uptake checkpoint remained at fixed-l partial signal without adding loss suffix hits or contract passes.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_TEXT_FILENAME",
    "build_stabilized_loss_suffix_uptake_stagnation_diagnostic",
    "locate_completion_surface_stabilization_replay_comparison",
    "locate_stabilized_loss_suffix_uptake_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
