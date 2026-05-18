from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict,
    csv_cell,
    html_escape,
    list_of_dicts,
    markdown_cell,
    number_or_default,
    string_list,
    utc_now,
    write_json_payload,
)


def build_test_coverage_report(
    coverage_json_path: str | Path,
    *,
    project_root: str | Path | None = None,
    title: str = "MiniGPT test coverage report",
    generated_at: str | None = None,
    test_command: list[str] | None = None,
    fail_under: float | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve() if project_root is not None else None
    path = Path(coverage_json_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = _file_rows(payload, root)
    totals = as_dict(payload.get("totals"))
    fail_under_value = _fail_under_value(fail_under)
    line_coverage_percent = _round_percent(totals.get("percent_covered"))
    coverage_gap = _coverage_gap(line_coverage_percent, fail_under_value)
    threshold_enabled = fail_under_value is not None
    passed_threshold = coverage_gap == 0.0
    summary = {
        "status": "pass" if passed_threshold else "fail",
        "decision": _decision(threshold_enabled, passed_threshold),
        "coverage_json_path": _relative_path(path, root),
        "line_coverage_percent": line_coverage_percent,
        "covered_lines": _as_int(totals.get("covered_lines")),
        "num_statements": _as_int(totals.get("num_statements")),
        "missing_lines": _as_int(totals.get("missing_lines")),
        "file_count": len(files),
        "measured_file_count": sum(1 for item in files if _as_int(item.get("num_statements")) > 0),
        "threshold_enabled": threshold_enabled,
        "fail_under": fail_under_value,
        "coverage_gap": coverage_gap,
    }
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "summary": summary,
        "test_command": test_command or [],
        "files": files,
        "recommendations": _recommendations(summary),
    }


def write_test_coverage_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_test_coverage_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["path", "line_coverage_percent", "covered_lines", "num_statements", "missing_lines"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("files")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_test_coverage_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT test coverage report')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Decision: `{summary.get('decision')}`",
        f"- Line coverage: `{summary.get('line_coverage_percent')}`",
        f"- Covered lines: `{summary.get('covered_lines')}/{summary.get('num_statements')}`",
        f"- Threshold enabled: `{summary.get('threshold_enabled')}`",
        f"- Fail under: `{summary.get('fail_under')}`",
        f"- Coverage gap: `{summary.get('coverage_gap')}`",
        "",
        "## Lowest Coverage Files",
        "",
        "| File | Coverage | Covered | Statements | Missing |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in _lowest_coverage_files(report):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("path")),
                    markdown_cell(row.get("line_coverage_percent")),
                    markdown_cell(row.get("covered_lines")),
                    markdown_cell(row.get("num_statements")),
                    markdown_cell(row.get("missing_lines")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {markdown_cell(item)}" for item in string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_test_coverage_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_test_coverage_markdown(report), encoding="utf-8")


def render_test_coverage_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", summary.get("status")),
        ("Decision", summary.get("decision")),
        ("Line coverage", summary.get("line_coverage_percent")),
        ("Covered lines", f"{summary.get('covered_lines')}/{summary.get('num_statements')}"),
        ("Files", summary.get("file_count")),
        ("Threshold", f">= {summary.get('fail_under')}" if summary.get("threshold_enabled") else "off"),
        ("Gap", summary.get("coverage_gap")),
    ]
    rows = []
    for row in _lowest_coverage_files(report):
        rows.append(
            "<tr>"
            f"<td>{html_escape(row.get('path'))}</td>"
            f"<td>{html_escape(row.get('line_coverage_percent'))}</td>"
            f"<td>{html_escape(row.get('covered_lines'))}</td>"
            f"<td>{html_escape(row.get('num_statements'))}</td>"
            f"<td>{html_escape(row.get('missing_lines'))}</td>"
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
            f"<title>{html_escape(report.get('title', 'MiniGPT test coverage report'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{html_escape(report.get('title', 'MiniGPT test coverage report'))}</h1></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Lowest Coverage Files</h2><table><thead><tr><th>File</th><th>Coverage</th><th>Covered</th><th>Statements</th><th>Missing</th></tr></thead><tbody>'
            + "".join(rows)
            + "</tbody></table></section>",
            _list_section("Recommendations", report.get("recommendations")),
            "</body>",
            "</html>",
        ]
    )


def write_test_coverage_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_test_coverage_html(report), encoding="utf-8")


def write_test_coverage_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "test_coverage_report.json",
        "csv": root / "test_coverage_report.csv",
        "markdown": root / "test_coverage_report.md",
        "html": root / "test_coverage_report.html",
    }
    write_test_coverage_json(report, paths["json"])
    write_test_coverage_csv(report, paths["csv"])
    write_test_coverage_markdown(report, paths["markdown"])
    write_test_coverage_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _file_rows(payload: dict[str, Any], root: Path | None) -> list[dict[str, Any]]:
    files = as_dict(payload.get("files"))
    rows = []
    for raw_path, data in sorted(files.items()):
        file_data = as_dict(data)
        summary = as_dict(file_data.get("summary"))
        rows.append(
            {
                "path": _relative_path(Path(str(raw_path)), root),
                "line_coverage_percent": _round_percent(summary.get("percent_covered")),
                "covered_lines": _as_int(summary.get("covered_lines")),
                "num_statements": _as_int(summary.get("num_statements")),
                "missing_lines": _as_int(summary.get("missing_lines")),
            }
        )
    return rows


def _lowest_coverage_files(report: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    files = [row for row in list_of_dicts(report.get("files")) if _as_int(row.get("num_statements")) > 0]
    return sorted(files, key=lambda row: (float(row.get("line_coverage_percent") or 0), -_as_int(row.get("num_statements"))))[:limit]


def _recommendations(summary: dict[str, Any]) -> list[str]:
    percent = summary.get("line_coverage_percent")
    recommendations = []
    if summary.get("threshold_enabled"):
        fail_under = summary.get("fail_under")
        if summary.get("status") == "pass":
            recommendations.append(f"Coverage {percent}% meets the configured fail-under gate of {fail_under}%.")
        else:
            recommendations.append(
                f"Coverage {percent}% is {summary.get('coverage_gap')}% below the fail-under gate of {fail_under}%; add focused tests before raising the threshold."
            )
    else:
        recommendations.append(f"Use {percent}% as the initial observed coverage baseline before introducing a fail-under gate.")
    recommendations.append("Review the lowest-coverage files first; add focused tests before raising any threshold.")
    return recommendations


def _relative_path(path: Path, root: Path | None) -> str:
    try:
        value = str(path.resolve().relative_to(root)) if root is not None else str(path)
    except (OSError, ValueError):
        value = str(path)
    return value.replace("\\", "/")


def _round_percent(value: Any) -> float:
    return round(float(number_or_default(value, 0.0, float)), 2)


def _fail_under_value(value: float | None) -> float | None:
    if value is None:
        return None
    threshold = _round_percent(value)
    if threshold < 0 or threshold > 100:
        raise ValueError("fail_under must be between 0 and 100")
    return threshold


def _coverage_gap(percent: float, fail_under: float | None) -> float:
    if fail_under is None:
        return 0.0
    return round(max(0.0, fail_under - percent), 2)


def _decision(threshold_enabled: bool, passed_threshold: bool) -> str:
    if not threshold_enabled:
        return "record_coverage_baseline"
    return "continue_with_coverage_gate" if passed_threshold else "improve_test_coverage"


def _as_int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{html_escape(label)}</div>'
        f'<div class="value">{html_escape(value)}</div>'
        "</div>"
    )


def _list_section(title: str, values: Any) -> str:
    items = [item for item in string_list(values) if item.strip()]
    if not items:
        return ""
    return f'<section class="panel"><h2>{html_escape(title)}</h2><ul>' + "".join(f"<li>{html_escape(item)}</li>" for item in items) + "</ul></section>"


def _style() -> str:
    return """<style>
body { margin:0; background:#f7f8f3; color:#172033; font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid #d9dfd2; }
h1 { margin:0; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:#fff; border:1px solid #d9dfd2; border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:#596579; font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:19px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:760px; }
th, td { padding:9px 8px; border-bottom:1px solid #d9dfd2; text-align:left; vertical-align:top; }
th { color:#596579; font-size:12px; text-transform:uppercase; }
li { margin:8px 0; }
</style>"""


__all__ = [
    "build_test_coverage_report",
    "render_test_coverage_html",
    "render_test_coverage_markdown",
    "write_test_coverage_outputs",
]
