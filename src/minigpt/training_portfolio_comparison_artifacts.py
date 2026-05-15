from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any


def write_training_portfolio_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_training_portfolio_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "source_path",
        "status",
        "run_name",
        "dataset",
        "artifact_coverage",
        "available_artifact_count",
        "artifact_count",
        "overall_score",
        "rubric_avg_score",
        "final_val_loss",
        "best_val_loss",
        "parameter_count",
        "train_token_count",
        "eval_case_count",
        "generation_quality_status",
        "dataset_readiness_status",
        "dataset_quality_status",
        "dataset_warning_count",
        "maturity_portfolio_status",
        "baseline_name",
        "is_baseline",
        "artifact_coverage_delta",
        "available_artifact_delta",
        "overall_score_delta",
        "rubric_avg_score_delta",
        "final_val_loss_delta",
        "final_val_loss_relation",
        "dataset_warning_delta",
        "overall_relation",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for portfolio in _list_of_dicts(report.get("portfolios")):
            row = dict(portfolio)
            row.update(deltas.get(portfolio.get("name"), {}))
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_training_portfolio_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    lines = [
        f"# {report.get('title', 'MiniGPT training portfolio comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Portfolios: `{report.get('portfolio_count')}`",
        f"- Baseline: `{baseline.get('name')}`",
        f"- Best overall score: `{_pick(_dict(report.get('best_by_overall_score')), 'name') or 'missing'}`",
        f"- Best final validation loss: `{_pick(_dict(report.get('best_by_final_val_loss')), 'name') or 'missing'}`",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Completed | {_md(summary.get('completed_count'))} |",
        f"| Failed | {_md(summary.get('failed_count'))} |",
        f"| Planned | {_md(summary.get('planned_count'))} |",
        f"| Score improvements | {_md(summary.get('score_improvement_count'))} |",
        f"| Score regressions | {_md(summary.get('score_regression_count'))} |",
        f"| Artifact regressions | {_md(summary.get('artifact_regression_count'))} |",
        f"| Dataset warnings | {_md(summary.get('dataset_warning_count'))} |",
        f"| Maturity reviews | {_md(summary.get('maturity_review_count'))} |",
        "",
        "## Portfolios",
        "",
        "| Portfolio | Status | Dataset | Artifacts | Score | Val Loss | Dataset | Maturity | Relation |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    for portfolio in _list_of_dicts(report.get("portfolios")):
        delta = deltas.get(portfolio.get("name"), {})
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(portfolio.get("name")),
                    _md(portfolio.get("status")),
                    _md(portfolio.get("dataset")),
                    _md(f"{portfolio.get('available_artifact_count')}/{portfolio.get('artifact_count')}"),
                    _md(f"{_fmt(portfolio.get('overall_score'))} ({_fmt_signed(delta.get('overall_score_delta'))})"),
                    _md(f"{_fmt(portfolio.get('final_val_loss'))} ({_fmt_signed(delta.get('final_val_loss_delta'))})"),
                    _md(portfolio.get("dataset_readiness_status")),
                    _md(portfolio.get("maturity_portfolio_status")),
                    _md(delta.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Artifact Coverage", "", "| Portfolio | Artifact | Exists | Path |", "| --- | --- | --- | --- |"])
    for portfolio in _list_of_dicts(report.get("portfolios")):
        for artifact in _list_of_dicts(portfolio.get("core_artifacts")):
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md(portfolio.get("name")),
                        _md(artifact.get("key")),
                        _md(artifact.get("exists")),
                        _md(artifact.get("path")),
                    ]
                )
                + " |"
            )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_portfolio_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_portfolio_comparison_markdown(report), encoding="utf-8")


def render_training_portfolio_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    stats = [
        ("Baseline", baseline.get("name")),
        ("Portfolios", report.get("portfolio_count")),
        ("Completed", summary.get("completed_count")),
        ("Failed", summary.get("failed_count")),
        ("Score improved", summary.get("score_improvement_count")),
        ("Score regressed", summary.get("score_regression_count")),
        ("Best score", _pick(_dict(report.get("best_by_overall_score")), "name")),
        ("Best val loss", _pick(_dict(report.get("best_by_final_val_loss")), "name")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training portfolio comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training portfolio comparison'))}</h1><p>Baseline: {_e(baseline.get('name'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _portfolio_table(report),
            _artifact_table(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training portfolio comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_portfolio_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_portfolio_comparison_html(report), encoding="utf-8")


def write_training_portfolio_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_portfolio_comparison.json",
        "csv": root / "training_portfolio_comparison.csv",
        "markdown": root / "training_portfolio_comparison.md",
        "html": root / "training_portfolio_comparison.html",
    }
    write_training_portfolio_comparison_json(report, paths["json"])
    write_training_portfolio_comparison_csv(report, paths["csv"])
    write_training_portfolio_comparison_markdown(report, paths["markdown"])
    write_training_portfolio_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _portfolio_table(report: dict[str, Any]) -> str:
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    body = []
    for item in _list_of_dicts(report.get("portfolios")):
        delta = deltas.get(item.get("name"), {})
        body.append(
            "<tr>"
            f"<td><strong>{_e(item.get('name'))}</strong><br><span>{_e(item.get('source_path'))}</span></td>"
            f"<td>{_e(item.get('status'))}<br><span>{_e(item.get('completed_steps'))}/{_e(item.get('step_count'))} steps</span></td>"
            f"<td>{_e(item.get('dataset'))}</td>"
            f"<td>{_e(item.get('available_artifact_count'))}/{_e(item.get('artifact_count'))}<br><span>{_e(item.get('artifact_coverage'))}</span></td>"
            f"<td>{_e(_fmt(item.get('overall_score')))}<br><span>{_e(_fmt_signed(delta.get('overall_score_delta')))}</span></td>"
            f"<td>{_e(_fmt(item.get('rubric_avg_score')))}<br><span>{_e(_fmt_signed(delta.get('rubric_avg_score_delta')))}</span></td>"
            f"<td>{_e(_fmt(item.get('final_val_loss')))}<br><span>{_e(delta.get('final_val_loss_relation'))}</span></td>"
            f"<td>{_e(item.get('dataset_readiness_status'))}<br><span>warnings={_e(item.get('dataset_warning_count'))}</span></td>"
            f"<td>{_e(item.get('maturity_portfolio_status'))}</td>"
            f"<td>{_e(delta.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Portfolio Deltas</h2>'
        '<table><thead><tr><th>Portfolio</th><th>Status</th><th>Dataset</th><th>Artifacts</th><th>Overall</th><th>Rubric</th><th>Val Loss</th><th>Dataset Card</th><th>Maturity</th><th>Explanation</th></tr></thead><tbody>'
        + "".join(body)
        + "</tbody></table></section>"
    )


def _artifact_table(report: dict[str, Any]) -> str:
    rows = []
    for portfolio in _list_of_dicts(report.get("portfolios")):
        for artifact in _list_of_dicts(portfolio.get("core_artifacts")):
            rows.append(
                "<tr>"
                f"<td>{_e(portfolio.get('name'))}</td>"
                f"<td>{_e(artifact.get('key'))}</td>"
                f"<td>{_e(artifact.get('exists'))}</td>"
                f"<td>{_e(artifact.get('path'))}</td>"
                "</tr>"
            )
    return (
        '<section class="panel"><h2>Core Artifact Coverage</h2>'
        '<table><thead><tr><th>Portfolio</th><th>Artifact</th><th>Exists</th><th>Path</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _list_section(title: str, values: Any) -> str:
    items = _string_list(values)
    if not items:
        return ""
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _style() -> str:
    return """<style>
:root { --ink:#172033; --muted:#596579; --line:#d9dfd2; --page:#f7f8f3; --panel:#fff; --blue:#1f5f74; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, p { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:19px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:1060px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _pick(mapping: Any, key: str) -> Any:
    return mapping.get(key) if isinstance(mapping, dict) else None


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _fmt(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "missing"
    return f"{float(number):.4g}"


def _fmt_signed(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "missing"
    return f"{float(number):+.4g}"


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


__all__ = [
    "render_training_portfolio_comparison_html",
    "render_training_portfolio_comparison_markdown",
    "write_training_portfolio_comparison_csv",
    "write_training_portfolio_comparison_html",
    "write_training_portfolio_comparison_json",
    "write_training_portfolio_comparison_markdown",
    "write_training_portfolio_comparison_outputs",
]
