from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell as _csv_value,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_json_payload,
)


GATE_ORDER = {"fail": 0, "warn": 1, "pass": 2}


def load_training_scale_run(path: str | Path) -> dict[str, Any]:
    run_path = _resolve_run_path(Path(path))
    payload = json.loads(run_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale run must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(run_path)
    return payload


def build_training_scale_run_comparison(
    run_paths: list[str | Path],
    *,
    names: list[str] | None = None,
    baseline: str | int | None = None,
    title: str = "MiniGPT training scale run comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not run_paths:
        raise ValueError("at least one training scale run is required")
    if names is not None and len(names) != len(run_paths):
        raise ValueError("names length must match run_paths length")
    reports = [load_training_scale_run(path) for path in run_paths]
    resolved_names = _resolve_names(reports, names)
    runs = [_run_summary(report, resolved_names[index], index) for index, report in enumerate(reports)]
    baseline_run = _select_baseline(runs, baseline)
    deltas = [_run_delta(row, baseline_run) for row in runs]
    summary = _comparison_summary(runs, baseline_run, deltas)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "run_count": len(runs),
        "baseline": baseline_run,
        "runs": runs,
        "baseline_deltas": deltas,
        "summary": summary,
        "best_by_readiness": _best_by_readiness(runs),
        "recommendations": _recommendations(summary, deltas),
    }


def write_training_scale_run_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_run_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "source_path",
        "status",
        "allowed",
        "gate_status",
        "gate_profile",
        "gate_fail_count",
        "gate_warn_count",
        "scale_tier",
        "char_count",
        "variant_count",
        "batch_status",
        "comparison_status",
        "execute",
        "blocked_reason",
        "readiness_score",
        "baseline_name",
        "is_baseline",
        "allowed_delta",
        "readiness_delta",
        "gate_relation",
        "batch_relation",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for run in _list_of_dicts(report.get("runs")):
            row = dict(run)
            row.update(deltas.get(run.get("name"), {}))
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_training_scale_run_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale run comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runs: `{report.get('run_count')}`",
        f"- Baseline: `{baseline.get('name')}`",
        f"- Allowed: `{summary.get('allowed_count')}`",
        f"- Blocked: `{summary.get('blocked_count')}`",
        f"- Batch started: `{summary.get('batch_started_count')}`",
        f"- Gate warnings: `{summary.get('gate_warn_count')}`",
        f"- Gate failures: `{summary.get('gate_fail_count')}`",
        "",
        "## Runs",
        "",
        "| Run | Status | Allowed | Gate | Profile | Scale | Variants | Batch | Score | Relation |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("name"), {})
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(run.get("name")),
                    _md(run.get("status")),
                    _md(run.get("allowed")),
                    _md(run.get("gate_status")),
                    _md(run.get("gate_profile")),
                    _md(run.get("scale_tier")),
                    _md(run.get("variant_count")),
                    _md(run.get("batch_status")),
                    _md(run.get("readiness_score")),
                    _md(delta.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_run_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_comparison_markdown(report), encoding="utf-8")


def render_training_scale_run_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    best = _dict(report.get("best_by_readiness"))
    stats = [
        ("Baseline", baseline.get("name")),
        ("Runs", report.get("run_count")),
        ("Allowed", summary.get("allowed_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Batch started", summary.get("batch_started_count")),
        ("Gate warn", summary.get("gate_warn_count")),
        ("Gate fail", summary.get("gate_fail_count")),
        ("Best", best.get("name")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale run comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale run comparison'))}</h1><p>Baseline: {_e(baseline.get('name'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _runs_table(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale run comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_run_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_comparison_html(report), encoding="utf-8")


def write_training_scale_run_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_run_comparison.json",
        "csv": root / "training_scale_run_comparison.csv",
        "markdown": root / "training_scale_run_comparison.md",
        "html": root / "training_scale_run_comparison.html",
    }
    write_training_scale_run_comparison_json(report, paths["json"])
    write_training_scale_run_comparison_csv(report, paths["csv"])
    write_training_scale_run_comparison_markdown(report, paths["markdown"])
    write_training_scale_run_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_run_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.append(path / "training_scale_run.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _resolve_names(reports: list[dict[str, Any]], names: list[str] | None) -> list[str]:
    if names is not None:
        resolved = [str(name).strip() for name in names]
    else:
        resolved = [
            str(report.get("name") or Path(str(report.get("_source_path") or f"run-{index + 1}")).parent.name or f"run-{index + 1}")
            for index, report in enumerate(reports)
        ]
    if any(not name for name in resolved):
        raise ValueError("run names cannot be empty")
    if len(set(resolved)) != len(resolved):
        raise ValueError("run names must be unique")
    return resolved


def _run_summary(report: dict[str, Any], name: str, index: int) -> dict[str, Any]:
    gate = _dict(report.get("gate"))
    plan = _dict(report.get("scale_plan_summary"))
    batch = _dict(report.get("batch_summary"))
    row = {
        "index": index + 1,
        "name": name,
        "source_path": report.get("_source_path"),
        "status": report.get("status"),
        "allowed": bool(report.get("allowed")),
        "execute": bool(report.get("execute")),
        "gate_status": gate.get("overall_status"),
        "gate_profile": report.get("gate_profile") or gate.get("profile"),
        "gate_pass_count": gate.get("pass_count"),
        "gate_warn_count": gate.get("warn_count"),
        "gate_fail_count": gate.get("fail_count"),
        "dataset_name": plan.get("dataset_name"),
        "version_prefix": plan.get("version_prefix"),
        "scale_tier": plan.get("scale_tier"),
        "char_count": plan.get("char_count"),
        "warning_count": plan.get("warning_count"),
        "variant_count": plan.get("variant_count"),
        "baseline": plan.get("baseline"),
        "batch_status": batch.get("status"),
        "comparison_status": batch.get("comparison_status"),
        "completed_variant_count": batch.get("completed_variant_count"),
        "blocked_reason": report.get("blocked_reason"),
        "gate_outputs": _dict(report.get("gate_outputs")),
        "batch_outputs": _dict(report.get("batch_outputs")),
    }
    row["readiness_score"] = _readiness_score(row)
    return row


def _readiness_score(row: dict[str, Any]) -> int:
    score = 0
    if row.get("allowed"):
        score += 35
    score += {"pass": 35, "warn": 18, "fail": 0}.get(str(row.get("gate_status")), 0)
    score += {"completed": 25, "planned": 18, "skipped": 0, "failed": -10}.get(str(row.get("batch_status")), 0)
    if row.get("comparison_status") == "written":
        score += 7
    if row.get("execute"):
        score += 5
    return max(0, score)


def _select_baseline(runs: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    if baseline is None:
        return runs[0]
    if isinstance(baseline, int) or (isinstance(baseline, str) and str(baseline).isdigit()):
        index = int(baseline)
        if index < 0 or index >= len(runs):
            raise ValueError("baseline index out of range")
        return runs[index]
    for run in runs:
        if run.get("name") == baseline:
            return run
    raise ValueError(f"baseline not found: {baseline}")


def _run_delta(run: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    readiness_delta = _int(run.get("readiness_score")) - _int(baseline.get("readiness_score"))
    gate_delta = GATE_ORDER.get(str(run.get("gate_status")), -1) - GATE_ORDER.get(str(baseline.get("gate_status")), -1)
    allowed_delta = int(bool(run.get("allowed"))) - int(bool(baseline.get("allowed")))
    return {
        "name": run.get("name"),
        "baseline_name": baseline.get("name"),
        "is_baseline": run.get("name") == baseline.get("name"),
        "allowed_delta": allowed_delta,
        "readiness_delta": readiness_delta,
        "gate_relation": _relation(gate_delta),
        "batch_relation": _batch_relation(run, baseline),
        "explanation": _delta_explanation(run, baseline, readiness_delta, gate_delta, allowed_delta),
    }


def _comparison_summary(runs: list[dict[str, Any]], baseline: dict[str, Any], deltas: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "baseline_name": baseline.get("name"),
        "run_count": len(runs),
        "allowed_count": sum(1 for row in runs if row.get("allowed")),
        "blocked_count": sum(1 for row in runs if row.get("status") == "blocked" or not row.get("allowed")),
        "batch_started_count": sum(1 for row in runs if row.get("batch_status") not in {None, "skipped"}),
        "batch_skipped_count": sum(1 for row in runs if row.get("batch_status") in {None, "skipped"}),
        "gate_pass_count": sum(1 for row in runs if row.get("gate_status") == "pass"),
        "gate_warn_count": sum(1 for row in runs if row.get("gate_status") == "warn"),
        "gate_fail_count": sum(1 for row in runs if row.get("gate_status") == "fail"),
        "readiness_improvement_count": sum(1 for row in deltas if _int(row.get("readiness_delta")) > 0),
        "readiness_regression_count": sum(1 for row in deltas if _int(row.get("readiness_delta")) < 0),
    }


def _best_by_readiness(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        return {}
    return dict(max(runs, key=lambda row: _int(row.get("readiness_score"))))


def _recommendations(summary: dict[str, Any], deltas: list[dict[str, Any]]) -> list[str]:
    recommendations = []
    if _int(summary.get("blocked_count")):
        recommendations.append("Review blocked gated runs before executing larger-corpus batches.")
    if _int(summary.get("gate_fail_count")):
        recommendations.append("Gate failures should be fixed or explicitly justified before using --allow-fail.")
    if _int(summary.get("gate_warn_count")):
        recommendations.append("Gate warnings can support smoke evidence, but should not be treated as model capability proof.")
    if _int(summary.get("batch_started_count")) and not _int(summary.get("blocked_count")):
        recommendations.append("All compared runs reached the batch layer; review batch comparisons before moving to --execute.")
    if any(_int(row.get("readiness_delta")) < 0 for row in deltas):
        recommendations.append("At least one run regressed against the baseline readiness score.")
    if not recommendations:
        recommendations.append("No blocked or regressed scale runs were found.")
    return recommendations


def _relation(delta: int) -> str:
    if delta > 0:
        return "improved"
    if delta < 0:
        return "regressed"
    return "unchanged"


def _batch_relation(run: dict[str, Any], baseline: dict[str, Any]) -> str:
    if run.get("batch_status") == baseline.get("batch_status"):
        return "unchanged"
    if run.get("batch_status") != "skipped" and baseline.get("batch_status") == "skipped":
        return "improved"
    if run.get("batch_status") == "skipped" and baseline.get("batch_status") != "skipped":
        return "regressed"
    return "changed"


def _delta_explanation(run: dict[str, Any], baseline: dict[str, Any], readiness_delta: int, gate_delta: int, allowed_delta: int) -> str:
    if run.get("name") == baseline.get("name"):
        return "baseline"
    parts = []
    if readiness_delta:
        parts.append(f"readiness {_signed(readiness_delta)}")
    if gate_delta:
        parts.append(f"gate {_relation(gate_delta)}")
    if allowed_delta:
        parts.append("allowed changed")
    if run.get("batch_status") != baseline.get("batch_status"):
        parts.append(f"batch {baseline.get('batch_status')} -> {run.get('batch_status')}")
    return "; ".join(parts) or "unchanged"


def _runs_table(report: dict[str, Any]) -> str:
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    rows = []
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("name"), {})
        rows.append(
            "<tr>"
            f"<td>{_e(run.get('name'))}</td>"
            f"<td>{_e(run.get('status'))}</td>"
            f"<td>{_e(run.get('allowed'))}</td>"
            f"<td>{_e(run.get('gate_status'))}</td>"
            f"<td>{_e(run.get('gate_profile'))}</td>"
            f"<td>{_e(run.get('scale_tier'))}</td>"
            f"<td>{_e(run.get('variant_count'))}</td>"
            f"<td>{_e(run.get('batch_status'))}</td>"
            f"<td>{_e(run.get('readiness_score'))}</td>"
            f"<td>{_e(delta.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Runs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Run</th><th>Status</th><th>Allowed</th><th>Gate</th><th>Profile</th><th>Scale</th><th>Variants</th><th>Batch</th><th>Score</th><th>Relation</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f7f2; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1160px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 900px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
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


def _signed(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)
