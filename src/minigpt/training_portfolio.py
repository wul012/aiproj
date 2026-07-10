from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from minigpt.report_utils import utc_now
from minigpt.training_portfolio_artifacts import (
    render_training_portfolio_html,  # noqa: F401
    render_training_portfolio_markdown,  # noqa: F401
    write_training_portfolio_html,  # noqa: F401
    write_training_portfolio_json,  # noqa: F401
    write_training_portfolio_markdown,  # noqa: F401
    write_training_portfolio_outputs,  # noqa: F401
)
from minigpt.training_portfolio_plan import build_training_portfolio_plan  # noqa: F401


def run_training_portfolio_plan(
    plan: dict[str, Any],
    *,
    execute: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(str(plan.get("project_root") or "."))
    step_results = []
    failed_key = None
    if execute:
        for step in _list_of_dicts(plan.get("steps")):
            result = _run_step(root, step)
            step_results.append(result)
            if result["returncode"] != 0:
                failed_key = str(step.get("key"))
                break
    status = "planned"
    if execute and failed_key is None:
        status = "completed"
    elif execute:
        status = "failed"
    artifact_rows = _artifact_rows(plan.get("artifacts"), root)
    return {
        **plan,
        "generated_at": generated_at or utc_now(),
        "execution": {
            "status": status,
            "execute": execute,
            "step_count": len(_list_of_dicts(plan.get("steps"))),
            "completed_steps": sum(1 for item in step_results if item.get("returncode") == 0),
            "failed_step": failed_key,
            "artifact_count": len(artifact_rows),
            "available_artifact_count": sum(1 for item in artifact_rows if item["exists"]),
        },
        "step_results": step_results,
        "artifact_rows": artifact_rows,
        "recommendations": _recommendations(status, artifact_rows, failed_key),
    }


def _run_step(root: Path, step: dict[str, Any]) -> dict[str, Any]:
    command = _string_list(step.get("command"))
    started_at = utc_now()
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
    finished_at = utc_now()
    return {
        "key": step.get("key"),
        "title": step.get("title"),
        "returncode": completed.returncode,
        "started_at": started_at,
        "finished_at": finished_at,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
    }


def _artifact_rows(artifacts: Any, base_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for key, value in sorted(_dict(artifacts).items()):
        path = Path(str(value))
        check_path = path if path.is_absolute() else base_dir / path
        rows.append({"key": key, "path": str(path), "exists": check_path.exists()})
    return rows


def _recommendations(status: str, artifacts: list[dict[str, Any]], failed_key: str | None) -> list[str]:
    if status == "planned":
        return ["Run the pipeline with --execute when you want to create the training portfolio artifacts."]
    if status == "failed":
        return [f"Inspect the `{failed_key}` step stdout/stderr before trusting downstream artifacts."]
    missing = [row["key"] for row in artifacts if not row.get("exists")]
    if missing:
        return ["Pipeline completed, but these expected artifacts are missing: " + ", ".join(missing)]
    return ["Use training_portfolio.html as the run-level entry point, then open the linked dataset, benchmark, and maturity artifacts."]


def _tail(text: str, line_count: int = 8) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-line_count:])


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
