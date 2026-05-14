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


def load_promoted_training_scale_decision(path: str | Path) -> dict[str, Any]:
    decision_path = _resolve_decision_path(Path(path))
    payload = json.loads(decision_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted training scale decision must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(decision_path)
    return payload


def build_promoted_training_scale_seed(
    decision_path: str | Path,
    sources: list[str | Path] | None = None,
    *,
    project_root: str | Path | None = None,
    plan_out_dir: str | Path = "runs/training-scale-plan-from-promoted-baseline",
    batch_out_root: str | Path = "runs/training-portfolio-batch-from-promoted-baseline",
    dataset_name: str = "portfolio-zh",
    dataset_version_prefix: str = "v81",
    dataset_description: str = "MiniGPT corpus seeded from a promoted training scale baseline.",
    sample_prompt: str = "MiniGPT",
    max_variants: int = 3,
    python_executable: str = "python",
    title: str = "MiniGPT promoted training scale next-cycle seed",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if max_variants < 1:
        raise ValueError("max_variants must be at least 1")
    decision = load_promoted_training_scale_decision(decision_path)
    decision_file = Path(str(decision.get("_source_path")))
    decision_dir = decision_file.parent
    selected = _dict(decision.get("selected_baseline"))
    selected_run_path = _resolve_selected_run_path(selected.get("training_scale_run_path"), decision_dir)
    selected_run = _load_selected_run(selected_run_path)
    source_rows = _source_rows(sources or [])
    root = Path(project_root) if project_root is not None else Path.cwd()
    blockers = _blockers(decision, selected, selected_run_path, source_rows)
    seed_status = _seed_status(str(decision.get("decision_status") or ""), blockers)
    command = [] if blockers else _plan_command(
        source_rows,
        project_root=root,
        plan_out_dir=Path(plan_out_dir),
        batch_out_root=Path(batch_out_root),
        dataset_name=dataset_name,
        dataset_version_prefix=dataset_version_prefix,
        dataset_description=dataset_description,
        sample_prompt=sample_prompt,
        max_variants=max_variants,
        python_executable=python_executable,
    )
    seed = {
        "selected_name": selected.get("name"),
        "decision_status": decision.get("decision_status"),
        "gate_status": selected.get("gate_status"),
        "batch_status": selected.get("batch_status"),
        "readiness_score": selected.get("readiness_score"),
        "training_scale_run_path": str(selected_run_path) if selected_run_path is not None else None,
        "training_scale_run_exists": bool(selected_run_path and selected_run_path.exists()),
        "comparison_path": decision.get("comparison_path"),
        "selected_run_summary": _selected_run_summary(selected_run),
    }
    plan = {
        "project_root": str(root),
        "dataset_name": dataset_name,
        "dataset_version_prefix": dataset_version_prefix,
        "dataset_description": dataset_description,
        "sample_prompt": sample_prompt,
        "max_variants": int(max_variants),
        "plan_out_dir": str(plan_out_dir),
        "batch_out_root": str(batch_out_root),
        "sources": source_rows,
        "command": command,
        "command_text": _display_command(command),
        "command_available": bool(command),
        "execution_ready": seed_status == "ready",
    }
    summary = _summary(seed_status, decision, seed, plan, blockers)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "decision_path": str(decision_file),
        "seed_status": seed_status,
        "baseline_seed": seed,
        "next_plan": plan,
        "blockers": blockers,
        "summary": summary,
        "recommendations": _recommendations(seed_status, seed, plan, blockers),
    }


def write_promoted_training_scale_seed_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_seed_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seed = _dict(report.get("baseline_seed"))
    plan = _dict(report.get("next_plan"))
    summary = _dict(report.get("summary"))
    fieldnames = [
        "seed_status",
        "selected_baseline",
        "decision_status",
        "gate_status",
        "batch_status",
        "readiness_score",
        "source_count",
        "missing_source_count",
        "command_available",
        "execution_ready",
        "command",
    ]
    write_csv_row(
        {
            "seed_status": report.get("seed_status"),
            "selected_baseline": seed.get("selected_name"),
            "decision_status": seed.get("decision_status"),
            "gate_status": seed.get("gate_status"),
            "batch_status": seed.get("batch_status"),
            "readiness_score": seed.get("readiness_score"),
            "source_count": summary.get("source_count"),
            "missing_source_count": summary.get("missing_source_count"),
            "command_available": plan.get("command_available"),
            "execution_ready": plan.get("execution_ready"),
            "command": plan.get("command_text"),
        },
        out_path,
        fieldnames,
    )


def render_promoted_training_scale_seed_markdown(report: dict[str, Any]) -> str:
    seed = _dict(report.get("baseline_seed"))
    plan = _dict(report.get("next_plan"))
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale next-cycle seed')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Seed status: `{report.get('seed_status')}`",
        f"- Selected baseline: `{seed.get('selected_name')}`",
        f"- Decision status: `{seed.get('decision_status')}`",
        f"- Gate: `{seed.get('gate_status')}`",
        f"- Batch: `{seed.get('batch_status')}`",
        f"- Readiness: `{seed.get('readiness_score')}`",
        f"- Sources: `{summary.get('source_count')}`",
        f"- Missing sources: `{summary.get('missing_source_count')}`",
        "",
        "## Next Plan Command",
        "",
        "```powershell",
        str(plan.get("command_text") or "No command is available."),
        "```",
        "",
        "## Sources",
        "",
        "| Source | Exists | Kind |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(plan.get("sources")):
        lines.append(f"| {_md(row.get('path'))} | {_md(row.get('exists'))} | {_md(row.get('kind'))} |")
    blockers = _string_list(report.get("blockers"))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_seed_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_markdown(report), encoding="utf-8")


def render_promoted_training_scale_seed_html(report: dict[str, Any]) -> str:
    seed = _dict(report.get("baseline_seed"))
    plan = _dict(report.get("next_plan"))
    summary = _dict(report.get("summary"))
    stats = [
        ("Status", report.get("seed_status")),
        ("Baseline", seed.get("selected_name")),
        ("Decision", seed.get("decision_status")),
        ("Gate", seed.get("gate_status")),
        ("Batch", seed.get("batch_status")),
        ("Score", seed.get("readiness_score")),
        ("Sources", summary.get("source_count")),
        ("Missing", summary.get("missing_source_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale next-cycle seed'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale next-cycle seed'))}</h1><p>{_e(report.get('decision_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _baseline_section(seed),
            _command_section(plan),
            _source_table(plan),
            _list_section("Blockers", report.get("blockers")),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale next-cycle seed.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_promoted_training_scale_seed_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_html(report), encoding="utf-8")


def write_promoted_training_scale_seed_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_seed.json",
        "csv": root / "promoted_training_scale_seed.csv",
        "markdown": root / "promoted_training_scale_seed.md",
        "html": root / "promoted_training_scale_seed.html",
    }
    write_promoted_training_scale_seed_json(report, paths["json"])
    write_promoted_training_scale_seed_csv(report, paths["csv"])
    write_promoted_training_scale_seed_markdown(report, paths["markdown"])
    write_promoted_training_scale_seed_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_decision_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "promoted_training_scale_decision.json",
                path / "promoted-decision" / "promoted_training_scale_decision.json",
                path / "decision" / "promoted_training_scale_decision.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _resolve_selected_run_path(value: Any, decision_dir: Path) -> Path | None:
    if value is None:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidates = [decision_dir / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _load_selected_run(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _source_rows(sources: list[str | Path]) -> list[dict[str, Any]]:
    rows = []
    for source in sources:
        path = Path(source)
        exists = path.exists()
        if path.is_dir():
            kind = "directory"
        elif path.is_file():
            kind = "file"
        else:
            kind = "missing"
        rows.append(
            {
                "path": str(path),
                "resolved_path": str(path.resolve()) if exists else str(path),
                "exists": exists,
                "kind": kind,
            }
        )
    return rows


def _blockers(
    decision: dict[str, Any],
    selected: dict[str, Any],
    selected_run_path: Path | None,
    source_rows: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    decision_status = str(decision.get("decision_status") or "")
    if decision_status not in {"accepted", "review"}:
        blockers.append(f"decision status is {decision_status or 'missing'}")
    if not selected:
        blockers.append("decision does not contain selected_baseline")
    if selected_run_path is None:
        blockers.append("selected baseline does not include training_scale_run_path")
    elif not selected_run_path.exists():
        blockers.append("selected training_scale_run.json is missing")
    if not source_rows:
        blockers.append("no corpus sources provided for the next training scale plan")
    missing = [row.get("path") for row in source_rows if not row.get("exists")]
    if missing:
        blockers.append("missing corpus sources: " + ", ".join(str(item) for item in missing))
    return blockers


def _seed_status(decision_status: str, blockers: list[str]) -> str:
    if blockers:
        return "blocked"
    if decision_status == "review":
        return "review"
    return "ready"


def _plan_command(
    source_rows: list[dict[str, Any]],
    *,
    project_root: Path,
    plan_out_dir: Path,
    batch_out_root: Path,
    dataset_name: str,
    dataset_version_prefix: str,
    dataset_description: str,
    sample_prompt: str,
    max_variants: int,
    python_executable: str,
) -> list[str]:
    if not source_rows or any(not row.get("exists") for row in source_rows):
        return []
    return [
        str(python_executable),
        "scripts/plan_training_scale.py",
        *[str(row.get("path")) for row in source_rows],
        "--project-root",
        str(project_root),
        "--out-dir",
        str(plan_out_dir),
        "--batch-out-root",
        str(batch_out_root),
        "--dataset-name",
        dataset_name,
        "--dataset-version-prefix",
        dataset_version_prefix,
        "--dataset-description",
        dataset_description,
        "--sample-prompt",
        sample_prompt,
        "--max-variants",
        str(int(max_variants)),
    ]


def _selected_run_summary(run: dict[str, Any]) -> dict[str, Any]:
    scale = _dict(run.get("scale_plan_summary"))
    batch = _dict(run.get("batch_summary"))
    gate = _dict(run.get("gate"))
    return {
        "name": run.get("name"),
        "status": run.get("status"),
        "allowed": run.get("allowed"),
        "gate_profile": run.get("gate_profile"),
        "gate_status": gate.get("overall_status"),
        "batch_status": batch.get("status"),
        "dataset_name": scale.get("dataset_name"),
        "dataset_version_prefix": scale.get("version_prefix"),
        "scale_tier": scale.get("scale_tier"),
        "char_count": scale.get("char_count"),
        "variant_count": scale.get("variant_count") or batch.get("variant_count"),
    }


def _summary(
    seed_status: str,
    decision: dict[str, Any],
    seed: dict[str, Any],
    plan: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    sources = _list_of_dicts(plan.get("sources"))
    return {
        "seed_status": seed_status,
        "decision_status": decision.get("decision_status"),
        "selected_name": seed.get("selected_name"),
        "selected_gate_status": seed.get("gate_status"),
        "selected_batch_status": seed.get("batch_status"),
        "selected_readiness_score": seed.get("readiness_score"),
        "selected_run_exists": seed.get("training_scale_run_exists"),
        "source_count": len(sources),
        "missing_source_count": sum(1 for row in sources if not row.get("exists")),
        "command_available": plan.get("command_available"),
        "execution_ready": plan.get("execution_ready"),
        "blocker_count": len(blockers),
    }


def _recommendations(
    seed_status: str,
    seed: dict[str, Any],
    plan: dict[str, Any],
    blockers: list[str],
) -> list[str]:
    if seed_status == "ready":
        return [
            "Run the generated plan command on the next corpus, then pass its outputs through the v70-v80 training scale chain.",
            "Keep the selected promoted baseline path in the seed report so the next cycle can explain where it came from.",
        ]
    if seed_status == "review":
        return [
            "Review the promoted baseline decision before running the next plan command.",
            "If the review is accepted, reuse the generated command and keep this seed as the cycle handoff artifact.",
        ]
    if blockers:
        return ["Fix the seed blockers before starting the next training scale planning cycle."]
    return ["Inspect the promoted baseline decision before building a next-cycle plan."]


def _baseline_section(seed: dict[str, Any]) -> str:
    rows = [
        ("Selected baseline", seed.get("selected_name")),
        ("Decision status", seed.get("decision_status")),
        ("Training scale run", seed.get("training_scale_run_path")),
        ("Run exists", seed.get("training_scale_run_exists")),
        ("Comparison", seed.get("comparison_path")),
    ]
    summary = _dict(seed.get("selected_run_summary"))
    rows.extend(
        [
            ("Source scale tier", summary.get("scale_tier")),
            ("Source characters", summary.get("char_count")),
            ("Source variants", summary.get("variant_count")),
        ]
    )
    body = "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
    return f"<section><h2>Baseline Seed</h2><table>{body}</table></section>"


def _command_section(plan: dict[str, Any]) -> str:
    command = str(plan.get("command_text") or "No command is available until blockers are fixed.")
    return f"<section><h2>Next Plan Command</h2><pre>{_e(command)}</pre></section>"


def _source_table(plan: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(plan.get("sources")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('path'))}</td>"
            f"<td>{_e(row.get('exists'))}</td>"
            f"<td>{_e(row.get('kind'))}</td>"
            "</tr>"
        )
    if not rows:
        return "<section><h2>Sources</h2><p>No sources provided.</p></section>"
    return (
        '<section><h2>Sources</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Source</th><th>Exists</th><th>Kind</th></tr></thead>"
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
th { color: #435047; font-size: 12px; text-transform: uppercase; width: 190px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'
