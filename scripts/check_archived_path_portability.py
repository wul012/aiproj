from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.report_utils import (  # noqa: E402
    archived_reference_path,
    html_escape as _e,
    markdown_cell as _md,
    resolve_archived_reference_path,
)

CHECK_JSON_FILENAME = "archived_path_portability.json"
CHECK_CSV_FILENAME = "archived_path_portability.csv"
CHECK_TEXT_FILENAME = "archived_path_portability.txt"
CHECK_MARKDOWN_FILENAME = "archived_path_portability.md"
CHECK_HTML_FILENAME = "archived_path_portability.html"

DEFAULT_INPUTS = (
    Path("d") / "448" / "解释" / "promoted-handoff" / "promoted_training_scale_seed_handoff.json",
    Path("d") / "448" / "解释" / "receipt-check" / "promoted_training_scale_seed_handoff_automation_receipt_check.json",
    Path("d") / "448" / "解释" / "embedded-receipt-check" / "promoted_training_scale_seed_handoff_embedded_receipt_check.json",
    Path("d") / "448" / "解释" / "handoff-assurance" / "promoted_training_scale_seed_handoff_assurance.json",
)

PATH_VALUE_KEYS = {
    "path",
    "json",
    "csv",
    "text",
    "markdown",
    "html",
    "svg",
    "receipt_path",
    "receipt_check_json",
    "receipt_check_text",
    "handoff_report_path",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check archived JSON path references for cross-platform portability.")
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help="JSON files to scan. Defaults to the archived v448 promoted seed receipt handoff sidecars.",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root used to resolve archived relative paths.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "archived-path-portability")
    parser.add_argument("--no-fail", action="store_true", help="Write outputs but do not exit non-zero on failures.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    inputs = tuple(args.inputs) if args.inputs else DEFAULT_INPUTS
    report = build_archived_path_portability_report(inputs, root=args.root)
    outputs = write_archived_path_portability_outputs(report, args.out_dir)
    print(render_archived_path_portability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report["status"] == "fail" and not args.no_fail:
        raise SystemExit(1)


def build_archived_path_portability_report(inputs: Sequence[str | Path], *, root: str | Path = ROOT) -> dict[str, Any]:
    root_path = Path(root)
    source_rows = [_source_row(item, root_path) for item in inputs]
    references: list[dict[str, Any]] = []
    source_issues: list[str] = []
    for row in source_rows:
        source_path = Path(str(row["resolved_path"]))
        if not row["exists"]:
            source_issues.append(f"source JSON does not exist: {row['input']}")
            continue
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            source_issues.append(f"source JSON could not be read: {row['input']}: {exc}")
            continue
        references.extend(_reference_rows(payload, source_path=source_path, root=root_path))
    failed_references = [row for row in references if row["status"] != "pass"]
    status = "pass" if not source_issues and not failed_references and references else "fail"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "continue" if status == "pass" else "fix_archived_path_portability",
        "root": str(root_path),
        "source_count": len(source_rows),
        "missing_source_count": sum(1 for row in source_rows if not row["exists"]),
        "path_reference_count": len(references),
        "windows_separator_count": sum(1 for row in references if row["has_windows_separator"]),
        "portable_reference_count": sum(1 for row in references if row["status"] == "pass"),
        "failed_reference_count": len(failed_references),
        "sources": source_rows,
        "references": references,
        "issues": source_issues + [row["detail"] for row in failed_references],
    }


def render_archived_path_portability_text(report: dict[str, Any]) -> str:
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("source_count", report.get("source_count")),
        ("missing_source_count", report.get("missing_source_count")),
        ("path_reference_count", report.get("path_reference_count")),
        ("windows_separator_count", report.get("windows_separator_count")),
        ("portable_reference_count", report.get("portable_reference_count")),
        ("failed_reference_count", report.get("failed_reference_count")),
    ]
    for index, issue in enumerate(_string_list(report.get("issues")), start=1):
        rows.append((f"issue_{index}", issue))
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_archived_path_portability_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Archived Path Portability Check",
        "",
        f"- Status: `{_md(report.get('status'))}`",
        f"- Decision: `{_md(report.get('decision'))}`",
        f"- Sources: `{_md(report.get('source_count'))}`",
        f"- Path references: `{_md(report.get('path_reference_count'))}`",
        f"- Windows separator references: `{_md(report.get('windows_separator_count'))}`",
        f"- Failed references: `{_md(report.get('failed_reference_count'))}`",
        "",
        "## References",
        "",
        "| Source | JSON path | Raw | Normalized | Exists | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in _dict_list(report.get("references")):
        lines.append(
            f"| {_md(row.get('source_json'))} | {_md(row.get('json_path'))} | {_md(row.get('raw'))} | "
            f"{_md(row.get('normalized'))} | {_md(row.get('exists'))} | {_md(row.get('status'))} |"
        )
    lines.extend(["", "## Issues", ""])
    issues = _string_list(report.get("issues"))
    lines.extend(f"- {_md(issue)}" for issue in issues) if issues else lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def render_archived_path_portability_html(report: dict[str, Any]) -> str:
    reference_rows = "\n".join(
        "<tr>"
        f"<td>{_e(row.get('source_json'))}</td>"
        f"<td>{_e(row.get('json_path'))}</td>"
        f"<td>{_e(row.get('raw'))}</td>"
        f"<td>{_e(row.get('normalized'))}</td>"
        f"<td>{_e(row.get('exists'))}</td>"
        f"<td>{_e(row.get('status'))}</td>"
        f"<td>{_e(row.get('detail'))}</td>"
        "</tr>"
        for row in _dict_list(report.get("references"))
    )
    issue_items = "\n".join(f"<li>{_e(issue)}</li>" for issue in _string_list(report.get("issues"))) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT archived path portability</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f6f8fa; color: #172029; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1120px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d7dee3; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ margin: 0 0 12px; font-size: 28px; letter-spacing: 0; }}
h2 {{ margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d7dee3; border-radius: 8px; background: #fbfcfd; padding: 10px; }}
.metric span {{ color: #5a6871; display: block; font-size: 12px; }}
.metric strong {{ display: block; overflow-wrap: anywhere; margin-top: 6px; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid #d7dee3; padding: 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }}
th {{ background: #eef3f6; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT archived path portability</h1>
<section>
<h2>Summary</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{_e(report.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{_e(report.get('decision'))}</strong></div>
<div class="metric"><span>Sources</span><strong>{_e(report.get('source_count'))}</strong></div>
<div class="metric"><span>References</span><strong>{_e(report.get('path_reference_count'))}</strong></div>
<div class="metric"><span>Windows separators</span><strong>{_e(report.get('windows_separator_count'))}</strong></div>
<div class="metric"><span>Failed</span><strong>{_e(report.get('failed_reference_count'))}</strong></div>
</div>
</section>
<section>
<h2>References</h2>
<table>
<thead><tr><th>Source</th><th>JSON path</th><th>Raw</th><th>Normalized</th><th>Exists</th><th>Status</th><th>Detail</th></tr></thead>
<tbody>
{reference_rows}
</tbody>
</table>
</section>
<section>
<h2>Issues</h2>
<ul>
{issue_items}
</ul>
</section>
</main>
</body>
</html>
"""


def write_archived_path_portability_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / CHECK_JSON_FILENAME,
        "csv": root / CHECK_CSV_FILENAME,
        "text": root / CHECK_TEXT_FILENAME,
        "markdown": root / CHECK_MARKDOWN_FILENAME,
        "html": root / CHECK_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_archived_path_portability_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_archived_path_portability_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_archived_path_portability_html(report), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _source_row(path: str | Path, root: Path) -> dict[str, Any]:
    raw_path = Path(path)
    resolved = raw_path if raw_path.is_absolute() else root / raw_path
    return {"input": str(path), "resolved_path": str(resolved), "exists": resolved.is_file()}


def _reference_rows(payload: Any, *, source_path: Path, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key_path, key, value in _walk_json(payload):
        if not _is_path_reference_key(key) or not _looks_like_path(value):
            continue
        if not _is_receipt_portability_reference(value):
            continue
        normalized_path = archived_reference_path(value)
        resolved_path = resolve_archived_reference_path(value, root)
        exists = bool(resolved_path and resolved_path.exists())
        rows.append(
            {
                "id": f"{source_path.name}:{key_path}",
                "source_json": str(source_path),
                "json_path": key_path,
                "raw": value,
                "normalized": str(normalized_path),
                "resolved": str(resolved_path) if resolved_path is not None else "",
                "has_windows_separator": "\\" in value,
                "exists": exists,
                "status": "pass" if exists else "fail",
                "detail": (
                    "Archived path resolves on this platform."
                    if exists
                    else f"Archived path does not resolve after separator normalization: {value}"
                ),
            }
        )
    return rows


def _walk_json(value: Any, prefix: str = "$") -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            rows.extend(_walk_json(item, f"{prefix}.{key_text}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(_walk_json(item, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        rows.append((prefix, prefix.rsplit(".", 1)[-1].split("[", 1)[0], value))
    return rows


def _is_path_reference_key(key: str) -> bool:
    key_lower = key.lower()
    return key_lower in PATH_VALUE_KEYS or key_lower.endswith("_path") or key_lower.endswith("_resolved")


def _looks_like_path(value: str) -> bool:
    if not value or "\n" in value:
        return False
    return "/" in value or "\\" in value


def _is_receipt_portability_reference(value: str) -> bool:
    normalized = value.replace("\\", "/").lower()
    return any(
        marker in normalized
        for marker in (
            "receipt",
            "assurance",
            "promoted-handoff",
            "embedded-receipt-check",
            "handoff-assurance",
        )
    )


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["id", "source_json", "json_path", "raw", "normalized", "resolved", "has_windows_separator", "exists", "status", "detail"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(_dict_list(report.get("references")))


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


if __name__ == "__main__":
    main()
