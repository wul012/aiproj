from __future__ import annotations

import csv
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
    "render_promoted_training_scale_comparison_html",
    "render_promoted_training_scale_comparison_markdown",
    "write_promoted_training_scale_comparison_csv",
    "write_promoted_training_scale_comparison_html",
    "write_promoted_training_scale_comparison_json",
    "write_promoted_training_scale_comparison_markdown",
    "write_promoted_training_scale_comparison_outputs",
]

def write_promoted_training_scale_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    comparison = _dict(report.get("comparison"))
    deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "promotion_status",
        "promoted_for_comparison",
        "training_scale_run_path",
        "status",
        "allowed",
        "gate_status",
        "batch_status",
        "readiness_score",
        "baseline_name",
        "is_baseline",
        "readiness_delta",
        "gate_relation",
        "batch_relation",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("promotions")):
            delta = deltas.get(row.get("name"), {})
            writer.writerow(
                {
                    "name": row.get("name"),
                    "promotion_status": row.get("promotion_status"),
                    "promoted_for_comparison": row.get("promoted_for_comparison"),
                    "training_scale_run_path": row.get("training_scale_run_path"),
                    "status": row.get("comparison_status"),
                    "allowed": row.get("allowed"),
                    "gate_status": row.get("gate_status"),
                    "batch_status": row.get("batch_status"),
                    "readiness_score": row.get("readiness_score"),
                    "baseline_name": delta.get("baseline_name"),
                    "is_baseline": delta.get("is_baseline"),
                    "readiness_delta": delta.get("readiness_delta"),
                    "gate_relation": delta.get("gate_relation"),
                    "batch_relation": delta.get("batch_relation"),
                    "explanation": delta.get("explanation"),
                }
            )


def render_promoted_training_scale_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    comparison = _dict(report.get("comparison"))
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Comparison status: `{report.get('comparison_status')}`",
        f"- Promoted inputs: `{summary.get('promoted_count')}`",
        f"- Compare-ready inputs: `{summary.get('comparison_ready_count')}`",
        f"- Compared runs: `{summary.get('compared_run_count')}`",
        f"- Baseline: `{summary.get('baseline_name')}`",
        "",
        "## Promoted Inputs",
        "",
        "| Name | Status | Compare | Readiness | Run |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in _list_of_dicts(report.get("promotions")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(row.get("promotion_status")),
                    _md(row.get("promoted_for_comparison")),
                    _md(row.get("readiness_score")),
                    _md(row.get("training_scale_run_path")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Comparison", ""])
    if report.get("comparison_status") == "compared":
        lines.extend(
            [
                f"- Compared runs: `{comparison.get('run_count')}`",
                f"- Allowed: `{comparison.get('summary', {}).get('allowed_count')}`",
                f"- Blocked: `{comparison.get('summary', {}).get('blocked_count')}`",
                f"- Best by readiness: `{_dict(comparison.get('best_by_readiness')).get('name')}`",
            ]
        )
        lines.extend(["", "| Run | Status | Allowed | Gate | Batch | Score | Relation |", "| --- | --- | --- | --- | --- | ---: | --- |"])
        deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
        for row in _list_of_dicts(comparison.get("runs")):
            delta = deltas.get(row.get("name"), {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md(row.get("name")),
                        _md(row.get("status")),
                        _md(row.get("allowed")),
                        _md(row.get("gate_status")),
                        _md(row.get("batch_status")),
                        _md(row.get("readiness_score")),
                        _md(delta.get("explanation")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("- " + (_block_reason(report) or "Comparison is blocked."))
    blockers = _string_list(report.get("blockers"))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_comparison_markdown(report), encoding="utf-8")


def render_promoted_training_scale_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    comparison = _dict(report.get("comparison"))
    stats = [
        ("Status", report.get("comparison_status")),
        ("Promoted", summary.get("promoted_count")),
        ("Compare-ready", summary.get("comparison_ready_count")),
        ("Compared", summary.get("compared_run_count")),
        ("Baseline", summary.get("baseline_name")),
        ("Best", _dict(comparison.get("best_by_readiness")).get("name")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale comparison'))}</h1><p>{_e(report.get('promotion_index_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _promotion_table(report),
            _comparison_table(report),
            _list_section("Blockers", report.get("blockers")),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_promoted_training_scale_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_comparison_html(report), encoding="utf-8")


def write_promoted_training_scale_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_comparison.json",
        "csv": root / "promoted_training_scale_comparison.csv",
        "markdown": root / "promoted_training_scale_comparison.md",
        "html": root / "promoted_training_scale_comparison.html",
    }
    write_promoted_training_scale_comparison_json(report, paths["json"])
    write_promoted_training_scale_comparison_csv(report, paths["csv"])
    write_promoted_training_scale_comparison_markdown(report, paths["markdown"])
    write_promoted_training_scale_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}

def _promotion_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("promotions")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(row.get('promotion_status'))}</td>"
            f"<td>{_e(row.get('promoted_for_comparison'))}</td>"
            f"<td>{_e(row.get('readiness_score'))}</td>"
            f"<td>{_e(row.get('training_scale_run_path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Promoted Inputs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Name</th><th>Status</th><th>Compare</th><th>Readiness</th><th>Run</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _comparison_table(report: dict[str, Any]) -> str:
    comparison = _dict(report.get("comparison"))
    if report.get("comparison_status") != "compared":
        return f'<section><h2>Comparison</h2><p>{_e(_block_reason(report) or "Comparison is blocked.")}</p></section>'
    deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
    rows = []
    for row in _list_of_dicts(comparison.get("runs")):
        delta = deltas.get(row.get("name"), {})
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(row.get('status'))}</td>"
            f"<td>{_e(row.get('allowed'))}</td>"
            f"<td>{_e(row.get('gate_status'))}</td>"
            f"<td>{_e(row.get('batch_status'))}</td>"
            f"<td>{_e(row.get('readiness_score'))}</td>"
            f"<td>{_e(delta.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Comparison</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Run</th><th>Status</th><th>Allowed</th><th>Gate</th><th>Batch</th><th>Score</th><th>Relation</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f8f4; color: #162126; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1180px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d6ddd6; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #52635a; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9e1da; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(22, 33, 38, 0.05); }
.card span { display: block; color: #64756c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 860px; }
th, td { text-align: left; border-bottom: 1px solid #e4e9e4; padding: 9px; vertical-align: top; }
th { color: #435249; font-size: 12px; text-transform: uppercase; }
li { margin: 7px 0; }
footer { color: #69786e; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'

def _block_reason(report: dict[str, Any]) -> str | None:
    return _dict(report.get("summary")).get("blocked_reason") or (_string_list(report.get("blockers"))[0] if _string_list(report.get("blockers")) else None)
