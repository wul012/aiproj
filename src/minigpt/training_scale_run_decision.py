from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    display_command as _display_command,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_csv_row,
    write_json_payload,
)
from minigpt.training_scale_run_comparison import load_training_scale_run


GATE_ORDER = {"fail": 0, "warn": 1, "pass": 2}
BATCH_ORDER = {"skipped": 0, None: 0, "failed": 1, "planned": 2, "completed": 3}


def load_training_scale_run_comparison(path: str | Path) -> dict[str, Any]:
    comparison_path = _resolve_comparison_path(Path(path))
    payload = json.loads(comparison_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale run comparison must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(comparison_path)
    return payload


def build_training_scale_run_decision(
    comparison_path: str | Path,
    *,
    min_readiness: int = 60,
    require_gate_pass: bool = False,
    require_batch_started: bool = True,
    execute_out_root: str | Path | None = None,
    python_executable: str = "python",
    title: str = "MiniGPT training scale run decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    comparison = load_training_scale_run_comparison(comparison_path)
    runs = _list_of_dicts(comparison.get("runs"))
    if not runs:
        raise ValueError("comparison must contain at least one run")
    base_dir = Path(str(comparison.get("_source_path"))).parent
    deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for run in runs:
        reasons = _rejection_reasons(
            run,
            min_readiness=min_readiness,
            require_gate_pass=require_gate_pass,
            require_batch_started=require_batch_started,
        )
        row = {
            "name": run.get("name"),
            "gate_status": run.get("gate_status"),
            "batch_status": run.get("batch_status"),
            "allowed": bool(run.get("allowed")),
            "readiness_score": _int(run.get("readiness_score")),
            "reasons": reasons,
        }
        if reasons:
            rejected.append(row)
        else:
            candidates.append(run)
    selected = _select_candidate(candidates)
    selected_delta = dict(deltas.get(selected.get("name"), {})) if selected else {}
    origin = _load_origin_run(selected, base_dir) if selected else {}
    execute_command = _build_execute_command(
        origin,
        selected,
        execute_out_root=execute_out_root,
        python_executable=python_executable,
    )
    status = _decision_status(selected, require_gate_pass=require_gate_pass)
    action = _recommended_action(status)
    report = {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "comparison_path": str(comparison.get("_source_path")),
        "comparison_title": comparison.get("title"),
        "min_readiness": int(min_readiness),
        "require_gate_pass": bool(require_gate_pass),
        "require_batch_started": bool(require_batch_started),
        "decision_status": status,
        "recommended_action": action,
        "selected_run": dict(selected) if selected else None,
        "selected_delta": selected_delta,
        "selected_origin": _origin_summary(origin),
        "execute_command": execute_command,
        "execute_command_text": _display_command(execute_command),
        "rejected_runs": rejected,
        "summary": _decision_summary(runs, candidates, rejected, selected, status, action),
        "recommendations": _recommendations(status, selected, rejected, execute_command),
    }
    return report


def write_training_scale_run_decision_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_run_decision_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    selected = _dict(report.get("selected_run"))
    summary = _dict(report.get("summary"))
    fieldnames = [
        "decision_status",
        "recommended_action",
        "selected_run",
        "selected_gate_status",
        "selected_batch_status",
        "selected_readiness_score",
        "candidate_count",
        "rejected_count",
        "execute_command",
    ]
    write_csv_row(
        {
            "decision_status": report.get("decision_status"),
            "recommended_action": report.get("recommended_action"),
            "selected_run": selected.get("name"),
            "selected_gate_status": selected.get("gate_status"),
            "selected_batch_status": selected.get("batch_status"),
            "selected_readiness_score": selected.get("readiness_score"),
            "candidate_count": summary.get("candidate_count"),
            "rejected_count": summary.get("rejected_count"),
            "execute_command": report.get("execute_command_text"),
        },
        out_path,
        fieldnames,
    )


def render_training_scale_run_decision_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    selected = _dict(report.get("selected_run"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale run decision')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{report.get('decision_status')}`",
        f"- Action: `{report.get('recommended_action')}`",
        f"- Selected run: `{selected.get('name')}`",
        f"- Gate: `{selected.get('gate_status')}`",
        f"- Batch: `{selected.get('batch_status')}`",
        f"- Readiness: `{selected.get('readiness_score')}`",
        f"- Candidates: `{summary.get('candidate_count')}`",
        f"- Rejected: `{summary.get('rejected_count')}`",
        "",
        "## Execute command",
        "",
        "```powershell",
        str(report.get("execute_command_text") or ""),
        "```",
        "",
        "## Rejected runs",
        "",
        "| Run | Gate | Batch | Score | Reasons |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for run in _list_of_dicts(report.get("rejected_runs")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(run.get("name")),
                    _md(run.get("gate_status")),
                    _md(run.get("batch_status")),
                    _md(run.get("readiness_score")),
                    _md("; ".join(_string_list(run.get("reasons")))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_run_decision_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_decision_markdown(report), encoding="utf-8")


def render_training_scale_run_decision_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    selected = _dict(report.get("selected_run"))
    stats = [
        ("Status", report.get("decision_status")),
        ("Action", report.get("recommended_action")),
        ("Selected", selected.get("name")),
        ("Gate", selected.get("gate_status")),
        ("Batch", selected.get("batch_status")),
        ("Readiness", selected.get("readiness_score")),
        ("Candidates", summary.get("candidate_count")),
        ("Rejected", summary.get("rejected_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale run decision'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale run decision'))}</h1><p>{_e(report.get('comparison_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _command_section(report),
            _rejected_table(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale run decision.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_run_decision_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_decision_html(report), encoding="utf-8")


def write_training_scale_run_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_run_decision.json",
        "csv": root / "training_scale_run_decision.csv",
        "markdown": root / "training_scale_run_decision.md",
        "html": root / "training_scale_run_decision.html",
    }
    write_training_scale_run_decision_json(report, paths["json"])
    write_training_scale_run_decision_csv(report, paths["csv"])
    write_training_scale_run_decision_markdown(report, paths["markdown"])
    write_training_scale_run_decision_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_comparison_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.append(path / "training_scale_run_comparison.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _rejection_reasons(
    run: dict[str, Any],
    *,
    min_readiness: int,
    require_gate_pass: bool,
    require_batch_started: bool,
) -> list[str]:
    reasons: list[str] = []
    gate_status = str(run.get("gate_status") or "")
    batch_status = run.get("batch_status")
    if not run.get("allowed"):
        reasons.append("gate did not allow this run")
    if gate_status == "fail":
        reasons.append("gate failed")
    elif require_gate_pass and gate_status != "pass":
        reasons.append("gate is not pass")
    elif not require_gate_pass and gate_status not in {"pass", "warn"}:
        reasons.append("gate is not pass or warn")
    if require_batch_started and batch_status in {None, "skipped"}:
        reasons.append("batch dry-run was not started")
    if _int(run.get("readiness_score")) < int(min_readiness):
        reasons.append(f"readiness_score below {int(min_readiness)}")
    return reasons


def _select_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    return dict(
        max(
            candidates,
            key=lambda row: (
                _int(row.get("readiness_score")),
                GATE_ORDER.get(str(row.get("gate_status")), -1),
                BATCH_ORDER.get(row.get("batch_status"), 0),
                -_int(row.get("warning_count")),
                -_int(row.get("gate_warn_count")),
            ),
        )
    )


def _load_origin_run(selected: dict[str, Any] | None, base_dir: Path) -> dict[str, Any]:
    if not selected:
        return {}
    source = selected.get("source_path")
    if not source:
        return {}
    path = _resolve_existing_path(Path(str(source)), base_dir)
    if path is None:
        return {}
    try:
        return load_training_scale_run(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _resolve_existing_path(path: Path, base_dir: Path) -> Path | None:
    candidates = [path, base_dir / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _build_execute_command(
    origin: dict[str, Any],
    selected: dict[str, Any] | None,
    *,
    execute_out_root: str | Path | None,
    python_executable: str,
) -> list[str]:
    if not selected:
        return []
    plan_path = origin.get("plan_path")
    project_root = origin.get("project_root")
    gate_profile = selected.get("gate_profile") or origin.get("gate_profile") or "review"
    out_root = execute_out_root or _default_execute_out_root(origin, selected)
    if not plan_path:
        return []
    command = [
        str(python_executable),
        "scripts/run_training_scale_plan.py",
        "--plan",
        str(plan_path),
    ]
    if project_root:
        command.extend(["--project-root", str(project_root)])
    command.extend(["--out-root", str(out_root), "--gate-profile", str(gate_profile), "--execute"])
    if origin.get("compare") is False:
        command.append("--no-compare")
    if origin.get("allow_warn") is False:
        command.append("--no-allow-warn")
    if origin.get("allow_fail") is True:
        command.append("--allow-fail")
    return command


def _default_execute_out_root(origin: dict[str, Any], selected: dict[str, Any]) -> str:
    out_root = origin.get("out_root")
    if out_root:
        return f"{out_root}-execute"
    source_path = selected.get("source_path")
    if source_path:
        return f"{Path(str(source_path)).parent}-execute"
    return "runs/training-scale-run-execute"


def _decision_status(selected: dict[str, Any] | None, *, require_gate_pass: bool) -> str:
    if not selected:
        return "blocked"
    gate_status = selected.get("gate_status")
    if gate_status == "pass":
        return "ready"
    if gate_status == "warn" and not require_gate_pass:
        return "review"
    return "blocked"


def _recommended_action(status: str) -> str:
    return {
        "ready": "execute_selected_run",
        "review": "review_warnings_then_execute",
        "blocked": "fix_gate_or_data_before_execute",
    }.get(status, "review")


def _origin_summary(origin: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_path": origin.get("plan_path"),
        "project_root": origin.get("project_root"),
        "out_root": origin.get("out_root"),
        "execute": origin.get("execute"),
        "compare": origin.get("compare"),
        "allow_warn": origin.get("allow_warn"),
        "allow_fail": origin.get("allow_fail"),
    }


def _decision_summary(
    runs: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    status: str,
    action: str,
) -> dict[str, Any]:
    return {
        "decision_status": status,
        "recommended_action": action,
        "run_count": len(runs),
        "candidate_count": len(candidates),
        "rejected_count": len(rejected),
        "selected_run_name": None if selected is None else selected.get("name"),
        "selected_gate_status": None if selected is None else selected.get("gate_status"),
        "selected_batch_status": None if selected is None else selected.get("batch_status"),
        "selected_readiness_score": None if selected is None else selected.get("readiness_score"),
    }


def _recommendations(
    status: str,
    selected: dict[str, Any] | None,
    rejected: list[dict[str, Any]],
    execute_command: list[str],
) -> list[str]:
    recommendations: list[str] = []
    if status == "blocked":
        recommendations.append("Do not execute the scale run until a gate-allowed candidate reaches the batch dry-run layer.")
    elif status == "review":
        recommendations.append("Review gate warnings and dry-run batch artifacts before running the execute command.")
    else:
        recommendations.append("The selected scale run is ready for staged execution after reviewing the dry-run evidence.")
    if selected and selected.get("gate_status") == "warn":
        recommendations.append("A warn-status gate is acceptable for smoke evidence, but it should be justified before larger training.")
    if rejected:
        recommendations.append("Keep rejected runs as comparison evidence; they explain why the selected run is safer.")
    if execute_command:
        recommendations.append("Use the execute command only after confirming dataset quality, hardware budget, and expected runtime.")
    return recommendations


def _command_section(report: dict[str, Any]) -> str:
    text = str(report.get("execute_command_text") or "")
    if not text:
        text = "No execute command because no eligible run was selected."
    return f"<section><h2>Execute Command</h2><pre>{_e(text)}</pre></section>"


def _rejected_table(report: dict[str, Any]) -> str:
    rows = []
    for run in _list_of_dicts(report.get("rejected_runs")):
        rows.append(
            "<tr>"
            f"<td>{_e(run.get('name'))}</td>"
            f"<td>{_e(run.get('gate_status'))}</td>"
            f"<td>{_e(run.get('batch_status'))}</td>"
            f"<td>{_e(run.get('readiness_score'))}</td>"
            f"<td>{_e('; '.join(_string_list(run.get('reasons'))))}</td>"
            "</tr>"
        )
    if not rows:
        return "<section><h2>Rejected Runs</h2><p>No rejected runs.</p></section>"
    return (
        '<section><h2>Rejected Runs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Run</th><th>Gate</th><th>Batch</th><th>Score</th><th>Reasons</th></tr></thead>"
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
header, section, footer { max-width: 1160px; margin: 0 auto 18px; }
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
th { color: #435047; font-size: 12px; text-transform: uppercase; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
