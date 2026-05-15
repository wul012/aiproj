from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import html_escape as _e
from minigpt.report_utils import list_of_dicts as _list_of_dicts
from minigpt.report_utils import list_of_strs as _string_list
from minigpt.report_utils import markdown_cell as _md


def write_training_portfolio_batch_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_training_portfolio_batch_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "description",
        "status",
        "out_root",
        "portfolio_json",
        "artifact_count",
        "available_artifact_count",
        "max_iters",
        "batch_size",
        "block_size",
        "n_layer",
        "n_head",
        "n_embd",
        "seed",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        rows = _list_of_dicts(report.get("variant_results")) or _planned_rows(report)
        for row in rows:
            config = _dict(row.get("config"))
            writer.writerow(
                {
                    "name": row.get("name"),
                    "description": row.get("description"),
                    "status": row.get("status") or "planned",
                    "out_root": row.get("out_root"),
                    "portfolio_json": row.get("portfolio_json") or row.get("portfolio_path"),
                    "artifact_count": row.get("artifact_count"),
                    "available_artifact_count": row.get("available_artifact_count"),
                    "max_iters": config.get("max_iters"),
                    "batch_size": config.get("batch_size"),
                    "block_size": config.get("block_size"),
                    "n_layer": config.get("n_layer"),
                    "n_head": config.get("n_head"),
                    "n_embd": config.get("n_embd"),
                    "seed": config.get("seed"),
                }
            )


def render_training_portfolio_batch_markdown(report: dict[str, Any]) -> str:
    execution = _dict(report.get("execution"))
    summary = _dict(report.get("summary"))
    comparison = _dict(report.get("comparison"))
    lines = [
        f"# {report.get('title', 'MiniGPT training portfolio batch')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Project root: `{report.get('project_root')}`",
        f"- Out root: `{report.get('out_root')}`",
        f"- Status: `{execution.get('status', 'planned')}`",
        f"- Variants: `{report.get('variant_count')}`",
        f"- Baseline: `{report.get('baseline_name')}`",
        f"- Total planned iterations: `{summary.get('total_max_iters')}`",
        "",
        "## Variants",
        "",
        "| Variant | Status | Config | Out Root | Portfolio |",
        "| --- | --- | --- | --- | --- |",
    ]
    rows = _list_of_dicts(report.get("variant_results")) or _planned_rows(report)
    for row in rows:
        config = _dict(row.get("config"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(row.get("status") or "planned"),
                    _md(_config_label(config)),
                    _md(row.get("out_root")),
                    _md(row.get("portfolio_json") or row.get("portfolio_path")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Comparison",
            "",
            *_markdown_table(
                [
                    ("Baseline", comparison.get("baseline_name")),
                    ("Out dir", comparison.get("out_dir")),
                    ("Status", execution.get("comparison_status", "planned")),
                    ("Command", _display_command(comparison.get("command"))),
                ]
            ),
            "",
            "## Recommendations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    warnings = _string_list(report.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_training_portfolio_batch_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_portfolio_batch_markdown(report), encoding="utf-8")


def render_training_portfolio_batch_html(report: dict[str, Any]) -> str:
    execution = _dict(report.get("execution"))
    summary = _dict(report.get("summary"))
    stats = [
        ("Status", execution.get("status", "planned")),
        ("Variants", report.get("variant_count")),
        ("Baseline", report.get("baseline_name")),
        ("Total iters", summary.get("total_max_iters")),
        ("Max block", summary.get("max_block_size")),
        ("Max embd", summary.get("max_n_embd")),
        ("Compare", execution.get("comparison_status", "planned")),
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
            f"<title>{_e(report.get('title', 'MiniGPT training portfolio batch'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training portfolio batch'))}</h1><p>{_e(report.get('out_root'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _variant_table(report),
            _comparison_panel(report),
            _list_section("Recommendations", report.get("recommendations")),
            _list_section("Warnings", report.get("warnings")),
            "<footer>Generated by MiniGPT training portfolio batch.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_portfolio_batch_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_portfolio_batch_html(report), encoding="utf-8")


def write_training_portfolio_batch_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_portfolio_batch.json",
        "csv": root / "training_portfolio_batch.csv",
        "markdown": root / "training_portfolio_batch.md",
        "html": root / "training_portfolio_batch.html",
    }
    write_training_portfolio_batch_json(report, paths["json"])
    write_training_portfolio_batch_csv(report, paths["csv"])
    write_training_portfolio_batch_markdown(report, paths["markdown"])
    write_training_portfolio_batch_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _planned_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": row.get("name"),
            "description": row.get("description"),
            "status": "planned",
            "out_root": row.get("out_root"),
            "portfolio_path": row.get("portfolio_path"),
            "config": row.get("config"),
        }
        for row in _list_of_dicts(report.get("variants"))
    ]


def _recommendations(execution: dict[str, Any], comparison_summary: dict[str, Any] | None, warnings: list[str]) -> list[str]:
    if warnings:
        return ["Inspect batch warnings before trusting the comparison outputs."]
    if execution.get("status") == "planned":
        return ["Review the batch HTML, then rerun with --execute when the variant matrix is ready to train."]
    if execution.get("status") == "failed":
        return [f"Inspect failed variant `{execution.get('failed_variant')}` before continuing the batch."]
    if execution.get("comparison_status") == "written" and comparison_summary:
        return ["Open the batch comparison HTML to choose the next baseline for larger-corpus or model-size experiments."]
    return ["Use the generated per-variant training_portfolio.html files to inspect each run before comparing them."]


def _variant_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("variant_results")) or _planned_rows(report):
        config = _dict(row.get("config"))
        rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('name'))}</strong><br><span>{_e(row.get('description'))}</span></td>"
            f"<td>{_e(row.get('status') or 'planned')}<br><span>{_e(row.get('completed_steps'))}/{_e(row.get('step_count'))} steps</span></td>"
            f"<td>{_e(_config_label(config))}</td>"
            f"<td>{_e(row.get('out_root'))}</td>"
            f"<td>{_e(row.get('portfolio_json') or row.get('portfolio_path'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Variant Matrix</h2>'
        '<table><thead><tr><th>Variant</th><th>Status</th><th>Config</th><th>Out Root</th><th>Portfolio</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _comparison_panel(report: dict[str, Any]) -> str:
    comparison = _dict(report.get("comparison"))
    execution = _dict(report.get("execution"))
    outputs = _dict(report.get("comparison_outputs"))
    rows = [
        ("Baseline", comparison.get("baseline_name")),
        ("Status", execution.get("comparison_status", "planned")),
        ("Out dir", comparison.get("out_dir")),
        ("Command", _display_command(comparison.get("command"))),
    ]
    rows.extend((f"Output {key}", value) for key, value in outputs.items())
    body = "".join(f"<tr><td>{_e(label)}</td><td>{_e(value)}</td></tr>" for label, value in rows)
    return '<section class="panel"><h2>Comparison Hook</h2><table><tbody>' + body + "</tbody></table></section>"


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
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _config_label(config: dict[str, Any]) -> str:
    return (
        f"iters={config.get('max_iters')}, batch={config.get('batch_size')}, block={config.get('block_size')}, "
        f"layers={config.get('n_layer')}, heads={config.get('n_head')}, embd={config.get('n_embd')}, seed={config.get('seed')}"
    )


def _display_command(command: Any) -> str:
    return " ".join(_quote(part) for part in _string_list(command))


def _quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"' if not value or any(ch.isspace() for ch in value) else value


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(label)} | {_md(value)} |" for label, value in rows)
    return lines


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


__all__ = [
    "render_training_portfolio_batch_html",
    "render_training_portfolio_batch_markdown",
    "write_training_portfolio_batch_csv",
    "write_training_portfolio_batch_html",
    "write_training_portfolio_batch_json",
    "write_training_portfolio_batch_markdown",
    "write_training_portfolio_batch_outputs",
]
