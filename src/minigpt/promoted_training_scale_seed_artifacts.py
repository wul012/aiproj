from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_csv_rows import (
    promoted_seed_csv_fieldnames,
    promoted_seed_csv_row,
)
from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_csv_row,
    write_json_payload,
)
from minigpt.promoted_training_scale_seed_sections import render_promoted_training_scale_seed_html


def write_promoted_training_scale_seed_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_seed_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv_row(promoted_seed_csv_row(report), out_path, promoted_seed_csv_fieldnames())


def render_promoted_training_scale_seed_markdown(report: dict[str, Any]) -> str:
    seed = _dict(report.get("baseline_seed"))
    plan = _dict(report.get("next_plan"))
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale next-cycle seed')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Seed status: `{report.get('seed_status')}`",
        f"- Selected baseline: `{seed.get('selected_name')}`",
        f"- Decision status: `{seed.get('decision_status')}`",
        f"- Gate: `{seed.get('gate_status')}`",
        f"- Batch: `{seed.get('batch_status')}`",
        f"- Readiness: `{seed.get('readiness_score')}`",
        f"- Sources: `{summary.get('source_count')}`",
        f"- Missing sources: `{summary.get('missing_source_count')}`",
        f"- Baseline suite: `{summary.get('baseline_suite_path')}`",
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
        f"- Next suite: `{summary.get('next_suite_path')}`",
        f"- Next suite source: `{summary.get('next_suite_source')}`",
        "",
        "## Next Plan Command",
        "",
        "```powershell",
        str(plan.get("command_text") or "No command is available."),
        "```",
        "",
        "## Sources",
        "",
        "| Source | Exists | Kind |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(plan.get("sources")):
        lines.append(f"| {_md(row.get('path'))} | {_md(row.get('exists'))} | {_md(row.get('kind'))} |")
    blockers = _string_list(report.get("blockers"))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_seed_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_markdown(report), encoding="utf-8")


def write_promoted_training_scale_seed_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_html(report), encoding="utf-8")


def write_promoted_training_scale_seed_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_seed.json",
        "csv": root / "promoted_training_scale_seed.csv",
        "markdown": root / "promoted_training_scale_seed.md",
        "html": root / "promoted_training_scale_seed.html",
    }
    write_promoted_training_scale_seed_json(report, paths["json"])
    write_promoted_training_scale_seed_csv(report, paths["csv"])
    write_promoted_training_scale_seed_markdown(report, paths["markdown"])
    write_promoted_training_scale_seed_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "render_promoted_training_scale_seed_html",
    "render_promoted_training_scale_seed_markdown",
    "write_promoted_training_scale_seed_csv",
    "write_promoted_training_scale_seed_html",
    "write_promoted_training_scale_seed_json",
    "write_promoted_training_scale_seed_markdown",
    "write_promoted_training_scale_seed_outputs",
]
