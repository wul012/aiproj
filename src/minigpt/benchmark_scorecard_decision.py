from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_json_payload,
)


def load_benchmark_scorecard_comparison(path: str | Path) -> dict[str, Any]:
    comparison_path = _resolve_comparison_path(Path(path))
    payload = json.loads(comparison_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("benchmark scorecard comparison must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(comparison_path)
    return payload


def build_benchmark_scorecard_decision(
    comparison_path: str | Path,
    *,
    min_rubric_score: float = 80.0,
    title: str = "MiniGPT benchmark scorecard promotion decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    comparison = load_benchmark_scorecard_comparison(comparison_path)
    runs = _list_of_dicts(comparison.get("runs"))
    if not runs:
        raise ValueError("comparison must contain at least one run")
    deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
    case_counts = _case_delta_counts(comparison)
    evaluations = [_evaluate_run(run, deltas.get(run.get("name"), {}), case_counts, min_rubric_score) for run in runs]
    candidates = [row for row in evaluations if not row.get("is_baseline") and not row.get("blockers")]
    clean_candidates = [row for row in candidates if not row.get("review_items")]
    selected = _select_candidate(clean_candidates or candidates)
    decision_status = _decision_status(selected)
    summary = _summary(comparison, evaluations, candidates, clean_candidates, selected, decision_status)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "comparison_path": str(comparison.get("_source_path")),
        "comparison_title": comparison.get("title"),
        "baseline_name": _dict(comparison.get("baseline")).get("name") or _dict(comparison.get("summary")).get("baseline_name"),
        "min_rubric_score": float(min_rubric_score),
        "decision_status": decision_status,
        "recommended_action": _recommended_action(decision_status),
        "selected_run": selected,
        "candidate_evaluations": evaluations,
        "summary": summary,
        "recommendations": _recommendations(decision_status, selected, evaluations, comparison),
    }


def write_benchmark_scorecard_decision_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_benchmark_scorecard_decision_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "is_baseline",
        "decision_relation",
        "overall_score",
        "rubric_avg_score",
        "overall_score_delta",
        "rubric_avg_score_delta",
        "generation_quality_total_flags",
        "generation_quality_total_flags_delta",
        "generation_quality_flag_relation",
        "case_regression_count",
        "case_improvement_count",
        "blockers",
        "review_items",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("candidate_evaluations")):
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_benchmark_scorecard_decision_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    selected = _dict(report.get("selected_run"))
    lines = [
        f"# {report.get('title', 'MiniGPT benchmark scorecard promotion decision')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Decision: `{report.get('decision_status')}`",
        f"- Action: `{report.get('recommended_action')}`",
        f"- Baseline: `{report.get('baseline_name')}`",
        f"- Selected run: `{selected.get('name')}`",
        f"- Selected rubric: `{selected.get('rubric_avg_score')}`",
        f"- Selected gen flags delta: `{_fmt_signed(selected.get('generation_quality_total_flags_delta'))}`",
        f"- Candidates: `{summary.get('candidate_count')}`",
        f"- Clean candidates: `{summary.get('clean_candidate_count')}`",
        f"- Review candidates: `{summary.get('review_candidate_count')}`",
        f"- Blocked candidates: `{summary.get('blocked_candidate_count')}`",
        "",
        "## Candidate Evaluations",
        "",
        "| Run | Relation | Rubric | Overall Delta | Flag Delta | Case Regressions | Blockers | Review Items |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("candidate_evaluations")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(row.get("decision_relation")),
                    _md(row.get("rubric_avg_score")),
                    _md(_fmt_signed(row.get("overall_score_delta"))),
                    _md(_fmt_signed(row.get("generation_quality_total_flags_delta"))),
                    _md(row.get("case_regression_count")),
                    _md("; ".join(_string_list(row.get("blockers")))),
                    _md("; ".join(_string_list(row.get("review_items")))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_benchmark_scorecard_decision_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_decision_markdown(report), encoding="utf-8")


def render_benchmark_scorecard_decision_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    selected = _dict(report.get("selected_run"))
    stats = [
        ("Decision", report.get("decision_status")),
        ("Action", report.get("recommended_action")),
        ("Baseline", report.get("baseline_name")),
        ("Selected", selected.get("name")),
        ("Selected rubric", selected.get("rubric_avg_score")),
        ("Flag delta", _fmt_signed(selected.get("generation_quality_total_flags_delta"))),
        ("Clean", summary.get("clean_candidate_count")),
        ("Review", summary.get("review_candidate_count")),
        ("Blocked", summary.get("blocked_candidate_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT benchmark scorecard promotion decision'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT benchmark scorecard promotion decision'))}</h1><p>{_e(report.get('comparison_title'))} · {_e(report.get('comparison_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _candidate_table(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT benchmark scorecard promotion decision.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_benchmark_scorecard_decision_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_decision_html(report), encoding="utf-8")


def write_benchmark_scorecard_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "benchmark_scorecard_decision.json",
        "csv": root / "benchmark_scorecard_decision.csv",
        "markdown": root / "benchmark_scorecard_decision.md",
        "html": root / "benchmark_scorecard_decision.html",
    }
    write_benchmark_scorecard_decision_json(report, paths["json"])
    write_benchmark_scorecard_decision_csv(report, paths["csv"])
    write_benchmark_scorecard_decision_markdown(report, paths["markdown"])
    write_benchmark_scorecard_decision_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_comparison_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "benchmark_scorecard_comparison.json",
                path / "benchmark-scorecard-comparison" / "benchmark_scorecard_comparison.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _case_delta_counts(comparison: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in _list_of_dicts(comparison.get("case_deltas")):
        if row.get("is_baseline"):
            continue
        name = str(row.get("run_name") or "")
        bucket = counts.setdefault(name, {"regressed": 0, "improved": 0})
        if row.get("relation") == "regressed":
            bucket["regressed"] += 1
        elif row.get("relation") == "improved":
            bucket["improved"] += 1
    return counts


def _evaluate_run(
    run: dict[str, Any],
    delta: dict[str, Any],
    case_counts: dict[str, dict[str, int]],
    min_rubric_score: float,
) -> dict[str, Any]:
    name = run.get("name")
    is_baseline = bool(delta.get("is_baseline"))
    blockers: list[str] = []
    review_items: list[str] = []
    rubric_score = _number(run.get("rubric_avg_score"))
    if is_baseline:
        blockers.append("baseline run is not a promotion candidate")
    if rubric_score is None:
        blockers.append("rubric_avg_score is missing")
    elif rubric_score < float(min_rubric_score):
        blockers.append(f"rubric_avg_score below {float(min_rubric_score):.1f}")
    if delta.get("rubric_relation") == "regressed":
        blockers.append("rubric score regressed from baseline")
    if delta.get("overall_relation") == "regressed":
        blockers.append("overall score regressed from baseline")
    if _int(delta.get("rubric_fail_count_delta")) > 0:
        review_items.append("rubric fail count increased")
    flag_delta = _int_or_none(delta.get("generation_quality_total_flags_delta"))
    if flag_delta is not None and flag_delta > 0:
        review_items.append(f"generation-quality flags increased by {flag_delta}")
    if delta.get("generation_quality_dominant_flag_changed"):
        review_items.append("dominant generation-quality flag changed")
    if delta.get("generation_quality_worst_case_changed"):
        review_items.append("worst generation-quality case changed")
    counts = case_counts.get(str(name), {"regressed": 0, "improved": 0})
    if counts.get("regressed"):
        review_items.append(f"{counts.get('regressed')} case regression(s)")
    relation = "baseline" if is_baseline else "blocked" if blockers else "review" if review_items else "promote"
    return {
        "name": name,
        "source_path": run.get("source_path"),
        "run_dir": run.get("run_dir"),
        "is_baseline": is_baseline,
        "decision_relation": relation,
        "overall_score": _number(run.get("overall_score")),
        "rubric_avg_score": rubric_score,
        "overall_score_delta": _number(delta.get("overall_score_delta")),
        "rubric_avg_score_delta": _number(delta.get("rubric_avg_score_delta")),
        "generation_quality_total_flags": _int_or_none(run.get("generation_quality_total_flags")),
        "generation_quality_total_flags_delta": flag_delta,
        "generation_quality_flag_relation": delta.get("generation_quality_flag_relation"),
        "generation_quality_dominant_flag": run.get("generation_quality_dominant_flag"),
        "generation_quality_worst_case": run.get("generation_quality_worst_case"),
        "case_regression_count": int(counts.get("regressed") or 0),
        "case_improvement_count": int(counts.get("improved") or 0),
        "blockers": blockers,
        "review_items": review_items,
    }


def _select_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    return dict(
        max(
            candidates,
            key=lambda row: (
                _number(row.get("rubric_avg_score")) or 0.0,
                _number(row.get("overall_score")) or 0.0,
                -(_int_or_none(row.get("generation_quality_total_flags")) or 0),
                str(row.get("name") or ""),
            ),
        )
    )


def _decision_status(selected: dict[str, Any] | None) -> str:
    if not selected:
        return "blocked"
    if selected.get("review_items"):
        return "review"
    return "promote"


def _recommended_action(status: str) -> str:
    return {
        "promote": "promote_selected_scorecard",
        "review": "review_generation_flags_and_case_deltas",
        "blocked": "keep_baseline_or_fix_candidate",
    }.get(status, "review_generation_flags_and_case_deltas")


def _summary(
    comparison: dict[str, Any],
    evaluations: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    clean_candidates: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    decision_status: str,
) -> dict[str, Any]:
    nonbaseline = [row for row in evaluations if not row.get("is_baseline")]
    comparison_summary = _dict(comparison.get("summary"))
    return {
        "decision_status": decision_status,
        "comparison_scorecard_count": comparison.get("scorecard_count"),
        "candidate_count": len(candidates),
        "clean_candidate_count": len(clean_candidates),
        "review_candidate_count": sum(1 for row in nonbaseline if row.get("review_items") and not row.get("blockers")),
        "blocked_candidate_count": sum(1 for row in nonbaseline if row.get("blockers")),
        "selected_name": None if selected is None else selected.get("name"),
        "selected_relation": None if selected is None else selected.get("decision_relation"),
        "selected_rubric_avg_score": None if selected is None else selected.get("rubric_avg_score"),
        "selected_generation_quality_total_flags_delta": None if selected is None else selected.get("generation_quality_total_flags_delta"),
        "comparison_case_regression_count": comparison_summary.get("case_regression_count"),
        "comparison_generation_quality_flag_regression_count": comparison_summary.get("generation_quality_flag_regression_count"),
        "comparison_generation_quality_dominant_flag_change_count": comparison_summary.get("generation_quality_dominant_flag_change_count"),
    }


def _recommendations(
    decision_status: str,
    selected: dict[str, Any] | None,
    evaluations: list[dict[str, Any]],
    comparison: dict[str, Any],
) -> list[str]:
    recommendations: list[str] = []
    if decision_status == "promote":
        recommendations.append("Promote the selected scorecard only as benchmark evidence, not as proof of broad model quality.")
    elif decision_status == "review":
        recommendations.append("Review generation-quality flags and case deltas before promoting the selected scorecard.")
    else:
        recommendations.append("Keep the baseline or fix candidate scorecard regressions before promotion.")
    if selected and selected.get("review_items"):
        recommendations.append("Selected review item(s): " + "; ".join(_string_list(selected.get("review_items"))) + ".")
    if any(row.get("blockers") for row in evaluations if not row.get("is_baseline")):
        recommendations.append("Blocked candidates should stay in the comparison as evidence for why they were not promoted.")
    summary = _dict(comparison.get("summary"))
    if _int(summary.get("generation_quality_flag_regression_count")):
        recommendations.append("At least one compared scorecard increased generation-quality flags; inspect raw generation-quality reports.")
    if _int(summary.get("case_regression_count")):
        recommendations.append("Case regressions are present; verify whether they are wording drift or true task failures.")
    return recommendations


def _candidate_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("candidate_evaluations")):
        relation = str(row.get("decision_relation") or "missing")
        rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('name'))}</strong><br><span>{_e(row.get('run_dir') or row.get('source_path'))}</span></td>"
            f"<td><span class=\"pill {_relation_class(relation)}\">{_e(relation)}</span></td>"
            f"<td>{_e(_fmt(row.get('rubric_avg_score')))}<br><span>{_e(_fmt_signed(row.get('rubric_avg_score_delta')))}</span></td>"
            f"<td>{_e(_fmt(row.get('overall_score')))}<br><span>{_e(_fmt_signed(row.get('overall_score_delta')))}</span></td>"
            f"<td>{_e(_fmt(row.get('generation_quality_total_flags')))}<br><span>{_e(_fmt_signed(row.get('generation_quality_total_flags_delta')))}</span></td>"
            f"<td>{_e(row.get('case_regression_count'))} regressed / {_e(row.get('case_improvement_count'))} improved</td>"
            f"<td>{_e('; '.join(_string_list(row.get('blockers'))))}</td>"
            f"<td>{_e('; '.join(_string_list(row.get('review_items'))))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Candidate Evaluations</h2><table><thead><tr>'
        "<th>Run</th><th>Relation</th><th>Rubric</th><th>Overall</th><th>Gen Flags</th><th>Cases</th><th>Blockers</th><th>Review Items</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>'


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee8; --page:#f7f7f2; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; --blue:#2563eb; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:18px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:1120px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:74px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
.pill.base { background:var(--blue); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e(_fmt(value))}</div></div>'


def _relation_class(relation: str) -> str:
    if relation == "promote":
        return "pass"
    if relation in {"review", "missing"}:
        return "warn"
    if relation == "baseline":
        return "base"
    return "fail"


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_signed(value: Any) -> str:
    if value is None:
        return "missing"
    number = float(value)
    return f"{number:+.5g}"
