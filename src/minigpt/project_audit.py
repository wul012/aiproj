from __future__ import annotations

from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any


CHECK_WEIGHTS = {
    "pass": 1.0,
    "warn": 0.5,
    "fail": 0.0,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_project_audit(
    registry_path: str | Path,
    *,
    model_card_path: str | Path | None = None,
    title: str = "MiniGPT project audit",
    generated_at: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    registry_file = Path(registry_path)
    registry = _read_required_json(registry_file)
    model_card_file = _resolve_model_card_path(registry_file, model_card_path)
    model_card = _read_json(model_card_file, warnings) if model_card_file is not None else None
    runs = _build_run_rows(registry, model_card if isinstance(model_card, dict) else None)
    checks = _build_checks(registry, model_card if isinstance(model_card, dict) else None, runs)
    summary = _summarize_checks(checks, registry, model_card if isinstance(model_card, dict) else None, runs)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "registry_path": str(registry_file),
        "model_card_path": None if model_card_file is None else str(model_card_file),
        "summary": summary,
        "checks": checks,
        "runs": runs,
        "recommendations": _build_recommendations(checks, summary),
        "warnings": warnings,
    }


def write_project_audit_json(audit: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")


def render_project_audit_markdown(audit: dict[str, Any]) -> str:
    summary = _dict(audit.get("summary"))
    lines = [
        f"# {audit.get('title', 'MiniGPT project audit')}",
        "",
        f"- Generated: `{audit.get('generated_at')}`",
        f"- Registry: `{audit.get('registry_path')}`",
        f"- Model card: `{audit.get('model_card_path') or 'missing'}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Overall status", summary.get("overall_status")),
                ("Score", summary.get("score_percent")),
                ("Runs", summary.get("run_count")),
                ("Best run", summary.get("best_run_name")),
                ("Ready runs", summary.get("ready_runs")),
                ("Pass checks", summary.get("pass_count")),
                ("Warn checks", summary.get("warn_count")),
                ("Fail checks", summary.get("fail_count")),
            ]
        ),
        "",
        "## Checks",
        "",
        "| Status | Check | Detail |",
        "| --- | --- | --- |",
    ]
    for check in _list_of_dicts(audit.get("checks")):
        lines.append(f"| {_md(check.get('status'))} | {_md(check.get('title'))} | {_md(check.get('detail'))} |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(audit.get("recommendations")))
    lines.extend(["", "## Runs", ""])
    lines.extend(_run_table(_list_of_dicts(audit.get("runs"))))
    warnings = _string_list(audit.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_project_audit_markdown(audit: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_project_audit_markdown(audit), encoding="utf-8")


def render_project_audit_html(audit: dict[str, Any]) -> str:
    summary = _dict(audit.get("summary"))
    stats = [
        ("Status", summary.get("overall_status")),
        ("Score", f"{summary.get('score_percent')}%"),
        ("Runs", summary.get("run_count")),
        ("Best run", summary.get("best_run_name")),
        ("Ready", summary.get("ready_runs")),
        ("Pass", summary.get("pass_count")),
        ("Warn", summary.get("warn_count")),
        ("Fail", summary.get("fail_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(audit.get('title', 'MiniGPT project audit'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(audit.get('title', 'MiniGPT project audit'))}</h1><p>{_e(audit.get('registry_path'))}</p></header>",
            '<section class="stats">' + "".join(_stat_card(label, value) for label, value in stats) + "</section>",
            _check_section(_list_of_dicts(audit.get("checks"))),
            _list_section("Recommendations", audit.get("recommendations")),
            _run_section(_list_of_dicts(audit.get("runs"))),
            _list_section("Warnings", audit.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT project audit exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_project_audit_html(audit: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_project_audit_html(audit), encoding="utf-8")


def write_project_audit_outputs(audit: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "project_audit.json",
        "markdown": root / "project_audit.md",
        "html": root / "project_audit.html",
    }
    write_project_audit_json(audit, paths["json"])
    write_project_audit_markdown(audit, paths["markdown"])
    write_project_audit_html(audit, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_model_card_path(registry_path: Path, model_card_path: str | Path | None) -> Path | None:
    if model_card_path is not None:
        return Path(model_card_path)
    candidates = [
        registry_path.parent / "model_card.json",
        registry_path.parent / "model-card" / "model_card.json",
        registry_path.parent.parent / "model-card" / "model_card.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"project audit input must be a JSON object: {path}")
    return payload


def _read_json(path: Path, warnings: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        warnings.append(f"model card not found: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"{path} must contain a JSON object")
        return None
    return payload


def _build_run_rows(registry: dict[str, Any], model_card: dict[str, Any] | None) -> list[dict[str, Any]]:
    model_runs = {}
    if isinstance(model_card, dict):
        for run in model_card.get("runs", []):
            if isinstance(run, dict) and run.get("path"):
                model_runs[str(run["path"])] = run
    rows = []
    for run in registry.get("runs", []):
        if not isinstance(run, dict):
            continue
        model_run = model_runs.get(str(run.get("path")), {})
        status = model_run.get("status") or _derive_status(run)
        row = {
            "name": run.get("name"),
            "path": run.get("path"),
            "status": status,
            "best_val_loss_rank": run.get("best_val_loss_rank"),
            "best_val_loss": run.get("best_val_loss"),
            "best_val_loss_delta": run.get("best_val_loss_delta"),
            "dataset_quality": run.get("dataset_quality"),
            "eval_suite_cases": run.get("eval_suite_cases"),
            "generation_quality_status": run.get("generation_quality_status"),
            "generation_quality_cases": run.get("generation_quality_cases"),
            "generation_quality_pass_count": run.get("generation_quality_pass_count"),
            "generation_quality_warn_count": run.get("generation_quality_warn_count"),
            "generation_quality_fail_count": run.get("generation_quality_fail_count"),
            "artifact_count": run.get("artifact_count"),
            "checkpoint_exists": bool(run.get("checkpoint_exists")),
            "dashboard_exists": bool(run.get("dashboard_exists")),
            "experiment_card_exists": bool(model_run.get("experiment_card_exists")),
            "tags": model_run.get("tags") or run.get("tags") or [],
            "note": model_run.get("note") or run.get("note"),
        }
        rows.append(row)
    rows.sort(key=lambda item: (_rank_sort(item.get("best_val_loss_rank")), str(item.get("name") or "")))
    return rows


def _build_checks(registry: dict[str, Any], model_card: dict[str, Any] | None, runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(runs)
    checks = [
        _check("registry_runs", "Registry has runs", "pass" if total > 0 else "fail", f"{total} registered run(s)."),
        _check(
            "best_run",
            "Best run is identified",
            "pass" if isinstance(registry.get("best_by_best_val_loss"), dict) else "fail",
            f"best={_pick(_dict(registry.get('best_by_best_val_loss')), 'name') or 'missing'}",
        ),
        _coverage_check("Comparable loss coverage", "comparable_loss", sum(1 for run in runs if run.get("best_val_loss") is not None), total),
        _coverage_check("Experiment card coverage", "experiment_cards", sum(1 for run in runs if run.get("experiment_card_exists")), total),
        _coverage_check("Dataset quality coverage", "dataset_quality", sum(1 for run in runs if run.get("dataset_quality") not in {None, "missing"}), total),
        _coverage_check("Eval suite coverage", "eval_suite", sum(1 for run in runs if run.get("eval_suite_cases") not in {None, 0}), total),
        _coverage_check("Generation quality coverage", "generation_quality", sum(1 for run in runs if run.get("generation_quality_status") not in {None, "missing"}), total),
        _coverage_check("Checkpoint coverage", "checkpoints", sum(1 for run in runs if run.get("checkpoint_exists")), total),
        _coverage_check("Dashboard coverage", "dashboards", sum(1 for run in runs if run.get("dashboard_exists")), total),
        _check(
            "model_card",
            "Model card is available",
            "pass" if isinstance(model_card, dict) else "warn",
            "model_card.json loaded" if isinstance(model_card, dict) else "model_card.json missing or unreadable",
        ),
        _check(
            "ready_run",
            "At least one ready run",
            "pass" if any(run.get("status") == "ready" for run in runs) else "warn",
            f"{sum(1 for run in runs if run.get('status') == 'ready')} ready run(s).",
        ),
    ]
    non_pass_quality = [run.get("name") for run in runs if run.get("dataset_quality") not in {"pass", None, "missing"}]
    checks.append(
        _check(
            "non_pass_quality",
            "No non-pass dataset quality runs",
            "pass" if not non_pass_quality else "warn",
            "all checked runs pass" if not non_pass_quality else "review: " + ", ".join(str(name) for name in non_pass_quality),
        )
    )
    non_pass_generation = [
        run.get("name")
        for run in runs
        if run.get("generation_quality_status") not in {"pass", None, "missing"}
    ]
    checks.append(
        _check(
            "non_pass_generation_quality",
            "No non-pass generation quality runs",
            "pass" if not non_pass_generation else "warn",
            "all analyzed runs pass" if not non_pass_generation else "review: " + ", ".join(str(name) for name in non_pass_generation),
        )
    )
    return checks


def _coverage_check(title: str, check_id: str, count: int, total: int) -> dict[str, Any]:
    if total == 0:
        status = "fail"
    elif count == total:
        status = "pass"
    elif count > 0:
        status = "warn"
    else:
        status = "fail"
    return _check(check_id, title, status, f"{count}/{total} run(s).", {"count": count, "total": total, "ratio": _ratio(count, total)})


def _check(check_id: str, title: str, status: str, detail: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": check_id,
        "title": title,
        "status": status,
        "detail": detail,
        "evidence": evidence or {},
    }


def _summarize_checks(
    checks: list[dict[str, Any]],
    registry: dict[str, Any],
    model_card: dict[str, Any] | None,
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    pass_count = sum(1 for check in checks if check["status"] == "pass")
    warn_count = sum(1 for check in checks if check["status"] == "warn")
    fail_count = sum(1 for check in checks if check["status"] == "fail")
    score = round(100 * sum(CHECK_WEIGHTS[check["status"]] for check in checks) / max(1, len(checks)), 1)
    if fail_count:
        overall = "fail"
    elif warn_count:
        overall = "warn"
    else:
        overall = "pass"
    model_summary = _dict(model_card.get("summary")) if isinstance(model_card, dict) else {}
    best = _dict(registry.get("best_by_best_val_loss"))
    return {
        "overall_status": overall,
        "score_percent": score,
        "check_count": len(checks),
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "run_count": len(runs),
        "best_run_name": best.get("name"),
        "best_val_loss": best.get("best_val_loss"),
        "ready_runs": model_summary.get("ready_runs") if model_summary else sum(1 for run in runs if run.get("status") == "ready"),
        "review_runs": model_summary.get("review_runs") if model_summary else sum(1 for run in runs if run.get("status") == "review"),
    }


def _build_recommendations(checks: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    items = []
    for check in checks:
        if check["status"] == "pass":
            continue
        if check["id"] == "experiment_cards":
            items.append("Generate experiment cards for every registered run before presenting the project.")
        elif check["id"] == "dataset_quality":
            items.append("Run dataset quality checks for all registered runs.")
        elif check["id"] == "eval_suite":
            items.append("Run the fixed prompt eval suite for all registered checkpoints.")
        elif check["id"] == "generation_quality":
            items.append("Run generation quality analysis for all registered eval suite or sampling outputs.")
        elif check["id"] == "model_card":
            items.append("Build model_card.json so the audit can include project-level context.")
        elif check["id"] == "non_pass_quality":
            items.append("Review runs with non-pass dataset quality before using them as baselines.")
        elif check["id"] == "non_pass_generation_quality":
            items.append("Review runs with non-pass generation quality before release-style handoff.")
        elif check["id"] == "ready_run":
            items.append("Promote at least one run to ready status by completing checkpoint, data quality, and eval artifacts.")
        elif check["id"] == "dashboards":
            items.append("Build dashboards for missing runs to improve reviewability.")
        elif check["id"] == "checkpoints":
            items.append("Restore or create missing checkpoints for registered runs.")
    if not items:
        items.append("All audit checks passed; keep the audit with the model card as release evidence.")
    elif summary.get("overall_status") == "fail":
        items.insert(0, "Fix failed audit checks before treating this MiniGPT state as release-ready.")
    return items


def _derive_status(run: dict[str, Any]) -> str:
    if not run.get("checkpoint_exists") or run.get("best_val_loss") is None:
        return "incomplete"
    if run.get("dataset_quality") in {None, "missing"}:
        return "needs-data-quality"
    if run.get("dataset_quality") != "pass":
        return "review"
    if run.get("eval_suite_cases") in {None, 0}:
        return "needs-eval"
    if run.get("generation_quality_status") in {None, "missing"}:
        return "needs-generation-quality"
    if run.get("generation_quality_status") != "pass":
        return "review"
    return "ready"


def _check_section(checks: list[dict[str, Any]]) -> str:
    rows = []
    for check in checks:
        status = str(check.get("status") or "missing")
        rows.append(
            "<tr>"
            f'<td><span class="pill {status}">{_e(status)}</span></td>'
            f"<td><strong>{_e(check.get('title'))}</strong><br><span>{_e(check.get('id'))}</span></td>"
            f"<td>{_e(check.get('detail'))}</td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Checks</h2><table><thead><tr><th>Status</th><th>Check</th><th>Detail</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _run_section(runs: list[dict[str, Any]]) -> str:
    rows = []
    for run in runs:
        rows.append(
            "<tr>"
            f"<td>{_e(_rank_label(run.get('best_val_loss_rank')))}</td>"
            f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('path'))}</span></td>"
            f"<td>{_e(run.get('status'))}</td>"
            f"<td>{_e(_fmt(run.get('best_val_loss')))}<br><span>{_e(_fmt_delta(run.get('best_val_loss_delta')))}</span></td>"
            f"<td>{_e(run.get('dataset_quality'))}</td>"
            f"<td>{_e(run.get('eval_suite_cases'))}</td>"
            f"<td>{_e(_generation_quality_label(run))}</td>"
            f"<td>{_e('yes' if run.get('experiment_card_exists') else 'no')}</td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Runs</h2><table><thead><tr><th>Rank</th><th>Run</th><th>Status</th><th>Best Val</th><th>Quality</th><th>Eval</th><th>Gen Quality</th><th>Card</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _run_table(runs: list[dict[str, Any]]) -> list[str]:
    lines = ["| Rank | Run | Status | Best Val | Quality | Eval | Gen Quality | Card |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for run in runs:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(_rank_label(run.get("best_val_loss_rank"))),
                    _md(run.get("name")),
                    _md(run.get("status")),
                    _md(_fmt(run.get("best_val_loss"))),
                    _md(run.get("dataset_quality")),
                    _md(run.get("eval_suite_cases")),
                    _md(_generation_quality_label(run)),
                    _md("yes" if run.get("experiment_card_exists") else "no"),
                ]
            )
            + " |"
        )
    return lines


def _list_section(title: str, values: Any, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _stat_card(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt_any(value))}</div>' + "</div>"


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --green:#047857; --amber:#b45309; --red:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:860px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:54px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {_md(key)} | {_md(value)} |")
    return lines


def _ratio(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 4)


def _rank_sort(value: Any) -> int:
    if value is None or value == "":
        return 1_000_000
    return int(value)


def _rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def _generation_quality_label(run: dict[str, Any]) -> str:
    status = run.get("generation_quality_status") or "missing"
    cases = run.get("generation_quality_cases")
    if cases in {None, ""}:
        return str(status)
    return f"{status} ({cases} cases)"


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_delta(value: Any) -> str:
    if value is None or value == "":
        return "missing"
    return f"{float(value):+.5g}"


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(payload: dict[str, Any], key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _md(value: Any) -> str:
    return _fmt_any(value).replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
