from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_decision_review import (
    append_decision_handoff_batch_recommendations,
    build_decision_handoff_review_summary,
)
from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    number_or_default,
    string_list as _string_list,
    utc_now,
    write_csv_row,
    write_json_payload,
)


GATE_ORDER = {"fail": 0, "warn": 1, "pass": 2}
BATCH_ORDER = {"skipped": 0, None: 0, "failed": 1, "planned": 2, "completed": 3}


def load_promoted_training_scale_comparison(path: str | Path) -> dict[str, Any]:
    comparison_path = _resolve_comparison_path(Path(path))
    payload = json.loads(comparison_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted training scale comparison must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(comparison_path)
    return payload


def build_promoted_training_scale_decision(
    comparison_path: str | Path,
    *,
    min_readiness: int = 70,
    require_gate_pass: bool = False,
    require_batch_completed: bool = True,
    require_suite_consistency: bool = False,
    title: str = "MiniGPT promoted training scale baseline decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    comparison = load_promoted_training_scale_comparison(comparison_path)
    comparison_file = Path(str(comparison.get("_source_path")))
    comparison_dir = comparison_file.parent
    comparison_summary = _dict(comparison.get("summary"))
    suite_reasons = _suite_consistency_reasons(comparison_summary, require_suite_consistency)
    promotions = _promotion_rows(comparison, comparison_dir)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    report_compared = comparison.get("comparison_status") == "compared"
    for row in promotions:
        reasons = ["comparison report is not compared"] if not report_compared else _rejection_reasons(
            row,
            min_readiness=min_readiness,
            require_gate_pass=require_gate_pass,
            require_batch_completed=require_batch_completed,
        )
        reasons.extend(suite_reasons)
        if reasons:
            rejected.append({**row, "reasons": reasons})
        else:
            candidates.append(row)
    selected = _select_candidate(candidates)
    decision_status = _decision_status(comparison, selected, rejected)
    summary = _summary(
        comparison_summary,
        promotions,
        candidates,
        rejected,
        selected,
        decision_status,
        require_suite_consistency=require_suite_consistency,
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "comparison_path": str(comparison_file),
        "comparison_status": comparison.get("comparison_status"),
        "promotions": promotions,
        "selected_baseline": selected,
        "rejected_runs": rejected,
        "summary": summary,
        "decision_status": decision_status,
        "recommendations": _recommendations(
            decision_status,
            selected,
            rejected,
            comparison_summary=comparison_summary,
            require_suite_consistency=require_suite_consistency,
        ),
    }


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


def _resolve_comparison_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "promoted_training_scale_comparison.json",
                path / "comparison" / "promoted_training_scale_comparison.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _promotion_rows(comparison: dict[str, Any], comparison_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for row in _list_of_dicts(comparison.get("promotions")):
        resolved_path = _resolve_path(row.get("training_scale_run_path"), comparison_dir)
        rows.append(
            {
                "name": row.get("name"),
                "promotion_status": row.get("promotion_status"),
                "promoted_for_comparison": bool(row.get("promoted_for_comparison")),
                "comparison_status": row.get("comparison_status") or comparison.get("comparison_status"),
                "gate_status": row.get("gate_status"),
                "batch_status": row.get("batch_status"),
                "readiness_score": row.get("readiness_score"),
                "suite_path": row.get("suite_path"),
                "handoff_require_suite_consistency": bool(row.get("handoff_require_suite_consistency")),
                "handoff_suite_consistency": row.get("handoff_suite_consistency"),
                "handoff_suite_mismatch_count": row.get("handoff_suite_mismatch_count"),
                "handoff_selected_suite_path": row.get("handoff_selected_suite_path"),
                "handoff_selected_batch_review_status": row.get("handoff_selected_batch_review_status"),
                "handoff_selected_batch_comparison_review_action_count": row.get(
                    "handoff_selected_batch_comparison_review_action_count"
                ),
                "handoff_selected_batch_comparison_blocker_action_count": row.get(
                    "handoff_selected_batch_comparison_blocker_action_count"
                ),
                "handoff_selected_batch_maturity_coverage_regression_count": row.get(
                    "handoff_selected_batch_maturity_coverage_regression_count"
                ),
                "handoff_batch_comparison_review_action_count": row.get("handoff_batch_comparison_review_action_count"),
                "handoff_batch_comparison_blocker_action_count": row.get(
                    "handoff_batch_comparison_blocker_action_count"
                ),
                "handoff_batch_comparison_blocker_reasons": _string_list(
                    row.get("handoff_batch_comparison_blocker_reasons")
                ),
                "training_scale_run_path": str(resolved_path),
                "source_path": row.get("source_path"),
            }
        )
    return rows


def _rejection_reasons(
    row: dict[str, Any],
    *,
    min_readiness: int,
    require_gate_pass: bool,
    require_batch_completed: bool,
) -> list[str]:
    reasons: list[str] = []
    if not row.get("promoted_for_comparison"):
        reasons.append("run was not promoted for comparison")
    if row.get("gate_status") == "fail":
        reasons.append("gate failed")
    elif require_gate_pass and row.get("gate_status") != "pass":
        reasons.append("gate is not pass")
    if require_batch_completed and row.get("batch_status") != "completed":
        reasons.append("batch did not complete")
    if _int(row.get("readiness_score")) < int(min_readiness):
        reasons.append(f"readiness_score below {int(min_readiness)}")
    if not row.get("training_scale_run_path") or not Path(str(row.get("training_scale_run_path"))).exists():
        reasons.append("training_scale_run.json is missing")
    return reasons


def _suite_consistency_reasons(comparison_summary: dict[str, Any], require_suite_consistency: bool) -> list[str]:
    if not require_suite_consistency:
        return []
    suite_consistency = str(comparison_summary.get("suite_consistency") or "")
    if suite_consistency == "consistent":
        return []
    return [f"benchmark suite consistency is {suite_consistency or 'missing'}"]


def _select_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    return dict(
        max(
            candidates,
            key=lambda row: (
                _int(row.get("readiness_score")),
                GATE_ORDER.get(str(row.get("gate_status")), -1),
                BATCH_ORDER.get(row.get("batch_status"), 0),
            ),
        )
    )


def _decision_status(
    comparison: dict[str, Any],
    selected: dict[str, Any] | None,
    rejected: list[dict[str, Any]],
) -> str:
    if _string_list(comparison.get("blockers")):
        return "blocked"
    if not selected:
        return "blocked"
    if selected.get("gate_status") == "warn" or rejected:
        return "review"
    return "accepted"


def _summary(
    comparison_summary: dict[str, Any],
    promotions: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    decision_status: str,
    *,
    require_suite_consistency: bool,
) -> dict[str, Any]:
    summary = {
        "decision_status": decision_status,
        "comparison_status": comparison_summary.get("comparison_status"),
        "promotion_index_status": comparison_summary.get("promotion_index_status"),
        "promotion_count": len(promotions),
        "candidate_count": len(candidates),
        "rejected_count": len(rejected),
        "selected_name": None if selected is None else selected.get("name"),
        "selected_gate_status": None if selected is None else selected.get("gate_status"),
        "selected_batch_status": None if selected is None else selected.get("batch_status"),
        "selected_readiness_score": None if selected is None else selected.get("readiness_score"),
        "selected_suite_path": None if selected is None else selected.get("suite_path"),
        "require_suite_consistency": bool(require_suite_consistency),
        "selected_promotion_status": None if selected is None else selected.get("promotion_status"),
        "suite_consistency": comparison_summary.get("suite_consistency"),
        "suite_paths": comparison_summary.get("suite_paths"),
        "suite_mismatch_count": comparison_summary.get("suite_mismatch_count"),
    }
    summary.update(build_decision_handoff_review_summary(comparison_summary, promotions, selected))
    return summary


def _recommendations(
    decision_status: str,
    selected: dict[str, Any] | None,
    rejected: list[dict[str, Any]],
    *,
    comparison_summary: dict[str, Any],
    require_suite_consistency: bool,
) -> list[str]:
    if decision_status == "accepted":
        recommendations = [
            "Use the selected promoted baseline for the next training-scale planning cycle.",
            "Keep the rejected promoted runs around as comparison evidence so the baseline choice stays explainable.",
        ]
        if selected and selected.get("suite_path"):
            recommendations.append(f"Carry `{selected.get('suite_path')}` into the next promoted seed so later comparisons stay suite-consistent.")
        if require_suite_consistency and comparison_summary.get("suite_consistency") != "consistent":
            recommendations.append("Fix benchmark suite consistency before using this promoted baseline as clean model-quality evidence.")
        elif comparison_summary.get("suite_consistency") == "mixed":
            recommendations.append("Promoted runs use different benchmark suites; treat this baseline as governance triage, not clean model-quality evidence.")
        append_decision_handoff_batch_recommendations(recommendations, selected, comparison_summary)
        return recommendations
    if decision_status == "review":
        recommendations = [
            "Review the remaining promoted runs before turning this baseline into the next run seed.",
            "Gate warnings can be accepted for review, but they should be justified before larger training.",
        ]
        if require_suite_consistency and comparison_summary.get("suite_consistency") != "consistent":
            recommendations.append("Fix benchmark suite consistency before using this promoted baseline as clean model-quality evidence.")
        elif comparison_summary.get("suite_consistency") == "mixed":
            recommendations.append("Promoted runs use different benchmark suites; treat this baseline as governance triage, not clean model-quality evidence.")
        append_decision_handoff_batch_recommendations(recommendations, selected, comparison_summary)
        return recommendations
    recommendations = [
        "Fix the promoted comparison or promote more runs before selecting a new baseline.",
    ]
    if require_suite_consistency and comparison_summary.get("suite_consistency") != "consistent":
        recommendations.append("Fix benchmark suite consistency before using this promoted baseline as clean model-quality evidence.")
    elif comparison_summary.get("suite_consistency") == "mixed":
        recommendations.append("Promoted runs use different benchmark suites; treat this baseline as governance triage, not clean model-quality evidence.")
    append_decision_handoff_batch_recommendations(recommendations, selected, comparison_summary)
    return recommendations


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


def _resolve_path(value: Any, base_dir: Path) -> Path:
    if value is None:
        return base_dir
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidates = [base_dir / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))
