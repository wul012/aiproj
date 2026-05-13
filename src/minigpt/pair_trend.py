from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any


def load_pair_batch_report(path: str | Path) -> dict[str, Any]:
    report_path = Path(path)
    payload = json.loads(report_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair batch report must be a JSON object")
    if payload.get("kind") not in {None, "minigpt_pair_generation_batch"}:
        raise ValueError(f"unsupported pair batch report kind: {payload.get('kind')}")
    payload = dict(payload)
    payload["_source_path"] = str(report_path)
    return payload


def build_pair_batch_trend_report(
    reports: list[dict[str, Any]],
    *,
    names: list[str] | None = None,
) -> dict[str, Any]:
    if not reports:
        raise ValueError("pair batch trend report requires at least one report")
    resolved_names = _resolve_names(reports, names)
    summaries = [_report_summary(report, resolved_names[index], index) for index, report in enumerate(reports)]
    case_trends = _case_trends(reports, resolved_names)
    max_abs_generated = max((int(item.get("max_abs_generated_char_delta") or 0) for item in case_trends), default=0)
    max_abs_continuation = max((int(item.get("max_abs_continuation_char_delta") or 0) for item in case_trends), default=0)
    changed_cases = sum(1 for item in case_trends if item.get("generated_equal_variants") not in ([], [True], [False]))
    return {
        "schema_version": 1,
        "kind": "minigpt_pair_batch_trend",
        "report_count": len(reports),
        "case_count": len(case_trends),
        "changed_generated_equal_cases": changed_cases,
        "max_abs_generated_char_delta": max_abs_generated,
        "max_abs_continuation_char_delta": max_abs_continuation,
        "reports": summaries,
        "case_trends": case_trends,
        "largest_generated_delta_cases": sorted(
            case_trends,
            key=lambda item: (int(item.get("max_abs_generated_char_delta") or 0), item.get("name") or ""),
            reverse=True,
        )[:10],
    }


def write_pair_batch_trend_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_pair_batch_trend_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case",
        "task_type",
        "difficulty",
        "report_name",
        "left_checkpoint_id",
        "right_checkpoint_id",
        "generated_equal",
        "continuation_equal",
        "generated_char_delta",
        "continuation_char_delta",
        "left_continuation_chars",
        "right_continuation_chars",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in report.get("case_trends", []):
            for entry in case.get("entries", []):
                writer.writerow(
                    {
                        "case": case.get("name"),
                        "task_type": case.get("task_type"),
                        "difficulty": case.get("difficulty"),
                        "report_name": entry.get("report_name"),
                        "left_checkpoint_id": entry.get("left_checkpoint_id"),
                        "right_checkpoint_id": entry.get("right_checkpoint_id"),
                        "generated_equal": entry.get("generated_equal"),
                        "continuation_equal": entry.get("continuation_equal"),
                        "generated_char_delta": entry.get("generated_char_delta"),
                        "continuation_char_delta": entry.get("continuation_char_delta"),
                        "left_continuation_chars": entry.get("left_continuation_chars"),
                        "right_continuation_chars": entry.get("right_continuation_chars"),
                    }
                )


def render_pair_batch_trend_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MiniGPT Pair Batch Trend",
        "",
        f"- Reports: {report.get('report_count')}",
        f"- Cases: {report.get('case_count')}",
        f"- Changed generated-equal cases: {report.get('changed_generated_equal_cases')}",
        f"- Max abs generated delta: {report.get('max_abs_generated_char_delta')}",
        f"- Max abs continuation delta: {report.get('max_abs_continuation_char_delta')}",
        "",
        "## Reports",
        "",
        "| Name | Suite | Pair | Cases | Generated Diff | Avg Abs Gen Delta |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for item in report.get("reports", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("name")),
                    _md(f"{item.get('suite_name') or 'n/a'} v{item.get('suite_version') or 'n/a'}"),
                    _md(f"{item.get('left_checkpoint_id')} -> {item.get('right_checkpoint_id')}"),
                    _md(item.get("case_count")),
                    _md(item.get("generated_difference_count")),
                    _md(item.get("avg_abs_generated_char_delta")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Case Trends",
            "",
            "| Case | Task | Appearances | Equal Variants | Max Abs Gen Delta | Max Abs Cont Delta |",
            "| --- | --- | ---: | --- | ---: | ---: |",
        ]
    )
    for case in report.get("case_trends", []):
        variants = ",".join(str(value) for value in case.get("generated_equal_variants") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(case.get("name")),
                    _md(case.get("task_type")),
                    _md(case.get("appearances")),
                    _md(variants),
                    _md(case.get("max_abs_generated_char_delta")),
                    _md(case.get("max_abs_continuation_char_delta")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_pair_batch_trend_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_pair_batch_trend_markdown(report), encoding="utf-8")


def render_pair_batch_trend_html(report: dict[str, Any]) -> str:
    stats = [
        ("Reports", report.get("report_count")),
        ("Cases", report.get("case_count")),
        ("Changed", report.get("changed_generated_equal_cases")),
        ("Max Gen Delta", report.get("max_abs_generated_char_delta")),
        ("Max Cont Delta", report.get("max_abs_continuation_char_delta")),
    ]
    report_rows = []
    for item in report.get("reports", []):
        report_rows.append(
            "<tr>"
            f"<td>{_e(item.get('name'))}</td>"
            f"<td>{_e(item.get('suite_name'))} v{_e(item.get('suite_version'))}</td>"
            f"<td>{_e(item.get('left_checkpoint_id'))} -> {_e(item.get('right_checkpoint_id'))}</td>"
            f"<td>{_e(item.get('case_count'))}</td>"
            f"<td>{_e(item.get('generated_difference_count'))}</td>"
            f"<td>{_e(item.get('avg_abs_generated_char_delta'))}</td>"
            "</tr>"
        )
    case_rows = []
    for case in report.get("case_trends", []):
        variants = ", ".join(str(value) for value in case.get("generated_equal_variants") or [])
        case_rows.append(
            "<tr>"
            f"<td>{_e(case.get('name'))}</td>"
            f"<td>{_e(case.get('task_type'))}</td>"
            f"<td>{_e(case.get('difficulty'))}</td>"
            f"<td>{_e(case.get('appearances'))}</td>"
            f"<td>{_e(variants)}</td>"
            f"<td>{_e(case.get('max_abs_generated_char_delta'))}</td>"
            f"<td>{_e(case.get('max_abs_continuation_char_delta'))}</td>"
            "</tr>"
        )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>MiniGPT pair batch trend</title>",
            _html_style(),
            "</head>",
            "<body>",
            "<header><h1>MiniGPT Pair Batch Trend</h1><p>Compare saved pair-generation batch reports across checkpoint pairs or versions.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Reports</h2><table><thead><tr><th>Name</th><th>Suite</th><th>Pair</th><th>Cases</th><th>Generated Diff</th><th>Avg Abs Gen Delta</th></tr></thead><tbody>'
            + "".join(report_rows)
            + "</tbody></table></section>",
            '<section class="panel"><h2>Case Trends</h2><table><thead><tr><th>Case</th><th>Task</th><th>Difficulty</th><th>Appearances</th><th>Equal Variants</th><th>Max Abs Gen Delta</th><th>Max Abs Cont Delta</th></tr></thead><tbody>'
            + "".join(case_rows)
            + "</tbody></table></section>",
            "<footer>Generated by MiniGPT pair batch trend.</footer>",
            "</body></html>",
        ]
    )


def write_pair_batch_trend_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_pair_batch_trend_html(report), encoding="utf-8")


def write_pair_batch_trend_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "pair_batch_trend.json",
        "csv": root / "pair_batch_trend.csv",
        "md": root / "pair_batch_trend.md",
        "html": root / "pair_batch_trend.html",
    }
    write_pair_batch_trend_json(report, paths["json"])
    write_pair_batch_trend_csv(report, paths["csv"])
    write_pair_batch_trend_markdown(report, paths["md"])
    write_pair_batch_trend_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_names(reports: list[dict[str, Any]], names: list[str] | None) -> list[str]:
    if names is not None and len(names) != len(reports):
        raise ValueError("--name count must match report count")
    if names is not None:
        return [str(name) for name in names]
    resolved = []
    for index, report in enumerate(reports, start=1):
        source = report.get("_source_path")
        if source:
            path = Path(str(source))
            resolved.append(path.parent.name or path.stem)
        else:
            resolved.append(f"report-{index}")
    return resolved


def _report_summary(report: dict[str, Any], name: str, index: int) -> dict[str, Any]:
    suite = _pick_dict(report, "suite")
    left = _pick_dict(report, "left")
    right = _pick_dict(report, "right")
    return {
        "index": index,
        "name": name,
        "path": report.get("_source_path"),
        "suite_name": suite.get("name"),
        "suite_version": suite.get("version"),
        "left_checkpoint_id": left.get("checkpoint_id"),
        "right_checkpoint_id": right.get("checkpoint_id"),
        "case_count": report.get("case_count"),
        "generated_equal_count": report.get("generated_equal_count"),
        "generated_difference_count": report.get("generated_difference_count"),
        "continuation_difference_count": report.get("continuation_difference_count"),
        "avg_abs_generated_char_delta": report.get("avg_abs_generated_char_delta"),
        "avg_abs_continuation_char_delta": report.get("avg_abs_continuation_char_delta"),
    }


def _case_trends(reports: list[dict[str, Any]], names: list[str]) -> list[dict[str, Any]]:
    cases: dict[str, list[dict[str, Any]]] = {}
    for report_index, report in enumerate(reports):
        report_name = names[report_index]
        left = _pick_dict(report, "left")
        right = _pick_dict(report, "right")
        for result in report.get("results", []):
            if not isinstance(result, dict):
                continue
            name = str(result.get("name") or f"case-{len(cases) + 1}")
            comparison = _pick_dict(result, "comparison")
            entry = {
                "report_name": report_name,
                "report_index": report_index,
                "left_checkpoint_id": left.get("checkpoint_id"),
                "right_checkpoint_id": right.get("checkpoint_id"),
                "generated_equal": comparison.get("generated_equal"),
                "continuation_equal": comparison.get("continuation_equal"),
                "generated_char_delta": comparison.get("generated_char_delta"),
                "continuation_char_delta": comparison.get("continuation_char_delta"),
                "left_continuation_chars": comparison.get("left_continuation_chars"),
                "right_continuation_chars": comparison.get("right_continuation_chars"),
            }
            cases.setdefault(name, []).append(
                {
                    "meta": {
                        "name": name,
                        "task_type": result.get("task_type"),
                        "difficulty": result.get("difficulty"),
                    },
                    "entry": entry,
                }
            )
    trends = []
    for name in sorted(cases):
        items = cases[name]
        entries = [item["entry"] for item in items]
        meta = next((item["meta"] for item in items if item.get("meta")), {"name": name})
        generated_variants = sorted({entry.get("generated_equal") for entry in entries if entry.get("generated_equal") is not None}, key=str)
        continuation_variants = sorted({entry.get("continuation_equal") for entry in entries if entry.get("continuation_equal") is not None}, key=str)
        trends.append(
            {
                "name": name,
                "task_type": meta.get("task_type"),
                "difficulty": meta.get("difficulty"),
                "appearances": len(entries),
                "generated_difference_reports": sum(1 for entry in entries if entry.get("generated_equal") is False),
                "continuation_difference_reports": sum(1 for entry in entries if entry.get("continuation_equal") is False),
                "generated_equal_variants": generated_variants,
                "continuation_equal_variants": continuation_variants,
                "max_abs_generated_char_delta": _max_abs(entry.get("generated_char_delta") for entry in entries),
                "max_abs_continuation_char_delta": _max_abs(entry.get("continuation_char_delta") for entry in entries),
                "entries": entries,
            }
        )
    return trends


def _max_abs(values: Any) -> int:
    items = [abs(int(value)) for value in values if value is not None]
    return max(items, default=0)


def _pick_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _md(value: Any) -> str:
    return str("" if value is None else value).replace("|", "\\|").replace("\n", "\\n")


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
