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


def write_training_scale_promotion_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_promotion_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "promotion_status",
        "handoff_status",
        "scale_run_status",
        "batch_status",
        "variant",
        "variant_status",
        "checkpoint_exists",
        "run_manifest_exists",
        "registry_exists",
        "maturity_narrative_exists",
        "missing_required",
        "portfolio_json",
    ]
    summary = _dict(report.get("summary"))
    rows = _list_of_dicts(report.get("variants")) or [{}]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "promotion_status": summary.get("promotion_status"),
                    "handoff_status": summary.get("handoff_status"),
                    "scale_run_status": summary.get("scale_run_status"),
                    "batch_status": summary.get("batch_status"),
                    "variant": row.get("name"),
                    "variant_status": row.get("promotion_status"),
                    "checkpoint_exists": row.get("checkpoint_exists"),
                    "run_manifest_exists": row.get("run_manifest_exists"),
                    "registry_exists": row.get("registry_exists"),
                    "maturity_narrative_exists": row.get("maturity_narrative_exists"),
                    "missing_required": ", ".join(_string_list(row.get("missing_required"))),
                    "portfolio_json": row.get("portfolio_json"),
                }
            )


def render_training_scale_promotion_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale promotion')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Promotion status: `{summary.get('promotion_status')}`",
        f"- Handoff status: `{summary.get('handoff_status')}`",
        f"- Scale run: `{summary.get('scale_run_status')}`",
        f"- Batch: `{summary.get('batch_status')}`",
        f"- Variants: `{summary.get('ready_variant_count')}/{summary.get('variant_count')}` ready",
        f"- Required artifacts: `{summary.get('available_required_artifact_count')}/{summary.get('required_artifact_count')}`",
        "",
        "## Evidence",
        "",
        "| Key | Exists | Path |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("evidence_rows")):
        lines.append(f"| {_md(row.get('key'))} | {_md(row.get('exists'))} | {_md(row.get('path'))} |")
    lines.extend(["", "## Variant Readiness", "", "| Variant | Status | Missing Required | Portfolio |", "| --- | --- | --- | --- |"])
    for row in _list_of_dicts(report.get("variants")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(row.get("promotion_status")),
                    _md(", ".join(_string_list(row.get("missing_required")))),
                    _md(row.get("portfolio_json")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    blockers = _string_list(report.get("blockers"))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    review_items = _string_list(report.get("review_items"))
    if review_items:
        lines.extend(["", "## Review Items", ""])
        lines.extend(f"- {item}" for item in review_items)
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_promotion_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_promotion_markdown(report), encoding="utf-8")


def render_training_scale_promotion_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Promotion", summary.get("promotion_status")),
        ("Handoff", summary.get("handoff_status")),
        ("Scale run", summary.get("scale_run_status")),
        ("Batch", summary.get("batch_status")),
        ("Ready variants", f"{summary.get('ready_variant_count')}/{summary.get('variant_count')}"),
        (
            "Required artifacts",
            f"{summary.get('available_required_artifact_count')}/{summary.get('required_artifact_count')}",
        ),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale promotion'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale promotion'))}</h1><p>{_e(report.get('handoff_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _evidence_section(report),
            _variant_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            _list_section("Blockers", report.get("blockers")),
            _list_section("Review Items", report.get("review_items")),
            "<footer>Generated by MiniGPT training scale promotion.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_promotion_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_promotion_html(report), encoding="utf-8")


def write_training_scale_promotion_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_promotion.json",
        "csv": root / "training_scale_promotion.csv",
        "markdown": root / "training_scale_promotion.md",
        "html": root / "training_scale_promotion.html",
    }
    write_training_scale_promotion_json(report, paths["json"])
    write_training_scale_promotion_csv(report, paths["csv"])
    write_training_scale_promotion_markdown(report, paths["markdown"])
    write_training_scale_promotion_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _evidence_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("evidence_rows")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('key'))}</td>"
            f"<td>{_e(row.get('exists'))}</td>"
            f"<td>{_e(row.get('path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Evidence</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Key</th><th>Exists</th><th>Path</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _variant_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("variants")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(row.get('promotion_status'))}</td>"
            f"<td>{_e(row.get('checkpoint_exists'))}</td>"
            f"<td>{_e(row.get('registry_exists'))}</td>"
            f"<td>{_e(row.get('maturity_narrative_exists'))}</td>"
            f"<td>{_e(', '.join(_string_list(row.get('missing_required'))))}</td>"
            f"<td>{_e(row.get('portfolio_json'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Variant Readiness</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Variant</th><th>Status</th><th>Checkpoint</th><th>Registry</th><th>Narrative</th><th>Missing</th><th>Portfolio</th></tr></thead>"
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
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
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


__all__ = [
    "render_training_scale_promotion_html",
    "render_training_scale_promotion_markdown",
    "write_training_scale_promotion_csv",
    "write_training_scale_promotion_html",
    "write_training_scale_promotion_json",
    "write_training_scale_promotion_markdown",
    "write_training_scale_promotion_outputs",
]
