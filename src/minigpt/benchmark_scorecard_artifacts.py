from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any


def write_benchmark_scorecard_json(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(scorecard, ensure_ascii=False, indent=2), encoding="utf-8")


def write_benchmark_scorecard_csv(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["key", "title", "status", "score", "weight", "weighted_score", "evidence_path", "detail"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for component in _list_of_dicts(scorecard.get("components")):
            writer.writerow({field: _csv_value(component.get(field)) for field in fieldnames})


def write_benchmark_scorecard_drilldown_csv(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "group_by",
        "key",
        "status",
        "score",
        "case_count",
        "coverage_score",
        "rubric_score",
        "rubric_pass_count",
        "rubric_warn_count",
        "rubric_fail_count",
        "generation_quality_score",
        "pair_consistency_score",
        "pair_delta_stability_score",
        "generation_pass_count",
        "generation_warn_count",
        "generation_fail_count",
        "pair_equal_count",
        "pair_difference_count",
        "avg_abs_generated_delta",
        "max_abs_generated_delta",
        "avg_eval_chars",
        "cases",
    ]
    rows = []
    drilldowns = _dict(scorecard.get("drilldowns"))
    rows.extend(_list_of_dicts(drilldowns.get("task_type")))
    rows.extend(_list_of_dicts(drilldowns.get("difficulty")))
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def write_benchmark_scorecard_rubric_csv(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "task_type",
        "difficulty",
        "status",
        "score",
        "passed_checks",
        "total_checks",
        "matched_terms",
        "missing_terms",
        "failed_checks",
        "expected_behavior",
    ]
    rows = _list_of_dicts(_dict(scorecard.get("rubric_scores")).get("cases"))
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_benchmark_scorecard_markdown(scorecard: dict[str, Any]) -> str:
    summary = _dict(scorecard.get("summary"))
    drilldowns = _dict(scorecard.get("drilldowns"))
    rubric_scores = _dict(scorecard.get("rubric_scores"))
    lines = [
        f"# {scorecard.get('title', 'MiniGPT benchmark scorecard')}",
        "",
        f"- Generated: `{scorecard.get('generated_at')}`",
        f"- Run dir: `{scorecard.get('run_dir')}`",
        f"- Registry: `{scorecard.get('registry_path') or 'missing'}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Overall status", summary.get("overall_status")),
                ("Overall score", summary.get("overall_score")),
                ("Eval cases", summary.get("eval_suite_cases")),
                ("Generation quality", summary.get("generation_quality_status")),
                ("Generation flags", summary.get("generation_quality_total_flags")),
                ("Dominant generation flag", summary.get("generation_quality_dominant_flag")),
                ("Worst generation case", summary.get("generation_quality_worst_case")),
                ("Rubric correctness", summary.get("rubric_status")),
                ("Rubric average", summary.get("rubric_avg_score")),
                ("Weakest rubric case", summary.get("weakest_rubric_case")),
                ("Pair batch cases", summary.get("pair_batch_cases")),
                ("Pair generated differences", summary.get("pair_generated_differences")),
                ("Pair comparison mode", summary.get("pair_comparison_mode")),
                ("Task type groups", summary.get("task_type_group_count")),
                ("Weakest task type", summary.get("weakest_task_type")),
                ("Difficulty groups", summary.get("difficulty_group_count")),
                ("Weakest difficulty", summary.get("weakest_difficulty")),
            ]
        ),
        "",
        "## Components",
        "",
        "| Component | Status | Score | Weight | Detail |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for component in _list_of_dicts(scorecard.get("components")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(component.get("title")),
                    _md(component.get("status")),
                    _md(component.get("score")),
                    _md(component.get("weight")),
                    _md(component.get("detail")),
                ]
            )
            + " |"
        )
    lines.extend(_markdown_drilldown_table("Task Type Drilldown", drilldowns.get("task_type")))
    lines.extend(_markdown_drilldown_table("Difficulty Drilldown", drilldowns.get("difficulty")))
    lines.extend(_markdown_rubric_table(rubric_scores.get("cases")))
    lines.extend(["", "## Case Scores", "", "| Case | Task | Eval chars | Gen status | Rubric | Pair delta | Pair equal |", "| --- | --- | ---: | --- | ---: | ---: | --- |"])
    for case in _list_of_dicts(scorecard.get("case_scores")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(case.get("name")),
                    _md(case.get("task_type")),
                    _md(case.get("eval_char_count")),
                    _md(case.get("generation_quality_status")),
                    _md(case.get("rubric_score")),
                    _md(case.get("pair_generated_char_delta")),
                    _md(case.get("pair_generated_equal")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(scorecard.get("recommendations")))
    warnings = _string_list(scorecard.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_benchmark_scorecard_markdown(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_markdown(scorecard), encoding="utf-8")


def render_benchmark_scorecard_html(scorecard: dict[str, Any]) -> str:
    summary = _dict(scorecard.get("summary"))
    drilldowns = _dict(scorecard.get("drilldowns"))
    rubric_scores = _dict(scorecard.get("rubric_scores"))
    stats = [
        ("Status", summary.get("overall_status")),
        ("Score", summary.get("overall_score")),
        ("Eval cases", summary.get("eval_suite_cases")),
        ("Gen quality", summary.get("generation_quality_status")),
        ("Gen flags", summary.get("generation_quality_total_flags")),
        ("Dominant flag", summary.get("generation_quality_dominant_flag")),
        ("Rubric", summary.get("rubric_status")),
        ("Rubric avg", summary.get("rubric_avg_score")),
        ("Pair cases", summary.get("pair_batch_cases")),
        ("Pair diff", summary.get("pair_generated_differences")),
        ("Pair mode", summary.get("pair_comparison_mode")),
        ("Max delta", summary.get("max_abs_generated_delta")),
        ("Task groups", summary.get("task_type_group_count")),
        ("Difficulty groups", summary.get("difficulty_group_count")),
        ("Registry rank", _dict(scorecard.get("registry_context")).get("best_val_loss_rank")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(scorecard.get('title', 'MiniGPT benchmark scorecard'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(scorecard.get('title', 'MiniGPT benchmark scorecard'))}</h1><p>{_e(scorecard.get('run_dir'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _component_section(_list_of_dicts(scorecard.get("components"))),
            _rubric_section(_list_of_dicts(rubric_scores.get("cases"))),
            _drilldown_section("Task Type Drilldown", _list_of_dicts(drilldowns.get("task_type"))),
            _drilldown_section("Difficulty Drilldown", _list_of_dicts(drilldowns.get("difficulty"))),
            _case_section(_list_of_dicts(scorecard.get("case_scores"))),
            _registry_section(_dict(scorecard.get("registry_context"))),
            _list_section("Recommendations", scorecard.get("recommendations")),
            _list_section("Warnings", scorecard.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT benchmark scorecard exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_benchmark_scorecard_html(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_html(scorecard), encoding="utf-8")


def write_benchmark_scorecard_outputs(scorecard: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "benchmark_scorecard.json",
        "csv": root / "benchmark_scorecard.csv",
        "drilldowns_csv": root / "benchmark_scorecard_drilldowns.csv",
        "rubric_csv": root / "benchmark_scorecard_rubric.csv",
        "markdown": root / "benchmark_scorecard.md",
        "html": root / "benchmark_scorecard.html",
    }
    write_benchmark_scorecard_json(scorecard, paths["json"])
    write_benchmark_scorecard_csv(scorecard, paths["csv"])
    write_benchmark_scorecard_drilldown_csv(scorecard, paths["drilldowns_csv"])
    write_benchmark_scorecard_rubric_csv(scorecard, paths["rubric_csv"])
    write_benchmark_scorecard_markdown(scorecard, paths["markdown"])
    write_benchmark_scorecard_html(scorecard, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _csv_value(value: Any) -> Any:
    if isinstance(value, float):
        return f"{value:.4f}"
    return value


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _markdown_drilldown_table(title: str, rows: Any) -> list[str]:
    lines = ["", f"## {title}", "", "| Group | Status | Score | Cases |", "| --- | --- | ---: | ---: |"]
    for row in _list_of_dicts(rows):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("key")),
                    _md(row.get("status")),
                    _md(row.get("score")),
                    _md(row.get("case_count")),
                ]
            )
            + " |"
        )
    return lines


def _markdown_rubric_table(rows: Any) -> list[str]:
    lines = ["", "## Rubric Scores", "", "| Case | Status | Score | Missing Terms |", "| --- | --- | ---: | --- |"]
    for row in _list_of_dicts(rows):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(row.get("status")),
                    _md(row.get("score")),
                    _md(row.get("missing_terms")),
                ]
            )
            + " |"
        )
    return lines


def _style() -> str:
    return """<style>
:root { --ink:#172033; --muted:#536176; --line:#d9e2ec; --panel:#ffffff; --page:#f5f7f4; --blue:#1d4ed8; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.5; }
header { padding:24px 32px 16px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 6px; font-size:27px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; letter-spacing:0; }
p { margin:0; color:var(--muted); overflow-wrap:anywhere; }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(155px, 1fr)); gap:12px; padding:18px 32px 0; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:13px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; }
td, th { padding:8px 6px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:22px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _component_section(components: list[dict[str, Any]]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{_e(item.get('title'))}</td>"
        f"<td>{_e(item.get('status'))}</td>"
        f"<td>{_e(item.get('score'))}</td>"
        f"<td>{_e(item.get('weight'))}</td>"
        f"<td>{_e(item.get('detail'))}</td>"
        "</tr>"
        for item in components
    )
    return (
        '<section class="panel"><h2>Benchmark Components</h2><table><thead><tr><th>Component</th><th>Status</th><th>Score</th><th>Weight</th><th>Detail</th></tr></thead><tbody>'
        + (rows or "<tr><td>missing</td><td>missing</td><td>0</td><td>0</td><td>missing</td></tr>")
        + "</tbody></table></section>"
    )


def _drilldown_section(title: str, rows: list[dict[str, Any]]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{_e(row.get('key'))}</td>"
        f"<td>{_e(row.get('status'))}</td>"
        f"<td>{_e(row.get('score'))}</td>"
        f"<td>{_e(row.get('case_count'))}</td>"
        "</tr>"
        for row in rows
    )
    return f'<section class="panel"><h2>{_e(title)}</h2><table><thead><tr><th>Group</th><th>Status</th><th>Score</th><th>Cases</th></tr></thead><tbody>{body or "<tr><td>missing</td><td>missing</td><td>0</td><td>0</td></tr>"}</tbody></table></section>'


def _rubric_section(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{_e(row.get('name'))}</td>"
        f"<td>{_e(row.get('status'))}</td>"
        f"<td>{_e(row.get('score'))}</td>"
        f"<td>{_e(row.get('missing_terms'))}</td>"
        "</tr>"
        for row in rows
    )
    return f'<section class="panel"><h2>Rubric Scores</h2><table><thead><tr><th>Case</th><th>Status</th><th>Score</th><th>Missing Terms</th></tr></thead><tbody>{body or "<tr><td>missing</td><td>missing</td><td>0</td><td>[]</td></tr>"}</tbody></table></section>'


def _case_section(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{_e(row.get('name'))}</td>"
        f"<td>{_e(row.get('task_type'))}</td>"
        f"<td>{_e(row.get('eval_char_count'))}</td>"
        f"<td>{_e(row.get('generation_quality_status'))}</td>"
        f"<td>{_e(row.get('rubric_score'))}</td>"
        f"<td>{_e(row.get('pair_generated_char_delta'))}</td>"
        f"<td>{_e(row.get('pair_generated_equal'))}</td>"
        "</tr>"
        for row in rows
    )
    return f'<section class="panel"><h2>Case Scores</h2><table><thead><tr><th>Case</th><th>Task</th><th>Eval chars</th><th>Gen status</th><th>Rubric</th><th>Pair delta</th><th>Pair equal</th></tr></thead><tbody>{body or "<tr><td>missing</td><td>missing</td><td>0</td><td>missing</td><td>0</td><td>0</td><td>false</td></tr>"}</tbody></table></section>'


def _registry_section(registry: dict[str, Any]) -> str:
    rows = [
        ("Run count", registry.get("run_count")),
        ("Best rank", registry.get("best_val_loss_rank")),
        ("Pair report count", _dict(registry.get("pair_report_counts")).get("pair_batch")),
        ("Max pair delta", _dict(registry.get("pair_delta_summary")).get("max_abs_generated_char_delta")),
    ]
    body = "".join(f"<tr><td>{_e(label)}</td><td>{_e(value)}</td></tr>" for label, value in rows)
    return f'<section class="panel"><h2>Registry Context</h2><table><tbody>{body}</tbody></table></section>'


def _list_section(title: str, values: Any, *, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    body = "".join(f"<li>{_e(item)}</li>" for item in items) or "<li>missing</li>"
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>{body}</ul></section>'


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=False)
