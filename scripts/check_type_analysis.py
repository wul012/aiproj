from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from collections.abc import Callable
from typing import Any

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path  # type: ignore[import-not-found,no-redef]

ensure_src_path()

from minigpt.report_utils import html_escape, markdown_cell, utc_now, write_json_payload  # noqa: E402

DEFAULT_SCOPE_PATH = Path("docs/static-analysis/mypy-scope.json")
DEFAULT_OUT_DIR = Path("runs/type-analysis")
DIAGNOSTIC_PATTERN = re.compile(
    r"^(?P<path>.*?):(?P<line>\d+)(?::(?P<column>\d+))?: (?P<severity>error|note): "
    r"(?P<message>.*?)(?: \[(?P<code>[^\]]+)\])?$"
)


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def load_scope(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("mypy scope must be a JSON object")
    return dict(payload)


def validate_scope(scope: dict[str, Any], project_root: str | Path) -> list[str]:
    root = Path(project_root).resolve()
    issues: list[str] = []
    if scope.get("schema_version") != 1:
        issues.append("schema_version must equal 1")
    if scope.get("tool") != "mypy":
        issues.append("tool must equal mypy")

    raw_targets = scope.get("targets")
    targets = [str(item) for item in raw_targets] if isinstance(raw_targets, list) else []
    if not targets:
        issues.append("targets must be a non-empty list")
    if len(targets) != len(set(targets)):
        issues.append("targets must not contain duplicates")

    floor = scope.get("scope_floor")
    if not isinstance(floor, int) or isinstance(floor, bool) or floor < 1:
        issues.append("scope_floor must be a positive integer")
    elif len(targets) < floor:
        issues.append(f"target count {len(targets)} is below scope_floor {floor}")

    target_set = set(targets)
    for target in targets:
        candidate = (root / target).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            issues.append(f"target escapes project root: {target}")
            continue
        if candidate.suffix != ".py":
            issues.append(f"target is not a Python file: {target}")
        if not candidate.is_file():
            issues.append(f"target does not exist: {target}")

    groups = scope.get("groups")
    grouped_targets: set[str] = set()
    if not isinstance(groups, dict) or not groups:
        issues.append("groups must be a non-empty object")
    else:
        for group_name, raw_group_targets in groups.items():
            if not isinstance(raw_group_targets, list) or not raw_group_targets:
                issues.append(f"group {group_name} must contain at least one target")
                continue
            for target in raw_group_targets:
                name = str(target)
                grouped_targets.add(name)
                if name not in target_set:
                    issues.append(f"group {group_name} references an undeclared target: {name}")
    for target in sorted(target_set - grouped_targets):
        issues.append(f"target is not assigned to a group: {target}")
    return issues


def scope_targets(scope: dict[str, Any]) -> tuple[str, ...]:
    raw_targets = scope.get("targets")
    if not isinstance(raw_targets, list):
        return ()
    return tuple(str(item) for item in raw_targets)


def parse_diagnostics(output: str, project_root: str | Path) -> list[dict[str, Any]]:
    root = Path(project_root).resolve()
    diagnostics: list[dict[str, Any]] = []
    for line in output.splitlines():
        match = DIAGNOSTIC_PATTERN.match(line.strip())
        if not match:
            continue
        path = Path(match.group("path"))
        if path.is_absolute():
            try:
                path_text = path.resolve().relative_to(root).as_posix()
            except ValueError:
                path_text = path.as_posix()
        else:
            path_text = path.as_posix()
        diagnostics.append(
            {
                "path": path_text,
                "line": int(match.group("line")),
                "column": int(match.group("column") or 0),
                "severity": match.group("severity"),
                "code": match.group("code") or "",
                "message": match.group("message"),
            }
        )
    return diagnostics


def build_report(
    *,
    project_root: str | Path = PROJECT_ROOT,
    scope_path: str | Path = DEFAULT_SCOPE_PATH,
    runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    manifest_path = Path(scope_path)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    scope = load_scope(manifest_path)
    scope_issues = validate_scope(scope, root)
    targets = scope_targets(scope)
    command = [sys.executable, "-m", "mypy", "--config-file", str(root / "pyproject.toml"), *targets]

    if scope_issues:
        return _report_payload(
            scope=scope,
            scope_path=manifest_path,
            command=command,
            return_code=2,
            diagnostics=[],
            scope_issues=scope_issues,
        )

    completed = runner(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    diagnostics = parse_diagnostics("\n".join([completed.stdout or "", completed.stderr or ""]), root)
    return _report_payload(
        scope=scope,
        scope_path=manifest_path,
        command=command,
        return_code=completed.returncode,
        diagnostics=diagnostics,
        scope_issues=[],
    )


def _report_payload(
    *,
    scope: dict[str, Any],
    scope_path: Path,
    command: list[str],
    return_code: int,
    diagnostics: list[dict[str, Any]],
    scope_issues: list[str],
) -> dict[str, Any]:
    status = "pass" if return_code == 0 and not scope_issues else "fail"
    decision = "continue_with_typed_scope" if status == "pass" else "repair_type_analysis"
    targets = scope_targets(scope)
    return {
        "schema_version": 1,
        "title": "MiniGPT scoped type analysis",
        "generated_at": utc_now(),
        "status": status,
        "decision": decision,
        "scope_path": str(scope_path),
        "command": command,
        "return_code": return_code,
        "summary": {
            "status": status,
            "decision": decision,
            "target_count": len(targets),
            "scope_floor": scope.get("scope_floor"),
            "group_count": len(scope.get("groups", {})) if isinstance(scope.get("groups"), dict) else 0,
            "diagnostic_count": len(diagnostics),
            "scope_issue_count": len(scope_issues),
        },
        "targets": list(targets),
        "scope_issues": scope_issues,
        "diagnostics": diagnostics,
    }


def write_report_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "type_analysis.json",
        "csv": root / "type_analysis.csv",
        "markdown": root / "type_analysis.md",
        "html": root / "type_analysis.html",
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["markdown"].write_text(render_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_html(report), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["kind", "path", "line", "column", "severity", "code", "message"]
    rows = [
        {"kind": "scope", "path": target, "line": "", "column": "", "severity": "", "code": "", "message": ""}
        for target in report.get("targets", [])
    ]
    rows.extend(
        {
            "kind": "diagnostic",
            "path": item.get("path"),
            "line": item.get("line"),
            "column": item.get("column"),
            "severity": item.get("severity"),
            "code": item.get("code"),
            "message": item.get("message"),
        }
        for item in report.get("diagnostics", [])
        if isinstance(item, dict)
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(report: dict[str, Any]) -> str:
    raw_summary = report.get("summary")
    summary = dict(raw_summary) if isinstance(raw_summary, dict) else {}
    lines = [
        "# MiniGPT Scoped Type Analysis",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Scope: `{report.get('scope_path')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in ("target_count", "scope_floor", "group_count", "diagnostic_count", "scope_issue_count"):
        lines.append(f"| {key} | {markdown_cell(summary.get(key))} |")
    lines.extend(["", "## Targets", ""])
    lines.extend(f"- `{target}`" for target in report.get("targets", []))
    lines.extend(["", "## Scope Issues", ""])
    scope_issues = report.get("scope_issues", [])
    lines.extend(f"- {markdown_cell(issue)}" for issue in scope_issues)
    if not scope_issues:
        lines.append("- none")
    lines.extend(["", "## Diagnostics", ""])
    diagnostics = report.get("diagnostics", [])
    for item in diagnostics:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('path')}:{item.get('line')}:{item.get('column')}` "
                f"`{item.get('code')}` {markdown_cell(item.get('message'))}"
            )
    if not diagnostics:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def render_html(report: dict[str, Any]) -> str:
    raw_summary = report.get("summary")
    summary = dict(raw_summary) if isinstance(raw_summary, dict) else {}
    target_rows = "".join(f"<li><code>{html_escape(target)}</code></li>" for target in report.get("targets", []))
    diagnostic_rows = "".join(
        "<tr>"
        f"<td>{html_escape(item.get('path'))}</td>"
        f"<td>{html_escape(item.get('line'))}</td>"
        f"<td>{html_escape(item.get('code'))}</td>"
        f"<td>{html_escape(item.get('message'))}</td>"
        "</tr>"
        for item in report.get("diagnostics", [])
        if isinstance(item, dict)
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MiniGPT scoped type analysis</title><style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f4f7f8;color:#172026;margin:0}}
main{{max-width:1080px;margin:auto;padding:28px}}header,.panel{{background:#fff;border:1px solid #d8dee4;border-radius:8px;padding:18px;margin-bottom:14px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.stat{{background:#eef4f5;padding:12px;border-radius:6px}}
table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #d8dee4;padding:8px;text-align:left}}code{{overflow-wrap:anywhere}}
</style></head><body><main>
<header><h1>MiniGPT scoped type analysis</h1><p>Status: <strong>{html_escape(report.get("status"))}</strong> | Decision: <code>{html_escape(report.get("decision"))}</code></p></header>
<section class="panel stats"><div class="stat">Targets<br><strong>{html_escape(summary.get("target_count"))}</strong></div><div class="stat">Scope floor<br><strong>{html_escape(summary.get("scope_floor"))}</strong></div><div class="stat">Diagnostics<br><strong>{html_escape(summary.get("diagnostic_count"))}</strong></div><div class="stat">Scope issues<br><strong>{html_escape(summary.get("scope_issue_count"))}</strong></div></section>
<section class="panel"><h2>Checked targets</h2><ul>{target_rows}</ul></section>
<section class="panel"><h2>Diagnostics</h2><table><thead><tr><th>Path</th><th>Line</th><th>Code</th><th>Message</th></tr></thead><tbody>{diagnostic_rows}</tbody></table></section>
</main></body></html>"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run strict mypy over the committed ratcheted scope.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--no-fail", action="store_true", help="Always return zero after writing the report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(project_root=args.project_root, scope_path=args.scope)
    outputs = write_report_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"target_count={summary['target_count']}")
    print(f"diagnostic_count={summary['diagnostic_count']}")
    print(f"scope_issue_count={summary['scope_issue_count']}")
    print(f"outputs={json.dumps(outputs, ensure_ascii=False)}")
    return 0 if report["status"] == "pass" or args.no_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
