from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time
from typing import Any

from minigpt.training_scale_handoff_artifacts import (
    render_training_scale_handoff_html,
    render_training_scale_handoff_markdown,
    write_training_scale_handoff_csv,
    write_training_scale_handoff_html,
    write_training_scale_handoff_json,
    write_training_scale_handoff_markdown,
    write_training_scale_handoff_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    count_available_artifacts,
    display_command as _display_command,
    first_present,
    make_artifact_row,
    string_list as _string_list,
    utc_now,
)


def load_training_scale_workflow(path: str | Path) -> dict[str, Any]:
    workflow_path = _resolve_workflow_path(Path(path))
    payload = json.loads(workflow_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale workflow must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(workflow_path)
    return payload


def build_training_scale_handoff(
    workflow_path: str | Path,
    *,
    execute: bool = False,
    allow_review: bool = True,
    timeout_seconds: int = 900,
    generated_at: str | None = None,
    title: str = "MiniGPT training scale execution handoff",
) -> dict[str, Any]:
    workflow = load_training_scale_workflow(workflow_path)
    workflow_file = Path(str(workflow.get("_source_path")))
    workflow_dir = workflow_file.parent
    decision = _load_decision(workflow, workflow_dir)
    decision_status = str(decision.get("decision_status") or _dict(workflow.get("summary")).get("decision_status") or "")
    command = _command_from_decision(decision)
    allowed, blocked_reason = _handoff_allowed(decision_status, command, allow_review=allow_review)
    execution = _execution_result(
        command,
        project_root=Path(str(workflow.get("project_root") or workflow_dir)),
        execute=execute,
        allowed=allowed,
        blocked_reason=blocked_reason,
        timeout_seconds=timeout_seconds,
    )
    artifact_rows = _artifact_rows(command)
    suite_guard = _suite_guard(workflow, decision)
    summary = _summary(workflow, decision, execution, artifact_rows, suite_guard=suite_guard)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "workflow_path": str(workflow_file),
        "workflow_summary": _dict(workflow.get("summary")),
        "suite_guard": suite_guard,
        "decision_path": _dict(workflow.get("decision_outputs")).get("json"),
        "decision_status": decision_status,
        "allow_review": bool(allow_review),
        "execute": bool(execute),
        "timeout_seconds": int(timeout_seconds),
        "handoff_allowed": allowed,
        "blocked_reason": blocked_reason,
        "command": command,
        "command_text": _display_command(command),
        "execution": execution,
        "artifact_rows": artifact_rows,
        "summary": summary,
        "recommendations": _recommendations(summary, execution, artifact_rows),
    }


def _resolve_workflow_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.append(path / "training_scale_workflow.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _load_decision(workflow: dict[str, Any], workflow_dir: Path) -> dict[str, Any]:
    decision_path = _dict(workflow.get("decision_outputs")).get("json")
    if not decision_path:
        return {}
    path = Path(str(decision_path))
    candidates = [path, workflow_dir / path]
    for candidate in candidates:
        if candidate.is_file():
            payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
            return dict(payload) if isinstance(payload, dict) else {}
    return {}


def _command_from_decision(decision: dict[str, Any]) -> list[str]:
    value = decision.get("execute_command")
    if not isinstance(value, list):
        return []
    return [str(part) for part in value]


def _handoff_allowed(decision_status: str, command: list[str], *, allow_review: bool) -> tuple[bool, str | None]:
    if not command:
        return False, "decision did not provide an execute command"
    if decision_status == "ready":
        return True, None
    if decision_status == "review" and allow_review:
        return True, None
    if decision_status == "review":
        return False, "decision status is review and allow_review is false"
    return False, f"decision status is {decision_status or 'missing'}"


def _execution_result(
    command: list[str],
    *,
    project_root: Path,
    execute: bool,
    allowed: bool,
    blocked_reason: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not execute:
        return {
            "status": "planned" if allowed else "blocked",
            "returncode": None,
            "elapsed_seconds": 0.0,
            "stdout_tail": "",
            "stderr_tail": "",
            "blocked_reason": blocked_reason,
        }
    if not allowed:
        return {
            "status": "blocked",
            "returncode": None,
            "elapsed_seconds": 0.0,
            "stdout_tail": "",
            "stderr_tail": "",
            "blocked_reason": blocked_reason,
        }
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout_seconds)),
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = round(time.perf_counter() - started, 3)
        return {
            "status": "timeout",
            "returncode": None,
            "elapsed_seconds": elapsed,
            "stdout_tail": _tail(_decode_timeout_text(exc.stdout)),
            "stderr_tail": _tail(_decode_timeout_text(exc.stderr)),
            "blocked_reason": f"command exceeded timeout_seconds={timeout_seconds}",
        }
    elapsed = round(time.perf_counter() - started, 3)
    return {
        "status": "completed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
        "blocked_reason": None if completed.returncode == 0 else "execute command returned non-zero",
    }


def _artifact_rows(command: list[str]) -> list[dict[str, Any]]:
    out_root = _option_value(command, "--out-root")
    if not out_root:
        return []
    root = Path(out_root)
    rows = [
        make_artifact_row("training_scale_run_json", root / "training_scale_run.json"),
        make_artifact_row("training_scale_run_html", root / "training_scale_run.html"),
        make_artifact_row("batch_json", root / "batch" / "training_portfolio_batch.json"),
        make_artifact_row("batch_html", root / "batch" / "training_portfolio_batch.html"),
    ]
    variant_reports = sorted((root / "batch" / "variants").glob("*/training_portfolio.json")) if (root / "batch" / "variants").exists() else []
    rows.append(make_artifact_row("variant_portfolio_reports", root / "batch" / "variants", exists=bool(variant_reports), count=len(variant_reports)))
    checkpoints = sorted((root / "batch" / "variants").glob("*/runs/*/checkpoint.pt")) if (root / "batch" / "variants").exists() else []
    rows.append(make_artifact_row("variant_checkpoints", root / "batch" / "variants", exists=bool(checkpoints), count=len(checkpoints)))
    return rows


def _summary(
    workflow: dict[str, Any],
    decision: dict[str, Any],
    execution: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    *,
    suite_guard: dict[str, Any],
) -> dict[str, Any]:
    decision_summary = _dict(decision.get("summary"))
    workflow_summary = _dict(workflow.get("summary"))
    return {
        "handoff_status": execution.get("status"),
        "decision_status": decision.get("decision_status") or workflow_summary.get("decision_status"),
        "selected_profile": decision_summary.get("selected_run_name") or workflow_summary.get("selected_profile"),
        "recommended_action": decision.get("recommended_action") or workflow_summary.get("recommended_action"),
        "decision_require_suite_consistency": suite_guard.get("decision_require_suite_consistency"),
        "require_suite_consistency": suite_guard.get("require_suite_consistency"),
        "suite_consistency": suite_guard.get("suite_consistency"),
        "suite_mismatch_count": suite_guard.get("suite_mismatch_count"),
        "selected_suite_path": suite_guard.get("selected_suite_path"),
        "selected_batch_review_status": decision_summary.get("selected_batch_review_status"),
        "selected_batch_comparison_review_action_count": decision_summary.get("selected_batch_comparison_review_action_count"),
        "selected_batch_comparison_blocker_action_count": decision_summary.get("selected_batch_comparison_blocker_action_count"),
        "selected_batch_maturity_coverage_regression_count": decision_summary.get("selected_batch_maturity_coverage_regression_count"),
        "batch_comparison_review_action_count": decision_summary.get("batch_comparison_review_action_count"),
        "batch_comparison_blocker_action_count": decision_summary.get("batch_comparison_blocker_action_count"),
        "batch_maturity_coverage_regression_count": decision_summary.get("batch_maturity_coverage_regression_count"),
        "batch_comparison_blocker_reasons": _string_list(decision_summary.get("batch_comparison_blocker_reasons")),
        "artifact_count": len(artifact_rows),
        "available_artifact_count": count_available_artifacts(artifact_rows),
        "returncode": execution.get("returncode"),
    }


def _recommendations(summary: dict[str, Any], execution: dict[str, Any], artifact_rows: list[dict[str, Any]]) -> list[str]:
    if summary.get("decision_require_suite_consistency") and summary.get("suite_consistency") != "consistent":
        return ["Fix benchmark suite consistency before executing this handoff as clean model-quality evidence."]
    if summary.get("selected_batch_review_status") == "blocker":
        return ["Resolve selected batch comparison blocker actions before executing this handoff as clean evidence."]
    status = str(summary.get("handoff_status") or "")
    if status == "planned":
        if summary.get("selected_batch_review_status") == "review":
            return ["Review selected batch comparison actions, then rerun this tool with --execute when ready."]
        return ["Review the handoff command, then rerun this tool with --execute when ready."]
    if status == "blocked":
        return ["Do not execute until the workflow decision provides an allowed handoff command."]
    if status == "timeout":
        return ["Inspect the partial output directory and rerun with a larger --timeout-seconds if the training command is still valid."]
    if status == "failed":
        return ["Inspect stdout/stderr tails and the selected run output directory before retrying."]
    if artifact_rows and summary.get("available_artifact_count") != summary.get("artifact_count"):
        return ["Execution completed, but some expected artifacts are missing; inspect the batch output tree."]
    return ["Execution completed and expected handoff artifacts were found."]


def _suite_guard(workflow: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    decision_summary = _dict(decision.get("summary"))
    workflow_summary = _dict(workflow.get("summary"))
    required = (
        decision_summary.get("require_suite_consistency")
        if "require_suite_consistency" in decision_summary
        else workflow_summary.get("decision_require_suite_consistency")
    )
    return {
        "decision_require_suite_consistency": bool(required),
        "require_suite_consistency": bool(required),
        "suite_consistency": first_present(decision_summary.get("suite_consistency"), workflow_summary.get("suite_consistency")),
        "suite_mismatch_count": first_present(decision_summary.get("suite_mismatch_count"), workflow_summary.get("suite_mismatch_count")),
        "selected_suite_path": first_present(decision_summary.get("selected_suite_path"), workflow_summary.get("selected_suite_path")),
        "workflow_suite_path": workflow_summary.get("suite_path"),
        "workflow_suite_name": workflow_summary.get("suite_name"),
    }


def _option_value(command: list[str], option: str) -> str | None:
    for index, part in enumerate(command):
        if part == option and index + 1 < len(command):
            return command[index + 1]
    return None


def _decode_timeout_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _tail(text: str, max_chars: int = 700) -> str:
    text = text.strip()
    return text[-max_chars:] if len(text) > max_chars else text
