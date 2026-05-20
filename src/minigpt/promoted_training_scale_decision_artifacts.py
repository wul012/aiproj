from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_csv_row,
    write_json_payload,
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
        "selected_handoff_batch_maturity_ci_regression_names",
        "selected_handoff_selected_batch_maturity_ci_regression_count",
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
        "handoff_selected_batch_maturity_ci_regression_total",
        "handoff_batch_maturity_ci_regression_names",
        "comparison_exclusion_reasons",
        "comparison_ready_handoff_require_clean_batch_review_count",
        "comparison_ready_handoff_clean_batch_review_count",
        "comparison_ready_handoff_unclean_batch_review_count",
        "comparison_ready_handoff_batch_maturity_ci_regression_count",
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total",
        "comparison_ready_handoff_batch_maturity_ci_regression_names",
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
            "selected_handoff_batch_maturity_ci_regression_names": "; ".join(
                _string_list(summary.get("selected_handoff_batch_maturity_ci_regression_names"))
            ),
            "selected_handoff_selected_batch_maturity_ci_regression_count": summary.get(
                "selected_handoff_selected_batch_maturity_ci_regression_count"
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
            "handoff_selected_batch_maturity_ci_regression_total": summary.get(
                "handoff_selected_batch_maturity_ci_regression_total"
            ),
            "handoff_batch_maturity_ci_regression_names": "; ".join(
                _string_list(summary.get("handoff_batch_maturity_ci_regression_names"))
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
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": summary.get(
                "comparison_ready_handoff_selected_batch_maturity_ci_regression_total"
            ),
            "comparison_ready_handoff_batch_maturity_ci_regression_names": "; ".join(
                _string_list(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_names"))
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
        f"- Selected handoff selected batch CI regressions: `{summary.get('selected_handoff_selected_batch_maturity_ci_regression_count')}`",
        f"- Selected comparison exclusion reasons: `{', '.join(_string_list(summary.get('selected_comparison_exclusion_reasons')))}`",
        f"- Handoff require clean batch review: `{summary.get('handoff_require_clean_batch_review_count')}`",
        f"- Handoff clean batch review: `{summary.get('handoff_clean_batch_review_count')}`",
        f"- Handoff unclean batch review: `{summary.get('handoff_unclean_batch_review_count')}`",
        f"- Handoff batch CI regressions: `{summary.get('handoff_batch_maturity_ci_regression_count')}`",
        f"- Handoff selected batch CI regressions: `{summary.get('handoff_selected_batch_maturity_ci_regression_total')}`",
        f"- Handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('handoff_batch_maturity_ci_regression_names')))}`",
        f"- Comparison exclusion reasons: `{', '.join(_string_list(summary.get('comparison_exclusion_reasons')))}`",
        f"- Comparison-ready clean-required handoffs: `{summary.get('comparison_ready_handoff_require_clean_batch_review_count')}`",
        f"- Comparison-ready clean handoffs: `{summary.get('comparison_ready_handoff_clean_batch_review_count')}`",
        f"- Comparison-ready unclean handoffs: `{summary.get('comparison_ready_handoff_unclean_batch_review_count')}`",
        f"- Comparison-ready handoff batch CI regressions: `{summary.get('comparison_ready_handoff_batch_maturity_ci_regression_count')}`",
        f"- Comparison-ready selected batch CI regressions: `{summary.get('comparison_ready_handoff_selected_batch_maturity_ci_regression_total')}`",
        f"- Comparison-ready handoff batch CI-regressed names: `{', '.join(_string_list(summary.get('comparison_ready_handoff_batch_maturity_ci_regression_names')))}`",
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
        ("Selected selected CI regressions", summary.get("selected_handoff_selected_batch_maturity_ci_regression_count")),
        ("Handoff clean required", summary.get("handoff_require_clean_batch_review_count")),
        ("Handoff clean", summary.get("handoff_clean_batch_review_count")),
        ("Handoff unclean", summary.get("handoff_unclean_batch_review_count")),
        ("Handoff CI regressions", summary.get("handoff_batch_maturity_ci_regression_count")),
        ("Handoff selected CI regressions", summary.get("handoff_selected_batch_maturity_ci_regression_total")),
        ("Ready clean-required", summary.get("comparison_ready_handoff_require_clean_batch_review_count")),
        ("Ready clean batch", summary.get("comparison_ready_handoff_clean_batch_review_count")),
        ("Ready unclean batch", summary.get("comparison_ready_handoff_unclean_batch_review_count")),
        ("Ready CI regressions", summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")),
        (
            "Ready selected CI regressions",
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_total"),
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
    "render_promoted_training_scale_decision_markdown",
    "write_promoted_training_scale_decision_csv",
    "write_promoted_training_scale_decision_html",
    "write_promoted_training_scale_decision_json",
    "write_promoted_training_scale_decision_markdown",
    "write_promoted_training_scale_decision_outputs",
]
