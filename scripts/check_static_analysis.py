from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT  # type: ignore[import-not-found,no-redef]

ROOT = PROJECT_ROOT
DEFAULT_TARGETS = ("src", "scripts")
DEFAULT_BASELINE = ROOT / "docs" / "static-analysis" / "ruff-baseline.json"
DEFAULT_OUT_DIR = ROOT / "runs" / "static-analysis"
DEFAULT_STRICT_PATHS = (
    "scripts/check_static_analysis.py",
    "scripts/check_type_analysis.py",
    "scripts/check_model_capability_honest_measurement.py",
    "scripts/check_artifact_schema_guard.py",
    "scripts/check_file_size_ratchet.py",
    "scripts/check_aiproj_track_closeout.py",
    "scripts/check_archive_runs_inventory.py",
    "scripts/check_engineering_health.py",
    "scripts/_bootstrap.py",
    "scripts/_engineering_health.py",
    "src/minigpt/ci_workflow_hygiene.py",
    "src/minigpt/ci_workflow_hygiene_policy.py",
    "src/minigpt/model_capability_honest_measurement.py",
    "src/minigpt/artifact_schema_guard.py",
    "src/minigpt/file_size_ratchet.py",
    "src/minigpt/aiproj_track_closeout.py",
)

Runner = Callable[..., subprocess.CompletedProcess[str]]
IssueKey = tuple[str, str, str, str]


@dataclass(frozen=True)
class RuffCommandResult:
    command: tuple[str, ...]
    return_code: int
    stdout: str
    stderr: str

    @property
    def command_text(self) -> str:
        return subprocess.list2cmdline(self.command)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MiniGPT staged ruff static-analysis gate.")
    parser.add_argument("targets", nargs="*", default=list(DEFAULT_TARGETS))
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--strict-path", action="append", dest="strict_paths")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--no-format-check", action="store_true")
    parser.add_argument("--no-fail", action="store_true")
    return parser.parse_args(argv)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_baseline(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "schema_version": 1,
            "tool": "ruff",
            "targets": list(DEFAULT_TARGETS),
            "strict_paths": list(DEFAULT_STRICT_PATHS),
            "issues": [],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Baseline must be a JSON object: {path}")
    return payload


def build_report(
    *,
    project_root: Path,
    baseline_path: Path,
    targets: Sequence[str],
    strict_paths: Sequence[str] | None = None,
    update_baseline: bool = False,
    format_check: bool = True,
    runner: Runner | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    runner = runner or subprocess.run
    root = project_root.resolve()
    baseline_path = _resolve_path(baseline_path, root)
    baseline_exists = baseline_path.is_file()
    baseline = load_baseline(baseline_path)
    strict = tuple(strict_paths or baseline.get("strict_paths") or DEFAULT_STRICT_PATHS)
    check_result = run_ruff_check(targets, project_root=root, runner=runner)
    current_issues = parse_ruff_issues(check_result.stdout, project_root=root)
    baseline_issues = _baseline_issues(baseline)
    comparison = compare_issues(baseline_issues, current_issues)
    baseline_update_blockers = comparison["new_issues"] if update_baseline and baseline_exists else []
    baseline_update_allowed = not baseline_update_blockers
    effective_new_issues = [] if update_baseline and not baseline_exists else comparison["new_issues"]
    strict_lint_issues = [issue for issue in current_issues if issue.get("path") in strict]
    format_result = None
    format_status = "skipped"
    if format_check and strict:
        format_result = run_ruff_format_check(strict, project_root=root, runner=runner)
        format_status = "pass" if format_result.return_code == 0 else "fail"
    command_status = "pass" if check_result.return_code in (0, 1) else "fail"
    status = (
        "pass"
        if command_status == "pass"
        and not effective_new_issues
        and baseline_update_allowed
        and not strict_lint_issues
        and format_status != "fail"
        else "fail"
    )
    report = {
        "schema_version": 1,
        "title": "MiniGPT staged static analysis",
        "generated_at": generated_at or utc_now(),
        "tool": "ruff",
        "status": status,
        "decision": "continue_with_static_analysis_gate" if status == "pass" else "repair_static_analysis_gate",
        "project_root": str(root),
        "baseline_path": str(_relative_path(baseline_path, root)),
        "targets": list(targets),
        "strict_paths": list(strict),
        "summary": {
            "status": status,
            "decision": "continue_with_static_analysis_gate" if status == "pass" else "repair_static_analysis_gate",
            "command_status": command_status,
            "current_issue_count": len(current_issues),
            "baseline_issue_count": len(baseline_issues),
            "new_issue_count": len(effective_new_issues),
            "resolved_baseline_issue_count": len(comparison["resolved_issues"]),
            "baseline_update_requested": update_baseline,
            "baseline_update_allowed": baseline_update_allowed,
            "baseline_update_blocker_count": len(baseline_update_blockers),
            "strict_lint_issue_count": len(strict_lint_issues),
            "strict_format_status": format_status,
            "strict_path_count": len(strict),
        },
        "commands": _command_records(check_result, format_result),
        "new_issues": effective_new_issues,
        "baseline_update_blockers": baseline_update_blockers,
        "resolved_baseline_issues": comparison["resolved_issues"],
        "strict_lint_issues": strict_lint_issues,
        "current_issue_counts": _issue_counts(current_issues),
    }
    if update_baseline and baseline_update_allowed:
        write_baseline(
            baseline_path,
            targets=targets,
            strict_paths=strict,
            issues=current_issues,
            generated_at=str(report["generated_at"]),
        )
    return report


def run_ruff_check(targets: Sequence[str], *, project_root: Path, runner: Runner = subprocess.run) -> RuffCommandResult:
    command = [sys.executable, "-m", "ruff", "check", "--output-format=json", *targets]
    completed = runner(
        command,
        cwd=project_root,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return RuffCommandResult(tuple(command), int(completed.returncode), completed.stdout or "", completed.stderr or "")


def run_ruff_format_check(
    paths: Sequence[str], *, project_root: Path, runner: Runner = subprocess.run
) -> RuffCommandResult:
    command = [sys.executable, "-m", "ruff", "format", "--check", *paths]
    completed = runner(
        command,
        cwd=project_root,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return RuffCommandResult(tuple(command), int(completed.returncode), completed.stdout or "", completed.stderr or "")


def parse_ruff_issues(stdout: str, *, project_root: Path) -> list[dict[str, Any]]:
    if not stdout.strip():
        return []
    payload = json.loads(stdout)
    if not isinstance(payload, list):
        raise ValueError("ruff JSON output must be a list")
    return [_normalize_issue(item, project_root=project_root) for item in payload if isinstance(item, dict)]


def compare_issues(
    baseline_issues: Sequence[dict[str, Any]], current_issues: Sequence[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    baseline_counter = Counter(_issue_key(issue) for issue in baseline_issues)
    current_counter = Counter(_issue_key(issue) for issue in current_issues)
    new_keys = current_counter - baseline_counter
    resolved_keys = baseline_counter - current_counter
    return {
        "new_issues": _expand_counter(new_keys, current_issues),
        "resolved_issues": _expand_counter(resolved_keys, baseline_issues),
    }


def write_baseline(
    path: Path,
    *,
    targets: Sequence[str],
    strict_paths: Sequence[str],
    issues: Sequence[dict[str, Any]],
    generated_at: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "tool": "ruff",
        "generated_at": generated_at,
        "targets": list(targets),
        "strict_paths": list(strict_paths),
        "issue_count": len(issues),
        "issues": list(issues),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_report_outputs(report: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "json": out_dir / "static_analysis.json",
        "csv": out_dir / "static_analysis_issues.csv",
        "markdown": out_dir / "static_analysis.md",
        "html": out_dir / "static_analysis.html",
    }
    outputs["json"].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_issues_csv(report, outputs["csv"])
    outputs["markdown"].write_text(render_markdown(report), encoding="utf-8")
    outputs["html"].write_text(render_html(report), encoding="utf-8")
    return {key: str(path) for key, path in outputs.items()}


def write_issues_csv(report: dict[str, Any], path: Path) -> None:
    rows = list(_issue_rows(report))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["bucket", "path", "line", "column", "code", "message"])
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# {report['title']}",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Status: `{report['status']}`",
        f"- Decision: `{report['decision']}`",
        f"- Baseline: `{report['baseline_path']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Commands", "", "| Command | Return Code |", "| --- | --- |"])
    for command in report["commands"]:
        lines.append(f"| `{command['command']}` | {command['return_code']} |")
    lines.extend(["", "## New Issues", "", "| Path | Line | Code | Message |", "| --- | ---: | --- | --- |"])
    for issue in report["new_issues"]:
        lines.append(f"| `{issue['path']}` | {issue['line']} | {issue['code']} | {issue['message']} |")
    if not report["new_issues"]:
        lines.append("| none |  |  |  |")
    lines.extend(["", "## Strict Lint Issues", "", "| Path | Line | Code | Message |", "| --- | ---: | --- | --- |"])
    for issue in report["strict_lint_issues"]:
        lines.append(f"| `{issue['path']}` | {issue['line']} | {issue['code']} | {issue['message']} |")
    if not report["strict_lint_issues"]:
        lines.append("| none |  |  |  |")
    return "\n".join(lines).rstrip() + "\n"


def render_html(report: dict[str, Any]) -> str:
    markdown = html.escape(render_markdown(report))
    status = html.escape(str(report["status"]))
    return (
        "<!doctype html>\n"
        '<html><head><meta charset="utf-8"><title>MiniGPT static analysis</title>'
        '<link rel="icon" href="data:,">'
        "<style>body{font-family:Arial,sans-serif;margin:24px;line-height:1.45}"
        "pre{background:#f6f8fa;padding:16px;border-radius:8px;white-space:pre-wrap}"
        ".status{font-weight:700}</style></head><body>"
        f'<h1>MiniGPT staged static analysis</h1><p class="status">status={status}</p><pre>{markdown}</pre>'
        "</body></html>\n"
    )


def _normalize_issue(item: dict[str, Any], *, project_root: Path) -> dict[str, Any]:
    path = _relative_path(Path(str(item.get("filename", ""))), project_root)
    raw_location = item.get("location")
    location = dict(raw_location) if isinstance(raw_location, dict) else {}
    line = int(location.get("row") or 0)
    column = int(location.get("column") or 0)
    source_line = _source_line(project_root / path, line)
    return {
        "path": path.as_posix(),
        "line": line,
        "column": column,
        "code": str(item.get("code") or ""),
        "message": str(item.get("message") or ""),
        "source_line": source_line,
    }


def _baseline_issues(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    issues = baseline.get("issues", [])
    return list(issues) if isinstance(issues, list) else []


def _issue_key(issue: dict[str, Any]) -> IssueKey:
    return (
        str(issue.get("path") or ""),
        str(issue.get("code") or ""),
        str(issue.get("message") or ""),
        str(issue.get("source_line") or "").strip(),
    )


def _expand_counter(counter: Counter[IssueKey], issues: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = Counter(counter)
    expanded: list[dict[str, Any]] = []
    for issue in issues:
        key = _issue_key(issue)
        if remaining[key] <= 0:
            continue
        expanded.append(dict(issue))
        remaining[key] -= 1
    return expanded


def _issue_counts(issues: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = Counter((str(issue.get("path")), str(issue.get("code"))) for issue in issues)
    return [
        {"path": path, "code": code, "count": count}
        for (path, code), count in sorted(counter.items(), key=lambda item: (item[0][0], item[0][1]))
    ]


def _issue_rows(report: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for bucket in ("new_issues", "strict_lint_issues", "resolved_baseline_issues"):
        for issue in report.get(bucket, []):
            yield {
                "bucket": bucket,
                "path": issue.get("path", ""),
                "line": issue.get("line", ""),
                "column": issue.get("column", ""),
                "code": issue.get("code", ""),
                "message": issue.get("message", ""),
            }


def _command_records(*results: RuffCommandResult | None) -> list[dict[str, Any]]:
    return [
        {
            "command": result.command_text,
            "return_code": result.return_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        for result in results
        if result is not None
    ]


def _source_line(path: Path, line: int) -> str:
    if line <= 0 or not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return ""
    return lines[line - 1].strip() if line <= len(lines) else ""


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _relative_path(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root)
    except ValueError:
        return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.project_root.resolve()
    baseline_path = _resolve_path(args.baseline, root)
    out_dir = _resolve_path(args.out_dir, root)
    report = build_report(
        project_root=root,
        baseline_path=baseline_path,
        targets=tuple(args.targets),
        strict_paths=tuple(args.strict_paths) if args.strict_paths else None,
        update_baseline=args.update_baseline,
        format_check=not args.no_format_check,
    )
    outputs = write_report_outputs(report, out_dir)
    summary = report["summary"]
    print(f"status={summary['status']}")
    print(f"decision={summary['decision']}")
    print(f"current_issue_count={summary['current_issue_count']}")
    print(f"baseline_issue_count={summary['baseline_issue_count']}")
    print(f"new_issue_count={summary['new_issue_count']}")
    print(f"baseline_update_allowed={summary['baseline_update_allowed']}")
    print(f"baseline_update_blocker_count={summary['baseline_update_blocker_count']}")
    print(f"strict_lint_issue_count={summary['strict_lint_issue_count']}")
    print(f"strict_format_status={summary['strict_format_status']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report["status"] != "pass" and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
