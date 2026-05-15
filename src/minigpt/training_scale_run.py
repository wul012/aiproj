from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    list_of_strs as _list_of_strings,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_csv_row,
    write_json_payload,
)
from minigpt.training_portfolio_batch import (
    build_training_portfolio_batch_plan,
    load_training_portfolio_batch_variants,
    run_training_portfolio_batch_plan,
)
from minigpt.training_portfolio_batch_artifacts import (
    render_training_portfolio_batch_html,
    render_training_portfolio_batch_markdown,
    write_training_portfolio_batch_outputs,
)
from minigpt.training_scale_gate import build_training_scale_gate, load_training_scale_plan, write_training_scale_gate_outputs
from minigpt.training_scale_plan import write_training_scale_variants_json


def run_training_scale_plan(
    plan_path: str | Path,
    *,
    project_root: str | Path,
    out_root: str | Path,
    gate_profile: str = "review",
    execute: bool = False,
    compare: bool = True,
    allow_warn: bool = True,
    allow_fail: bool = False,
    python_executable: str = "python",
    generated_at: str | None = None,
    title: str = "MiniGPT gated training scale run",
) -> dict[str, Any]:
    plan_file = Path(plan_path)
    scale_plan = load_training_scale_plan(plan_file)
    root = Path(project_root)
    out = Path(out_root)
    gate = build_training_scale_gate(
        scale_plan,
        plan_path=plan_file,
        profile=gate_profile,
        generated_at=generated_at,
        title="MiniGPT gated training scale gate",
    )
    gate_out = out / "gate"
    gate_outputs = write_training_scale_gate_outputs(gate, gate_out)
    allowed, reason = _is_allowed(gate, allow_warn=allow_warn, allow_fail=allow_fail)
    variants_path = out / "training_scale_variants.json"
    write_training_scale_variants_json(scale_plan, variants_path)
    batch_report: dict[str, Any] | None = None
    batch_outputs: dict[str, str] = {}
    if allowed:
        variants = load_training_portfolio_batch_variants(variants_path)
        batch_plan = build_training_portfolio_batch_plan(
            root,
            [Path(source) for source in _list_of_strings(scale_plan.get("sources"))],
            out_root=out / "batch",
            variants=variants,
            dataset_name=str(_dict(scale_plan.get("dataset")).get("name") or "portfolio-zh"),
            dataset_description=str(_dict(scale_plan.get("dataset")).get("description") or "MiniGPT gated scale run dataset."),
            python_executable=python_executable,
            baseline=str(_dict(scale_plan.get("batch")).get("baseline") or variants[0]["name"]),
            title="MiniGPT gated training portfolio batch",
        )
        batch_report = run_training_portfolio_batch_plan(batch_plan, execute=execute, compare=compare)
        batch_outputs = write_training_portfolio_batch_outputs(batch_report, out / "batch")
    status = _run_status(gate, allowed, batch_report)
    report = {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "plan_path": str(plan_file),
        "project_root": str(root),
        "out_root": str(out),
        "execute": bool(execute),
        "compare": bool(compare),
        "allow_warn": bool(allow_warn),
        "allow_fail": bool(allow_fail),
        "gate_profile": gate_profile,
        "status": status,
        "allowed": allowed,
        "blocked_reason": reason,
        "scale_plan_summary": _scale_plan_summary(scale_plan),
        "gate": _gate_summary(gate),
        "gate_outputs": gate_outputs,
        "variants_path": str(variants_path),
        "batch_outputs": batch_outputs,
        "batch_summary": _batch_summary(batch_report),
        "recommendations": _recommendations(status, gate, batch_report, allowed, reason),
    }
    write_training_scale_run_outputs(report, out)
    return report


def write_training_scale_run_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_run_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["status", "allowed", "gate_status", "gate_profile", "execute", "variant_count", "batch_status", "blocked_reason"]
    gate = _dict(report.get("gate"))
    batch = _dict(report.get("batch_summary"))
    plan = _dict(report.get("scale_plan_summary"))
    write_csv_row(
        {
            "status": report.get("status"),
            "allowed": report.get("allowed"),
            "gate_status": gate.get("overall_status"),
            "gate_profile": report.get("gate_profile"),
            "execute": report.get("execute"),
            "variant_count": plan.get("variant_count"),
            "batch_status": batch.get("status"),
            "blocked_reason": report.get("blocked_reason"),
        },
        out_path,
        fieldnames,
    )


def render_training_scale_run_markdown(report: dict[str, Any]) -> str:
    gate = _dict(report.get("gate"))
    batch = _dict(report.get("batch_summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT gated training scale run')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{report.get('status')}`",
        f"- Allowed: `{report.get('allowed')}`",
        f"- Gate: `{gate.get('overall_status')}` / `{report.get('gate_profile')}`",
        f"- Execute: `{report.get('execute')}`",
        f"- Batch status: `{batch.get('status')}`",
        f"- Plan: `{report.get('plan_path')}`",
        f"- Variants: `{report.get('variants_path')}`",
        "",
        "## Gate",
        "",
        *_markdown_table(
            [
                ("Status", gate.get("overall_status")),
                ("Pass", gate.get("pass_count")),
                ("Warn", gate.get("warn_count")),
                ("Fail", gate.get("fail_count")),
                ("Outputs", _display_dict(report.get("gate_outputs"))),
            ]
        ),
        "",
        "## Batch",
        "",
        *_markdown_table(
            [
                ("Status", batch.get("status")),
                ("Variant count", batch.get("variant_count")),
                ("Comparison", batch.get("comparison_status")),
                ("Outputs", _display_dict(report.get("batch_outputs"))),
                ("Blocked reason", report.get("blocked_reason")),
            ]
        ),
        "",
        "## Recommendations",
        "",
    ]
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_run_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_markdown(report), encoding="utf-8")


def render_training_scale_run_html(report: dict[str, Any]) -> str:
    gate = _dict(report.get("gate"))
    batch = _dict(report.get("batch_summary"))
    plan = _dict(report.get("scale_plan_summary"))
    stats = [
        ("Status", report.get("status")),
        ("Allowed", report.get("allowed")),
        ("Gate", gate.get("overall_status")),
        ("Profile", report.get("gate_profile")),
        ("Dataset", plan.get("dataset_name")),
        ("Execute", report.get("execute")),
        ("Scale", plan.get("scale_tier")),
        ("Variants", plan.get("variant_count")),
        ("Batch", batch.get("status")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT gated training scale run'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT gated training scale run'))}</h1><p>{_e(report.get('plan_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _summary_section("Gate", [("Status", gate.get("overall_status")), ("Pass", gate.get("pass_count")), ("Warn", gate.get("warn_count")), ("Fail", gate.get("fail_count")), ("Outputs", _display_dict(report.get("gate_outputs")))]),
            _summary_section("Batch", [("Status", batch.get("status")), ("Variant count", batch.get("variant_count")), ("Comparison", batch.get("comparison_status")), ("Outputs", _display_dict(report.get("batch_outputs"))), ("Blocked reason", report.get("blocked_reason"))]),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT gated training scale run.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_run_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_html(report), encoding="utf-8")


def write_training_scale_run_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_run.json",
        "csv": root / "training_scale_run.csv",
        "markdown": root / "training_scale_run.md",
        "html": root / "training_scale_run.html",
    }
    write_training_scale_run_json(report, paths["json"])
    write_training_scale_run_csv(report, paths["csv"])
    write_training_scale_run_markdown(report, paths["markdown"])
    write_training_scale_run_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _is_allowed(gate: dict[str, Any], *, allow_warn: bool, allow_fail: bool) -> tuple[bool, str | None]:
    status = str(gate.get("overall_status") or "fail")
    if status == "fail" and not allow_fail:
        return False, "gate failed"
    if status == "warn" and not allow_warn:
        return False, "gate warned and allow_warn is false"
    return True, None


def _run_status(gate: dict[str, Any], allowed: bool, batch_report: dict[str, Any] | None) -> str:
    if not allowed:
        return "blocked"
    execution = _dict(batch_report.get("execution") if batch_report else {})
    if execution.get("status") == "failed":
        return "failed"
    if execution.get("status") == "completed":
        return "completed"
    if gate.get("overall_status") == "warn":
        return "planned_with_warnings"
    return "planned"


def _scale_plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
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


def _gate_summary(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "overall_status": gate.get("overall_status"),
        "pass_count": gate.get("pass_count"),
        "warn_count": gate.get("warn_count"),
        "fail_count": gate.get("fail_count"),
        "profile": gate.get("profile"),
    }


def _batch_summary(batch_report: dict[str, Any] | None) -> dict[str, Any]:
    if not batch_report:
        return {"status": "skipped", "variant_count": 0, "comparison_status": "skipped"}
    execution = _dict(batch_report.get("execution"))
    return {
        "status": execution.get("status"),
        "variant_count": execution.get("variant_count"),
        "completed_variant_count": execution.get("completed_variant_count"),
        "failed_variant": execution.get("failed_variant"),
        "comparison_status": execution.get("comparison_status"),
    }


def _recommendations(
    status: str,
    gate: dict[str, Any],
    batch_report: dict[str, Any] | None,
    allowed: bool,
    reason: str | None,
) -> list[str]:
    if not allowed:
        return [f"Batch was not started because {reason}. Fix failed checks or select a looser profile."]
    recommendations = ["Gate allowed the scale plan to reach the training portfolio batch runner."]
    if gate.get("overall_status") == "warn":
        recommendations.append("Review gate warnings before treating batch outputs as capability evidence.")
    if batch_report:
        recommendations.extend(str(item) for item in _string_list(batch_report.get("recommendations")))
    if status == "completed":
        recommendations.append("Executed batch outputs are available under the batch directory.")
    return recommendations


def _summary_section(title: str, rows: list[tuple[str, Any]]) -> str:
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return f'<section><h2>{_e(title)}</h2><table>{body}</table></section>'


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f7f2; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1120px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { width: 180px; color: #435047; font-size: 12px; text-transform: uppercase; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    output = ["| Field | Value |", "| --- | --- |"]
    for label, value in rows:
        output.append(f"| {_md(label)} | {_md(value)} |")
    return output


def _display_dict(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    return ", ".join(f"{key}={item}" for key, item in value.items())
