from __future__ import annotations

from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    string_list as _string_list,
)

PROMOTED_SEED_CSV_FIELDNAMES: tuple[str, ...] = (
    "seed_status",
    "selected_baseline",
    "decision_status",
    "gate_status",
    "batch_status",
    "readiness_score",
    "source_count",
    "missing_source_count",
    "baseline_suite_path",
    "selected_handoff_require_suite_consistency",
    "selected_handoff_suite_consistency",
    "selected_handoff_suite_mismatch_count",
    "selected_handoff_selected_suite_path",
    "selected_handoff_require_clean_batch_review",
    "selected_handoff_clean_batch_review_status",
    "selected_handoff_batch_maturity_ci_regression_count",
    "selected_handoff_batch_maturity_ci_regression_reason_counts",
    "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "selected_handoff_batch_maturity_ci_regression_names",
    "selected_handoff_batch_maturity_suite_design_regression_count",
    "selected_handoff_batch_maturity_suite_design_regression_names",
    "selected_handoff_selected_batch_maturity_ci_regression_count",
    "selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
    "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "selected_handoff_selected_batch_maturity_suite_design_regression_count",
    "selected_handoff_selected_batch_maturity_suite_design_regression_names",
    "selected_comparison_exclusion_reasons",
    "handoff_require_clean_batch_review_count",
    "handoff_clean_batch_review_count",
    "handoff_unclean_batch_review_count",
    "handoff_batch_maturity_ci_regression_count",
    "handoff_batch_maturity_ci_regression_reason_counts",
    "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "handoff_selected_batch_maturity_ci_regression_total",
    "handoff_selected_batch_maturity_ci_regression_reason_counts",
    "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    "handoff_batch_maturity_ci_regression_names",
    "handoff_batch_maturity_suite_design_regression_count",
    "handoff_selected_batch_maturity_suite_design_regression_total",
    "handoff_batch_maturity_suite_design_regression_names",
    "handoff_selected_batch_maturity_suite_design_regression_names",
    "comparison_exclusion_reasons",
    "comparison_ready_handoff_require_clean_batch_review_count",
    "comparison_ready_handoff_clean_batch_review_count",
    "comparison_ready_handoff_unclean_batch_review_count",
    "comparison_ready_handoff_batch_maturity_ci_regression_count",
    "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
    "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "comparison_ready_handoff_selected_batch_maturity_ci_regression_total",
    "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
    "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    "comparison_ready_handoff_batch_maturity_ci_regression_names",
    "comparison_ready_handoff_batch_maturity_suite_design_regression_count",
    "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total",
    "comparison_ready_handoff_batch_maturity_suite_design_regression_names",
    "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names",
    "selected_handoff_selected_batch_review_status",
    "selected_handoff_selected_batch_comparison_review_action_count",
    "selected_handoff_selected_batch_comparison_blocker_action_count",
    "selected_handoff_batch_comparison_blocker_reasons",
    "comparison_ready_handoff_selected_batch_review_count",
    "comparison_ready_handoff_selected_batch_blocker_count",
    "comparison_ready_handoff_selected_batch_comparison_review_action_total",
    "comparison_ready_handoff_selected_batch_comparison_blocker_action_total",
    "comparison_ready_handoff_batch_comparison_blocker_reasons",
    "handoff_suite_consistent_count",
    "handoff_suite_mismatch_total",
    "next_suite_path",
    "next_suite_source",
    "command_available",
    "execution_ready",
    "command",
)


def promoted_seed_csv_fieldnames() -> list[str]:
    return list(PROMOTED_SEED_CSV_FIELDNAMES)


def promoted_seed_csv_row(report: dict[str, Any]) -> dict[str, Any]:
    seed = _dict(report.get("baseline_seed"))
    plan = _dict(report.get("next_plan"))
    summary = _dict(report.get("summary"))
    return {
        "seed_status": report.get("seed_status"),
        "selected_baseline": seed.get("selected_name"),
        "decision_status": seed.get("decision_status"),
        "gate_status": seed.get("gate_status"),
        "batch_status": seed.get("batch_status"),
        "readiness_score": seed.get("readiness_score"),
        "source_count": summary.get("source_count"),
        "missing_source_count": summary.get("missing_source_count"),
        "baseline_suite_path": summary.get("baseline_suite_path"),
        "selected_handoff_require_suite_consistency": summary.get("selected_handoff_require_suite_consistency"),
        "selected_handoff_suite_consistency": summary.get("selected_handoff_suite_consistency"),
        "selected_handoff_suite_mismatch_count": summary.get("selected_handoff_suite_mismatch_count"),
        "selected_handoff_selected_suite_path": summary.get("selected_handoff_selected_suite_path"),
        "selected_handoff_require_clean_batch_review": summary.get("selected_handoff_require_clean_batch_review"),
        "selected_handoff_clean_batch_review_status": summary.get("selected_handoff_clean_batch_review_status"),
        "selected_handoff_batch_maturity_ci_regression_count": summary.get(
            "selected_handoff_batch_maturity_ci_regression_count"
        ),
        "selected_handoff_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts")
        ),
        "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": summary.get(
            "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "selected_handoff_batch_maturity_ci_regression_names": "; ".join(
            _string_list(summary.get("selected_handoff_batch_maturity_ci_regression_names"))
        ),
        "selected_handoff_batch_maturity_suite_design_regression_count": summary.get(
            "selected_handoff_batch_maturity_suite_design_regression_count"
        ),
        "selected_handoff_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("selected_handoff_batch_maturity_suite_design_regression_names"))
        ),
        "selected_handoff_selected_batch_maturity_ci_regression_count": summary.get(
            "selected_handoff_selected_batch_maturity_ci_regression_count"
        ),
        "selected_handoff_selected_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")
        ),
        "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": summary.get(
            "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "selected_handoff_selected_batch_maturity_suite_design_regression_count": summary.get(
            "selected_handoff_selected_batch_maturity_suite_design_regression_count"
        ),
        "selected_handoff_selected_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_names"))
        ),
        "selected_comparison_exclusion_reasons": "; ".join(
            _string_list(summary.get("selected_comparison_exclusion_reasons"))
        ),
        "handoff_require_clean_batch_review_count": summary.get("handoff_require_clean_batch_review_count"),
        "handoff_clean_batch_review_count": summary.get("handoff_clean_batch_review_count"),
        "handoff_unclean_batch_review_count": summary.get("handoff_unclean_batch_review_count"),
        "handoff_batch_maturity_ci_regression_count": summary.get("handoff_batch_maturity_ci_regression_count"),
        "handoff_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("handoff_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": summary.get(
            "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "handoff_selected_batch_maturity_ci_regression_total": summary.get(
            "handoff_selected_batch_maturity_ci_regression_total"
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": summary.get(
            "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
        ),
        "handoff_batch_maturity_ci_regression_names": "; ".join(
            _string_list(summary.get("handoff_batch_maturity_ci_regression_names"))
        ),
        "handoff_batch_maturity_suite_design_regression_count": summary.get(
            "handoff_batch_maturity_suite_design_regression_count"
        ),
        "handoff_selected_batch_maturity_suite_design_regression_total": summary.get(
            "handoff_selected_batch_maturity_suite_design_regression_total"
        ),
        "handoff_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("handoff_batch_maturity_suite_design_regression_names"))
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("handoff_selected_batch_maturity_suite_design_regression_names"))
        ),
        "comparison_exclusion_reasons": "; ".join(_string_list(summary.get("comparison_exclusion_reasons"))),
        "comparison_ready_handoff_require_clean_batch_review_count": summary.get(
            "comparison_ready_handoff_require_clean_batch_review_count"
        ),
        "comparison_ready_handoff_clean_batch_review_count": summary.get(
            "comparison_ready_handoff_clean_batch_review_count"
        ),
        "comparison_ready_handoff_unclean_batch_review_count": summary.get(
            "comparison_ready_handoff_unclean_batch_review_count"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_count": summary.get(
            "comparison_ready_handoff_batch_maturity_ci_regression_count"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")
        ),
        "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": summary.get(
            "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": summary.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_total"
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": _fmt_mapping(
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": summary.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_names": "; ".join(
            _string_list(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_names"))
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count": summary.get(
            "comparison_ready_handoff_batch_maturity_suite_design_regression_count"
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total": summary.get(
            "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"
        ),
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names"))
        ),
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names": "; ".join(
            _string_list(
                summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names")
            )
        ),
        "selected_handoff_selected_batch_review_status": summary.get("selected_handoff_selected_batch_review_status"),
        "selected_handoff_selected_batch_comparison_review_action_count": summary.get(
            "selected_handoff_selected_batch_comparison_review_action_count"
        ),
        "selected_handoff_selected_batch_comparison_blocker_action_count": summary.get(
            "selected_handoff_selected_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_reasons": "; ".join(
            _string_list(summary.get("selected_handoff_batch_comparison_blocker_reasons"))
        ),
        "comparison_ready_handoff_selected_batch_review_count": summary.get(
            "comparison_ready_handoff_selected_batch_review_count"
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": summary.get(
            "comparison_ready_handoff_selected_batch_blocker_count"
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": summary.get(
            "comparison_ready_handoff_selected_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": summary.get(
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": "; ".join(
            _string_list(summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons"))
        ),
        "handoff_suite_consistent_count": summary.get("handoff_suite_consistent_count"),
        "handoff_suite_mismatch_total": summary.get("handoff_suite_mismatch_total"),
        "next_suite_path": summary.get("next_suite_path"),
        "next_suite_source": summary.get("next_suite_source"),
        "command_available": plan.get("command_available"),
        "execution_ready": plan.get("execution_ready"),
        "command": plan.get("command_text"),
    }


__all__ = ["promoted_seed_csv_fieldnames", "promoted_seed_csv_row"]
