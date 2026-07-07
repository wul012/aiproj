from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict,
    csv_cell,
    html_escape,
    list_of_dicts,
    list_of_strs,
    markdown_cell,
    read_json_object,
    utc_now,
    write_json_payload,
    write_output_bundle,
)

DEFAULT_CONFIG_PATH = Path("docs") / "code-health" / "file-size-ratchet.json"
DEFAULT_WARNING_LINE_LIMIT = 500
DEFAULT_MAX_LINE_LIMIT = 800


def build_file_size_ratchet_report(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    project_root: str | Path = ".",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    path = _resolve_config_path(config_path, root)
    config = read_json_object(path, description="file size ratchet config")
    warning_limit = _positive_int(config.get("warning_line_limit"), DEFAULT_WARNING_LINE_LIMIT)
    max_limit = _positive_int(config.get("max_line_limit"), DEFAULT_MAX_LINE_LIMIT)
    targets = tuple(list_of_strs(config.get("targets")) or ["src", "scripts", "tests"])
    waivers = _waivers_by_path(config)
    files = _scan_files(root, targets=targets, warning_limit=warning_limit, max_limit=max_limit, waivers=waivers)
    checks = _config_checks(config, config_path=path, project_root=root, targets=targets, waivers=waivers)
    checks.extend(_file_checks(files, max_limit=max_limit))
    failed_checks = [item for item in checks if item["status"] != "pass"]
    over_warning = [item for item in files if item["line_count"] > warning_limit]
    over_limit = [item for item in files if item["line_count"] > max_limit]
    largest = max(files, key=lambda item: int(item["line_count"]), default={})
    status = "pass" if not failed_checks else "fail"
    decision = "continue_with_file_size_ratchet" if status == "pass" else "repair_file_size_ratchet"
    return {
        "schema_version": 1,
        "title": "MiniGPT file size ratchet",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "config_path": _relative_path(path, root),
        "summary": {
            "status": status,
            "decision": decision,
            "target_count": len(targets),
            "scanned_file_count": len(files),
            "warning_line_limit": warning_limit,
            "max_line_limit": max_limit,
            "over_warning_count": len(over_warning),
            "over_limit_count": len(over_limit),
            "waiver_count": len(waivers),
            "waived_over_limit_count": sum(1 for item in over_limit if item["waived"]),
            "unwaived_over_limit_count": sum(1 for item in over_limit if not item["waived"]),
            "waiver_growth_violation_count": sum(1 for item in files if item["waiver_status"] == "grew"),
            "src_scripts_over_warning_count": sum(
                1 for item in over_warning if str(item["path"]).startswith(("src/", "scripts/"))
            ),
            "largest_file_path": largest.get("path", ""),
            "largest_file_lines": largest.get("line_count", 0),
            "failed_check_count": len(failed_checks),
        },
        "targets": list(targets),
        "waivers": list(waivers.values()),
        "files": files,
        "checks": checks,
        "recommendations": _recommendations(failed_checks),
    }


def write_file_size_ratchet_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    def write_markdown(path: Path) -> None:
        path.write_text(render_file_size_ratchet_markdown(report), encoding="utf-8")

    def write_html(path: Path) -> None:
        path.write_text(render_file_size_ratchet_html(report), encoding="utf-8")

    return write_output_bundle(
        out_dir,
        {
            "json": "file_size_ratchet.json",
            "csv": "file_size_ratchet.csv",
            "markdown": "file_size_ratchet.md",
            "html": "file_size_ratchet.html",
        },
        {
            "json": lambda path: write_json_payload(report, path),
            "csv": lambda path: _write_csv(report, path),
            "markdown": write_markdown,
            "html": write_html,
        },
    )


def render_file_size_ratchet_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# MiniGPT File Size Ratchet",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Config: `{report.get('config_path')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in (
        "scanned_file_count",
        "warning_line_limit",
        "max_line_limit",
        "over_warning_count",
        "over_limit_count",
        "waiver_count",
        "unwaived_over_limit_count",
        "waiver_growth_violation_count",
        "largest_file_path",
        "largest_file_lines",
        "failed_check_count",
    ):
        lines.append(f"| {markdown_cell(key)} | {markdown_cell(summary.get(key))} |")
    lines.extend(
        ["", "## Oversize Files", "", "| Path | Lines | Waived | Waiver Status |", "| --- | ---: | --- | --- |"]
    )
    for item in _files(report):
        if int(item.get("line_count") or 0) <= int(summary.get("warning_line_limit") or DEFAULT_WARNING_LINE_LIMIT):
            continue
        lines.append(
            "| "
            + " | ".join(markdown_cell(item.get(field)) for field in ("path", "line_count", "waived", "waiver_status"))
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_file_size_ratchet_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = "".join(
        "<tr>"
        f"<td>{html_escape(item.get('path'))}</td>"
        f"<td>{html_escape(item.get('line_count'))}</td>"
        f"<td>{html_escape(item.get('bucket'))}</td>"
        f"<td>{html_escape(item.get('waived'))}</td>"
        f"<td>{html_escape(item.get('waiver_status'))}</td>"
        "</tr>"
        for item in _files(report)
        if int(item.get("line_count") or 0) > int(summary.get("warning_line_limit") or DEFAULT_WARNING_LINE_LIMIT)
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MiniGPT file size ratchet</title><style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f6f7f9;color:#172026;margin:0}}
main{{max-width:1120px;margin:auto;padding:28px}}header,.panel{{background:white;border:1px solid #d8dee4;border-radius:8px;padding:18px;margin-bottom:14px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.stat{{background:#eef2f6;padding:12px;border-radius:6px}}
table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}}code{{overflow-wrap:anywhere}}
</style></head><body><main>
<header><h1>MiniGPT file size ratchet</h1><p>Status: <strong>{html_escape(report.get("status"))}</strong> | Decision: <code>{html_escape(report.get("decision"))}</code></p><p>Config: <code>{html_escape(report.get("config_path"))}</code></p></header>
<section class="panel stats"><div class="stat">Files<br><strong>{html_escape(summary.get("scanned_file_count"))}</strong></div><div class="stat">Warnings<br><strong>{html_escape(summary.get("over_warning_count"))}</strong></div><div class="stat">Over limit<br><strong>{html_escape(summary.get("over_limit_count"))}</strong></div><div class="stat">Failures<br><strong>{html_escape(summary.get("failed_check_count"))}</strong></div></section>
<section class="panel"><h2>Oversize Files</h2><table><thead><tr><th>Path</th><th>Lines</th><th>Bucket</th><th>Waived</th><th>Waiver Status</th></tr></thead><tbody>{rows}</tbody></table></section>
</main></body></html>"""


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 0 if not require_pass or report.get("status") == "pass" else 1


def _scan_files(
    root: Path,
    *,
    targets: tuple[str, ...],
    warning_limit: int,
    max_limit: int,
    waivers: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for target in targets:
        base = _resolve_inside_root(target, root)
        candidates = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for path in candidates:
            if not path.is_file() or path.suffix != ".py":
                continue
            relative = _relative_path(path, root)
            line_count = _line_count(path)
            waiver = waivers.get(relative)
            files.append(
                {
                    "path": relative,
                    "line_count": line_count,
                    "bucket": _bucket(line_count, warning_limit=warning_limit, max_limit=max_limit),
                    "waived": waiver is not None,
                    "waiver_status": _waiver_status(line_count, waiver),
                    "waiver_baseline_lines": waiver.get("baseline_lines") if waiver else "",
                }
            )
    return sorted(files, key=lambda item: (-int(item["line_count"]), str(item["path"])))


def _config_checks(
    config: dict[str, Any],
    *,
    config_path: Path,
    project_root: Path,
    targets: tuple[str, ...],
    waivers: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        _check("config_schema_version", 1, config.get("schema_version"), config.get("schema_version") == 1),
        _check(
            "config_policy",
            "aiproj_file_size_ratchet",
            config.get("policy"),
            config.get("policy") == "aiproj_file_size_ratchet",
        ),
        _check("targets_present", "non-empty list", len(targets), bool(targets)),
        _check(
            "config_inside_project",
            "inside project",
            _relative_path(config_path, project_root),
            _is_inside(config_path, project_root),
        ),
    ]
    for target in targets:
        path = _resolve_inside_root(target, project_root)
        checks.append(_check(f"target_exists:{target}", "existing file or directory", target, path.exists()))
    for waiver in waivers.values():
        path_text = str(waiver.get("path"))
        baseline = waiver.get("baseline_lines")
        checks.append(
            _check(
                f"waiver_exists:{path_text}", "existing Python file", path_text, (project_root / path_text).is_file()
            )
        )
        checks.append(
            _check(
                f"waiver_baseline:{path_text}",
                "positive integer",
                baseline,
                isinstance(baseline, int) and not isinstance(baseline, bool) and baseline > 0,
            )
        )
        checks.append(
            _check(f"waiver_reason:{path_text}", "non-empty", waiver.get("reason"), bool(waiver.get("reason")))
        )
    return checks


def _file_checks(files: list[dict[str, Any]], *, max_limit: int) -> list[dict[str, Any]]:
    checks = []
    for item in files:
        path = str(item["path"])
        line_count = int(item["line_count"])
        checks.append(
            _check(
                f"max_lines:{path}", f"<= {max_limit} or waived", line_count, line_count <= max_limit or item["waived"]
            )
        )
        if item["waived"]:
            checks.append(
                _check(
                    f"waiver_no_growth:{path}",
                    "current <= baseline",
                    item["waiver_status"],
                    item["waiver_status"] != "grew",
                )
            )
    return checks


def _check(check_id: str, expected: Any, actual: Any, passed: bool) -> dict[str, Any]:
    return {"check_id": check_id, "expected": expected, "actual": actual, "status": "pass" if passed else "fail"}


def _waivers_by_path(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("path")): dict(item) for item in list_of_dicts(config.get("waivers")) if item.get("path")}


def _bucket(line_count: int, *, warning_limit: int, max_limit: int) -> str:
    if line_count > max_limit:
        return "over_limit"
    if line_count > warning_limit:
        return "over_warning"
    return "within_limit"


def _waiver_status(line_count: int, waiver: dict[str, Any] | None) -> str:
    if waiver is None:
        return "not_waived"
    baseline = _positive_int(waiver.get("baseline_lines"), 0)
    if line_count > baseline:
        return "grew"
    if line_count < baseline:
        return "shrunk"
    return "at_baseline"


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["path", "line_count", "bucket", "waived", "waiver_status", "waiver_baseline_lines"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in _files(report):
            writer.writerow({field: csv_cell(item.get(field)) for field in fieldnames})


def _recommendations(failed_checks: list[dict[str, Any]]) -> list[str]:
    if not failed_checks:
        return ["Keep new Python files below the hard limit, and split waived legacy tests before they grow again."]
    return ["Split unwaived over-limit files or update a justified waiver after reducing/splitting legacy coverage."]


def _files(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("files"))


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8-sig").splitlines())


def _positive_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def _resolve_inside_root(path: str | Path, root: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if not _is_inside(resolved, root):
        raise ValueError(f"path escapes project root: {path}")
    return resolved


def _resolve_config_path(path: str | Path, root: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if not _is_inside(resolved, root):
        raise ValueError(f"config path escapes project root: {path}")
    return resolved


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "DEFAULT_CONFIG_PATH",
    "build_file_size_ratchet_report",
    "render_file_size_ratchet_html",
    "render_file_size_ratchet_markdown",
    "resolve_exit_code",
    "write_file_size_ratchet_outputs",
]
