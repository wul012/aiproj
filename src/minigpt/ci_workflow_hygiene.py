from __future__ import annotations

from pathlib import Path

from minigpt.ci_workflow_hygiene_artifacts import (
    render_ci_workflow_hygiene_html,
    render_ci_workflow_hygiene_markdown,
    write_ci_workflow_hygiene_csv,
    write_ci_workflow_hygiene_html,
    write_ci_workflow_hygiene_json,
    write_ci_workflow_hygiene_markdown,
    write_ci_workflow_hygiene_outputs,
)
from minigpt.ci_workflow_hygiene_checks import build_checks, collect_actions
from minigpt.ci_workflow_hygiene_policy import (
    DEFAULT_WORKFLOW_PATH,
    FORBIDDEN_ENV_VARS,
    REQUIRED_ACTIONS,
    REQUIRED_COMMAND_FRAGMENTS,
    REQUIRED_COMMAND_ORDER,
    REQUIRED_EXECUTION_POLICY_FRAGMENTS,
    REQUIRED_PYTHON_VERSION,
)
from minigpt.ci_workflow_hygiene_summary import build_recommendations, build_summary
from minigpt.ci_workflow_hygiene_types import CiWorkflowReport
from minigpt.report_utils import utc_now


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
    actions = collect_actions(text)
    checks = build_checks(text, actions)
    summary = build_summary(text, actions, checks)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "workflow_path": _relative_path(path, root),
        "policy": {
            "required_actions": dict(REQUIRED_ACTIONS),
            "forbidden_env_vars": list(FORBIDDEN_ENV_VARS),
            "required_command_fragments": dict(REQUIRED_COMMAND_FRAGMENTS),
            "required_command_order": {
                key: {"before": before, "after": after} for key, (before, after) in REQUIRED_COMMAND_ORDER.items()
            },
            "required_execution_policy_fragments": dict(REQUIRED_EXECUTION_POLICY_FRAGMENTS),
            "required_python_version": REQUIRED_PYTHON_VERSION,
        },
        "summary": summary,
        "actions": actions,
        "checks": checks,
        "recommendations": build_recommendations(summary),
    }


def _relative_path(path: Path, project_root: Path | None) -> str:
    if project_root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(project_root))
    except ValueError:
        return str(path)


__all__ = [
    "DEFAULT_WORKFLOW_PATH",
    "FORBIDDEN_ENV_VARS",
    "REQUIRED_ACTIONS",
    "REQUIRED_COMMAND_FRAGMENTS",
    "REQUIRED_COMMAND_ORDER",
    "REQUIRED_EXECUTION_POLICY_FRAGMENTS",
    "build_ci_workflow_hygiene_report",
    "render_ci_workflow_hygiene_html",
    "render_ci_workflow_hygiene_markdown",
    "write_ci_workflow_hygiene_csv",
    "write_ci_workflow_hygiene_html",
    "write_ci_workflow_hygiene_json",
    "write_ci_workflow_hygiene_markdown",
    "write_ci_workflow_hygiene_outputs",
]
