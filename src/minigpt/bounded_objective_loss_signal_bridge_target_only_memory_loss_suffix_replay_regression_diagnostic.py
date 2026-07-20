from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison import (
    TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic.json"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic.csv"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic.txt"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic.md"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic.html"
)


def locate_current_loss_suffix_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME
    return source


def locate_baseline_target_only_memory_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective loss-suffix replay regression diagnostic input must be a JSON object")
    return dict(payload)


def read_sample_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def build_loss_suffix_replay_regression_diagnostic(
    current_replay_comparison: dict[str, Any],
    baseline_replay_comparison: dict[str, Any],
    sample_text: str,
    *,
    current_replay_comparison_path: str | Path | None = None,
    baseline_replay_comparison_path: str | Path | None = None,
    sample_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory loss-suffix replay regression diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    current_summary = as_dict(current_replay_comparison.get("summary"))
    baseline_summary = as_dict(baseline_replay_comparison.get("summary"))
    current_cases = [_case_diagnostic(row) for row in list_of_dicts(current_replay_comparison.get("replay_rows"))]
    baseline_cases = [_case_diagnostic(row) for row in list_of_dicts(baseline_replay_comparison.get("replay_rows"))]
    sample = _sample_diagnostic(sample_text)
    regression = _regression(current_summary, baseline_summary, current_cases, baseline_cases, sample)
    checks = _checks(current_replay_comparison, baseline_replay_comparison, current_summary, baseline_summary, current_cases, baseline_cases, sample, regression)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    interpretation = _interpretation(status, regression)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, regression),
        "failed_count": len(issues),
        "issues": issues,
        "source_current_replay_comparison": str(current_replay_comparison_path or ""),
        "source_baseline_replay_comparison": str(baseline_replay_comparison_path or ""),
        "source_sample": str(sample_path or ""),
        "current_summary": current_summary,
        "baseline_summary": baseline_summary,
        "sample_diagnostic": sample,
        "current_case_diagnostics": current_cases,
        "baseline_case_diagnostics": baseline_cases,
        "regression": regression,
        "check_rows": checks,
        "summary": _summary(status, current_cases, baseline_cases, regression),
        "interpretation": interpretation,
    }


def _case_diagnostic(row: dict[str, Any]) -> dict[str, Any]:
    hit_terms = [str(term) for term in row.get("hit_terms", [])]
    missed_terms = [str(term) for term in row.get("missed_terms", [])]
    continuation = str(row.get("continuation") or "")
    normalized = continuation.lower()
    has_fixed = "fixed" in hit_terms or "fixed" in normalized
    has_loss = "loss" in hit_terms or "loss" in normalized
    has_fixed_l_prefix = "fixed l" in normalized
    label = _case_label(str(row.get("case_id") or ""), bool(row.get("any_hit")), has_fixed, has_loss, has_fixed_l_prefix)
    return {
        "case_id": row.get("case_id"),
        "label": label,
        "case_pass": row.get("case_pass") is True,
        "any_hit": row.get("any_hit") is True or bool(hit_terms),
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "continuation": continuation,
        "has_fixed": has_fixed,
        "has_loss": has_loss,
        "has_fixed_l_prefix": has_fixed_l_prefix,
    }


def _case_label(case_id: str, any_hit: bool, has_fixed: bool, has_loss: bool, has_fixed_l_prefix: bool) -> str:
    if has_fixed and has_loss:
        return "contract_pair_hit"
    if case_id == "completion_label_surface" and not any_hit:
        return "completion_surface_zero_regression"
    if has_fixed_l_prefix and has_fixed and not has_loss:
        return "fixed_l_partial"
    if has_fixed and not has_loss:
        return "fixed_without_loss"
    if not any_hit:
        return "zero_hit"
    return "other_partial"


def _sample_diagnostic(sample_text: str) -> dict[str, Any]:
    normalized = " ".join(sample_text.lower().split())
    return {
        "sample_char_count": len(sample_text),
        "sample_fixed_loss": "fixed loss" in normalized,
        "sample_fixed": "fixed" in normalized,
        "sample_loss": "loss" in normalized,
        "sample_tail": sample_text[-120:],
    }


def _regression(
    current_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
    current_cases: list[dict[str, Any]],
    baseline_cases: list[dict[str, Any]],
    sample: dict[str, Any],
) -> dict[str, Any]:
    current_any_hit = int(current_summary.get("any_hit_case_count") or 0)
    baseline_any_hit = int(baseline_summary.get("any_hit_case_count") or 0)
    current_zero_hit = int(current_summary.get("zero_hit_case_count") or 0)
    baseline_zero_hit = int(baseline_summary.get("zero_hit_case_count") or 0)
    current_passed = int(current_summary.get("passed_case_count") or 0)
    baseline_passed = int(baseline_summary.get("passed_case_count") or 0)
    completion_current = _case_by_id(current_cases, "completion_label_surface")
    completion_baseline = _case_by_id(baseline_cases, "completion_label_surface")
    any_hit_delta = current_any_hit - baseline_any_hit
    zero_hit_delta = current_zero_hit - baseline_zero_hit
    objective_contract_recovered = current_summary.get("objective_contract_recovered") is True
    return {
        "ready": sample.get("sample_fixed_loss") is True and not objective_contract_recovered and (any_hit_delta < 0 or zero_hit_delta > 0),
        "sample_contract_gap": sample.get("sample_fixed_loss") is True and not objective_contract_recovered,
        "objective_contract_recovered": objective_contract_recovered,
        "current_passed_case_count": current_passed,
        "baseline_passed_case_count": baseline_passed,
        "passed_case_delta": current_passed - baseline_passed,
        "current_any_hit_case_count": current_any_hit,
        "baseline_any_hit_case_count": baseline_any_hit,
        "any_hit_delta": any_hit_delta,
        "current_zero_hit_case_count": current_zero_hit,
        "baseline_zero_hit_case_count": baseline_zero_hit,
        "zero_hit_delta": zero_hit_delta,
        "completion_surface_regressed_to_zero": completion_baseline.get("any_hit") is True and completion_current.get("any_hit") is False,
        "fixed_l_partial_case_count": sum(1 for row in current_cases if row.get("label") == "fixed_l_partial"),
        "completion_surface_current_label": completion_current.get("label", ""),
        "completion_surface_baseline_label": completion_baseline.get("label", ""),
        "next_step": "build_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch",
    }


def _case_by_id(rows: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("case_id") == case_id:
            return row
    return {}


def _checks(
    current_replay: dict[str, Any],
    baseline_replay: dict[str, Any],
    current_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
    current_cases: list[dict[str, Any]],
    baseline_cases: list[dict[str, Any]],
    sample: dict[str, Any],
    regression: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _check("current_replay_passed", current_replay.get("status") == "pass", current_replay.get("status"), "current loss-suffix replay comparison must pass structurally"),
        _check("baseline_replay_passed", baseline_replay.get("status") == "pass", baseline_replay.get("status"), "baseline target-only memory replay comparison must pass structurally"),
        _check(
            "current_loss_suffix_replay_ready",
            current_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison_ready") is True,
            current_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison_ready"),
            "current loss-suffix replay summary must be ready",
        ),
        _check(
            "baseline_target_only_memory_replay_ready",
            baseline_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison_ready") is True,
            baseline_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison_ready"),
            "baseline target-only memory replay summary must be ready",
        ),
        _check("sample_contains_fixed_loss", sample.get("sample_fixed_loss") is True, sample.get("sample_tail"), "training sample must show the fixed loss phrase"),
        _check("current_contract_not_recovered", current_summary.get("objective_contract_recovered") is False, current_summary.get("objective_contract_recovered"), "diagnostic applies only while contract is unrecovered"),
        _check("has_current_cases", bool(current_cases), len(current_cases), "current replay rows must be present"),
        _check("has_baseline_cases", bool(baseline_cases), len(baseline_cases), "baseline replay rows must be present"),
        _check("sample_contract_gap", regression.get("sample_contract_gap") is True, regression.get("sample_contract_gap"), "sample success must be contrasted with replay contract failure"),
        _check("replay_signal_regressed", regression.get("any_hit_delta", 0) < 0 or regression.get("zero_hit_delta", 0) > 0, {"any_hit_delta": regression.get("any_hit_delta"), "zero_hit_delta": regression.get("zero_hit_delta")}, "current replay must regress against the baseline signal"),
        _check("completion_surface_regressed", regression.get("completion_surface_regressed_to_zero") is True, regression.get("completion_surface_regressed_to_zero"), "completion surface should explain the zero-hit regression"),
    ]


def _summary(status: str, current_cases: list[dict[str, Any]], baseline_cases: list[dict[str, Any]], regression: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_ready": status == "pass",
        "current_case_count": len(current_cases),
        "baseline_case_count": len(baseline_cases),
        "sample_contract_gap": regression.get("sample_contract_gap"),
        "objective_contract_recovered": regression.get("objective_contract_recovered"),
        "any_hit_delta": regression.get("any_hit_delta"),
        "zero_hit_delta": regression.get("zero_hit_delta"),
        "completion_surface_regressed_to_zero": regression.get("completion_surface_regressed_to_zero"),
        "fixed_l_partial_case_count": regression.get("fixed_l_partial_case_count"),
        "next_step": regression.get("next_step"),
    }


def _decision(status: str, regression: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic"
    if regression.get("completion_surface_regressed_to_zero") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_sample_success_contract_regression"
    return "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_signal_regression"


def _interpretation(status: str, regression: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Loss-suffix replay regression diagnostic inputs failed.",
            "next_action": "repair_loss_suffix_replay_regression_diagnostic_inputs",
        }
    return {
        "model_quality_claim": "sample_success_contract_regression",
        "reason": "The training sample emits fixed loss, but fixed replay prompts still fail the contract and the completion surface regressed to zero required-term hits.",
        "next_action": regression.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_TEXT_FILENAME",
    "build_loss_suffix_replay_regression_diagnostic",
    "locate_baseline_target_only_memory_replay_comparison",
    "locate_current_loss_suffix_replay_comparison",
    "read_json_report",
    "read_sample_text",
    "resolve_exit_code",
]
