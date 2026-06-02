from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_csv_row,
    write_json_payload,
)
from minigpt.promoted_training_scale_decision_html import (
    render_promoted_training_scale_decision_html,
    write_promoted_training_scale_decision_html,
)


def write_promoted_training_scale_decision_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_decision_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    selected = _dict(report.get("selected_baseline"))
    summary = _dict(report.get("summary"))
    fieldnames = [
        "decision_status",
        "selected_baseline",
        "selected_gate_status",
        "selected_batch_status",
        "selected_readiness_score",
        "selected_suite_path",
        "require_suite_consistency",
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
        "selected_handoff_selected_batch_review_status",
        "selected_handoff_selected_batch_comparison_review_action_count",
        "selected_handoff_selected_batch_comparison_blocker_action_count",
        "selected_handoff_selected_batch_maturity_coverage_regression_count",
        "selected_handoff_batch_comparison_review_action_count",
        "selected_handoff_batch_comparison_blocker_action_count",
        "selected_handoff_batch_comparison_blocker_reasons",
        "handoff_require_suite_consistency_count",
        "handoff_suite_consistent_count",
        "handoff_suite_mismatch_total",
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
        "comparison_ready_handoff_selected_batch_review_count",
        "comparison_ready_handoff_selected_batch_blocker_count",
        "comparison_ready_handoff_selected_batch_comparison_review_action_total",
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total",
        "comparison_ready_handoff_batch_comparison_review_action_total",
        "comparison_ready_handoff_batch_comparison_blocker_action_total",
        "comparison_ready_handoff_batch_comparison_blocker_reasons",
        "candidate_count",
        "rejected_count",
        "comparison_status",
        "suite_consistency",
    ]
    write_csv_row(
        {
            "decision_status": report.get("decision_status"),
            "selected_baseline": selected.get("name"),
            "selected_gate_status": selected.get("gate_status"),
            "selected_batch_status": selected.get("batch_status"),
            "selected_readiness_score": selected.get("readiness_score"),
            "selected_suite_path": summary.get("selected_suite_path"),
            "require_suite_consistency": summary.get("require_suite_consistency"),
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
            "selected_handoff_selected_batch_review_status": summary.get("selected_handoff_selected_batch_review_status"),
            "selected_handoff_selected_batch_comparison_review_action_count": summary.get(
                "selected_handoff_selected_batch_comparison_review_action_count"
            ),
            "selected_handoff_selected_batch_comparison_blocker_action_count": summary.get(
                "selected_handoff_selected_batch_comparison_blocker_action_count"
            ),
            "selected_handoff_selected_batch_maturity_coverage_regression_count": summary.get(
                "selected_handoff_selected_batch_maturity_coverage_regression_count"
            ),
            "selected_handoff_batch_comparison_review_action_count": summary.get(
                "selected_handoff_batch_comparison_review_action_count"
            ),
            "selected_handoff_batch_comparison_blocker_action_count": summary.get(
                "selected_handoff_batch_comparison_blocker_action_count"
            ),
            "selected_handoff_batch_comparison_blocker_reasons": "; ".join(
                _string_list(summary.get("selected_handoff_batch_comparison_blocker_reasons"))
            ),
            "handoff_require_suite_consistency_count": summary.get("handoff_require_suite_consistency_count"),
            "handoff_suite_consistent_count": summary.get("handoff_suite_consistent_count"),
            "handoff_suite_mismatch_total": summary.get("handoff_suite_mismatch_total"),
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
            "comparison_ready_handoff_batch_comparison_review_action_total": summary.get(
                "comparison_ready_handoff_batch_comparison_review_action_total"
            ),
            "comparison_ready_handoff_batch_comparison_blocker_action_total": summary.get(
                "comparison_ready_handoff_batch_comparison_blocker_action_total"
            ),
            "comparison_ready_handoff_batch_comparison_blocker_reasons": "; ".join(
                _string_list(summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons"))
            ),
            "candidate_count": summary.get("candidate_count"),
            "rejected_count": summary.get("rejected_count"),
            "comparison_status": summary.get("comparison_status"),
            "suite_consistency": summary.get("suite_consistency"),
        },
        out_path,
        fieldnames,
    )


def render_promoted_training_scale_decision_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    selected = _dict(report.get("selected_baseline"))
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale baseline decision')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Decision status: `{report.get('decision_status')}`",
        f"- Selected baseline: `{selected.get('name')}`",
        f"- Gate: `{selected.get('gate_status')}`",
        f"- Batch: `{selected.get('batch_status')}`",
        f"- Readiness: `{selected.get('readiness_score')}`",
        f"- Selected suite: `{summary.get('selected_suite_path')}`",
        f"- Require suite consistency: `{summary.get('require_suite_consistency')}`",
        f"- Selected handoff suite: `{summary.get('selected_handoff_suite_consistency')}`",
        f"- Selected handoff mismatches: `{summary.get('selected_handoff_suite_mismatch_count')}`",
        f"- Selected handoff suite path: `{summary.get('selected_handoff_selected_suite_path')}`",
        f"- Selected handoff require clean batch review: `{summary.get('selected_handoff_require_clean_batch_review')}`",
        f"- Selected handoff clean batch review: `{summary.get('selected_handoff_clean_batch_review_status')}`",
        f"- Selected handoff batch CI regressions: `{summary.get('selected_handoff_batch_maturity_ci_regression_count')}`",
        f"- Selected handoff batch CI regression reasons: `{_fmt_mapping(summary.get('selected_handoff_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Selected handoff batch CI boundary plan-check regressions: `{summary.get('selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Selected handoff batch suite-design regressions: `{summary.get('selected_handoff_batch_maturity_suite_design_regression_count')}`",
        f"- Selected handoff batch suite-design names: `{', '.join(_string_list(summary.get('selected_handoff_batch_maturity_suite_design_regression_names')))}`",
        f"- Selected handoff selected batch CI regressions: `{summary.get('selected_handoff_selected_batch_maturity_ci_regression_count')}`",
        f"- Selected handoff selected batch CI regression reasons: `{_fmt_mapping(summary.get('selected_handoff_selected_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Selected handoff selected batch CI boundary plan-check regressions: `{summary.get('selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Selected handoff selected batch suite-design regressions: `{summary.get('selected_handoff_selected_batch_maturity_suite_design_regression_count')}`",
        f"- Selected handoff selected batch suite-design names: `{', '.join(_string_list(summary.get('selected_handoff_selected_batch_maturity_suite_design_regression_names')))}`",
        f"- Selected comparison exclusion reasons: `{', '.join(_string_list(summary.get('selected_comparison_exclusion_reasons')))}`",
        f"- Handoff require clean batch review: `{summary.get('handoff_require_clean_batch_review_count')}`",
        f"- Handoff clean batch review: `{summary.get('handoff_clean_batch_review_count')}`",
        f"- Handoff unclean batch review: `{summary.get('handoff_unclean_batch_review_count')}`",
        f"- Handoff batch CI regressions: `{summary.get('handoff_batch_maturity_ci_regression_count')}`",
        f"- Handoff batch CI regression reasons: `{_fmt_mapping(summary.get('handoff_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Handoff batch CI boundary plan-check regressions: `{summary.get('handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Handoff selected batch CI regressions: `{summary.get('handoff_selected_batch_maturity_ci_regression_total')}`",
        f"- Handoff selected batch CI regression reasons: `{_fmt_mapping(summary.get('handoff_selected_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Handoff selected batch CI boundary plan-check regressions: `{summary.get('handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total')}`",
        f"- Handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('handoff_batch_maturity_ci_regression_names')))}`",
        f"- Handoff batch suite-design regressions: `{summary.get('handoff_batch_maturity_suite_design_regression_count')}`",
        f"- Handoff selected batch suite-design regressions: `{summary.get('handoff_selected_batch_maturity_suite_design_regression_total')}`",
        f"- Handoff batch suite-design names: `{', '.join(_string_list(summary.get('handoff_batch_maturity_suite_design_regression_names')))}`",
        f"- Handoff selected batch suite-design names: `{', '.join(_string_list(summary.get('handoff_selected_batch_maturity_suite_design_regression_names')))}`",
        f"- Comparison exclusion reasons: `{', '.join(_string_list(summary.get('comparison_exclusion_reasons')))}`",
        f"- Comparison-ready clean-required handoffs: `{summary.get('comparison_ready_handoff_require_clean_batch_review_count')}`",
        f"- Comparison-ready clean handoffs: `{summary.get('comparison_ready_handoff_clean_batch_review_count')}`",
        f"- Comparison-ready unclean handoffs: `{summary.get('comparison_ready_handoff_unclean_batch_review_count')}`",
        f"- Comparison-ready handoff batch CI regressions: `{summary.get('comparison_ready_handoff_batch_maturity_ci_regression_count')}`",
        f"- Comparison-ready handoff batch CI regression reasons: `{_fmt_mapping(summary.get('comparison_ready_handoff_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Comparison-ready handoff batch CI boundary plan-check regressions: `{summary.get('comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Comparison-ready selected batch CI regressions: `{summary.get('comparison_ready_handoff_selected_batch_maturity_ci_regression_total')}`",
        f"- Comparison-ready selected batch CI regression reasons: `{_fmt_mapping(summary.get('comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Comparison-ready selected batch CI boundary plan-check regressions: `{summary.get('comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total')}`",
        f"- Comparison-ready handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('comparison_ready_handoff_batch_maturity_ci_regression_names')))}`",
        f"- Comparison-ready handoff batch suite-design regressions: `{summary.get('comparison_ready_handoff_batch_maturity_suite_design_regression_count')}`",
        f"- Comparison-ready selected batch suite-design regressions: `{summary.get('comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total')}`",
        f"- Comparison-ready handoff batch suite-design names: `{', '.join(_string_list(summary.get('comparison_ready_handoff_batch_maturity_suite_design_regression_names')))}`",
        f"- Comparison-ready selected batch suite-design names: `{', '.join(_string_list(summary.get('comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names')))}`",
        f"- Selected handoff batch review: `{summary.get('selected_handoff_selected_batch_review_status')}`",
        f"- Selected handoff batch review actions: `{summary.get('selected_handoff_selected_batch_comparison_review_action_count')}`",
        f"- Selected handoff batch blocker actions: `{summary.get('selected_handoff_selected_batch_comparison_blocker_action_count')}`",
        f"- Comparison-ready handoff batch reviews: `{summary.get('comparison_ready_handoff_selected_batch_review_count')}`",
        f"- Comparison-ready handoff batch blockers: `{summary.get('comparison_ready_handoff_selected_batch_blocker_count')}`",
        f"- Comparison-ready handoff batch blocker reasons: `{', '.join(_string_list(summary.get('comparison_ready_handoff_batch_comparison_blocker_reasons')))}`",
        f"- Handoff suite consistent: `{summary.get('handoff_suite_consistent_count')}`",
        f"- Handoff suite mismatches: `{summary.get('handoff_suite_mismatch_total')}`",
        f"- Candidates: `{summary.get('candidate_count')}`",
        f"- Rejected: `{summary.get('rejected_count')}`",
        f"- Comparison status: `{summary.get('comparison_status')}`",
        f"- Suite consistency: `{summary.get('suite_consistency')}`",
        "",
        "## Rejected Runs",
        "",
        "| Run | Gate | Batch | Score | Reasons |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for run in _list_of_dicts(report.get("rejected_runs")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(run.get("name")),
                    _md(run.get("gate_status")),
                    _md(run.get("batch_status")),
                    _md(run.get("readiness_score")),
                    _md("; ".join(_string_list(run.get("reasons")))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_decision_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_decision_markdown(report), encoding="utf-8")


def write_promoted_training_scale_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_decision.json",
        "csv": root / "promoted_training_scale_decision.csv",
        "markdown": root / "promoted_training_scale_decision.md",
        "html": root / "promoted_training_scale_decision.html",
    }
    write_promoted_training_scale_decision_json(report, paths["json"])
    write_promoted_training_scale_decision_csv(report, paths["csv"])
    write_promoted_training_scale_decision_markdown(report, paths["markdown"])
    write_promoted_training_scale_decision_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}

__all__ = [
    "render_promoted_training_scale_decision_html",
    "render_promoted_training_scale_decision_markdown",
    "write_promoted_training_scale_decision_csv",
    "write_promoted_training_scale_decision_html",
    "write_promoted_training_scale_decision_json",
    "write_promoted_training_scale_decision_markdown",
    "write_promoted_training_scale_decision_outputs",
]
