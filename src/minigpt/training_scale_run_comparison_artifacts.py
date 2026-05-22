from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell as _csv_value,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_json_payload,
)


def write_training_scale_run_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_run_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "source_path",
        "status",
        "allowed",
        "gate_status",
        "gate_profile",
        "gate_fail_count",
        "gate_warn_count",
        "scale_tier",
        "char_count",
        "variant_count",
        "suite_mode",
        "suite_name",
        "suite_path",
        "batch_status",
        "comparison_status",
        "batch_comparison_review_action_count",
        "batch_comparison_blocker_action_count",
        "batch_maturity_coverage_regression_count",
        "batch_maturity_ci_regression_count",
        "batch_maturity_ci_regression_reason_counts",
        "execute",
        "blocked_reason",
        "readiness_score",
        "baseline_name",
        "is_baseline",
        "allowed_delta",
        "readiness_delta",
        "suite_relation",
        "gate_relation",
        "batch_relation",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for run in _list_of_dicts(report.get("runs")):
            row = dict(run)
            row.update(deltas.get(run.get("name"), {}))
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_training_scale_run_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale run comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runs: `{report.get('run_count')}`",
        f"- Baseline: `{baseline.get('name')}`",
        f"- Allowed: `{summary.get('allowed_count')}`",
        f"- Blocked: `{summary.get('blocked_count')}`",
        f"- Batch started: `{summary.get('batch_started_count')}`",
        f"- Gate warnings: `{summary.get('gate_warn_count')}`",
        f"- Gate failures: `{summary.get('gate_fail_count')}`",
        f"- Batch comparison reviews: `{summary.get('batch_comparison_review_action_count')}`",
        f"- Batch comparison blockers: `{summary.get('batch_comparison_blocker_action_count')}`",
        f"- Batch coverage regressions: `{summary.get('batch_maturity_coverage_regression_count')}`",
        f"- Batch CI regressions: `{summary.get('batch_maturity_ci_regression_count')}`",
        f"- Batch CI regression reasons: `{_fmt_mapping(summary.get('batch_maturity_ci_regression_reason_counts'))}`",
        f"- Suite consistency: `{summary.get('suite_consistency')}`",
        f"- Baseline suite: `{summary.get('baseline_suite_path')}`",
        "",
        "## Runs",
        "",
        "| Run | Status | Allowed | Gate | Profile | Scale | Suite | Variants | Batch | Review | Blockers | CI | CI Reasons | Score | Relation |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("name"), {})
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(run.get("name")),
                    _md(run.get("status")),
                    _md(run.get("allowed")),
                    _md(run.get("gate_status")),
                    _md(run.get("gate_profile")),
                    _md(run.get("scale_tier")),
                    _md(run.get("suite_path")),
                    _md(run.get("variant_count")),
                    _md(run.get("batch_status")),
                    _md(run.get("batch_comparison_review_action_count")),
                    _md(run.get("batch_comparison_blocker_action_count")),
                    _md(run.get("batch_maturity_ci_regression_count")),
                    _md(_fmt_mapping(run.get("batch_maturity_ci_regression_reason_counts"))),
                    _md(run.get("readiness_score")),
                    _md(delta.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_run_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_comparison_markdown(report), encoding="utf-8")


def render_training_scale_run_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    best = _dict(report.get("best_by_readiness"))
    stats = [
        ("Baseline", baseline.get("name")),
        ("Runs", report.get("run_count")),
        ("Allowed", summary.get("allowed_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Batch started", summary.get("batch_started_count")),
        ("Batch reviews", summary.get("batch_comparison_review_action_count")),
        ("Batch blockers", summary.get("batch_comparison_blocker_action_count")),
        ("Coverage regressions", summary.get("batch_maturity_coverage_regression_count")),
        ("CI regressions", summary.get("batch_maturity_ci_regression_count")),
        ("CI regression reasons", _fmt_mapping(summary.get("batch_maturity_ci_regression_reason_counts"))),
        ("Gate warn", summary.get("gate_warn_count")),
        ("Gate fail", summary.get("gate_fail_count")),
        ("Suite", summary.get("suite_consistency")),
        ("Best", best.get("name")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale run comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale run comparison'))}</h1><p>Baseline: {_e(baseline.get('name'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _runs_table(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale run comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_run_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_comparison_html(report), encoding="utf-8")


def write_training_scale_run_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_run_comparison.json",
        "csv": root / "training_scale_run_comparison.csv",
        "markdown": root / "training_scale_run_comparison.md",
        "html": root / "training_scale_run_comparison.html",
    }
    write_training_scale_run_comparison_json(report, paths["json"])
    write_training_scale_run_comparison_csv(report, paths["csv"])
    write_training_scale_run_comparison_markdown(report, paths["markdown"])
    write_training_scale_run_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _runs_table(report: dict[str, Any]) -> str:
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    rows = []
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("name"), {})
        rows.append(
            "<tr>"
            f"<td>{_e(run.get('name'))}</td>"
            f"<td>{_e(run.get('status'))}</td>"
            f"<td>{_e(run.get('allowed'))}</td>"
            f"<td>{_e(run.get('gate_status'))}</td>"
            f"<td>{_e(run.get('gate_profile'))}</td>"
            f"<td>{_e(run.get('scale_tier'))}</td>"
            f"<td>{_e(run.get('suite_path'))}</td>"
            f"<td>{_e(run.get('variant_count'))}</td>"
            f"<td>{_e(run.get('batch_status'))}</td>"
            f"<td>{_e(run.get('batch_comparison_review_action_count'))}</td>"
            f"<td>{_e(run.get('batch_comparison_blocker_action_count'))}</td>"
            f"<td>{_e(run.get('batch_maturity_ci_regression_count'))}</td>"
            f"<td>{_e(_fmt_mapping(run.get('batch_maturity_ci_regression_reason_counts')))}</td>"
            f"<td>{_e(run.get('readiness_score'))}</td>"
            f"<td>{_e(delta.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Runs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Run</th><th>Status</th><th>Allowed</th><th>Gate</th><th>Profile</th><th>Scale</th><th>Suite</th><th>Variants</th><th>Batch</th><th>Review</th><th>Blockers</th><th>CI</th><th>CI Reasons</th><th>Score</th><th>Relation</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f7f2; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1160px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 900px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _fmt_mapping(value: Any) -> str:
    counts = _dict(value)
    if not counts:
        return "none"
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))
