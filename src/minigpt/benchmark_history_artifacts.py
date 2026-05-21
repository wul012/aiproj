from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    csv_cell,
    html_escape as _e,
    markdown_cell as _md,
    string_list as _string_list,
    write_json_payload,
)


def write_benchmark_history_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_benchmark_history_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "index",
        "name",
        "comparison_path",
        "decision_path",
        "baseline_name",
        "candidate_name",
        "decision_status",
        "recommended_action",
        "promotion_readiness",
        "model_quality_claim",
        "overall_score_delta",
        "rubric_avg_score_delta",
        "case_regression_count",
        "case_improvement_count",
        "generation_quality_total_flags_delta",
        "generation_quality_flag_relation",
        "eval_suite_comparison_status",
        "non_comparison_ready_count",
        "remediation_plan_count",
        "boundary",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in _ledger_entries(report):
            writer.writerow({field: csv_cell(item.get(field)) for field in fieldnames})


def render_benchmark_history_markdown(report: dict[str, Any]) -> str:
    summary = _summary(report)
    requirement = _readiness_requirement(report)
    lines = [
        f"# {_md(report.get('title', 'MiniGPT benchmark history'))}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Entries: `{summary.get('entry_count')}`",
        f"- Promote decisions: `{summary.get('promote_count')}`",
        f"- Review decisions: `{summary.get('review_count')}`",
        f"- Blocked decisions: `{summary.get('blocked_count')}`",
        f"- Model quality claim: `{summary.get('model_quality_claim')}`",
        f"- Best candidate: `{summary.get('best_candidate_name')}`",
        f"- Readiness requirement: `{requirement.get('status', 'not-evaluated')}`",
        f"- Readiness decision: `{requirement.get('decision', 'not-evaluated')}`",
        f"- Readiness exit code: `{requirement.get('exit_code', 0)}`",
        f"- Readiness failed reasons: `{', '.join(_string_list(requirement.get('failed_reasons')))}`",
        "",
        "## Ledger",
        "",
        "| Name | Baseline | Candidate | Decision | Readiness | Rubric Delta | Case Regressions | Gen Flag Delta | Boundary |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in _ledger_entries(report):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("name")),
                    _md(item.get("baseline_name")),
                    _md(item.get("candidate_name")),
                    _md(item.get("decision_status")),
                    _md(item.get("promotion_readiness")),
                    _md(item.get("rubric_avg_score_delta")),
                    _md(item.get("case_regression_count")),
                    _md(item.get("generation_quality_total_flags_delta")),
                    _md(item.get("boundary")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_benchmark_history_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_history_markdown(report), encoding="utf-8")


def render_benchmark_history_html(report: dict[str, Any]) -> str:
    summary = _summary(report)
    requirement = _readiness_requirement(report)
    stats = [
        ("Entries", summary.get("entry_count")),
        ("Promote", summary.get("promote_count")),
        ("Review", summary.get("review_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Model claim", summary.get("model_quality_claim")),
        ("Best candidate", summary.get("best_candidate_name")),
        ("Readiness", requirement.get("status", "not-evaluated")),
        ("Readiness exit", requirement.get("exit_code", 0)),
    ]
    rows = "".join(_entry_row(item) for item in _ledger_entries(report))
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT benchmark history'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT benchmark history'))}</h1><p>Tracks scorecard comparison and promotion-decision history without claiming broad model quality from tiny smoke evidence.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _readiness_requirement_section(requirement),
            "<section><h2>Ledger</h2><table><tr><th>Name</th><th>Baseline</th><th>Candidate</th><th>Decision</th><th>Readiness</th><th>Rubric Delta</th><th>Cases</th><th>Gen Flags</th><th>Boundary</th></tr>"
            + rows
            + "</table></section>",
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT benchmark history.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_benchmark_history_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_history_html(report), encoding="utf-8")


def write_benchmark_history_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "benchmark_history.json",
        "csv": root / "benchmark_history.csv",
        "markdown": root / "benchmark_history.md",
        "html": root / "benchmark_history.html",
    }
    write_benchmark_history_json(report, paths["json"])
    write_benchmark_history_csv(report, paths["csv"])
    write_benchmark_history_markdown(report, paths["markdown"])
    write_benchmark_history_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _summary(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("summary")
    return dict(value) if isinstance(value, dict) else {}


def _readiness_requirement(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("readiness_requirement")
    return dict(value) if isinstance(value, dict) else {}


def _ledger_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("entries")
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _entry_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('name'))}</td>"
        f"<td>{_e(item.get('baseline_name'))}</td>"
        f"<td>{_e(item.get('candidate_name'))}</td>"
        f"<td>{_e(item.get('decision_status'))}</td>"
        f"<td>{_e(item.get('promotion_readiness'))}</td>"
        f"<td>{_e(item.get('rubric_avg_score_delta'))}</td>"
        f"<td>{_e(item.get('case_regression_count'))}</td>"
        f"<td>{_e(item.get('generation_quality_total_flags_delta'))}</td>"
        f"<td>{_e(item.get('boundary'))}</td>"
        "</tr>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return f"<section><h2>{_e(title)}</h2><p class=\"muted\">None.</p></section>"
    return f"<section><h2>{_e(title)}</h2><ul>" + "".join(f"<li>{_e(item)}</li>" for item in values) + "</ul></section>"


def _readiness_requirement_section(requirement: dict[str, Any]) -> str:
    if not requirement:
        return '<section><h2>Readiness Requirement</h2><p class="muted">Not evaluated.</p></section>'
    rows = [
        ("Status", requirement.get("status")),
        ("Decision", requirement.get("decision")),
        ("Exit code", requirement.get("exit_code")),
        ("Ready count", requirement.get("ready_count")),
        ("Min ready entries", requirement.get("min_ready_entries")),
        ("Evidence kind", requirement.get("evidence_kind")),
        ("Require real benchmark", requirement.get("require_real_benchmark")),
        ("Failed reasons", ", ".join(_string_list(requirement.get("failed_reasons")))),
    ]
    return (
        "<section><h2>Readiness Requirement</h2><table>"
        + "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
        + "</table></section>"
    )


def _stat(label: str, value: Any) -> str:
    return f'<article class="stat"><span>{_e(label)}</span><strong>{_e(value)}</strong></article>'


def _style() -> str:
    return """
<style>
:root { color-scheme: light; font-family: Arial, "Microsoft YaHei", sans-serif; color: #172026; background: #f6f8fa; }
body { margin: 0; padding: 24px; }
header, section, footer { max-width: 1160px; margin: 0 auto 18px; }
header { padding: 18px 0 8px; border-bottom: 3px solid #1f7a5c; }
h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
h2 { margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }
p { margin: 0 0 10px; line-height: 1.5; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.stat { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 12px; min-height: 64px; }
.stat span { display: block; color: #5c6b73; font-size: 12px; margin-bottom: 8px; }
.stat strong { display: block; font-size: 18px; overflow-wrap: anywhere; }
section { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px; border-bottom: 1px solid #e5e9ef; text-align: left; vertical-align: top; }
th { background: #eef3f6; }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; }
.muted { color: #687782; }
footer { color: #687782; font-size: 12px; }
</style>
""".strip()


__all__ = [
    "render_benchmark_history_html",
    "render_benchmark_history_markdown",
    "write_benchmark_history_csv",
    "write_benchmark_history_html",
    "write_benchmark_history_json",
    "write_benchmark_history_markdown",
    "write_benchmark_history_outputs",
]
