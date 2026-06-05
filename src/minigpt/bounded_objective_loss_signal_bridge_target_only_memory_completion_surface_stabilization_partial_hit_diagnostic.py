from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison import (
    TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic.json"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic.csv"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic.txt"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic.md"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic.html"
)


def locate_completion_surface_stabilization_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_REPLAY_COMPARISON_JSON_FILENAME
    return source


def locate_loss_suffix_replay_regression_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("completion-surface stabilization partial-hit diagnostic input must be a JSON object")
    return dict(payload)


def build_completion_surface_stabilization_partial_hit_diagnostic(
    replay_comparison: dict[str, Any],
    regression_diagnostic: dict[str, Any],
    *,
    replay_comparison_path: str | Path | None = None,
    regression_diagnostic_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory completion-surface stabilization partial-hit diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(replay_comparison.get("summary"))
    regression_summary = as_dict(regression_diagnostic.get("summary"))
    regression = as_dict(regression_diagnostic.get("regression"))
    case_rows = [_case_diagnostic(row) for row in list_of_dicts(replay_comparison.get("replay_rows"))]
    diagnostic = _diagnostic(replay_summary, regression_summary, regression, case_rows)
    checks = _checks(replay_comparison, replay_summary, regression_diagnostic, regression_summary, diagnostic, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, diagnostic),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_comparison": str(replay_comparison_path or ""),
        "source_regression_diagnostic": str(regression_diagnostic_path or ""),
        "replay_summary": replay_summary,
        "regression_summary": regression_summary,
        "regression": regression,
        "case_diagnostics": case_rows,
        "diagnostic": diagnostic,
        "check_rows": checks,
        "summary": _summary(status, case_rows, diagnostic),
        "interpretation": _interpretation(status, diagnostic),
    }


def resolve_exit_code(report: dict[str, Any], *, require_diagnostic_ready: bool) -> int:
    return 1 if require_diagnostic_ready and report.get("status") != "pass" else 0


def _case_diagnostic(row: dict[str, Any]) -> dict[str, Any]:
    hit_terms = [str(term) for term in row.get("hit_terms", [])]
    missed_terms = [str(term) for term in row.get("missed_terms", [])]
    continuation = str(row.get("continuation") or "")
    normalized = continuation.lower().strip()
    fixed_hit = "fixed" in hit_terms
    loss_hit = "loss" in hit_terms
    fixed_l_partial = fixed_hit and not loss_hit and "fixed l" in normalized
    label = "fixed_l_partial" if fixed_l_partial else ("contract_pair_hit" if fixed_hit and loss_hit else ("zero_hit" if not hit_terms else "other_partial"))
    return {
        "case_id": row.get("case_id"),
        "label": label,
        "case_pass": row.get("case_pass") is True,
        "any_hit": bool(hit_terms),
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "continuation": continuation,
        "has_fixed": fixed_hit,
        "has_loss": loss_hit,
        "has_fixed_l_prefix": fixed_l_partial,
    }


def _diagnostic(
    replay_summary: dict[str, Any],
    regression_summary: dict[str, Any],
    regression: dict[str, Any],
    case_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    fixed_l_count = sum(1 for row in case_rows if row["label"] == "fixed_l_partial")
    loss_hit_count = sum(1 for row in case_rows if row["has_loss"])
    completion_row = _case_by_id(case_rows, "completion_label_surface")
    surface_stabilized = completion_row.get("label") == "fixed_l_partial"
    zero_hit_resolved = int(replay_summary.get("zero_hit_case_count") or 0) == 0 and regression.get("completion_surface_regressed_to_zero") is True
    return {
        "ready": bool(case_rows) and fixed_l_count == len(case_rows) and loss_hit_count == 0 and surface_stabilized,
        "completion_surface_stabilized": surface_stabilized,
        "zero_hit_resolved": zero_hit_resolved,
        "all_cases_fixed_l_partial": bool(case_rows) and fixed_l_count == len(case_rows),
        "fixed_l_partial_case_count": fixed_l_count,
        "loss_hit_case_count": loss_hit_count,
        "suffix_gap_after_surface_stabilization": bool(case_rows) and fixed_l_count == len(case_rows) and loss_hit_count == 0,
        "source_any_hit_delta": regression.get("any_hit_delta"),
        "source_zero_hit_delta": regression.get("zero_hit_delta"),
        "current_any_hit_case_count": replay_summary.get("any_hit_case_count"),
        "current_zero_hit_case_count": replay_summary.get("zero_hit_case_count"),
        "source_sample_contract_gap": regression_summary.get("sample_contract_gap"),
        "next_step": "build_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch",
    }


def _case_by_id(rows: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("case_id") == case_id:
            return row
    return {}


def _checks(
    replay_comparison: dict[str, Any],
    replay_summary: dict[str, Any],
    regression_diagnostic: dict[str, Any],
    regression_summary: dict[str, Any],
    diagnostic: dict[str, Any],
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("replay_passed", replay_comparison.get("status") == "pass", replay_comparison.get("status"), "completion-surface stabilization replay must pass structurally"),
        _check(
            "replay_ready",
            replay_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison_ready") is True,
            replay_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison_ready"),
            "completion-surface stabilization replay must be ready",
        ),
        _check("regression_diagnostic_passed", regression_diagnostic.get("status") == "pass", regression_diagnostic.get("status"), "source regression diagnostic must pass"),
        _check("source_sample_contract_gap", regression_summary.get("sample_contract_gap") is True, regression_summary.get("sample_contract_gap"), "source diagnostic must have a sample-contract gap"),
        _check("contract_not_recovered", replay_summary.get("objective_contract_recovered") is False, replay_summary.get("objective_contract_recovered"), "diagnostic only applies before contract recovery"),
        _check("all_cases_have_required_signal", int(replay_summary.get("any_hit_case_count") or 0) == len(case_rows), replay_summary.get("any_hit_case_count"), "all current cases should have partial required-term signal"),
        _check("zero_hit_resolved", diagnostic.get("zero_hit_resolved") is True, diagnostic.get("zero_hit_resolved"), "completion zero-hit regression should be resolved"),
        _check("all_fixed_l_partial", diagnostic.get("all_cases_fixed_l_partial") is True, diagnostic.get("fixed_l_partial_case_count"), "all cases should stabilize at fixed l"),
        _check("loss_still_missing", int(diagnostic.get("loss_hit_case_count") or 0) == 0, diagnostic.get("loss_hit_case_count"), "diagnostic requires loss still missing"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, case_rows: list[dict[str, Any]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic_ready": status == "pass",
        "case_count": len(case_rows),
        "completion_surface_stabilized": diagnostic.get("completion_surface_stabilized"),
        "zero_hit_resolved": diagnostic.get("zero_hit_resolved"),
        "all_cases_fixed_l_partial": diagnostic.get("all_cases_fixed_l_partial"),
        "fixed_l_partial_case_count": diagnostic.get("fixed_l_partial_case_count"),
        "loss_hit_case_count": diagnostic.get("loss_hit_case_count"),
        "suffix_gap_after_surface_stabilization": diagnostic.get("suffix_gap_after_surface_stabilization"),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic"
    if diagnostic.get("suffix_gap_after_surface_stabilization") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilized_loss_suffix_missing"
    return "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilized_partial_gap"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Completion-surface stabilization partial-hit diagnostic inputs failed.", "next_action": "repair_completion_surface_stabilization_partial_hit_diagnostic_inputs"}
    return {
        "model_quality_claim": "completion_surface_stabilized_suffix_missing",
        "reason": "The completion surface recovered from zero-hit to fixed l, but every contract case still misses the loss suffix.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME",
    "build_completion_surface_stabilization_partial_hit_diagnostic",
    "locate_completion_surface_stabilization_replay_comparison",
    "locate_loss_suffix_replay_regression_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
