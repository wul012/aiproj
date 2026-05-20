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


def write_promoted_training_scale_seed_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_seed_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seed = _dict(report.get("baseline_seed"))
    plan = _dict(report.get("next_plan"))
    summary = _dict(report.get("summary"))
    fieldnames = [
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
        "selected_handoff_batch_maturity_ci_regression_names",
        "selected_handoff_selected_batch_maturity_ci_regression_count",
        "selected_comparison_exclusion_reasons",
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
    ]
    write_csv_row(
        {
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
            "selected_handoff_batch_maturity_ci_regression_names": "; ".join(
                _string_list(summary.get("selected_handoff_batch_maturity_ci_regression_names"))
            ),
            "selected_handoff_selected_batch_maturity_ci_regression_count": summary.get(
                "selected_handoff_selected_batch_maturity_ci_regression_count"
            ),
            "selected_comparison_exclusion_reasons": "; ".join(
                _string_list(summary.get("selected_comparison_exclusion_reasons"))
            ),
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
        },
        out_path,
        fieldnames,
    )


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


def render_promoted_training_scale_seed_html(report: dict[str, Any]) -> str:
    seed = _dict(report.get("baseline_seed"))
    plan = _dict(report.get("next_plan"))
    summary = _dict(report.get("summary"))
    stats = [
        ("Status", report.get("seed_status")),
        ("Baseline", seed.get("selected_name")),
        ("Decision", seed.get("decision_status")),
        ("Gate", seed.get("gate_status")),
        ("Batch", seed.get("batch_status")),
        ("Score", seed.get("readiness_score")),
        ("Sources", summary.get("source_count")),
        ("Missing", summary.get("missing_source_count")),
        ("Selected handoff suite", summary.get("selected_handoff_suite_consistency")),
        ("Selected handoff mismatch", summary.get("selected_handoff_suite_mismatch_count")),
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
        ("Handoff suite mismatches", summary.get("handoff_suite_mismatch_total")),
        ("Next suite", summary.get("next_suite_path")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale next-cycle seed'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale next-cycle seed'))}</h1><p>{_e(report.get('decision_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _baseline_section(seed),
            _command_section(plan),
            _source_table(plan),
            _list_section("Blockers", report.get("blockers")),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale next-cycle seed.</footer>",
            "</body>",
            "</html>",
        ]
    )


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


def _baseline_section(seed: dict[str, Any]) -> str:
    rows = [
        ("Selected baseline", seed.get("selected_name")),
        ("Decision status", seed.get("decision_status")),
        ("Training scale run", seed.get("training_scale_run_path")),
        ("Run exists", seed.get("training_scale_run_exists")),
        ("Comparison", seed.get("comparison_path")),
    ]
    guard = _dict(seed.get("handoff_suite_guard"))
    rows.extend(
        [
            ("Selected handoff strict", guard.get("selected_handoff_require_suite_consistency")),
            ("Selected handoff suite", guard.get("selected_handoff_suite_consistency")),
            ("Selected handoff mismatch", guard.get("selected_handoff_suite_mismatch_count")),
            ("Selected handoff suite path", guard.get("selected_handoff_selected_suite_path")),
        ]
    )
    clean_review = _dict(seed.get("handoff_clean_batch_review"))
    rows.extend(
        [
            ("Selected clean required", clean_review.get("selected_handoff_require_clean_batch_review")),
            ("Selected clean batch", clean_review.get("selected_handoff_clean_batch_review_status")),
            ("Selected CI regressions", clean_review.get("selected_handoff_batch_maturity_ci_regression_count")),
            (
                "Selected selected CI regressions",
                clean_review.get("selected_handoff_selected_batch_maturity_ci_regression_count"),
            ),
            (
                "Selected comparison exclusions",
                ", ".join(_string_list(clean_review.get("selected_comparison_exclusion_reasons"))),
            ),
            ("Handoff clean required", clean_review.get("handoff_require_clean_batch_review_count")),
            ("Handoff clean", clean_review.get("handoff_clean_batch_review_count")),
            ("Handoff unclean", clean_review.get("handoff_unclean_batch_review_count")),
            ("Handoff CI regressions", clean_review.get("handoff_batch_maturity_ci_regression_count")),
            (
                "Handoff CI-regressed names",
                ", ".join(_string_list(clean_review.get("handoff_batch_maturity_ci_regression_names"))),
            ),
            (
                "Comparison exclusions",
                ", ".join(_string_list(clean_review.get("comparison_exclusion_reasons"))),
            ),
            (
                "Comparison-ready clean-required",
                clean_review.get("comparison_ready_handoff_require_clean_batch_review_count"),
            ),
            ("Comparison-ready clean", clean_review.get("comparison_ready_handoff_clean_batch_review_count")),
            ("Comparison-ready unclean", clean_review.get("comparison_ready_handoff_unclean_batch_review_count")),
            (
                "Comparison-ready CI regressions",
                clean_review.get("comparison_ready_handoff_batch_maturity_ci_regression_count"),
            ),
        ]
    )
    batch_review = _dict(seed.get("handoff_batch_review"))
    rows.extend(
        [
            ("Selected handoff batch review", batch_review.get("selected_handoff_selected_batch_review_status")),
            (
                "Selected handoff batch review actions",
                batch_review.get("selected_handoff_selected_batch_comparison_review_action_count"),
            ),
            (
                "Selected handoff batch blocker actions",
                batch_review.get("selected_handoff_selected_batch_comparison_blocker_action_count"),
            ),
            (
                "Selected handoff batch blocker reasons",
                ", ".join(_string_list(batch_review.get("selected_handoff_batch_comparison_blocker_reasons"))),
            ),
            (
                "Comparison-ready batch blockers",
                batch_review.get("comparison_ready_handoff_selected_batch_blocker_count"),
            ),
        ]
    )
    summary = _dict(seed.get("selected_run_summary"))
    rows.extend(
        [
            ("Source scale tier", summary.get("scale_tier")),
            ("Source characters", summary.get("char_count")),
            ("Source variants", summary.get("variant_count")),
            ("Source suite mode", summary.get("suite_mode")),
            ("Source suite name", summary.get("suite_name")),
            ("Source suite path", summary.get("suite_path")),
        ]
    )
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return f"<section><h2>Baseline Seed</h2><table>{body}</table></section>"


def _command_section(plan: dict[str, Any]) -> str:
    command = str(plan.get("command_text") or "No command is available until blockers are fixed.")
    return f"<section><h2>Next Plan Command</h2><pre>{_e(command)}</pre></section>"


def _source_table(plan: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(plan.get("sources")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('path'))}</td>"
            f"<td>{_e(row.get('exists'))}</td>"
            f"<td>{_e(row.get('kind'))}</td>"
            "</tr>"
        )
    if not rows:
        return "<section><h2>Sources</h2><p>No sources provided.</p></section>"
    return (
        '<section><h2>Sources</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Source</th><th>Exists</th><th>Kind</th></tr></thead>"
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
th { color: #435047; font-size: 12px; text-transform: uppercase; width: 190px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


__all__ = [
    "render_promoted_training_scale_seed_html",
    "render_promoted_training_scale_seed_markdown",
    "write_promoted_training_scale_seed_csv",
    "write_promoted_training_scale_seed_html",
    "write_promoted_training_scale_seed_json",
    "write_promoted_training_scale_seed_markdown",
    "write_promoted_training_scale_seed_outputs",
]
