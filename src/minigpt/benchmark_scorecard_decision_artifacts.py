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
    write_json_payload,
)

__all__ = [
    "render_benchmark_scorecard_decision_html",
    "render_benchmark_scorecard_decision_markdown",
    "write_benchmark_scorecard_decision_csv",
    "write_benchmark_scorecard_decision_html",
    "write_benchmark_scorecard_decision_json",
    "write_benchmark_scorecard_decision_markdown",
    "write_benchmark_scorecard_decision_outputs",
]

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
    items_html = "".join(f"<li>{_e(item)}</li>" for item in values)
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>{items_html}</ul></section>'


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
