from __future__ import annotations

import html
from typing import Any


def render_benchmark_scorecard_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    lines = [
        f"# {report.get('title', 'MiniGPT benchmark scorecard comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Scorecards: `{report.get('scorecard_count')}`",
        f"- Baseline: `{baseline.get('name')}`",
        f"- Best overall: `{_pick(_dict(report.get('best_by_overall_score')), 'name') or 'missing'}`",
        f"- Best rubric: `{_pick(_dict(report.get('best_by_rubric_avg_score')), 'name') or 'missing'}`",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Improved overall | {_md(summary.get('improved_overall_count'))} |",
        f"| Regressed overall | {_md(summary.get('regressed_overall_count'))} |",
        f"| Improved rubric | {_md(summary.get('improved_rubric_count'))} |",
        f"| Regressed rubric | {_md(summary.get('regressed_rubric_count'))} |",
        f"| Generation flag improvements | {_md(summary.get('generation_quality_flag_improvement_count'))} |",
        f"| Generation flag regressions | {_md(summary.get('generation_quality_flag_regression_count'))} |",
        f"| Baseline dominant generation flag | {_md(summary.get('baseline_generation_quality_dominant_flag'))} |",
        f"| Case regressions | {_md(summary.get('case_regression_count'))} |",
        f"| Case improvements | {_md(summary.get('case_improvement_count'))} |",
        f"| Weakest regression case | {_md(summary.get('weakest_case_regression'))} |",
        "",
        "## Runs",
        "",
        "| Run | Overall | Rubric | Gen Flags | Dominant Flag | Case Count | Weakest Case | Relation | Explanation |",
        "| --- | ---: | ---: | ---: | --- | ---: | --- | --- | --- |",
    ]
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("name"), {})
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(run.get("name")),
                    _md(f"{_fmt(run.get('overall_score'))} ({_fmt_signed(delta.get('overall_score_delta'))})"),
                    _md(f"{_fmt(run.get('rubric_avg_score'))} ({_fmt_signed(delta.get('rubric_avg_score_delta'))})"),
                    _md(f"{_fmt(run.get('generation_quality_total_flags'))} ({_fmt_signed(delta.get('generation_quality_total_flags_delta'))})"),
                    _md(run.get("generation_quality_dominant_flag")),
                    _md(run.get("case_count")),
                    _md(f"{run.get('weakest_rubric_case')}:{_fmt(run.get('weakest_rubric_score'))}"),
                    _md(delta.get("rubric_relation")),
                    _md(delta.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Case Deltas",
            "",
            "| Case | Run | Task | Rubric Delta | Relation | Missing Terms Delta | Failed Checks Delta | Explanation |",
            "| --- | --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in _list_of_dicts(report.get("case_deltas")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("case")),
                    _md(row.get("run_name")),
                    _md(f"{row.get('task_type')}/{row.get('difficulty')}"),
                    _md(_fmt_signed(row.get("rubric_score_delta"))),
                    _md(row.get("relation")),
                    _md(_terms_delta(row, "missing_terms")),
                    _md(_terms_delta(row, "failed_checks")),
                    _md(row.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(_markdown_group_section("Task Type Deltas", report.get("task_type_deltas")))
    lines.extend(_markdown_group_section("Difficulty Deltas", report.get("difficulty_deltas")))
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def render_benchmark_scorecard_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    stats = [
        ("Baseline", baseline.get("name")),
        ("Scorecards", report.get("scorecard_count")),
        ("Best overall", _pick(_dict(report.get("best_by_overall_score")), "name")),
        ("Best rubric", _pick(_dict(report.get("best_by_rubric_avg_score")), "name")),
        ("Rubric regressions", summary.get("regressed_rubric_count")),
        ("Generation flag regressions", summary.get("generation_quality_flag_regression_count")),
        ("Baseline dominant flag", summary.get("baseline_generation_quality_dominant_flag")),
        ("Case regressions", summary.get("case_regression_count")),
        ("Weakest case", summary.get("weakest_case_regression")),
        ("Generated", report.get("generated_at")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT benchmark scorecard comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT benchmark scorecard comparison'))}</h1><p>Baseline: {_e(baseline.get('name'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _run_section(report),
            _case_delta_section(report),
            _group_delta_section("Task Type Deltas", report.get("task_type_deltas")),
            _group_delta_section("Difficulty Deltas", report.get("difficulty_deltas")),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT benchmark scorecard comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def _run_section(report: dict[str, Any]) -> str:
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    rows = []
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("name"), {})
        relation = str(delta.get("rubric_relation") or "missing")
        rows.append(
            "<tr>"
            f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('run_dir') or run.get('source_path'))}</span></td>"
            f"<td>{_e(_fmt(run.get('overall_score')))}<br><span>{_e(_fmt_signed(delta.get('overall_score_delta')))}</span></td>"
            f"<td><span class=\"pill {_relation_class(relation)}\">{_e(relation)}</span><br><span>{_e(_fmt(run.get('rubric_avg_score')))} ({_e(_fmt_signed(delta.get('rubric_avg_score_delta')))})</span></td>"
            f"<td><span class=\"pill {_relation_class(str(delta.get('generation_quality_flag_relation') or 'missing'))}\">{_e(delta.get('generation_quality_flag_relation'))}</span><br><span>{_e(_fmt(run.get('generation_quality_total_flags')))} ({_e(_fmt_signed(delta.get('generation_quality_total_flags_delta')))})</span></td>"
            f"<td>{_e(run.get('generation_quality_dominant_flag'))}<br><span>{_e(run.get('generation_quality_worst_case'))}</span></td>"
            f"<td>{_e(run.get('rubric_pass_count'))} pass / {_e(run.get('rubric_warn_count'))} warn / {_e(run.get('rubric_fail_count'))} fail</td>"
            f"<td>{_e(run.get('weakest_rubric_case'))}<br><span>{_e(_fmt(run.get('weakest_rubric_score')))}</span></td>"
            f"<td>{_e(delta.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Runs</h2><table><thead><tr>'
        "<th>Run</th><th>Overall</th><th>Rubric</th><th>Gen Flags</th><th>Dominant Flag</th><th>Rubric Counts</th><th>Weakest Case</th><th>Explanation</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _case_delta_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("case_deltas")):
        relation = str(row.get("relation") or "missing")
        rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('case'))}</strong><br><span>{_e(row.get('task_type'))} / {_e(row.get('difficulty'))}</span></td>"
            f"<td>{_e(row.get('run_name'))}</td>"
            f"<td><span class=\"pill {_relation_class(relation)}\">{_e(relation)}</span><br><span>{_e(_fmt_signed(row.get('rubric_score_delta')))}</span></td>"
            f"<td>{_e(_terms_delta(row, 'missing_terms'))}</td>"
            f"<td>{_e(_terms_delta(row, 'failed_checks'))}</td>"
            f"<td>{_e(row.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Case Deltas</h2><table><thead><tr>'
        "<th>Case</th><th>Run</th><th>Relation</th><th>Missing Terms</th><th>Failed Checks</th><th>Explanation</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _group_delta_section(title: str, rows: Any) -> str:
    html_rows = []
    for row in _list_of_dicts(rows):
        relation = str(row.get("relation") or "missing")
        html_rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('key'))}</strong><br><span>{_e(row.get('group_by'))}</span></td>"
            f"<td>{_e(row.get('run_name'))}</td>"
            f"<td><span class=\"pill {_relation_class(relation)}\">{_e(relation)}</span></td>"
            f"<td>{_e(_fmt(row.get('score')))}<br><span>{_e(_fmt_signed(row.get('score_delta')))}</span></td>"
            f"<td>{_e(_fmt(row.get('rubric_score')))}<br><span>{_e(_fmt_signed(row.get('rubric_score_delta')))}</span></td>"
            f"<td>{_e(row.get('case_count'))}</td>"
            f"<td>{_e(row.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        f'<section class="panel"><h2>{_e(title)}</h2><table><thead><tr>'
        "<th>Group</th><th>Run</th><th>Relation</th><th>Score</th><th>Rubric</th><th>Cases</th><th>Explanation</th>"
        "</tr></thead><tbody>"
        + "".join(html_rows)
        + "</tbody></table></section>"
    )


def _markdown_group_section(title: str, rows: Any) -> list[str]:
    lines = [
        "",
        f"## {title}",
        "",
        "| Group | Run | Score Delta | Rubric Delta | Relation | Explanation |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in _list_of_dicts(rows):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("key")),
                    _md(row.get("run_name")),
                    _md(_fmt_signed(row.get("score_delta"))),
                    _md(_fmt_signed(row.get("rubric_score_delta"))),
                    _md(row.get("relation")),
                    _md(row.get("explanation")),
                ]
            )
            + " |"
        )
    return lines


def _terms_delta(row: dict[str, Any], suffix: str) -> str:
    added = _string_list(row.get(f"added_{suffix}"))
    removed = _string_list(row.get(f"removed_{suffix}"))
    parts = []
    if added:
        parts.append("added: " + ", ".join(added))
    if removed:
        parts.append("removed: " + ", ".join(removed))
    return "; ".join(parts) if parts else "none"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(value: dict[str, Any], key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]


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


def _md(value: Any) -> str:
    return ("missing" if value is None else str(value)).replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _stat(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e(_fmt(value))}</div></div>'


def _relation_class(relation: str) -> str:
    if relation == "improved":
        return "pass"
    if relation == "regressed":
        return "fail"
    if relation == "baseline":
        return "base"
    return "warn"


def _list_section(title: str, values: Any) -> str:
    items = _string_list(values) or ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


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
table { width:100%; border-collapse:collapse; min-width:1020px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:68px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
.pill.base { background:var(--blue); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


__all__ = [
    "render_benchmark_scorecard_comparison_html",
    "render_benchmark_scorecard_comparison_markdown",
]
