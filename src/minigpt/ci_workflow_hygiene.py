from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Literal, TypedDict

from minigpt.report_utils import csv_cell, html_escape as _e, markdown_cell as _md, string_list as _string_list, utc_now, write_json_payload

DEFAULT_WORKFLOW_PATH = Path(".github") / "workflows" / "ci.yml"
REQUIRED_ACTIONS = {"actions/checkout": "v6", "actions/setup-python": "v6"}
FORBIDDEN_ENV_VARS = ("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24",)
REQUIRED_COMMAND_FRAGMENTS = {
    "source_encoding_gate": "scripts/check_source_encoding.py",
    "ci_workflow_hygiene_gate": "scripts/check_ci_workflow_hygiene.py",
    "unit_test_discovery": "unittest discover -s tests -v",
}
REQUIRED_PYTHON_VERSION = "3.11"

_USES_RE = re.compile(r"^\s*-\s+uses:\s*(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<version>[A-Za-z0-9_.-]+)\s*$")
_PYTHON_VERSION_RE = re.compile(r"python-version:\s*[\"']?(?P<version>[0-9.]+)[\"']?")
_ACTION_MAJOR_RE = re.compile(r"^v?(?P<major>[0-9]+)(?:\.[0-9]+){0,2}$")

CheckStatus = Literal["pass", "fail"]


class CiWorkflowCheck(TypedDict):
    id: str
    category: str
    target: str
    expected: str
    actual: str
    status: CheckStatus
    detail: str


class CiWorkflowAction(TypedDict):
    repository: str
    version: str
    raw: str
    line: int
    node24_native: bool


class CiWorkflowSummary(TypedDict):
    status: CheckStatus
    decision: str
    check_count: int
    passed_check_count: int
    failed_check_count: int
    action_count: int
    required_action_count: int
    found_required_action_count: int
    node24_native_action_count: int
    forbidden_env_count: int
    required_step_count: int
    missing_step_count: int
    python_version: str


class CiWorkflowReport(TypedDict):
    schema_version: int
    title: str
    generated_at: str
    workflow_path: str
    policy: dict[str, Any]
    summary: CiWorkflowSummary
    actions: list[CiWorkflowAction]
    checks: list[CiWorkflowCheck]
    recommendations: list[str]


def build_ci_workflow_hygiene_report(
    workflow_path: str | Path,
    *,
    project_root: str | Path | None = None,
    title: str = "MiniGPT CI workflow hygiene",
    generated_at: str | None = None,
) -> CiWorkflowReport:
    root = Path(project_root).resolve() if project_root is not None else None
    path = Path(workflow_path)
    text = path.read_text(encoding="utf-8")
    actions = _collect_actions(text)
    checks = _build_checks(text, actions)
    failed_checks = [item for item in checks if item.get("status") != "pass"]
    required_action_repos = set(REQUIRED_ACTIONS)
    found_required_actions = [item for item in actions if item.get("repository") in required_action_repos]
    forbidden_env_hits = _forbidden_env_hits(text)
    missing_steps = [check for check in checks if check.get("category") == "required_command" and check.get("status") != "pass"]
    summary: CiWorkflowSummary = {
        "status": "pass" if not failed_checks else "fail",
        "decision": "continue_with_node24_native_ci" if not failed_checks else "fix_ci_workflow_hygiene",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed_checks),
        "failed_check_count": len(failed_checks),
        "action_count": len(actions),
        "required_action_count": len(REQUIRED_ACTIONS),
        "found_required_action_count": len(found_required_actions),
        "node24_native_action_count": sum(1 for item in found_required_actions if item.get("node24_native")),
        "forbidden_env_count": len(forbidden_env_hits),
        "required_step_count": len(REQUIRED_COMMAND_FRAGMENTS),
        "missing_step_count": len(missing_steps),
        "python_version": _python_version(text),
    }
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "workflow_path": _relative_path(path, root),
        "policy": {
            "required_actions": dict(REQUIRED_ACTIONS),
            "forbidden_env_vars": list(FORBIDDEN_ENV_VARS),
            "required_command_fragments": dict(REQUIRED_COMMAND_FRAGMENTS),
            "required_python_version": REQUIRED_PYTHON_VERSION,
        },
        "summary": summary,
        "actions": actions,
        "checks": checks,
        "recommendations": _recommendations(summary),
    }


def write_ci_workflow_hygiene_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_ci_workflow_hygiene_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "category", "target", "expected", "actual", "status", "detail"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in _checks(report):
            writer.writerow({field: csv_cell(item.get(field)) for field in fieldnames})


def render_ci_workflow_hygiene_markdown(report: dict[str, Any]) -> str:
    summary = _summary(report)
    lines = [
        f"# {_md(report.get('title', 'MiniGPT CI workflow hygiene'))}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Workflow: `{report.get('workflow_path')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in [
        "check_count",
        "passed_check_count",
        "failed_check_count",
        "action_count",
        "found_required_action_count",
        "node24_native_action_count",
        "forbidden_env_count",
        "missing_step_count",
        "python_version",
    ]:
        lines.append(f"| {_md(key)} | {_md(summary.get(key))} |")
    lines.extend(["", "## Checks", "", "| ID | Category | Target | Expected | Actual | Status | Detail |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for item in _checks(report):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("id")),
                    _md(item.get("category")),
                    _md(item.get("target")),
                    _md(item.get("expected")),
                    _md(item.get("actual")),
                    _md(item.get("status")),
                    _md(item.get("detail")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Actions", "", "| Repository | Version | Line | Node 24 Native |", "| --- | --- | --- | --- |"])
    for item in _actions(report):
        lines.append(f"| {_md(item.get('repository'))} | {_md(item.get('version'))} | {_md(item.get('line'))} | {_md(item.get('node24_native'))} |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_ci_workflow_hygiene_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_ci_workflow_hygiene_markdown(report), encoding="utf-8")


def render_ci_workflow_hygiene_html(report: dict[str, Any]) -> str:
    summary = _summary(report)
    checks = "".join(_check_row(item) for item in _checks(report))
    actions = "".join(_action_row(item) for item in _actions(report))
    stats = [
        ("Status", summary.get("status")),
        ("Decision", summary.get("decision")),
        ("Checks", summary.get("check_count")),
        ("Failures", summary.get("failed_check_count")),
        ("Actions", summary.get("action_count")),
        ("Node 24 native", summary.get("node24_native_action_count")),
        ("Forbidden env", summary.get("forbidden_env_count")),
        ("Python", summary.get("python_version")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT CI workflow hygiene'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT CI workflow hygiene'))}</h1><p>Checks the CI workflow action versions, runtime policy, Python version, and required quality gates.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            "<section><h2>Checks</h2><table><tr><th>ID</th><th>Category</th><th>Target</th><th>Expected</th><th>Actual</th><th>Status</th><th>Detail</th></tr>"
            + checks
            + "</table></section>",
            "<section><h2>Actions</h2><table><tr><th>Repository</th><th>Version</th><th>Line</th><th>Node 24 Native</th></tr>" + actions + "</table></section>",
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT CI workflow hygiene.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_ci_workflow_hygiene_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_ci_workflow_hygiene_html(report), encoding="utf-8")


def write_ci_workflow_hygiene_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "ci_workflow_hygiene.json",
        "csv": root / "ci_workflow_hygiene.csv",
        "markdown": root / "ci_workflow_hygiene.md",
        "html": root / "ci_workflow_hygiene.html",
    }
    write_ci_workflow_hygiene_json(report, paths["json"])
    write_ci_workflow_hygiene_csv(report, paths["csv"])
    write_ci_workflow_hygiene_markdown(report, paths["markdown"])
    write_ci_workflow_hygiene_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _build_checks(text: str, actions: list[CiWorkflowAction]) -> list[CiWorkflowCheck]:
    checks: list[CiWorkflowCheck] = []
    action_versions = {str(item.get("repository")): str(item.get("version")) for item in actions}
    for repository, expected in REQUIRED_ACTIONS.items():
        actual = action_versions.get(repository, "")
        status = "pass" if actual == expected else "fail"
        detail = "Action uses the expected Node 24 native major." if status == "pass" else "Action version must be upgraded to the expected major."
        checks.append(_check(f"action:{repository}", "action_version", repository, expected, actual or "missing", status, detail))
    for env_name in FORBIDDEN_ENV_VARS:
        present = env_name in text
        checks.append(
            _check(
                f"env:{env_name}",
                "forbidden_env",
                env_name,
                "absent",
                "present" if present else "absent",
                "fail" if present else "pass",
                "Native action versions should not rely on force-runtime environment variables.",
            )
        )
    for step_id, fragment in REQUIRED_COMMAND_FRAGMENTS.items():
        present = fragment in text
        checks.append(
            _check(
                f"command:{step_id}",
                "required_command",
                step_id,
                fragment,
                "present" if present else "missing",
                "pass" if present else "fail",
                "Required CI quality command is present." if present else "Required CI quality command is missing.",
            )
        )
    actual_python = _python_version(text)
    checks.append(
        _check(
            "python:setup-version",
            "python_version",
            "actions/setup-python",
            REQUIRED_PYTHON_VERSION,
            actual_python or "missing",
            "pass" if actual_python == REQUIRED_PYTHON_VERSION else "fail",
            "CI parser target should remain aligned with source encoding compatibility checks.",
        )
    )
    return checks


def _check(check_id: str, category: str, target: str, expected: Any, actual: Any, status: CheckStatus, detail: str) -> CiWorkflowCheck:
    return {
        "id": check_id,
        "category": category,
        "target": target,
        "expected": str(expected),
        "actual": str(actual),
        "status": status,
        "detail": detail,
    }


def _collect_actions(text: str) -> list[CiWorkflowAction]:
    actions: list[CiWorkflowAction] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = _USES_RE.match(line)
        if not match:
            continue
        repository = match.group("repo")
        version = match.group("version")
        actions.append(
            {
                "repository": repository,
                "version": version,
                "raw": f"{repository}@{version}",
                "line": line_no,
                "node24_native": repository in REQUIRED_ACTIONS and _major(version) >= 6,
            }
        )
    return actions


def _major(version: str) -> int:
    match = _ACTION_MAJOR_RE.match(version.strip())
    return int(match.group("major")) if match else 0


def _python_version(text: str) -> str:
    match = _PYTHON_VERSION_RE.search(text)
    return match.group("version") if match else ""


def _forbidden_env_hits(text: str) -> list[str]:
    return [item for item in FORBIDDEN_ENV_VARS if item in text]


def _relative_path(path: Path, project_root: Path | None) -> str:
    if project_root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(project_root))
    except ValueError:
        return str(path)


def _summary(report: dict[str, Any]) -> dict[str, Any]:
    return dict(report.get("summary")) if isinstance(report.get("summary"), dict) else {}


def _actions(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("actions")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("checks")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _recommendations(summary: dict[str, Any]) -> list[str]:
    if summary.get("status") == "pass":
        return ["Keep CI workflow action versions and quality gates aligned with the Node 24 native policy."]
    recommendations: list[str] = []
    if summary.get("node24_native_action_count", 0) < summary.get("required_action_count", 0):
        recommendations.append("Upgrade required GitHub actions to the expected Node 24 native majors.")
    if summary.get("forbidden_env_count", 0):
        recommendations.append("Remove force-runtime environment variables and rely on native action metadata instead.")
    if summary.get("missing_step_count", 0):
        recommendations.append("Restore required source hygiene and unittest commands in the CI workflow.")
    if summary.get("python_version") != REQUIRED_PYTHON_VERSION:
        recommendations.append("Align actions/setup-python with the source compatibility target.")
    return recommendations


def _check_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('id'))}</td>"
        f"<td>{_e(item.get('category'))}</td>"
        f"<td>{_e(item.get('target'))}</td>"
        f"<td>{_e(item.get('expected'))}</td>"
        f"<td>{_e(item.get('actual'))}</td>"
        f"<td>{_e(item.get('status'))}</td>"
        f"<td>{_e(item.get('detail'))}</td>"
        "</tr>"
    )


def _action_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('repository'))}</td>"
        f"<td>{_e(item.get('version'))}</td>"
        f"<td>{_e(item.get('line'))}</td>"
        f"<td>{_e(item.get('node24_native'))}</td>"
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
header, section, footer { max-width: 1100px; margin: 0 auto 18px; }
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
    "DEFAULT_WORKFLOW_PATH",
    "FORBIDDEN_ENV_VARS",
    "REQUIRED_ACTIONS",
    "REQUIRED_COMMAND_FRAGMENTS",
    "build_ci_workflow_hygiene_report",
    "render_ci_workflow_hygiene_html",
    "render_ci_workflow_hygiene_markdown",
    "write_ci_workflow_hygiene_csv",
    "write_ci_workflow_hygiene_html",
    "write_ci_workflow_hygiene_json",
    "write_ci_workflow_hygiene_markdown",
    "write_ci_workflow_hygiene_outputs",
]
