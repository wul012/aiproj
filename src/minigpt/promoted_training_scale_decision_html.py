from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    string_list as _string_list,
)


def render_promoted_training_scale_decision_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    selected = _dict(report.get("selected_baseline"))
    stats = [
        ("Decision", report.get("decision_status")),
        ("Selected", selected.get("name")),
        ("Gate", selected.get("gate_status")),
        ("Batch", selected.get("batch_status")),
        ("Score", selected.get("readiness_score")),
        ("Suite path", summary.get("selected_suite_path")),
        ("Require suite consistency", summary.get("require_suite_consistency")),
        ("Selected handoff suite", summary.get("selected_handoff_suite_consistency")),
        ("Selected handoff mismatch", summary.get("selected_handoff_suite_mismatch_count")),
        ("Selected handoff suite path", summary.get("selected_handoff_selected_suite_path")),
        ("Selected clean required", summary.get("selected_handoff_require_clean_batch_review")),
        ("Selected clean batch", summary.get("selected_handoff_clean_batch_review_status")),
        ("Selected CI regressions", summary.get("selected_handoff_batch_maturity_ci_regression_count")),
        ("Selected CI reasons", _fmt_mapping(summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts"))),
        (
            "Selected CI boundary plan",
            summary.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Selected suite-design regressions",
            summary.get("selected_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Selected suite-design names",
            ", ".join(_string_list(summary.get("selected_handoff_batch_maturity_suite_design_regression_names"))),
        ),
        ("Selected selected CI regressions", summary.get("selected_handoff_selected_batch_maturity_ci_regression_count")),
        (
            "Selected selected CI reasons",
            _fmt_mapping(summary.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Selected selected CI boundary plan",
            summary.get("selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Selected selected suite-design regressions",
            summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Selected selected suite-design names",
            ", ".join(
                _string_list(summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_names"))
            ),
        ),
        ("Handoff clean required", summary.get("handoff_require_clean_batch_review_count")),
        ("Handoff clean", summary.get("handoff_clean_batch_review_count")),
        ("Handoff unclean", summary.get("handoff_unclean_batch_review_count")),
        ("Handoff CI regressions", summary.get("handoff_batch_maturity_ci_regression_count")),
        ("Handoff CI reasons", _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))),
        (
            "Handoff CI boundary plan",
            summary.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        ("Handoff selected CI regressions", summary.get("handoff_selected_batch_maturity_ci_regression_total")),
        (
            "Handoff selected CI reasons",
            _fmt_mapping(summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Handoff selected CI boundary plan",
            summary.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        ("Handoff suite-design regressions", summary.get("handoff_batch_maturity_suite_design_regression_count")),
        (
            "Handoff selected suite-design regressions",
            summary.get("handoff_selected_batch_maturity_suite_design_regression_total"),
        ),
        (
            "Suite-design names",
            ", ".join(_string_list(summary.get("handoff_batch_maturity_suite_design_regression_names"))),
        ),
        (
            "Selected suite-design names",
            ", ".join(_string_list(summary.get("handoff_selected_batch_maturity_suite_design_regression_names"))),
        ),
        ("Ready clean-required", summary.get("comparison_ready_handoff_require_clean_batch_review_count")),
        ("Ready clean batch", summary.get("comparison_ready_handoff_clean_batch_review_count")),
        ("Ready unclean batch", summary.get("comparison_ready_handoff_unclean_batch_review_count")),
        ("Ready CI regressions", summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")),
        (
            "Ready CI reasons",
            _fmt_mapping(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Ready CI boundary plan",
            summary.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "Ready selected CI regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_total"),
        ),
        (
            "Ready selected CI reasons",
            _fmt_mapping(summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")),
        ),
        (
            "Ready selected CI boundary plan",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "Ready suite-design regressions",
            summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "Ready selected suite-design regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"),
        ),
        (
            "Ready suite-design names",
            ", ".join(_string_list(summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names"))),
        ),
        (
            "Ready selected suite-design names",
            ", ".join(
                _string_list(summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names"))
            ),
        ),
        ("Selected handoff batch", summary.get("selected_handoff_selected_batch_review_status")),
        ("Selected batch blockers", summary.get("selected_handoff_selected_batch_comparison_blocker_action_count")),
        ("Ready batch reviews", summary.get("comparison_ready_handoff_selected_batch_review_count")),
        ("Ready batch blockers", summary.get("comparison_ready_handoff_selected_batch_blocker_count")),
        ("Handoff suite consistent", summary.get("handoff_suite_consistent_count")),
        ("Handoff suite mismatches", summary.get("handoff_suite_mismatch_total")),
        ("Candidates", summary.get("candidate_count")),
        ("Rejected", summary.get("rejected_count")),
        ("Suite", summary.get("suite_consistency")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale baseline decision'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale baseline decision'))}</h1><p>{_e(report.get('comparison_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _rejected_table(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale baseline decision.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_promoted_training_scale_decision_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_decision_html(report), encoding="utf-8")


def _rejected_table(report: dict[str, Any]) -> str:
    rows = []
    for run in _list_of_dicts(report.get("rejected_runs")):
        rows.append(
            "<tr>"
            f"<td>{_e(run.get('name'))}</td>"
            f"<td>{_e(run.get('gate_status'))}</td>"
            f"<td>{_e(run.get('batch_status'))}</td>"
            f"<td>{_e(run.get('readiness_score'))}</td>"
            f"<td>{_e('; '.join(_string_list(run.get('reasons'))))}</td>"
            "</tr>"
        )
    if not rows:
        return "<section><h2>Rejected Runs</h2><p>No rejected runs.</p></section>"
    return (
        '<section><h2>Rejected Runs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Run</th><th>Gate</th><th>Batch</th><th>Score</th><th>Reasons</th></tr></thead>"
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
header, section, footer { max-width: 1160px; margin: 0 auto 18px; }
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
th { color: #435047; font-size: 12px; text-transform: uppercase; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


__all__ = [
    "render_promoted_training_scale_decision_html",
    "write_promoted_training_scale_decision_html",
]
