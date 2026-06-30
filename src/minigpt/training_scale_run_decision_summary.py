from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    number_or_default,
    positive_int_mapping as _int_mapping,
    string_list as _string_list,
)


def build_training_scale_run_decision_summary(
    runs: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    status: str,
    action: str,
    *,
    comparison_summary: dict[str, Any],
    require_suite_consistency: bool,
    require_clean_batch_review: bool,
) -> dict[str, Any]:
    suite_paths = _string_list(comparison_summary.get("suite_paths"))
    selected_suite_path = None if selected is None else selected.get("suite_path")
    if not selected_suite_path and len(suite_paths) == 1:
        selected_suite_path = suite_paths[0]
    return {
        "decision_status": status,
        "recommended_action": action,
        "run_count": len(runs),
        "candidate_count": len(candidates),
        "rejected_count": len(rejected),
        "selected_run_name": None if selected is None else selected.get("name"),
        "selected_gate_status": None if selected is None else selected.get("gate_status"),
        "selected_batch_status": None if selected is None else selected.get("batch_status"),
        "selected_readiness_score": None if selected is None else selected.get("readiness_score"),
        "selected_batch_comparison_review_action_count": _selected_int(selected, "batch_comparison_review_action_count"),
        "selected_batch_comparison_blocker_action_count": _selected_int(
            selected,
            "batch_comparison_blocker_action_count",
        ),
        "selected_batch_maturity_coverage_regression_count": _selected_int(
            selected,
            "batch_maturity_coverage_regression_count",
        ),
        "selected_batch_maturity_suite_design_regression_count": _selected_int(
            selected,
            "batch_maturity_suite_design_regression_count",
        ),
        "selected_batch_maturity_suite_design_regression_names": _selected_list(
            selected,
            "batch_maturity_suite_design_regression_names",
        ),
        "selected_batch_maturity_ci_regression_count": _selected_int(selected, "batch_maturity_ci_regression_count"),
        "selected_batch_maturity_ci_regression_reason_counts": _selected_mapping(
            selected,
            "batch_maturity_ci_regression_reason_counts",
        ),
        "selected_batch_review_status": batch_review_status(selected),
        "selected_suite_path": selected_suite_path,
        "require_suite_consistency": bool(require_suite_consistency),
        "require_clean_batch_review": bool(require_clean_batch_review),
        "clean_batch_review_status": clean_batch_review_status(comparison_summary),
        "suite_consistency": comparison_summary.get("suite_consistency"),
        "suite_paths": suite_paths,
        "suite_mismatch_count": _int(comparison_summary.get("suite_mismatch_count")),
        "batch_comparison_review_action_count": _int(comparison_summary.get("batch_comparison_review_action_count")),
        "batch_comparison_blocker_action_count": _int(comparison_summary.get("batch_comparison_blocker_action_count")),
        "batch_maturity_review_count": _int(comparison_summary.get("batch_maturity_review_count")),
        "batch_maturity_coverage_regression_count": _int(
            comparison_summary.get("batch_maturity_coverage_regression_count")
        ),
        "batch_maturity_coverage_regression_names": _string_list(
            comparison_summary.get("batch_maturity_coverage_regression_names")
        ),
        "batch_maturity_suite_design_regression_count": _int(
            comparison_summary.get("batch_maturity_suite_design_regression_count")
        ),
        "batch_maturity_suite_design_regression_names": _string_list(
            comparison_summary.get("batch_maturity_suite_design_regression_names")
        ),
        "batch_maturity_ci_regression_count": _int(comparison_summary.get("batch_maturity_ci_regression_count")),
        "batch_maturity_ci_regression_names": _string_list(comparison_summary.get("batch_maturity_ci_regression_names")),
        "batch_maturity_ci_regression_reason_counts": _int_mapping(
            comparison_summary.get("batch_maturity_ci_regression_reason_counts")
        ),
        "batch_comparison_blocker_reasons": _string_list(comparison_summary.get("batch_comparison_blocker_reasons")),
    }


def clean_batch_review_status(comparison_summary: dict[str, Any]) -> str:
    if _int(comparison_summary.get("batch_comparison_blocker_action_count")):
        return "blocker"
    if (
        _int(comparison_summary.get("batch_comparison_review_action_count"))
        or _int(comparison_summary.get("batch_maturity_coverage_regression_count"))
        or _int(comparison_summary.get("batch_maturity_suite_design_regression_count"))
        or _int(comparison_summary.get("batch_maturity_ci_regression_count"))
    ):
        return "review"
    return "clean"


def batch_review_status(selected: dict[str, Any] | None) -> str:
    if selected is None:
        return "missing"
    if _int(selected.get("batch_comparison_blocker_action_count")):
        return "blocker"
    if (
        _int(selected.get("batch_comparison_review_action_count"))
        or _int(selected.get("batch_maturity_coverage_regression_count"))
        or _int(selected.get("batch_maturity_suite_design_regression_count"))
        or _int(selected.get("batch_maturity_ci_regression_count"))
    ):
        return "review"
    return "clean"


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


def _selected_int(selected: dict[str, Any] | None, key: str) -> int:
    return 0 if selected is None else _int(selected.get(key))


def _selected_mapping(selected: dict[str, Any] | None, key: str) -> dict[str, int]:
    return {} if selected is None else _int_mapping(selected.get(key))


def _selected_list(selected: dict[str, Any] | None, key: str) -> list[str]:
    return [] if selected is None else _string_list(selected.get(key))


__all__ = [
    "batch_review_status",
    "build_training_scale_run_decision_summary",
    "clean_batch_review_status",
]
