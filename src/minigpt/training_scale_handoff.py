from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    count_available_artifacts,
    display_command as _display_command,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    make_artifact_row,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_csv_row,
    write_json_payload,
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
    summary = _summary(workflow, decision, execution, artifact_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "workflow_path": str(workflow_file),
        "workflow_summary": _dict(workflow.get("summary")),
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


def write_training_scale_handoff_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_handoff_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    fieldnames = [
        "handoff_status",
        "decision_status",
        "execute",
        "returncode",
        "elapsed_seconds",
        "artifact_count",
        "available_artifact_count",
        "command",
        "blocked_reason",
    ]
    write_csv_row(
        {
            "handoff_status": summary.get("handoff_status"),
            "decision_status": report.get("decision_status"),
            "execute": report.get("execute"),
            "returncode": execution.get("returncode"),
            "elapsed_seconds": execution.get("elapsed_seconds"),
            "artifact_count": summary.get("artifact_count"),
            "available_artifact_count": summary.get("available_artifact_count"),
            "command": report.get("command_text"),
            "blocked_reason": report.get("blocked_reason"),
        },
        out_path,
        fieldnames,
    )


def render_training_scale_handoff_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale execution handoff')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Handoff status: `{summary.get('handoff_status')}`",
        f"- Decision status: `{report.get('decision_status')}`",
        f"- Execute: `{report.get('execute')}`",
        f"- Return code: `{execution.get('returncode')}`",
        f"- Artifacts: `{summary.get('available_artifact_count')}/{summary.get('artifact_count')}`",
        "",
        "## Command",
        "",
        "```powershell",
        str(report.get("command_text") or ""),
        "```",
        "",
        "## Execution",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Status | {_md(execution.get('status'))} |",
        f"| Elapsed seconds | {_md(execution.get('elapsed_seconds'))} |",
        f"| Stdout tail | {_md(execution.get('stdout_tail'))} |",
        f"| Stderr tail | {_md(execution.get('stderr_tail'))} |",
        "",
        "## Artifacts",
        "",
        "| Key | Exists | Path |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("artifact_rows")):
        lines.append(f"| {_md(row.get('key'))} | {_md(row.get('exists'))} | {_md(row.get('path'))} |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_handoff_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_handoff_markdown(report), encoding="utf-8")


def render_training_scale_handoff_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    stats = [
        ("Status", summary.get("handoff_status")),
        ("Decision", report.get("decision_status")),
        ("Execute", report.get("execute")),
        ("Return", execution.get("returncode")),
        ("Elapsed", execution.get("elapsed_seconds")),
        ("Artifacts", f"{summary.get('available_artifact_count')}/{summary.get('artifact_count')}"),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale execution handoff'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale execution handoff'))}</h1><p>{_e(report.get('workflow_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _command_section(report),
            _execution_section(execution),
            _artifact_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale execution handoff.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_handoff_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_handoff_html(report), encoding="utf-8")


def write_training_scale_handoff_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_handoff.json",
        "csv": root / "training_scale_handoff.csv",
        "markdown": root / "training_scale_handoff.md",
        "html": root / "training_scale_handoff.html",
    }
    write_training_scale_handoff_json(report, paths["json"])
    write_training_scale_handoff_csv(report, paths["csv"])
    write_training_scale_handoff_markdown(report, paths["markdown"])
    write_training_scale_handoff_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


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
) -> dict[str, Any]:
    decision_summary = _dict(decision.get("summary"))
    workflow_summary = _dict(workflow.get("summary"))
    return {
        "handoff_status": execution.get("status"),
        "decision_status": decision.get("decision_status") or workflow_summary.get("decision_status"),
        "selected_profile": decision_summary.get("selected_run_name") or workflow_summary.get("selected_profile"),
        "recommended_action": decision.get("recommended_action") or workflow_summary.get("recommended_action"),
        "artifact_count": len(artifact_rows),
        "available_artifact_count": count_available_artifacts(artifact_rows),
        "returncode": execution.get("returncode"),
    }


def _recommendations(summary: dict[str, Any], execution: dict[str, Any], artifact_rows: list[dict[str, Any]]) -> list[str]:
    status = str(summary.get("handoff_status") or "")
    if status == "planned":
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


def _option_value(command: list[str], option: str) -> str | None:
    for index, part in enumerate(command):
        if part == option and index + 1 < len(command):
            return command[index + 1]
    return None


def _command_section(report: dict[str, Any]) -> str:
    return f"<section><h2>Command</h2><pre>{_e(report.get('command_text'))}</pre></section>"


def _execution_section(execution: dict[str, Any]) -> str:
    rows = [
        ("Status", execution.get("status")),
        ("Return code", execution.get("returncode")),
        ("Elapsed seconds", execution.get("elapsed_seconds")),
        ("Blocked reason", execution.get("blocked_reason")),
        ("Stdout tail", execution.get("stdout_tail")),
        ("Stderr tail", execution.get("stderr_tail")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return f"<section><h2>Execution</h2><table>{body}</table></section>"


def _artifact_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("artifact_rows")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('key'))}</td>"
            f"<td>{_e(row.get('exists'))}</td>"
            f"<td>{_e(row.get('count'))}</td>"
            f"<td>{_e(row.get('path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Artifacts</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Key</th><th>Exists</th><th>Count</th><th>Path</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f8f3; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1180px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; width: 160px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _decode_timeout_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _tail(text: str, max_chars: int = 700) -> str:
    text = text.strip()
    return text[-max_chars:] if len(text) > max_chars else text
