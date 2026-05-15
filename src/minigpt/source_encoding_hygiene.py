from __future__ import annotations

import ast
import csv
from pathlib import Path
from typing import Any, Iterable

from minigpt.report_utils import csv_cell, html_escape as _e, markdown_cell as _md, string_list as _string_list, utc_now, write_json_payload

BOM = b"\xef\xbb\xbf"
DEFAULT_SCAN_ROOTS = (Path("src"), Path("scripts"), Path("tests"))


def build_source_encoding_report(
    paths: Iterable[str | Path],
    *,
    project_root: str | Path | None = None,
    title: str = "MiniGPT source encoding hygiene",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve() if project_root is not None else None
    files = sorted((_scan_source_file(Path(path), root) for path in paths), key=lambda item: str(item["path"]))
    bom_files = [item for item in files if item["has_bom"]]
    syntax_errors = [item for item in files if not item["syntax_ok"]]
    summary = {
        "status": "pass" if not bom_files and not syntax_errors else "fail",
        "decision": "continue_with_clean_sources" if not bom_files and not syntax_errors else "fix_bom_or_syntax_errors",
        "source_count": len(files),
        "clean_count": sum(1 for item in files if item["syntax_ok"] and not item["has_bom"]),
        "bom_count": len(bom_files),
        "syntax_error_count": len(syntax_errors),
        "bom_paths": [item["path"] for item in bom_files],
        "syntax_error_paths": [item["path"] for item in syntax_errors],
    }
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "policy": {
            "roots": [str(path) for path in DEFAULT_SCAN_ROOTS],
            "encoding": "utf-8-sig",
            "bom_marker": "UTF-8 BOM",
        },
        "summary": summary,
        "files": files,
        "recommendations": _recommendations(summary),
    }


def write_source_encoding_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_source_encoding_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["path", "has_bom", "syntax_ok", "byte_count", "parse_error"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in _files(report):
            writer.writerow({field: csv_cell(item.get(field)) for field in fieldnames})


def render_source_encoding_markdown(report: dict[str, Any]) -> str:
    summary = _summary(report)
    lines = [
        f"# {_md(report.get('title', 'MiniGPT source encoding hygiene'))}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in ["source_count", "clean_count", "bom_count", "syntax_error_count"]:
        lines.append(f"| {_md(key)} | {_md(summary.get(key))} |")
    lines.extend(["", "## Offending Files", "", "| Path | BOM | Syntax OK | Bytes | Parse Error |", "| --- | --- | --- | --- | --- |"])
    offenders = [item for item in _files(report) if item.get("has_bom") or not item.get("syntax_ok")]
    if offenders:
        for item in offenders:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md(item.get("path")),
                        _md(item.get("has_bom")),
                        _md(item.get("syntax_ok")),
                        _md(item.get("byte_count")),
                        _md(item.get("parse_error") or ""),
                    ]
                )
                + " |"
            )
    else:
        lines.append("|  |  |  |  |  |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_source_encoding_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_source_encoding_markdown(report), encoding="utf-8")


def render_source_encoding_html(report: dict[str, Any]) -> str:
    summary = _summary(report)
    files = _files(report)
    offenders = [item for item in files if item.get("has_bom") or not item.get("syntax_ok")]
    stats = [
        ("Status", summary.get("status")),
        ("Decision", summary.get("decision")),
        ("Sources", summary.get("source_count")),
        ("BOM", summary.get("bom_count")),
        ("Syntax errors", summary.get("syntax_error_count")),
        ("Clean", summary.get("clean_count")),
    ]
    rows = "".join(_file_row(item) for item in offenders)
    if not rows:
        rows = '<tr><td colspan="5" class="muted">No BOM or syntax errors detected.</td></tr>'
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT source encoding hygiene'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT source encoding hygiene'))}</h1><p>Python sources should stay UTF-8 clean, and CI should fail before BOMs can trigger parse-time surprises.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            "<section><h2>Offending Files</h2><table><tr><th>Path</th><th>BOM</th><th>Syntax OK</th><th>Bytes</th><th>Parse Error</th></tr>"
            + rows
            + "</table></section>",
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT source encoding hygiene.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_source_encoding_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_source_encoding_html(report), encoding="utf-8")


def write_source_encoding_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "source_encoding_hygiene.json",
        "csv": root / "source_encoding_hygiene.csv",
        "markdown": root / "source_encoding_hygiene.md",
        "html": root / "source_encoding_hygiene.html",
    }
    write_source_encoding_json(report, paths["json"])
    write_source_encoding_csv(report, paths["csv"])
    write_source_encoding_markdown(report, paths["markdown"])
    write_source_encoding_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _scan_source_file(path: Path, project_root: Path | None) -> dict[str, Any]:
    data = path.read_bytes()
    has_bom = data.startswith(BOM)
    parse_error = ""
    try:
        ast.parse(data.decode("utf-8-sig"), filename=str(path))
        syntax_ok = True
    except SyntaxError as exc:
        syntax_ok = False
        parse_error = f"syntax-error:{exc.lineno or 1}"
    return {
        "path": _relative_path(path, project_root),
        "absolute_path": str(path.resolve()),
        "has_bom": has_bom,
        "syntax_ok": syntax_ok,
        "parse_error": parse_error,
        "byte_count": len(data),
    }


def _relative_path(path: Path, project_root: Path | None) -> str:
    if project_root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(project_root))
    except ValueError:
        return str(path)


def _summary(report: dict[str, Any]) -> dict[str, Any]:
    return dict(report.get("summary")) if isinstance(report.get("summary"), dict) else {}


def _files(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("files")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _recommendations(summary: dict[str, Any]) -> list[str]:
    recommendations = []
    if summary.get("bom_count", 0):
        recommendations.append("Remove UTF-8 BOM markers from the offending Python files and rerun the hygiene gate.")
    if summary.get("syntax_error_count", 0):
        recommendations.append("Fix the syntax errors reported by the hygiene gate before merging.")
    if not recommendations:
        recommendations.append("Keep Python sources UTF-8 clean so CI syntax checks stay predictable.")
    return recommendations


def _file_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('path'))}</td>"
        f"<td>{_e(item.get('has_bom'))}</td>"
        f"<td>{_e(item.get('syntax_ok'))}</td>"
        f"<td>{_e(item.get('byte_count'))}</td>"
        f"<td>{_e(item.get('parse_error'))}</td>"
        "</tr>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return f"<section><h2>{_e(title)}</h2><p class=\"muted\">None.</p></section>"
    return f"<section><h2>{_e(title)}</h2><ul>" + "".join(f"<li>{_e(item)}</li>" for item in values) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return f'<article class="stat"><span>{_e(label)}</span><strong>{_e(value)}</strong></article>'


def _style() -> str:
    return """
<style>
:root { color-scheme: light; font-family: Arial, "Microsoft YaHei", sans-serif; color: #172026; background: #f6f8fa; }
body { margin: 0; padding: 24px; }
header, section, footer { max-width: 1040px; margin: 0 auto 18px; }
header { padding: 18px 0 8px; border-bottom: 3px solid #1f7a5c; }
h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
h2 { margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }
p { margin: 0 0 10px; line-height: 1.5; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.stat { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 12px; min-height: 64px; }
.stat span { display: block; color: #5c6b73; font-size: 12px; margin-bottom: 8px; }
.stat strong { display: block; font-size: 18px; overflow-wrap: anywhere; }
section { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px; border-bottom: 1px solid #e5e9ef; text-align: left; vertical-align: top; }
th { background: #eef3f6; }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; }
.muted { color: #687782; }
footer { color: #687782; font-size: 12px; }
</style>
""".strip()


__all__ = [
    "DEFAULT_SCAN_ROOTS",
    "build_source_encoding_report",
    "render_source_encoding_html",
    "render_source_encoding_markdown",
    "write_source_encoding_csv",
    "write_source_encoding_html",
    "write_source_encoding_json",
    "write_source_encoding_markdown",
    "write_source_encoding_outputs",
]
