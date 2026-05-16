from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    display_command as _display_command,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_json_payload,
)


def write_training_scale_plan_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_variants_json(report: dict[str, Any], path: str | Path) -> None:
    payload = {
        "schema_version": 1,
        "generated_at": report.get("generated_at"),
        "source": "training_scale_plan",
        "dataset": report.get("dataset", {}),
        "variants": list(report.get("variants", [])),
    }
    write_json_payload(payload, path)


def write_training_scale_plan_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "scale_tier",
        "dataset_version",
        "max_iters",
        "eval_interval",
        "batch_size",
        "block_size",
        "n_layer",
        "n_head",
        "n_embd",
        "seed",
        "token_budget",
        "corpus_pass_estimate",
        "description",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("variant_matrix")):
            writer.writerow({key: row.get(key) for key in fieldnames})


def render_training_scale_plan_markdown(report: dict[str, Any]) -> str:
    dataset = _dict(report.get("dataset"))
    batch = _dict(report.get("batch"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale plan')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Scale tier: `{dataset.get('scale_tier')}`",
        f"- Dataset: `{dataset.get('name')}` / `{dataset.get('version_prefix')}`",
        f"- Sources: `{dataset.get('source_count')}`",
        f"- Characters: `{dataset.get('char_count')}`",
        f"- Quality: `{dataset.get('quality_status')}` with `{dataset.get('warning_count')}` warnings",
        f"- Variants file: `{batch.get('variants_path')}`",
        "",
        "## Variant Matrix",
        "",
        "| Variant | Config | Token budget | Corpus passes | Purpose |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("variant_matrix")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(_config_label(row)),
                    _md(row.get("token_budget")),
                    _md(row.get("corpus_pass_estimate")),
                    _md(row.get("description")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Batch Command",
            "",
            f"`{_display_command(batch.get('command'))}`",
            "",
            "## Recommendations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    issues = _list_of_dicts(report.get("quality_issues"))
    if issues:
        lines.extend(["", "## Quality Issues", ""])
        for issue in issues[:8]:
            lines.append(f"- `{issue.get('code')}`: {issue.get('message')}")
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_plan_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_plan_markdown(report), encoding="utf-8")


def render_training_scale_plan_html(report: dict[str, Any]) -> str:
    dataset = _dict(report.get("dataset"))
    batch = _dict(report.get("batch"))
    stats = [
        ("Scale", dataset.get("scale_tier")),
        ("Sources", dataset.get("source_count")),
        ("Chars", dataset.get("char_count")),
        ("Lines", dataset.get("line_count")),
        ("Unique ratio", dataset.get("unique_char_ratio")),
        ("Quality", dataset.get("quality_status")),
        ("Warnings", dataset.get("warning_count")),
        ("Variants", len(_list_of_dicts(report.get("variants")))),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale plan'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale plan'))}</h1><p>{_e(dataset.get('name'))} / {_e(dataset.get('version_prefix'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _variant_table(report),
            _batch_panel(batch),
            _list_section("Recommendations", report.get("recommendations")),
            _quality_section(report),
            "<footer>Generated by MiniGPT training scale planner.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_plan_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_plan_html(report), encoding="utf-8")


def write_training_scale_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_plan.json",
        "variants": root / "training_scale_variants.json",
        "csv": root / "training_scale_plan.csv",
        "markdown": root / "training_scale_plan.md",
        "html": root / "training_scale_plan.html",
    }
    write_training_scale_plan_json(report, paths["json"])
    write_training_scale_variants_json(report, paths["variants"])
    write_training_scale_plan_csv(report, paths["csv"])
    write_training_scale_plan_markdown(report, paths["markdown"])
    write_training_scale_plan_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _variant_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("variant_matrix")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(_config_label(row))}</td>"
            f"<td>{_e(row.get('token_budget'))}</td>"
            f"<td>{_e(row.get('corpus_pass_estimate'))}</td>"
            f"<td>{_e(row.get('description'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Variant Matrix</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Variant</th><th>Config</th><th>Token budget</th><th>Corpus passes</th><th>Purpose</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _batch_panel(batch: dict[str, Any]) -> str:
    return (
        "<section><h2>Batch Handoff</h2>"
        f"<p><strong>Variants:</strong> {_e(batch.get('variants_path'))}</p>"
        f"<p><strong>Out root:</strong> {_e(batch.get('out_root'))}</p>"
        f"<pre>{_e(_display_command(batch.get('command')))}</pre>"
        "</section>"
    )


def _quality_section(report: dict[str, Any]) -> str:
    issues = _list_of_dicts(report.get("quality_issues"))
    if not issues:
        return "<section><h2>Quality Issues</h2><p>No quality issues found.</p></section>"
    rows = []
    for issue in issues[:8]:
        rows.append(
            "<li>"
            f"<strong>{_e(issue.get('code'))}</strong>: {_e(issue.get('message'))}"
            "</li>"
        )
    return f"<section><h2>Quality Issues</h2><ul>{''.join(rows)}</ul></section>"


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f7f2; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1120px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _config_label(row: dict[str, Any]) -> str:
    return (
        f"iters={row.get('max_iters')}, batch={row.get('batch_size')}, block={row.get('block_size')}, "
        f"layers={row.get('n_layer')}, heads={row.get('n_head')}, embd={row.get('n_embd')}, seed={row.get('seed')}"
    )


__all__ = [
    "render_training_scale_plan_html",
    "render_training_scale_plan_markdown",
    "write_training_scale_plan_csv",
    "write_training_scale_plan_html",
    "write_training_scale_plan_json",
    "write_training_scale_plan_markdown",
    "write_training_scale_plan_outputs",
    "write_training_scale_variants_json",
]
