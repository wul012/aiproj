from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_json_payload,
)
from minigpt.training_scale_plan import build_training_scale_plan, write_training_scale_plan_outputs
from minigpt.training_scale_run import run_training_scale_plan
from minigpt.training_scale_run_comparison import (
    build_training_scale_run_comparison,
    write_training_scale_run_comparison_outputs,
)
from minigpt.training_scale_run_decision import (
    build_training_scale_run_decision,
    write_training_scale_run_decision_outputs,
)


def run_training_scale_workflow(
    sources: list[str | Path],
    *,
    project_root: str | Path | None = None,
    out_root: str | Path = "runs/training-scale-workflow",
    profiles: list[str] | None = None,
    baseline_profile: str | None = None,
    dataset_name: str = "portfolio-zh",
    dataset_version_prefix: str = "v75",
    dataset_description: str = "MiniGPT corpus planned for scale-aware training.",
    recursive: bool = True,
    max_variants: int = 3,
    sample_prompt: str = "MiniGPT",
    execute: bool = False,
    compare: bool = True,
    allow_warn: bool = True,
    allow_fail: bool = False,
    decision_min_readiness: int = 60,
    decision_require_gate_pass: bool = False,
    decision_require_batch_started: bool = True,
    decision_execute_out_root: str | Path | None = None,
    python_executable: str = "python",
    generated_at: str | None = None,
    title: str = "MiniGPT training scale workflow",
) -> dict[str, Any]:
    resolved_profiles = _resolve_profiles(profiles)
    baseline = baseline_profile or resolved_profiles[0]
    if baseline not in resolved_profiles:
        raise ValueError("baseline_profile must be one of profiles")
    generated = generated_at or utc_now()
    root = Path(out_root)
    project = Path(project_root) if project_root is not None else Path.cwd()
    plan_dir = root / "plan"
    plan = build_training_scale_plan(
        sources,
        project_root=project,
        out_root=plan_dir,
        batch_out_root=root / "batch-from-plan",
        dataset_name=dataset_name,
        dataset_version_prefix=dataset_version_prefix,
        dataset_description=dataset_description,
        recursive=recursive,
        max_variants=max_variants,
        python_executable=python_executable,
        sample_prompt=sample_prompt,
        generated_at=generated,
        title="MiniGPT training scale workflow plan",
    )
    plan_outputs = write_training_scale_plan_outputs(plan, plan_dir)
    run_rows: list[dict[str, Any]] = []
    run_paths: list[Path] = []
    for profile in resolved_profiles:
        run_dir = root / "runs" / profile
        run_report = run_training_scale_plan(
            plan_outputs["json"],
            project_root=project,
            out_root=run_dir,
            gate_profile=profile,
            execute=execute,
            compare=compare,
            allow_warn=allow_warn,
            allow_fail=allow_fail,
            python_executable=python_executable,
            generated_at=generated,
            title=f"MiniGPT gated training scale run ({profile})",
        )
        run_json = run_dir / "training_scale_run.json"
        run_paths.append(run_json)
        run_rows.append(_profile_run_summary(profile, run_report, run_dir))
    comparison = build_training_scale_run_comparison(
        run_paths,
        names=resolved_profiles,
        baseline=baseline,
        title="MiniGPT training scale workflow comparison",
        generated_at=generated,
    )
    comparison_outputs = write_training_scale_run_comparison_outputs(comparison, root / "comparison")
    comparison_by_name = {row.get("name"): row for row in _list_of_dicts(comparison.get("runs"))}
    for row in run_rows:
        compared = comparison_by_name.get(row.get("profile"), {})
        row["readiness_score"] = compared.get("readiness_score")
        row["comparison_status"] = compared.get("comparison_status")
    decision = build_training_scale_run_decision(
        comparison_outputs["json"],
        min_readiness=decision_min_readiness,
        require_gate_pass=decision_require_gate_pass,
        require_batch_started=decision_require_batch_started,
        execute_out_root=decision_execute_out_root,
        python_executable=python_executable,
        title="MiniGPT training scale workflow decision",
        generated_at=generated,
    )
    decision_outputs = write_training_scale_run_decision_outputs(decision, root / "decision")
    summary = _workflow_summary(plan, comparison, decision, run_rows)
    report = {
        "schema_version": 1,
        "title": title,
        "generated_at": generated,
        "project_root": str(project),
        "out_root": str(root),
        "sources": [str(Path(source)) for source in sources],
        "profiles": resolved_profiles,
        "baseline_profile": baseline,
        "execute": bool(execute),
        "compare": bool(compare),
        "allow_warn": bool(allow_warn),
        "allow_fail": bool(allow_fail),
        "decision_min_readiness": int(decision_min_readiness),
        "decision_require_gate_pass": bool(decision_require_gate_pass),
        "decision_require_batch_started": bool(decision_require_batch_started),
        "plan_summary": _plan_summary(plan),
        "plan_outputs": plan_outputs,
        "runs": run_rows,
        "comparison_summary": comparison.get("summary"),
        "comparison_outputs": comparison_outputs,
        "decision_summary": decision.get("summary"),
        "decision_outputs": decision_outputs,
        "execute_command_text": decision.get("execute_command_text"),
        "summary": summary,
        "recommendations": _workflow_recommendations(summary, decision),
    }
    write_training_scale_workflow_outputs(report, root)
    return report


def write_training_scale_workflow_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_workflow_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = _dict(report.get("summary"))
    fieldnames = [
        "profile",
        "status",
        "allowed",
        "gate_status",
        "batch_status",
        "readiness_score",
        "run_json",
        "decision_status",
        "selected_profile",
        "recommended_action",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("runs")):
            writer.writerow(
                {
                    "profile": row.get("profile"),
                    "status": row.get("status"),
                    "allowed": row.get("allowed"),
                    "gate_status": row.get("gate_status"),
                    "batch_status": row.get("batch_status"),
                    "readiness_score": row.get("readiness_score"),
                    "run_json": row.get("outputs", {}).get("json") if isinstance(row.get("outputs"), dict) else None,
                    "decision_status": summary.get("decision_status"),
                    "selected_profile": summary.get("selected_profile"),
                    "recommended_action": summary.get("recommended_action"),
                }
            )


def render_training_scale_workflow_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    plan = _dict(report.get("plan_summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale workflow')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Scale: `{plan.get('scale_tier')}`",
        f"- Characters: `{plan.get('char_count')}`",
        f"- Profiles: `{', '.join(_string_list(report.get('profiles')))}`",
        f"- Decision: `{summary.get('decision_status')}`",
        f"- Selected profile: `{summary.get('selected_profile')}`",
        f"- Action: `{summary.get('recommended_action')}`",
        "",
        "## Runs",
        "",
        "| Profile | Status | Allowed | Gate | Batch | Score |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in _list_of_dicts(report.get("runs")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("profile")),
                    _md(row.get("status")),
                    _md(row.get("allowed")),
                    _md(row.get("gate_status")),
                    _md(row.get("batch_status")),
                    _md(row.get("readiness_score")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Execute command",
            "",
            "```powershell",
            str(report.get("execute_command_text") or ""),
            "```",
            "",
            "## Artifacts",
            "",
            f"- Plan: `{_dict(report.get('plan_outputs')).get('json')}`",
            f"- Comparison: `{_dict(report.get('comparison_outputs')).get('json')}`",
            f"- Decision: `{_dict(report.get('decision_outputs')).get('json')}`",
            "",
            "## Recommendations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_workflow_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_workflow_markdown(report), encoding="utf-8")


def render_training_scale_workflow_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    plan = _dict(report.get("plan_summary"))
    stats = [
        ("Scale", plan.get("scale_tier")),
        ("Chars", plan.get("char_count")),
        ("Profiles", summary.get("profile_count")),
        ("Allowed", summary.get("allowed_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Decision", summary.get("decision_status")),
        ("Selected", summary.get("selected_profile")),
        ("Action", summary.get("recommended_action")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale workflow'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale workflow'))}</h1><p>{_e(report.get('out_root'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _runs_table(report),
            _command_section(report),
            _artifact_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale workflow.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_workflow_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_workflow_html(report), encoding="utf-8")


def write_training_scale_workflow_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_workflow.json",
        "csv": root / "training_scale_workflow.csv",
        "markdown": root / "training_scale_workflow.md",
        "html": root / "training_scale_workflow.html",
    }
    write_training_scale_workflow_json(report, paths["json"])
    write_training_scale_workflow_csv(report, paths["csv"])
    write_training_scale_workflow_markdown(report, paths["markdown"])
    write_training_scale_workflow_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_profiles(profiles: list[str] | None) -> list[str]:
    resolved = [str(profile).strip() for profile in (profiles or ["review", "standard"])]
    if not resolved or any(not profile for profile in resolved):
        raise ValueError("profiles cannot be empty")
    if len(set(resolved)) != len(resolved):
        raise ValueError("profiles must be unique")
    return resolved


def _profile_run_summary(profile: str, report: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    gate = _dict(report.get("gate"))
    batch = _dict(report.get("batch_summary"))
    return {
        "profile": profile,
        "status": report.get("status"),
        "allowed": bool(report.get("allowed")),
        "gate_status": gate.get("overall_status"),
        "gate_pass_count": gate.get("pass_count"),
        "gate_warn_count": gate.get("warn_count"),
        "gate_fail_count": gate.get("fail_count"),
        "batch_status": batch.get("status"),
        "comparison_status": batch.get("comparison_status"),
        "blocked_reason": report.get("blocked_reason"),
        "outputs": _run_outputs(run_dir),
        "gate_outputs": _dict(report.get("gate_outputs")),
        "batch_outputs": _dict(report.get("batch_outputs")),
    }


def _run_outputs(run_dir: Path) -> dict[str, str]:
    return {
        "json": str(run_dir / "training_scale_run.json"),
        "csv": str(run_dir / "training_scale_run.csv"),
        "markdown": str(run_dir / "training_scale_run.md"),
        "html": str(run_dir / "training_scale_run.html"),
    }


def _plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    dataset = _dict(plan.get("dataset"))
    return {
        "dataset_name": dataset.get("name"),
        "version_prefix": dataset.get("version_prefix"),
        "scale_tier": dataset.get("scale_tier"),
        "char_count": dataset.get("char_count"),
        "warning_count": dataset.get("warning_count"),
        "variant_count": len(_list_of_dicts(plan.get("variants"))),
        "baseline": _dict(plan.get("batch")).get("baseline"),
    }


def _workflow_summary(
    plan: dict[str, Any],
    comparison: dict[str, Any],
    decision: dict[str, Any],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = _dict(decision.get("selected_run"))
    decision_summary = _dict(decision.get("summary"))
    plan_summary = _plan_summary(plan)
    return {
        "scale_tier": plan_summary.get("scale_tier"),
        "char_count": plan_summary.get("char_count"),
        "variant_count": plan_summary.get("variant_count"),
        "profile_count": len(runs),
        "allowed_count": sum(1 for row in runs if row.get("allowed")),
        "blocked_count": sum(1 for row in runs if not row.get("allowed")),
        "comparison_baseline": _dict(comparison.get("summary")).get("baseline_name"),
        "decision_status": decision.get("decision_status"),
        "recommended_action": decision.get("recommended_action"),
        "selected_profile": selected.get("name") or decision_summary.get("selected_run_name"),
        "selected_gate_status": selected.get("gate_status") or decision_summary.get("selected_gate_status"),
        "selected_batch_status": selected.get("batch_status") or decision_summary.get("selected_batch_status"),
        "selected_readiness_score": selected.get("readiness_score") or decision_summary.get("selected_readiness_score"),
    }


def _workflow_recommendations(summary: dict[str, Any], decision: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    status = str(summary.get("decision_status") or "")
    if status == "blocked":
        recommendations.append("Stop before execution; no compared profile produced an eligible scale run decision.")
    elif status == "review":
        recommendations.append("Review gate warnings and batch dry-run artifacts before using the generated execute command.")
    else:
        recommendations.append("Use the selected profile as the staged execution candidate after reviewing workflow evidence.")
    if int(summary.get("blocked_count") or 0):
        recommendations.append("Keep blocked profile outputs as evidence for why the selected profile was safer.")
    command = str(decision.get("execute_command_text") or "")
    if command:
        recommendations.append("The generated execute command is a handoff command, not automatically run by this workflow.")
    return recommendations


def _runs_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("runs")):
        outputs = _dict(row.get("outputs"))
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('profile'))}</td>"
            f"<td>{_e(row.get('status'))}</td>"
            f"<td>{_e(row.get('allowed'))}</td>"
            f"<td>{_e(row.get('gate_status'))}</td>"
            f"<td>{_e(row.get('batch_status'))}</td>"
            f"<td>{_e(row.get('readiness_score'))}</td>"
            f"<td>{_link(outputs.get('html'), 'run html')}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Profile Runs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Profile</th><th>Status</th><th>Allowed</th><th>Gate</th><th>Batch</th><th>Score</th><th>Artifact</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _command_section(report: dict[str, Any]) -> str:
    text = str(report.get("execute_command_text") or "No execute command because the workflow decision is blocked.")
    return f"<section><h2>Decision Execute Command</h2><pre>{_e(text)}</pre></section>"


def _artifact_section(report: dict[str, Any]) -> str:
    rows = [
        ("Plan", _dict(report.get("plan_outputs")).get("html")),
        ("Comparison", _dict(report.get("comparison_outputs")).get("html")),
        ("Decision", _dict(report.get("decision_outputs")).get("html")),
    ]
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_link(path, path)}</td></tr>" for label, path in rows)
    return f"<section><h2>Workflow Artifacts</h2><table>{body}</table></section>"


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
th { color: #435047; font-size: 12px; text-transform: uppercase; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
a { color: #1f6f68; text-decoration: none; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _link(path: Any, label: Any) -> str:
    if not path:
        return ""
    return f'<a href="{_e(path)}">{_e(label)}</a>'
