from __future__ import annotations

from typing import Any

from minigpt.promoted_training_scale_seed_handoff_markdown import (
    render_promoted_training_scale_seed_handoff_markdown,
    write_promoted_training_scale_seed_handoff_markdown,
)
from minigpt.report_utils import as_dict as _dict, display_command as _display_command, format_mapping as _fmt_mapping, html_escape as _e, list_of_dicts as _list_of_dicts, string_list as _string_list
from minigpt.promoted_training_scale_seed_handoff_receipt_artifacts import (
    _embedded_receipt_check,
    _embedded_receipt_check_outputs,
    _embedded_receipt_check_section,
    _handoff_assurance,
    _handoff_assurance_outputs,
    _handoff_assurance_section,
    _receipt_check,
    _receipt_check_outputs,
    _receipt_check_section,
)


def render_promoted_training_scale_seed_handoff_html(report: dict[str, Any]) -> str:
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
    clean_evidence_domain = ", ".join(
        str(item) for item in _string_list(summary.get("seed_handoff_clean_evidence_status_domain"))
    )
    clean_requirement_domain = ", ".join(
        str(item) for item in _string_list(clean_requirement.get("status_domain"))
    )
    clean_batch_requirement_domain = ", ".join(
        str(item) for item in _string_list(clean_batch_requirement.get("status_domain"))
    )
    automation_gate_domain = ", ".join(str(item) for item in _string_list(automation_gate.get("status_domain")))
    automation_gate_decision_domain = ", ".join(
        str(item) for item in _string_list(automation_gate.get("decision_domain"))
    )
    automation_summary_decision_domain = ", ".join(
        str(item) for item in _string_list(automation_summary.get("decision_domain"))
    )
    stats = [
        ("Status", summary.get("handoff_status")),
        ("Seed", report.get("seed_status")),
        ("Decision", summary.get("decision_status")),
        ("Execute", report.get("execute")),
        ("Return", execution.get("returncode")),
        ("Artifacts", f"{summary.get('available_artifact_count')}/{summary.get('artifact_count')}"),
        ("Plan", summary.get("plan_status")),
        ("Seed suite", summary.get("seed_suite_path")),
        ("Selected handoff suite", summary.get("selected_handoff_suite_consistency")),
        ("Selected handoff mismatch", summary.get("selected_handoff_suite_mismatch_count")),
        ("Selected clean required", summary.get("selected_handoff_require_clean_batch_review")),
        ("Selected clean batch", summary.get("selected_handoff_clean_batch_review_status")),
        ("Selected CI regressions", summary.get("selected_handoff_batch_maturity_ci_regression_count")),
        (
            "Selected CI boundary plan",
            summary.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Selected CI reasons", _fmt_mapping(summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts"))),
        (
            "Selected suite-design regressions",
            summary.get("selected_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Selected selected CI regressions",
            summary.get("selected_handoff_selected_batch_maturity_ci_regression_count"),
        ),
        (
            "Selected selected CI boundary plan",
            summary.get("selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Selected selected CI reasons",
            _fmt_mapping(summary.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Selected selected suite-design regressions",
            summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_count"),
        ),
        ("Handoff clean required", summary.get("handoff_require_clean_batch_review_count")),
        ("Handoff clean", summary.get("handoff_clean_batch_review_count")),
        ("Handoff unclean", summary.get("handoff_unclean_batch_review_count")),
        ("Handoff CI regressions", summary.get("handoff_batch_maturity_ci_regression_count")),
        (
            "Handoff CI boundary plan",
            summary.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Handoff selected CI regressions", summary.get("handoff_selected_batch_maturity_ci_regression_total")),
        (
            "Handoff selected CI boundary plan",
            summary.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        ("Handoff CI reasons", _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))),
        (
            "Handoff selected CI reasons",
            _fmt_mapping(summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        ("Handoff suite-design regressions", summary.get("handoff_batch_maturity_suite_design_regression_count")),
        (
            "Handoff selected suite-design regressions",
            summary.get("handoff_selected_batch_maturity_suite_design_regression_total"),
        ),
        ("Ready clean-required", summary.get("comparison_ready_handoff_require_clean_batch_review_count")),
        ("Ready clean batch", summary.get("comparison_ready_handoff_clean_batch_review_count")),
        ("Ready unclean batch", summary.get("comparison_ready_handoff_unclean_batch_review_count")),
        ("Ready CI regressions", summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")),
        (
            "Ready CI boundary plan",
            summary.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Ready selected CI regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_total"),
        ),
        (
            "Ready selected CI boundary plan",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "Ready CI reasons",
            _fmt_mapping(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Ready selected CI reasons",
            _fmt_mapping(summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Ready suite-design regressions",
            summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Ready selected suite-design regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"),
        ),
        ("Selected handoff batch", summary.get("selected_handoff_selected_batch_review_status")),
        ("Selected batch blockers", summary.get("selected_handoff_selected_batch_comparison_blocker_action_count")),
        ("Ready batch reviews", summary.get("comparison_ready_handoff_selected_batch_review_count")),
        ("Ready batch blockers", summary.get("comparison_ready_handoff_selected_batch_blocker_count")),
        ("Handoff suite mismatches", summary.get("handoff_suite_mismatch_total")),
        ("Plan suite", summary.get("plan_suite_path")),
        ("Suite alignment", summary.get("seed_handoff_suite_alignment_status")),
        ("Clean evidence", summary.get("seed_handoff_clean_evidence_status")),
        ("Clean evidence domain", clean_evidence_domain),
        ("Clean evidence gate", clean_requirement.get("status")),
        ("Clean evidence gate domain", clean_requirement_domain),
        ("Clean batch gate", clean_batch_requirement.get("status")),
        ("Clean batch gate selected CI", clean_batch_requirement.get("selected_ci_regression_count")),
        (
            "Clean batch gate selected CI boundary plan",
            clean_batch_requirement.get("selected_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Clean batch gate selected CI reasons", _fmt_mapping(clean_batch_requirement.get("selected_ci_regression_reason_counts"))),
        (
            "Clean batch gate selected suite-design",
            clean_batch_requirement.get("selected_suite_design_regression_count"),
        ),
        ("Clean batch gate domain", clean_batch_requirement_domain),
        ("Automation gate", automation_gate.get("status")),
        ("Automation decision", automation_gate.get("decision")),
        ("Automation exit", automation_gate.get("exit_code")),
        ("Automation required", automation_gate.get("required_requirement_count")),
        ("Automation blocking", automation_gate.get("blocking_requirement_count")),
        ("Automation gate domain", automation_gate_domain),
        ("Automation decision domain", automation_gate_decision_domain),
        ("Automation summary", automation_summary.get("decision")),
        ("Automation summary exit", automation_summary.get("exit_code")),
        ("Automation blocking source", automation_summary.get("blocking_source")),
        ("Automation summary domain", automation_summary_decision_domain),
        ("Receipt check", receipt_check.get("status")),
        ("Receipt decision", receipt_check.get("decision")),
        ("Receipt exit", receipt_check.get("exit_code")),
        ("Receipt checker exit", receipt_check.get("checker_exit_code")),
        ("Receipt blocking source", receipt_check.get("blocking_source")),
        ("Receipt failed requirements", ", ".join(_string_list(receipt_check.get("failed_requirements")))),
        ("Receipt issue count", receipt_check.get("issue_count")),
        ("Receipt receipt path", receipt_check.get("receipt_path")),
        ("Receipt json", receipt_check_outputs.get("json")),
        ("Receipt text", receipt_check_outputs.get("text")),
        ("Embedded receipt check", embedded_receipt_check.get("status")),
        ("Embedded receipt decision", embedded_receipt_check.get("decision")),
        ("Embedded receipt exit", embedded_receipt_check.get("exit_code")),
        ("Embedded receipt checker exit", embedded_receipt_check.get("checker_exit_code")),
        ("Embedded receipt sidecars", embedded_receipt_check.get("sidecar_status")),
        ("Embedded receipt issue count", embedded_receipt_check.get("issue_count")),
        ("Embedded receipt path exists", embedded_receipt_check.get("receipt_path_exists")),
        ("Embedded receipt json exists", embedded_receipt_check.get("receipt_check_json_exists")),
        ("Embedded receipt text exists", embedded_receipt_check.get("receipt_check_text_exists")),
        ("Embedded receipt output json", embedded_receipt_check_outputs.get("json")),
        ("Embedded receipt output text", embedded_receipt_check_outputs.get("text")),
        ("Handoff assurance", handoff_assurance.get("status")),
        ("Assurance decision", handoff_assurance.get("decision")),
        ("Assurance exit", handoff_assurance.get("exit_code")),
        ("Assurance checker exit", handoff_assurance.get("checker_exit_code")),
        ("Assurance embedded check", handoff_assurance.get("embedded_receipt_check_status")),
        ("Assurance sidecars", handoff_assurance.get("embedded_receipt_check_sidecar_status")),
        ("Assurance receipt schema", handoff_assurance.get("embedded_receipt_check_receipt_schema_version")),
        (
            "Assurance selected CI regressions",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count"
            ),
        ),
        (
            "Assurance selected CI reasons",
            _fmt_mapping(
                handoff_assurance.get(
                    "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts"
                )
            ),
        ),
        (
            "Assurance selected CI boundary plan",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Assurance CI regressions",
            handoff_assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "Assurance CI reasons",
            _fmt_mapping(
                handoff_assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts")
            ),
        ),
        (
            "Assurance CI boundary plan",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Assurance selected suite-design regressions",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count"
            ),
        ),
        (
            "Assurance suite-design regressions",
            handoff_assurance.get("embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Assurance ready suite-design regressions",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"
            ),
        ),
        (
            "Assurance ready CI boundary plan",
            handoff_assurance.get(
                "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
            ),
        ),
        (
            "Assurance ready CI reasons",
            _fmt_mapping(
                handoff_assurance.get(
                    "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"
                )
            ),
        ),
        (
            "Assurance comparison exclusions",
            ", ".join(_string_list(handoff_assurance.get("embedded_receipt_check_receipt_comparison_exclusion_reasons"))),
        ),
        ("Assurance output json exists", handoff_assurance.get("embedded_receipt_check_output_json_exists")),
        ("Assurance output text exists", handoff_assurance.get("embedded_receipt_check_output_text_exists")),
        ("Assurance issue count", handoff_assurance.get("issue_count")),
        ("Assurance json", handoff_assurance_outputs.get("json")),
        ("Assurance text", handoff_assurance_outputs.get("text")),
        ("Batch", summary.get("next_batch_command_available")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale seed handoff'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale seed handoff'))}</h1><p>{_e(report.get('seed_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _command_section(report),
            _execution_section(execution),
            _artifact_section(report),
            _plan_section(report),
            _receipt_check_section(report),
            _embedded_receipt_check_section(report),
            _handoff_assurance_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale seed handoff.</footer>",
            "</body>",
            "</html>",
        ]
    )


def _plan_section(report: dict[str, Any]) -> str:
    plan = _dict(report.get("plan_report"))
    if not plan:
        return "<section><h2>Plan Report</h2><p>No plan report was loaded.</p></section>"
    dataset = _dict(plan.get("dataset"))
    batch = _dict(plan.get("batch"))
    rows = [
        ("Scale tier", dataset.get("scale_tier")),
        ("Source count", dataset.get("source_count")),
        ("Character count", dataset.get("char_count")),
        ("Quality status", dataset.get("quality_status")),
        ("Warning count", dataset.get("warning_count")),
        ("Variant count", len(_list_of_dicts(plan.get("variants")))),
        ("Batch baseline", batch.get("baseline")),
        ("Suite mode", _dict(plan.get("suite")).get("mode")),
        ("Suite name", _dict(plan.get("suite")).get("name")),
        ("Suite path", _dict(plan.get("suite")).get("path")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    next_batch = _display_command(report.get("next_batch_command"))
    extra = (
        f"<p><strong>Next batch command:</strong></p><pre>{_e(next_batch)}</pre>"
        if next_batch
        else "<p>No next batch command is available yet.</p>"
    )
    return f"<section><h2>Plan Report</h2><table>{body}</table>{extra}</section>"


def _command_section(report: dict[str, Any]) -> str:
    return f"<section><h2>Seed Command</h2><pre>{_e(report.get('command_text'))}</pre></section>"


def _execution_section(execution: dict[str, Any]) -> str:
    rows = [
        ("Status", execution.get("status")),
        ("Return code", execution.get("returncode")),
        ("Elapsed seconds", execution.get("elapsed_seconds")),
        ("Blocked reason", execution.get("blocked_reason")),
        ("Stdout tail", execution.get("stdout_tail")),
        ("Stderr tail", execution.get("stderr_tail")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return f"<section><h2>Execution</h2><table>{body}</table></section>"


def _artifact_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("artifact_rows")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('key'))}</td>"
            f"<td>{_e(row.get('exists'))}</td>"
            f"<td>{_e(row.get('count'))}</td>"
            f"<td>{_e(row.get('path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Plan Artifacts</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Key</th><th>Exists</th><th>Count</th><th>Path</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f8f3; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1180px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; width: 180px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'
