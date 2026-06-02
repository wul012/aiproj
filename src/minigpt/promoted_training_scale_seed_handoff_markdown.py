from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_artifacts import (
    _embedded_receipt_check,
    _embedded_receipt_check_outputs,
    _handoff_assurance,
    _handoff_assurance_outputs,
    _receipt_check,
    _receipt_check_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
)


def render_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    clean_requirement = _dict(report.get("clean_evidence_requirement"))
    clean_batch_requirement = _dict(report.get("clean_batch_review_requirement"))
    automation_gate = _dict(report.get("automation_gate"))
    automation_summary = _dict(report.get("automation_summary"))
    receipt_check = _receipt_check(report)
    receipt_check_outputs = _receipt_check_outputs(report)
    embedded_receipt_check = _embedded_receipt_check(report)
    embedded_receipt_check_outputs = _embedded_receipt_check_outputs(report)
    handoff_assurance = _handoff_assurance(report)
    handoff_assurance_outputs = _handoff_assurance_outputs(report)
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale seed handoff')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Handoff status: `{summary.get('handoff_status')}`",
        f"- Seed status: `{report.get('seed_status')}`",
        f"- Decision status: `{summary.get('decision_status')}`",
        f"- Execute: `{report.get('execute')}`",
        f"- Return code: `{execution.get('returncode')}`",
        f"- Artifacts: `{summary.get('available_artifact_count')}/{summary.get('artifact_count')}`",
        f"- Plan status: `{summary.get('plan_status')}`",
        f"- Seed suite: `{summary.get('seed_suite_path')}`",
        f"- Selected handoff suite: `{summary.get('selected_handoff_suite_consistency')}`",
        f"- Selected handoff mismatches: `{summary.get('selected_handoff_suite_mismatch_count')}`",
        f"- Selected handoff suite path: `{summary.get('selected_handoff_selected_suite_path')}`",
        f"- Selected handoff require clean batch review: `{summary.get('selected_handoff_require_clean_batch_review')}`",
        f"- Selected handoff clean batch review: `{summary.get('selected_handoff_clean_batch_review_status')}`",
        f"- Selected handoff batch CI regressions: `{summary.get('selected_handoff_batch_maturity_ci_regression_count')}`",
        f"- Selected handoff batch CI boundary plan-check regressions: `{summary.get('selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Selected handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('selected_handoff_batch_maturity_ci_regression_names')))}`",
        f"- Selected handoff batch CI regression reasons: `{_fmt_mapping(summary.get('selected_handoff_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Selected handoff batch suite-design regressions: `{summary.get('selected_handoff_batch_maturity_suite_design_regression_count')}`",
        f"- Selected handoff batch suite-design names: `{', '.join(_string_list(summary.get('selected_handoff_batch_maturity_suite_design_regression_names')))}`",
        f"- Selected handoff selected batch CI regressions: `{summary.get('selected_handoff_selected_batch_maturity_ci_regression_count')}`",
        f"- Selected handoff selected batch CI boundary plan-check regressions: `{summary.get('selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Selected handoff selected batch CI regression reasons: `{_fmt_mapping(summary.get('selected_handoff_selected_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Selected handoff selected batch suite-design regressions: `{summary.get('selected_handoff_selected_batch_maturity_suite_design_regression_count')}`",
        f"- Selected handoff selected batch suite-design names: `{', '.join(_string_list(summary.get('selected_handoff_selected_batch_maturity_suite_design_regression_names')))}`",
        f"- Selected comparison exclusion reasons: `{', '.join(_string_list(summary.get('selected_comparison_exclusion_reasons')))}`",
        f"- Handoff require clean batch review: `{summary.get('handoff_require_clean_batch_review_count')}`",
        f"- Handoff clean batch review: `{summary.get('handoff_clean_batch_review_count')}`",
        f"- Handoff unclean batch review: `{summary.get('handoff_unclean_batch_review_count')}`",
        f"- Handoff batch CI regressions: `{summary.get('handoff_batch_maturity_ci_regression_count')}`",
        f"- Handoff batch CI boundary plan-check regressions: `{summary.get('handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Handoff selected batch CI regressions: `{summary.get('handoff_selected_batch_maturity_ci_regression_total')}`",
        f"- Handoff selected batch CI boundary plan-check regressions: `{summary.get('handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total')}`",
        f"- Handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('handoff_batch_maturity_ci_regression_names')))}`",
        f"- Handoff batch CI regression reasons: `{_fmt_mapping(summary.get('handoff_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Handoff selected batch CI regression reasons: `{_fmt_mapping(summary.get('handoff_selected_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Handoff batch suite-design regressions: `{summary.get('handoff_batch_maturity_suite_design_regression_count')}`",
        f"- Handoff selected batch suite-design regressions: `{summary.get('handoff_selected_batch_maturity_suite_design_regression_total')}`",
        f"- Handoff batch suite-design names: `{', '.join(_string_list(summary.get('handoff_batch_maturity_suite_design_regression_names')))}`",
        f"- Handoff selected batch suite-design names: `{', '.join(_string_list(summary.get('handoff_selected_batch_maturity_suite_design_regression_names')))}`",
        f"- Comparison exclusion reasons: `{', '.join(_string_list(summary.get('comparison_exclusion_reasons')))}`",
        f"- Comparison-ready clean-required handoffs: `{summary.get('comparison_ready_handoff_require_clean_batch_review_count')}`",
        f"- Comparison-ready clean handoffs: `{summary.get('comparison_ready_handoff_clean_batch_review_count')}`",
        f"- Comparison-ready unclean handoffs: `{summary.get('comparison_ready_handoff_unclean_batch_review_count')}`",
        f"- Comparison-ready handoff batch CI regressions: `{summary.get('comparison_ready_handoff_batch_maturity_ci_regression_count')}`",
        f"- Comparison-ready handoff batch CI boundary plan-check regressions: `{summary.get('comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Comparison-ready selected batch CI regressions: `{summary.get('comparison_ready_handoff_selected_batch_maturity_ci_regression_total')}`",
        f"- Comparison-ready selected batch CI boundary plan-check regressions: `{summary.get('comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total')}`",
        f"- Comparison-ready handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('comparison_ready_handoff_batch_maturity_ci_regression_names')))}`",
        f"- Comparison-ready handoff batch CI regression reasons: `{_fmt_mapping(summary.get('comparison_ready_handoff_batch_maturity_ci_regression_reason_counts'))}`",
        f"- Comparison-ready selected batch CI regression reasons: `{_fmt_mapping(summary.get('comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts'))}`",
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
        f"- Handoff suite mismatches: `{summary.get('handoff_suite_mismatch_total')}`",
        f"- Plan suite: `{summary.get('plan_suite_path')}`",
        f"- Seed handoff suite alignment: `{summary.get('seed_handoff_suite_alignment_status')}`",
        f"- Seed handoff suite alignment detail: `{summary.get('seed_handoff_suite_alignment_detail')}`",
        f"- Seed handoff clean evidence: `{summary.get('seed_handoff_clean_evidence_status')}`",
        f"- Seed handoff clean evidence ready: `{summary.get('seed_handoff_clean_evidence_ready')}`",
        f"- Seed handoff clean evidence detail: `{summary.get('seed_handoff_clean_evidence_detail')}`",
        f"- Seed handoff clean evidence status domain: `{summary.get('seed_handoff_clean_evidence_status_domain')}`",
        f"- Clean evidence requirement: `{clean_requirement.get('status')}`",
        f"- Clean evidence requirement detail: `{clean_requirement.get('detail')}`",
        f"- Clean evidence requirement status domain: `{clean_requirement.get('status_domain')}`",
        f"- Clean batch-review requirement: `{clean_batch_requirement.get('status')}`",
        f"- Clean batch-review requirement detail: `{clean_batch_requirement.get('detail')}`",
        f"- Clean batch-review requirement selected CI regressions: `{clean_batch_requirement.get('selected_ci_regression_count')}`",
        f"- Clean batch-review requirement selected CI boundary plan-check regressions: `{clean_batch_requirement.get('selected_ci_boundary_plan_check_ready_regression_count')}`",
        f"- Clean batch-review requirement selected CI reasons: `{_fmt_mapping(clean_batch_requirement.get('selected_ci_regression_reason_counts'))}`",
        f"- Clean batch-review requirement selected suite-design regressions: `{clean_batch_requirement.get('selected_suite_design_regression_count')}`",
        f"- Clean batch-review requirement selected suite-design names: `{', '.join(_string_list(clean_batch_requirement.get('selected_suite_design_regression_names')))}`",
        f"- Clean batch-review requirement status domain: `{clean_batch_requirement.get('status_domain')}`",
        f"- Automation gate: `{automation_gate.get('status')}`",
        f"- Automation gate decision: `{automation_gate.get('decision')}`",
        f"- Automation gate exit code: `{automation_gate.get('exit_code')}`",
        f"- Automation gate required count: `{automation_gate.get('required_requirement_count')}`",
        f"- Automation gate blocking count: `{automation_gate.get('blocking_requirement_count')}`",
        f"- Automation gate detail: `{automation_gate.get('detail')}`",
        f"- Automation gate failed requirements: `{automation_gate.get('failed_requirements')}`",
        f"- Automation gate status domain: `{automation_gate.get('status_domain')}`",
        f"- Automation gate decision domain: `{automation_gate.get('decision_domain')}`",
        f"- Automation summary decision: `{automation_summary.get('decision')}`",
        f"- Automation summary exit code: `{automation_summary.get('exit_code')}`",
        f"- Automation summary blocking source: `{automation_summary.get('blocking_source')}`",
        f"- Automation summary failed requirements: `{automation_summary.get('failed_requirements')}`",
        f"- Automation summary decision domain: `{automation_summary.get('decision_domain')}`",
        f"- Receipt check status: `{receipt_check.get('status')}`",
        f"- Receipt check decision: `{receipt_check.get('decision')}`",
        f"- Receipt check exit code: `{receipt_check.get('exit_code')}`",
        f"- Receipt check checker exit code: `{receipt_check.get('checker_exit_code')}`",
        f"- Receipt check blocking source: `{receipt_check.get('blocking_source')}`",
        f"- Receipt check failed requirements: `{receipt_check.get('failed_requirements')}`",
        f"- Receipt check issue count: `{receipt_check.get('issue_count')}`",
        f"- Receipt check issues: `{receipt_check.get('issues')}`",
        f"- Receipt check receipt path: `{receipt_check.get('receipt_path')}`",
        f"- Receipt check json: `{receipt_check_outputs.get('json')}`",
        f"- Receipt check text: `{receipt_check_outputs.get('text')}`",
        f"- Embedded receipt check status: `{embedded_receipt_check.get('status')}`",
        f"- Embedded receipt check decision: `{embedded_receipt_check.get('decision')}`",
        f"- Embedded receipt check exit code: `{embedded_receipt_check.get('exit_code')}`",
        f"- Embedded receipt check checker exit code: `{embedded_receipt_check.get('checker_exit_code')}`",
        f"- Embedded receipt check sidecar status: `{embedded_receipt_check.get('sidecar_status')}`",
        f"- Embedded receipt check issue count: `{embedded_receipt_check.get('issue_count')}`",
        f"- Embedded receipt check issues: `{embedded_receipt_check.get('issues')}`",
        f"- Embedded receipt check receipt path: `{embedded_receipt_check.get('receipt_path')}`",
        f"- Embedded receipt check receipt path exists: `{embedded_receipt_check.get('receipt_path_exists')}`",
        f"- Embedded receipt check json: `{embedded_receipt_check.get('receipt_check_json')}`",
        f"- Embedded receipt check json exists: `{embedded_receipt_check.get('receipt_check_json_exists')}`",
        f"- Embedded receipt check text: `{embedded_receipt_check.get('receipt_check_text')}`",
        f"- Embedded receipt check text exists: `{embedded_receipt_check.get('receipt_check_text_exists')}`",
        f"- Embedded receipt check output json: `{embedded_receipt_check_outputs.get('json')}`",
        f"- Embedded receipt check output text: `{embedded_receipt_check_outputs.get('text')}`",
        f"- Handoff assurance status: `{handoff_assurance.get('status')}`",
        f"- Handoff assurance decision: `{handoff_assurance.get('decision')}`",
        f"- Handoff assurance exit code: `{handoff_assurance.get('exit_code')}`",
        f"- Handoff assurance checker exit code: `{handoff_assurance.get('checker_exit_code')}`",
        f"- Handoff assurance embedded receipt check status: `{handoff_assurance.get('embedded_receipt_check_status')}`",
        f"- Handoff assurance embedded sidecar status: `{handoff_assurance.get('embedded_receipt_check_sidecar_status')}`",
        f"- Handoff assurance receipt schema version: `{handoff_assurance.get('embedded_receipt_check_receipt_schema_version')}`",
        (
            "- Handoff assurance receipt selected CI regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt selected CI reasons: "
            f"`{_fmt_mapping(handoff_assurance.get('embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts'))}`"
        ),
        (
            "- Handoff assurance receipt selected CI boundary plan-check regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt CI regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt CI reasons: "
            f"`{_fmt_mapping(handoff_assurance.get('embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts'))}`"
        ),
        (
            "- Handoff assurance receipt CI boundary plan-check regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt selected suite-design regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt selected suite-design names: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_names')}`"
        ),
        (
            "- Handoff assurance receipt suite-design regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt suite-design names: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names')}`"
        ),
        (
            "- Handoff assurance receipt ready suite-design regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt ready CI boundary plan-check regressions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count')}`"
        ),
        (
            "- Handoff assurance receipt ready CI reasons: "
            f"`{_fmt_mapping(handoff_assurance.get('embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts'))}`"
        ),
        (
            "- Handoff assurance receipt ready suite-design names: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names')}`"
        ),
        (
            "- Handoff assurance receipt comparison exclusions: "
            f"`{handoff_assurance.get('embedded_receipt_check_receipt_comparison_exclusion_reasons')}`"
        ),
        f"- Handoff assurance output json exists: `{handoff_assurance.get('embedded_receipt_check_output_json_exists')}`",
        f"- Handoff assurance output text exists: `{handoff_assurance.get('embedded_receipt_check_output_text_exists')}`",
        f"- Handoff assurance issue count: `{handoff_assurance.get('issue_count')}`",
        f"- Handoff assurance issues: `{handoff_assurance.get('issues')}`",
        f"- Handoff assurance json: `{handoff_assurance_outputs.get('json')}`",
        f"- Handoff assurance text: `{handoff_assurance_outputs.get('text')}`",
        f"- Next batch command: `{summary.get('next_batch_command_available')}`",
        "",
        "## Command",
        "",
        "```powershell",
        str(report.get("command_text") or ""),
        "```",
        "",
        "## Execution",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Status | {_md(execution.get('status'))} |",
        f"| Elapsed seconds | {_md(execution.get('elapsed_seconds'))} |",
        f"| Stdout tail | {_md(execution.get('stdout_tail'))} |",
        f"| Stderr tail | {_md(execution.get('stderr_tail'))} |",
        "",
        "## Plan Artifacts",
        "",
        "| Key | Exists | Path |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("artifact_rows")):
        lines.append(f"| {_md(row.get('key'))} | {_md(row.get('exists'))} | {_md(row.get('path'))} |")
    if report.get("next_batch_command"):
        lines.extend(
            ["", "## Next Batch Command", "", "```powershell", str(report.get("next_batch_command_text") or ""), "```"]
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_markdown(report), encoding="utf-8")


__all__ = [
    "render_promoted_training_scale_seed_handoff_markdown",
    "write_promoted_training_scale_seed_handoff_markdown",
]
