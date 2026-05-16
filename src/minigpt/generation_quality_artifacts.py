from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    write_json_payload,
)


def write_generation_quality_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_generation_quality_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "status",
        "char_count",
        "unique_char_count",
        "unique_ratio",
        "repeated_ngram_ratio",
        "longest_repeat_run",
        "flag_count",
        "flags",
        "prompt",
        "continuation_preview",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in _list_of_dicts(report.get("cases")):
            row = {field: case.get(field) for field in fieldnames}
            row["flags"] = ";".join(_flag_ids(case))
            writer.writerow(row)


def render_generation_quality_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    policy = _dict(report.get("policy"))
    lines = [
        f"# {report.get('title', 'MiniGPT generation quality report')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Source: `{report.get('source_path')}`",
        f"- Source type: `{report.get('source_type')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Overall status", summary.get("overall_status")),
                ("Cases", summary.get("case_count")),
                ("Pass", summary.get("pass_count")),
                ("Warn", summary.get("warn_count")),
                ("Fail", summary.get("fail_count")),
                ("Avg chars", summary.get("avg_continuation_chars")),
                ("Avg unique ratio", summary.get("avg_unique_ratio")),
                ("Avg repeated ngram ratio", summary.get("avg_repeated_ngram_ratio")),
                ("Max repeat run", summary.get("max_repeat_run")),
            ]
        ),
        "",
        "## Policy",
        "",
        *_markdown_table([(key, value) for key, value in policy.items()]),
        "",
        "## Cases",
        "",
        "| Status | Case | Chars | Unique Ratio | Repeated Ngram | Repeat Run | Flags |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in _list_of_dicts(report.get("cases")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(case.get("status")),
                    _md(case.get("name")),
                    _md(case.get("char_count")),
                    _md(_ratio_label(case.get("unique_ratio"))),
                    _md(_ratio_label(case.get("repeated_ngram_ratio"))),
                    _md(case.get("longest_repeat_run")),
                    _md(", ".join(_flag_ids(case)) or "none"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    warnings = _string_list(report.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_generation_quality_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_generation_quality_markdown(report), encoding="utf-8")


def write_generation_quality_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cases = _list_of_dicts(report.get("cases"))
    width = 1040
    row_h = 70
    top = 98
    height = top + row_h * len(cases) + 58
    bar_x = 290
    bar_w = 420
    rows: list[str] = []
    for index, case in enumerate(cases):
        y = top + index * row_h
        ratio = _number(case.get("unique_ratio")) or 0.0
        repeated = _number(case.get("repeated_ngram_ratio")) or 0.0
        unique_bar = max(2, int(bar_w * min(1.0, ratio)))
        repeated_bar = max(2, int(bar_w * min(1.0, repeated)))
        color = _status_color(str(case.get("status") or "warn"))
        label = f"{case.get('name')}  {case.get('status')}  flags={case.get('flag_count')}"
        rows.append(f'<text x="28" y="{y + 16}" font-family="Arial" font-size="13" fill="#111827">{_e(label)}</text>')
        rows.append(f'<rect x="{bar_x}" y="{y + 24}" width="{unique_bar}" height="12" rx="3" fill="{color}"/>')
        rows.append(f'<rect x="{bar_x}" y="{y + 42}" width="{repeated_bar}" height="12" rx="3" fill="#64748b"/>')
        rows.append(f'<text x="{bar_x + bar_w + 16}" y="{y + 35}" font-family="Arial" font-size="12" fill="#374151">unique={_ratio_label(ratio)}</text>')
        rows.append(f'<text x="{bar_x + bar_w + 16}" y="{y + 53}" font-family="Arial" font-size="12" fill="#374151">repeat={_ratio_label(repeated)}</text>')
        rows.append(f'<text x="28" y="{y + 48}" font-family="Arial" font-size="12" fill="#4b5563">{_e(str(case.get("continuation_preview") or ""))}</text>')
    summary = _dict(report.get("summary"))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">MiniGPT generation quality</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Status: {_e(str(summary.get("overall_status")))} | Cases: {summary.get("case_count")} | Avg chars: {summary.get("avg_continuation_chars")}</text>
  <text x="28" y="78" font-family="Arial" font-size="12" fill="#374151">Colored bars show unique ratio; gray bars show repeated n-gram ratio.</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def render_generation_quality_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Status", summary.get("overall_status")),
        ("Cases", summary.get("case_count")),
        ("Pass", summary.get("pass_count")),
        ("Warn", summary.get("warn_count")),
        ("Fail", summary.get("fail_count")),
        ("Avg chars", summary.get("avg_continuation_chars")),
        ("Avg unique", _ratio_label(summary.get("avg_unique_ratio"))),
        ("Max repeat", summary.get("max_repeat_run")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT generation quality report'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT generation quality report'))}</h1><p>{_e(report.get('source_path'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _key_value_section("Policy", _dict(report.get("policy"))),
            _case_section(_list_of_dicts(report.get("cases"))),
            _list_section("Recommendations", report.get("recommendations")),
            _list_section("Warnings", report.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT generation quality analyzer.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_generation_quality_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_generation_quality_html(report), encoding="utf-8")


def write_generation_quality_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "generation_quality.json",
        "csv": root / "generation_quality.csv",
        "markdown": root / "generation_quality.md",
        "svg": root / "generation_quality.svg",
        "html": root / "generation_quality.html",
    }
    write_generation_quality_json(report, paths["json"])
    write_generation_quality_csv(report, paths["csv"])
    write_generation_quality_markdown(report, paths["markdown"])
    write_generation_quality_svg(report, paths["svg"])
    write_generation_quality_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _case_section(cases: list[dict[str, Any]]) -> str:
    rows = []
    for case in cases:
        status = str(case.get("status") or "warn")
        flags = ", ".join(flag.get("id", "") for flag in _list_of_dicts(case.get("flags"))) or "none"
        rows.append(
            "<tr>"
            f'<td><span class="pill {status}">{_e(status)}</span></td>'
            f"<td><strong>{_e(case.get('name'))}</strong><br><span>{_e(case.get('prompt'))}</span></td>"
            f"<td>{_e(case.get('char_count'))}</td>"
            f"<td>{_e(_ratio_label(case.get('unique_ratio')))}</td>"
            f"<td>{_e(_ratio_label(case.get('repeated_ngram_ratio')))}</td>"
            f"<td>{_e(case.get('longest_repeat_run'))}</td>"
            f"<td>{_e(flags)}<br><span>{_e(case.get('continuation_preview'))}</span></td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Cases</h2><table><thead><tr><th>Status</th><th>Case</th><th>Chars</th><th>Unique</th><th>Repeated Ngram</th><th>Repeat Run</th><th>Flags</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _key_value_section(title: str, payload: dict[str, Any]) -> str:
    rows = "".join(f"<tr><th>{_e(key)}</th><td>{_e(_fmt_any(value))}</td></tr>" for key, value in payload.items())
    return f'<section class="panel"><h2>{_e(title)}</h2><table>{rows}</table></section>'


def _list_section(title: str, values: Any, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt_any(value))}</div>' + "</div>"


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#475569; --line:#d7dee8; --page:#f8fafc; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; --blue:#1d4ed8; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:900px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:54px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {_md(key)} | {_md(value)} |")
    return lines


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _flag_ids(case: dict[str, Any]) -> list[str]:
    return [str(flag.get("id")) for flag in _list_of_dicts(case.get("flags")) if flag.get("id")]


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _ratio_label(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "missing"
    return f"{number:.1%}"


def _status_color(status: str) -> str:
    return {"pass": "#047857", "warn": "#b45309", "fail": "#b91c1c"}.get(status, "#1d4ed8")


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


def _md(value: Any) -> str:
    return _fmt_any(value).replace("|", "\\|").replace("\n", " ")
