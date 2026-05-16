from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any


def write_eval_suite_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_eval_suite_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "task_type",
        "difficulty",
        "prompt",
        "expected_behavior",
        "tags",
        "max_new_tokens",
        "temperature",
        "top_k",
        "seed",
        "char_count",
        "unique_char_count",
        "continuation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in report["results"]:
            row = {field: result.get(field) for field in fieldnames}
            row["tags"] = ",".join(result.get("tags") or [])
            writer.writerow(row)


def write_eval_suite_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = list(report["results"])
    width = 980
    row_h = 64
    top = 92
    height = top + row_h * len(results) + 54
    bar_x = 240
    bar_w = 470
    max_unique = max((int(result["unique_char_count"]) for result in results), default=1)
    rows = []
    for index, result in enumerate(results):
        y = top + index * row_h
        unique = int(result["unique_char_count"])
        bar = 0 if max_unique == 0 else max(2, int(bar_w * unique / max_unique))
        label = (
            f"{result['name']} [{result.get('task_type', 'general')}/{result.get('difficulty', 'medium')}] "
            f"seed={result['seed']} temp={result['temperature']} top_k={result['top_k'] or 'none'}"
        )
        rows.append(f'<text x="28" y="{y + 18}" font-family="Arial" font-size="13" fill="#111827">{html.escape(label)}</text>')
        rows.append(f'<rect x="{bar_x}" y="{y + 28}" width="{bar}" height="16" rx="3" fill="#7c3aed"/>')
        rows.append(f'<text x="{bar_x + bar + 10}" y="{y + 42}" font-family="Arial" font-size="12" fill="#374151">unique={unique}</text>')
        rows.append(f'<text x="28" y="{y + 48}" font-family="Arial" font-size="12" fill="#4b5563">{html.escape(_clip(str(result.get("continuation", "")), 56))}</text>')
    benchmark = report.get("benchmark") if isinstance(report.get("benchmark"), dict) else {}
    title = benchmark.get("suite_name") or "MiniGPT benchmark eval suite"
    version = benchmark.get("suite_version")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f7f7f2"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">{html.escape(str(title))}</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Version: {html.escape(str(version or 'n/a'))} | Fixed prompts: {report.get('case_count')} | Avg continuation chars: {report.get('avg_continuation_chars')}</text>
  <text x="28" y="76" font-family="Arial" font-size="12" fill="#374151">Purple bars compare unique characters per continuation.</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def render_eval_suite_html(report: dict[str, Any]) -> str:
    benchmark = report.get("benchmark") if isinstance(report.get("benchmark"), dict) else {}
    task_counts = benchmark.get("task_type_counts") or report.get("task_type_counts") or {}
    difficulty_counts = benchmark.get("difficulty_counts") or report.get("difficulty_counts") or {}
    stats = [
        ("Suite", benchmark.get("suite_name") or report.get("suite")),
        ("Version", benchmark.get("suite_version")),
        ("Cases", report.get("case_count")),
        ("Avg chars", report.get("avg_continuation_chars")),
        ("Avg unique", report.get("avg_unique_chars")),
        ("Tasks", _join_counts(task_counts)),
        ("Difficulty", _join_counts(difficulty_counts)),
    ]
    result_rows = []
    for result in report.get("results", []):
        if not isinstance(result, dict):
            continue
        result_rows.append(
            "<tr>"
            f"<td>{_e(result.get('name'))}</td>"
            f"<td>{_e(result.get('task_type'))}</td>"
            f"<td>{_e(result.get('difficulty'))}</td>"
            f"<td>{_e(result.get('seed'))}</td>"
            f"<td>{_e(result.get('unique_char_count'))}</td>"
            f"<td>{_e(_clip(str(result.get('prompt', '')), 44))}</td>"
            f"<td>{_e(_clip(str(result.get('continuation', '')), 72))}</td>"
            f"<td>{_e(_clip(str(result.get('expected_behavior', '')), 72))}</td>"
            "</tr>"
        )
    summary_rows = []
    for item in benchmark.get("task_type_summary") or []:
        if isinstance(item, dict):
            summary_rows.append(
                "<tr>"
                f"<td>{_e(item.get('key'))}</td>"
                f"<td>{_e(item.get('case_count'))}</td>"
                f"<td>{_e(item.get('avg_continuation_chars'))}</td>"
                f"<td>{_e(item.get('avg_unique_chars'))}</td>"
                "</tr>"
            )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(benchmark.get('suite_name') or 'MiniGPT benchmark eval suite')}</title>",
            _html_style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(benchmark.get('suite_name') or 'MiniGPT benchmark eval suite')}</h1><p>{_e(benchmark.get('description') or 'Fixed prompt benchmark report')}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Task Summary</h2><table><thead><tr><th>Task</th><th>Cases</th><th>Avg Chars</th><th>Avg Unique</th></tr></thead><tbody>'
            + "".join(summary_rows)
            + "</tbody></table></section>",
            '<section class="panel"><h2>Prompt Results</h2><table><thead><tr><th>Name</th><th>Task</th><th>Difficulty</th><th>Seed</th><th>Unique</th><th>Prompt</th><th>Continuation</th><th>Expected Behavior</th></tr></thead><tbody>'
            + "".join(result_rows)
            + "</tbody></table></section>",
            "<footer>Generated by MiniGPT eval suite.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_eval_suite_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_eval_suite_html(report), encoding="utf-8")


def write_eval_suite_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "eval_suite.json",
        "csv": root / "eval_suite.csv",
        "svg": root / "eval_suite.svg",
        "html": root / "eval_suite.html",
    }
    write_eval_suite_json(report, paths["json"])
    write_eval_suite_csv(report, paths["csv"])
    write_eval_suite_svg(report, paths["svg"])
    write_eval_suite_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _clip(text: str, limit: int) -> str:
    flat = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "..."


def _join_counts(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return ""
    return ", ".join(f"{key}={count}" for key, count in value.items())


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _stat(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e(value)}</div></div>'


def _html_style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee8; --page:#f6f8fb; --panel:#ffffff; --accent:#2563eb; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:30px 36px 18px; background:#ffffff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 14px; font-size:20px; letter-spacing:0; }
p { margin:0; color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; padding:18px 36px 0; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
.card { padding:14px 16px; min-height:74px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:16px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 36px; padding:18px; overflow:auto; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th, td { padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:#1f2937; background:#eef2f7; font-weight:700; }
footer { padding:12px 36px 28px; color:var(--muted); font-size:12px; }
</style>"""


__all__ = [
    "render_eval_suite_html",
    "write_eval_suite_csv",
    "write_eval_suite_html",
    "write_eval_suite_json",
    "write_eval_suite_outputs",
    "write_eval_suite_svg",
]
