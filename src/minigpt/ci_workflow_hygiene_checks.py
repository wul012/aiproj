from __future__ import annotations

import re
from typing import Any

from minigpt.ci_workflow_hygiene_policy import (
    FORBIDDEN_ENV_VARS,
    REQUIRED_ACTIONS,
    REQUIRED_COMMAND_FRAGMENTS,
    REQUIRED_COMMAND_ORDER,
    REQUIRED_EXECUTION_POLICY_FRAGMENTS,
    REQUIRED_PYTHON_VERSION,
)
from minigpt.ci_workflow_hygiene_types import CheckStatus, CiWorkflowAction, CiWorkflowCheck


_USES_RE = re.compile(r"^\s*-\s+uses:\s*(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<version>[A-Za-z0-9_.-]+)\s*$")
_PYTHON_VERSION_RE = re.compile(r"python-version:\s*[\"']?(?P<version>[0-9.]+)[\"']?")
_ACTION_MAJOR_RE = re.compile(r"^v?(?P<major>[0-9]+)(?:\.[0-9]+){0,2}$")


def build_checks(text: str, actions: list[CiWorkflowAction]) -> list[CiWorkflowCheck]:
    checks: list[CiWorkflowCheck] = []
    action_versions = {str(item.get("repository")): str(item.get("version")) for item in actions}
    for repository, expected in REQUIRED_ACTIONS.items():
        actual = action_versions.get(repository, "")
        status: CheckStatus = "pass" if actual == expected else "fail"
        detail = (
            "Action uses the expected Node 24 native major."
            if status == "pass"
            else "Action version must be upgraded to the expected major."
        )
        checks.append(
            _check(f"action:{repository}", "action_version", repository, expected, actual or "missing", status, detail)
        )
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
    for policy_id, fragment in REQUIRED_EXECUTION_POLICY_FRAGMENTS.items():
        present = fragment in text
        checks.append(
            _check(
                f"execution:{policy_id}",
                "execution_policy",
                policy_id,
                fragment,
                "present" if present else "missing",
                "pass" if present else "fail",
                (
                    "Required CI execution-economy policy is present."
                    if present
                    else "Required CI execution-economy policy is missing."
                ),
            )
        )
    tags_present = re.search(r"^\s{4}tags(?:-ignore)?:", text, flags=re.MULTILINE) is not None
    checks.append(
        _check(
            "execution:no_tag_push_trigger",
            "execution_policy",
            "push.tags",
            "absent",
            "present" if tags_present else "absent",
            "fail" if tags_present else "pass",
            "Tag pushes stay excluded so a tested main commit is not verified twice.",
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
    for order_id, (before, after) in REQUIRED_COMMAND_ORDER.items():
        before_line = _first_line_number(text, before)
        after_line = _first_line_number(text, after)
        present = before_line > 0 and after_line > 0
        in_order = present and before_line < after_line
        if not present:
            actual = "missing"
            detail = "Required CI command order cannot be checked because one or both commands are missing."
        else:
            actual = f"before_line={before_line};after_line={after_line}"
            detail = (
                f"Required CI command order is preserved: before line {before_line}, after line {after_line}."
                if in_order
                else f"Required CI command order is violated: before line {before_line}, after line {after_line}."
            )
        checks.append(
            _check(
                f"order:{order_id}",
                "required_order",
                order_id,
                "before",
                actual,
                "pass" if in_order else "fail",
                detail,
            )
        )
    actual_python = python_version(text)
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


def collect_actions(text: str) -> list[CiWorkflowAction]:
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


def check_passed(checks: list[CiWorkflowCheck], check_id: str) -> bool:
    return any(item.get("id") == check_id and item.get("status") == "pass" for item in checks)


def forbidden_env_hits(text: str) -> list[str]:
    return [item for item in FORBIDDEN_ENV_VARS if item in text]


def python_version(text: str) -> str:
    match = _PYTHON_VERSION_RE.search(text)
    return match.group("version") if match else ""


def _check(
    check_id: str, category: str, target: str, expected: Any, actual: Any, status: CheckStatus, detail: str
) -> CiWorkflowCheck:
    return {
        "id": check_id,
        "category": category,
        "target": target,
        "expected": str(expected),
        "actual": str(actual),
        "status": status,
        "detail": detail,
    }


def _major(version: str) -> int:
    match = _ACTION_MAJOR_RE.match(version.strip())
    return int(match.group("major")) if match else 0


def _first_line_number(text: str, fragment: str) -> int:
    for line_no, line in enumerate(text.splitlines(), start=1):
        if fragment in line:
            return line_no
    return 0


__all__ = [
    "build_checks",
    "check_passed",
    "collect_actions",
    "forbidden_env_hits",
    "python_version",
]
