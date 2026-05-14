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
    list_of_strs as _list_of_strs,
    make_artifact_rows,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_csv_row,
    write_json_payload,
)


def load_promoted_training_scale_seed(path: str | Path) -> dict[str, Any]:
    seed_path = _resolve_seed_path(Path(path))
    payload = json.loads(seed_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted training scale seed must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(seed_path)
    return payload


def build_promoted_training_scale_seed_handoff(
    seed_path: str | Path,
    *,
    execute: bool = False,
    allow_review: bool = True,
    timeout_seconds: int = 900,
    generated_at: str | None = None,
    title: str = "MiniGPT promoted training scale seed handoff",
) -> dict[str, Any]:
    seed = load_promoted_training_scale_seed(seed_path)
    seed_file = Path(str(seed.get("_source_path")))
    seed_dir = seed_file.parent
    seed_status = str(seed.get("seed_status") or "")
    next_plan = _dict(seed.get("next_plan"))
    project_root = _resolve_path(next_plan.get("project_root"), seed_dir)
    command = _list_of_strs(next_plan.get("command"))
    allowed, blocked_reason = _handoff_allowed(seed_status, command, allow_review=allow_review)
    execution = _execution_result(
        command,
        project_root=project_root,
        execute=execute,
        allowed=allowed,
        blocked_reason=blocked_reason,
        timeout_seconds=timeout_seconds,
    )
    plan_report = _load_plan_report(project_root, next_plan)
    artifact_rows = _artifact_rows(project_root, next_plan)
    next_batch_command = _list_of_strs(_dict(plan_report.get("batch")).get("command"))
    summary = _summary(seed, next_plan, plan_report, execution, artifact_rows, next_batch_command)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "seed_path": str(seed_file),
        "seed_status": seed_status,
        "allow_review": bool(allow_review),
        "execute": bool(execute),
        "timeout_seconds": int(timeout_seconds),
        "handoff_allowed": allowed,
        "blocked_reason": blocked_reason,
        "command": command,
        "command_text": _display_command(command),
        "execution": execution,
        "plan_report_path": str(_plan_report_path(project_root, next_plan)),
        "plan_report": plan_report,
        "next_batch_command": next_batch_command,
        "next_batch_command_text": _display_command(next_batch_command),
        "artifact_rows": artifact_rows,
        "summary": summary,
        "recommendations": _recommendations(summary, plan_report, execution, artifact_rows, next_batch_command),
    }


def write_promoted_training_scale_seed_handoff_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_seed_handoff_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    fieldnames = [
        "handoff_status",
        "seed_status",
        "decision_status",
        "execute",
        "returncode",
        "elapsed_seconds",
        "artifact_count",
        "available_artifact_count",
        "plan_status",
        "plan_variant_count",
        "next_batch_command_available",
        "blocked_reason",
    ]
    write_csv_row(
        {
            "handoff_status": summary.get("handoff_status"),
            "seed_status": report.get("seed_status"),
            "decision_status": summary.get("decision_status"),
            "execute": report.get("execute"),
            "returncode": execution.get("returncode"),
            "elapsed_seconds": execution.get("elapsed_seconds"),
            "artifact_count": summary.get("artifact_count"),
            "available_artifact_count": summary.get("available_artifact_count"),
            "plan_status": summary.get("plan_status"),
            "plan_variant_count": summary.get("plan_variant_count"),
            "next_batch_command_available": summary.get("next_batch_command_available"),
            "blocked_reason": report.get("blocked_reason"),
        },
        out_path,
        fieldnames,
    )


def render_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale seed handoff')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Handoff status: `{summary.get('handoff_status')}`",
        f"- Seed status: `{report.get('seed_status')}`",
        f"- Decision status: `{summary.get('decision_status')}`",
        f"- Execute: `{report.get('execute')}`",
        f"- Return code: `{execution.get('returncode')}`",
        f"- Artifacts: `{summary.get('available_artifact_count')}/{summary.get('artifact_count')}`",
        f"- Plan status: `{summary.get('plan_status')}`",
        f"- Next batch command: `{summary.get('next_batch_command_available')}`",
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
        "## Plan Artifacts",
        "",
        "| Key | Exists | Path |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("artifact_rows")):
        lines.append(f"| {_md(row.get('key'))} | {_md(row.get('exists'))} | {_md(row.get('path'))} |")
    if report.get("next_batch_command"):
        lines.extend(["", "## Next Batch Command", "", "```powershell", str(report.get("next_batch_command_text") or ""), "```"])
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_markdown(report), encoding="utf-8")


def render_promoted_training_scale_seed_handoff_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    execution = _dict(report.get("execution"))
    stats = [
        ("Status", summary.get("handoff_status")),
        ("Seed", report.get("seed_status")),
        ("Decision", summary.get("decision_status")),
        ("Execute", report.get("execute")),
        ("Return", execution.get("returncode")),
        ("Artifacts", f"{summary.get('available_artifact_count')}/{summary.get('artifact_count')}"),
        ("Plan", summary.get("plan_status")),
        ("Batch", summary.get("next_batch_command_available")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale seed handoff'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale seed handoff'))}</h1><p>{_e(report.get('seed_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _command_section(report),
            _execution_section(execution),
            _artifact_section(report),
            _plan_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale seed handoff.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_promoted_training_scale_seed_handoff_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_html(report), encoding="utf-8")


def write_promoted_training_scale_seed_handoff_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_seed_handoff.json",
        "csv": root / "promoted_training_scale_seed_handoff.csv",
        "markdown": root / "promoted_training_scale_seed_handoff.md",
        "html": root / "promoted_training_scale_seed_handoff.html",
    }
    write_promoted_training_scale_seed_handoff_json(report, paths["json"])
    write_promoted_training_scale_seed_handoff_csv(report, paths["csv"])
    write_promoted_training_scale_seed_handoff_markdown(report, paths["markdown"])
    write_promoted_training_scale_seed_handoff_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_path(value: Any, base_dir: Path) -> Path:
    if value is None:
        return base_dir
    path = Path(str(value))
    if path.is_absolute():
        return path
    return base_dir / path


def _resolve_seed_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "promoted_training_scale_seed.json",
                path / "promoted-seed" / "promoted_training_scale_seed.json",
                path / "seed" / "promoted_training_scale_seed.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _load_plan_report(project_root: Path, next_plan: dict[str, Any]) -> dict[str, Any]:
    plan_path = _plan_report_path(project_root, next_plan)
    if not plan_path.is_file():
        return {}
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _plan_report_path(project_root: Path, next_plan: dict[str, Any]) -> Path:
    plan_out_dir = _resolve_path(next_plan.get("plan_out_dir"), project_root)
    return plan_out_dir / "training_scale_plan.json"


def _artifact_rows(project_root: Path, next_plan: dict[str, Any]) -> list[dict[str, Any]]:
    plan_out_dir = _resolve_path(next_plan.get("plan_out_dir"), project_root)
    return make_artifact_rows(
        [
            ("training_scale_plan_json", plan_out_dir / "training_scale_plan.json"),
            ("training_scale_variants_json", plan_out_dir / "training_scale_variants.json"),
            ("training_scale_plan_csv", plan_out_dir / "training_scale_plan.csv"),
            ("training_scale_plan_markdown", plan_out_dir / "training_scale_plan.md"),
            ("training_scale_plan_html", plan_out_dir / "training_scale_plan.html"),
        ]
    )


def _summary(
    seed: dict[str, Any],
    next_plan: dict[str, Any],
    plan_report: dict[str, Any],
    execution: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    next_batch_command: list[str],
) -> dict[str, Any]:
    baseline = _dict(seed.get("baseline_seed"))
    plan_summary = _dict(plan_report.get("summary"))
    plan_dataset = _dict(plan_report.get("dataset"))
    return {
        "handoff_status": execution.get("status"),
        "seed_status": seed.get("seed_status"),
        "decision_status": baseline.get("decision_status"),
        "selected_name": baseline.get("selected_name"),
        "selected_gate_status": baseline.get("gate_status"),
        "selected_batch_status": baseline.get("batch_status"),
        "selected_readiness_score": baseline.get("readiness_score"),
        "source_count": len(_list_of_dicts(next_plan.get("sources"))),
        "missing_source_count": sum(1 for row in _list_of_dicts(next_plan.get("sources")) if not row.get("exists")),
        "artifact_count": len(artifact_rows),
        "available_artifact_count": count_available_artifacts(artifact_rows),
        "plan_status": "available" if plan_report else "missing",
        "plan_scale_tier": plan_dataset.get("scale_tier"),
        "plan_variant_count": len(_list_of_dicts(plan_report.get("variants"))),
        "plan_source_count": plan_dataset.get("source_count"),
        "plan_quality_status": plan_dataset.get("quality_status"),
        "next_batch_command_available": bool(next_batch_command),
        "execution_returncode": execution.get("returncode"),
        "execution_elapsed_seconds": execution.get("elapsed_seconds"),
    }


def _recommendations(
    summary: dict[str, Any],
    plan_report: dict[str, Any],
    execution: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    next_batch_command: list[str],
) -> list[str]:
    status = str(summary.get("handoff_status") or "")
    if status == "planned":
        return ["Review the generated seed command, then rerun with --execute to materialize the next training scale plan."]
    if status == "blocked":
        return ["Fix the seed or plan blockers before trying to produce the next training scale plan."]
    if status == "timeout":
        return ["Inspect the partial plan output tree and rerun with a larger timeout if the plan command is still valid."]
    if status == "failed":
        return ["Inspect stdout/stderr tails and the seed command before retrying the next plan handoff."]
    recommendations = [
        "Use the generated plan report and batch command as the next input to the training-scale workflow.",
    ]
    if plan_report:
        recommendations.append("Keep the generated plan JSON and variants JSON as the evidence for the next cycle.")
    if artifact_rows and summary.get("available_artifact_count") != summary.get("artifact_count"):
        recommendations.append("Some expected plan artifacts are missing; inspect the plan output directory before moving on.")
    if next_batch_command:
        recommendations.append("The next batch command is ready, but it should be reviewed before executing training.")
    if execution.get("returncode") not in {None, 0}:
        recommendations.append("The plan command returned a non-zero exit code, so treat the seed handoff as failed.")
    return recommendations


def _handoff_allowed(seed_status: str, command: list[str], *, allow_review: bool) -> tuple[bool, str | None]:
    if not command:
        return False, "seed did not provide a plan command"
    if seed_status == "ready":
        return True, None
    if seed_status == "review" and allow_review:
        return True, None
    if seed_status == "review":
        return False, "seed status is review and allow_review is false"
    return False, f"seed status is {seed_status or 'missing'}"


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
        "blocked_reason": None if completed.returncode == 0 else "plan command returned non-zero",
    }


def _plan_section(report: dict[str, Any]) -> str:
    plan = _dict(report.get("plan_report"))
    if not plan:
        return "<section><h2>Plan Report</h2><p>No plan report was loaded.</p></section>"
    dataset = _dict(plan.get("dataset"))
    batch = _dict(plan.get("batch"))
    rows = [
        ("Scale tier", dataset.get("scale_tier")),
        ("Source count", dataset.get("source_count")),
        ("Character count", dataset.get("char_count")),
        ("Quality status", dataset.get("quality_status")),
        ("Warning count", dataset.get("warning_count")),
        ("Variant count", len(_list_of_dicts(plan.get("variants")))),
        ("Batch baseline", batch.get("baseline")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    next_batch = _display_command(report.get("next_batch_command"))
    extra = f"<p><strong>Next batch command:</strong></p><pre>{_e(next_batch)}</pre>" if next_batch else "<p>No next batch command is available yet.</p>"
    return f"<section><h2>Plan Report</h2><table>{body}</table>{extra}</section>"


def _command_section(report: dict[str, Any]) -> str:
    return f"<section><h2>Seed Command</h2><pre>{_e(report.get('command_text'))}</pre></section>"


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
        '<section><h2>Plan Artifacts</h2><div class="table-wrap"><table>'
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
th { color: #435047; font-size: 12px; text-transform: uppercase; width: 180px; }
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
