from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_benchmark_scorecard(
    run_dir: str | Path,
    *,
    registry_path: str | Path | None = None,
    title: str = "MiniGPT benchmark scorecard",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    warnings: list[str] = []
    eval_suite = _read_json(root / "eval_suite" / "eval_suite.json", warnings)
    generation_quality = _read_generation_quality(root, warnings)
    pair_batch = _read_json(root / "pair_batch" / "pair_generation_batch.json", warnings)
    registry = _read_json(Path(registry_path), warnings) if registry_path is not None else None

    components = [
        _eval_coverage_component(eval_suite, root / "eval_suite" / "eval_suite.json"),
        _generation_quality_component(generation_quality),
        _pair_consistency_component(pair_batch, root / "pair_batch" / "pair_generation_batch.json"),
        _pair_delta_stability_component(pair_batch, root / "pair_batch" / "pair_generation_batch.json"),
        _evidence_completeness_component(root),
    ]
    summary = _score_summary(components, eval_suite, generation_quality, pair_batch)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "run_dir": str(root),
        "registry_path": str(registry_path) if registry_path is not None else None,
        "summary": summary,
        "components": components,
        "case_scores": _case_scores(eval_suite, generation_quality, pair_batch),
        "registry_context": _registry_context(registry, root),
        "recommendations": _recommendations(summary, components),
        "warnings": warnings,
    }


def write_benchmark_scorecard_json(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(scorecard, ensure_ascii=False, indent=2), encoding="utf-8")


def write_benchmark_scorecard_csv(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["key", "title", "status", "score", "weight", "weighted_score", "evidence_path", "detail"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for component in _list_of_dicts(scorecard.get("components")):
            writer.writerow({field: _csv_value(component.get(field)) for field in fieldnames})


def render_benchmark_scorecard_markdown(scorecard: dict[str, Any]) -> str:
    summary = _dict(scorecard.get("summary"))
    lines = [
        f"# {scorecard.get('title', 'MiniGPT benchmark scorecard')}",
        "",
        f"- Generated: `{scorecard.get('generated_at')}`",
        f"- Run dir: `{scorecard.get('run_dir')}`",
        f"- Registry: `{scorecard.get('registry_path') or 'missing'}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Overall status", summary.get("overall_status")),
                ("Overall score", summary.get("overall_score")),
                ("Eval cases", summary.get("eval_suite_cases")),
                ("Generation quality", summary.get("generation_quality_status")),
                ("Pair batch cases", summary.get("pair_batch_cases")),
                ("Pair generated differences", summary.get("pair_generated_differences")),
            ]
        ),
        "",
        "## Components",
        "",
        "| Component | Status | Score | Weight | Detail |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for component in _list_of_dicts(scorecard.get("components")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(component.get("title")),
                    _md(component.get("status")),
                    _md(component.get("score")),
                    _md(component.get("weight")),
                    _md(component.get("detail")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Case Scores", "", "| Case | Task | Eval chars | Gen status | Pair delta | Pair equal |", "| --- | --- | ---: | --- | ---: | --- |"])
    for case in _list_of_dicts(scorecard.get("case_scores")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(case.get("name")),
                    _md(case.get("task_type")),
                    _md(case.get("eval_char_count")),
                    _md(case.get("generation_quality_status")),
                    _md(case.get("pair_generated_char_delta")),
                    _md(case.get("pair_generated_equal")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(scorecard.get("recommendations")))
    warnings = _string_list(scorecard.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_benchmark_scorecard_markdown(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_markdown(scorecard), encoding="utf-8")


def render_benchmark_scorecard_html(scorecard: dict[str, Any]) -> str:
    summary = _dict(scorecard.get("summary"))
    stats = [
        ("Status", summary.get("overall_status")),
        ("Score", summary.get("overall_score")),
        ("Eval cases", summary.get("eval_suite_cases")),
        ("Gen quality", summary.get("generation_quality_status")),
        ("Pair cases", summary.get("pair_batch_cases")),
        ("Pair diff", summary.get("pair_generated_differences")),
        ("Max delta", summary.get("max_abs_generated_delta")),
        ("Registry rank", _dict(scorecard.get("registry_context")).get("best_val_loss_rank")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(scorecard.get('title', 'MiniGPT benchmark scorecard'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(scorecard.get('title', 'MiniGPT benchmark scorecard'))}</h1><p>{_e(scorecard.get('run_dir'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _component_section(_list_of_dicts(scorecard.get("components"))),
            _case_section(_list_of_dicts(scorecard.get("case_scores"))),
            _registry_section(_dict(scorecard.get("registry_context"))),
            _list_section("Recommendations", scorecard.get("recommendations")),
            _list_section("Warnings", scorecard.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT benchmark scorecard exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_benchmark_scorecard_html(scorecard: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_html(scorecard), encoding="utf-8")


def write_benchmark_scorecard_outputs(scorecard: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "benchmark_scorecard.json",
        "csv": root / "benchmark_scorecard.csv",
        "markdown": root / "benchmark_scorecard.md",
        "html": root / "benchmark_scorecard.html",
    }
    write_benchmark_scorecard_json(scorecard, paths["json"])
    write_benchmark_scorecard_csv(scorecard, paths["csv"])
    write_benchmark_scorecard_markdown(scorecard, paths["markdown"])
    write_benchmark_scorecard_html(scorecard, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _eval_coverage_component(eval_suite: Any, path: Path) -> dict[str, Any]:
    case_count = _number(_pick(eval_suite, "case_count")) or 0
    score = min(100.0, case_count * 20.0)
    status = _status(score)
    return _component(
        "eval_coverage",
        "Eval Suite Coverage",
        score,
        0.2,
        status,
        str(path),
        f"{int(case_count)} fixed prompt case(s).",
        {"case_count": int(case_count)},
    )


def _generation_quality_component(report: Any) -> dict[str, Any]:
    summary = _dict(_pick(report, "summary"))
    case_count = _number(_pick(summary, "case_count")) or 0
    pass_count = _number(_pick(summary, "pass_count")) or 0
    warn_count = _number(_pick(summary, "warn_count")) or 0
    fail_count = _number(_pick(summary, "fail_count")) or 0
    score = 0.0 if case_count == 0 else ((pass_count + warn_count * 0.5) / case_count) * 100.0
    status = _status(score)
    return _component(
        "generation_quality",
        "Generation Quality",
        score,
        0.3,
        status,
        _as_str(_pick(report, "source_path")) or "generation_quality.json",
        f"{int(pass_count)} pass / {int(warn_count)} warn / {int(fail_count)} fail.",
        {
            "case_count": int(case_count),
            "pass_count": int(pass_count),
            "warn_count": int(warn_count),
            "fail_count": int(fail_count),
            "overall_status": _pick(summary, "overall_status"),
        },
    )


def _pair_consistency_component(pair_batch: Any, path: Path) -> dict[str, Any]:
    case_count = _number(_pick(pair_batch, "case_count")) or 0
    equal_count = _number(_pick(pair_batch, "generated_equal_count")) or 0
    score = 0.0 if case_count == 0 else (equal_count / case_count) * 100.0
    status = _status(score)
    return _component(
        "pair_consistency",
        "Pair Consistency",
        score,
        0.2,
        status,
        str(path),
        f"{int(equal_count)} / {int(case_count)} pair generations matched exactly.",
        {"case_count": int(case_count), "generated_equal_count": int(equal_count)},
    )


def _pair_delta_stability_component(pair_batch: Any, path: Path) -> dict[str, Any]:
    avg_delta = _number(_pick(pair_batch, "avg_abs_generated_char_delta"))
    max_delta = _max_abs_generated_delta(pair_batch)
    score = 0.0 if avg_delta is None else max(0.0, 100.0 - avg_delta * 10.0)
    status = _status(score)
    return _component(
        "pair_delta_stability",
        "Pair Delta Stability",
        score,
        0.2,
        status,
        str(path),
        f"avg abs generated delta={_fmt(avg_delta)}, max abs generated delta={_fmt(max_delta)}.",
        {"avg_abs_generated_char_delta": avg_delta, "max_abs_generated_char_delta": max_delta},
    )


def _evidence_completeness_component(root: Path) -> dict[str, Any]:
    paths = [
        root / "eval_suite" / "eval_suite.json",
        root / "generation-quality" / "generation_quality.json",
        root / "eval_suite" / "generation-quality" / "generation_quality.json",
        root / "pair_batch" / "pair_generation_batch.json",
        root / "pair_batch" / "pair_generation_batch.html",
    ]
    eval_exists = paths[0].exists()
    quality_exists = paths[1].exists() or paths[2].exists()
    pair_exists = paths[3].exists() and paths[4].exists()
    present = sum(1 for item in [eval_exists, quality_exists, pair_exists] if item)
    score = present / 3 * 100.0
    return _component(
        "evidence_completeness",
        "Benchmark Evidence Completeness",
        score,
        0.1,
        _status(score),
        str(root),
        f"{present} / 3 evidence groups present.",
        {"eval_suite": eval_exists, "generation_quality": quality_exists, "pair_batch": pair_exists},
    )


def _component(
    key: str,
    title: str,
    score: float,
    weight: float,
    status: str,
    evidence_path: str,
    detail: str,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    rounded = round(score, 2)
    return {
        "key": key,
        "title": title,
        "status": status,
        "score": rounded,
        "weight": weight,
        "weighted_score": round(rounded * weight, 2),
        "evidence_path": evidence_path,
        "detail": detail,
        "metrics": metrics,
    }


def _score_summary(components: list[dict[str, Any]], eval_suite: Any, generation_quality: Any, pair_batch: Any) -> dict[str, Any]:
    total_weight = sum(float(item.get("weight") or 0) for item in components)
    overall = 0.0 if total_weight == 0 else sum(float(item.get("weighted_score") or 0) for item in components) / total_weight
    return {
        "overall_score": round(overall, 2),
        "overall_status": _status(overall),
        "component_count": len(components),
        "eval_suite_cases": _pick(eval_suite, "case_count"),
        "generation_quality_status": _pick(_dict(_pick(generation_quality, "summary")), "overall_status"),
        "generation_quality_cases": _pick(_dict(_pick(generation_quality, "summary")), "case_count"),
        "pair_batch_cases": _pick(pair_batch, "case_count"),
        "pair_generated_differences": _pick(pair_batch, "generated_difference_count"),
        "max_abs_generated_delta": _max_abs_generated_delta(pair_batch),
    }


def _case_scores(eval_suite: Any, generation_quality: Any, pair_batch: Any) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for result in _list_of_dicts(_pick(eval_suite, "results")):
        name = str(result.get("name") or f"case-{len(rows) + 1}")
        rows.setdefault(name, {"name": name})
        rows[name].update(
            {
                "task_type": result.get("task_type"),
                "difficulty": result.get("difficulty"),
                "eval_char_count": result.get("char_count"),
                "eval_unique_char_count": result.get("unique_char_count"),
            }
        )
    for case in _list_of_dicts(_pick(generation_quality, "cases")):
        name = str(case.get("name") or f"case-{len(rows) + 1}")
        rows.setdefault(name, {"name": name})
        rows[name].update(
            {
                "generation_quality_status": case.get("status"),
                "generation_unique_ratio": case.get("unique_ratio"),
                "generation_flag_count": case.get("flag_count"),
            }
        )
    for result in _list_of_dicts(_pick(pair_batch, "results")):
        name = str(result.get("name") or f"case-{len(rows) + 1}")
        comparison = _dict(result.get("comparison"))
        rows.setdefault(name, {"name": name})
        rows[name].update(
            {
                "task_type": rows[name].get("task_type") or result.get("task_type"),
                "difficulty": rows[name].get("difficulty") or result.get("difficulty"),
                "pair_generated_equal": comparison.get("generated_equal"),
                "pair_continuation_equal": comparison.get("continuation_equal"),
                "pair_generated_char_delta": comparison.get("generated_char_delta"),
                "pair_continuation_char_delta": comparison.get("continuation_char_delta"),
            }
        )
    return [rows[key] for key in sorted(rows)]


def _registry_context(registry: Any, root: Path) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {"available": False}
    run = next((item for item in _list_of_dicts(registry.get("runs")) if Path(str(item.get("path", ""))).resolve() == root.resolve()), None)
    pair_delta = _dict(registry.get("pair_delta_summary"))
    return {
        "available": True,
        "run_count": registry.get("run_count"),
        "best_val_loss_rank": _pick(run, "best_val_loss_rank") if run else None,
        "pair_report_counts": registry.get("pair_report_counts") if isinstance(registry.get("pair_report_counts"), dict) else {},
        "pair_delta_cases": pair_delta.get("case_count"),
        "pair_delta_max_generated": pair_delta.get("max_abs_generated_char_delta"),
    }


def _recommendations(summary: dict[str, Any], components: list[dict[str, Any]]) -> list[str]:
    recs = []
    if summary.get("overall_status") == "pass":
        recs.append("Use this scorecard as the single benchmark entry point for the current run.")
    else:
        recs.append("Treat low scoring components as the next benchmark hardening targets.")
    weak = [item for item in components if item.get("status") != "pass"]
    if weak:
        recs.append("Improve weak components: " + ", ".join(str(item.get("title")) for item in weak) + ".")
    recs.append("Next step: add task-type and difficulty level scoring so benchmark changes are easier to explain.")
    return recs


def _read_generation_quality(root: Path, warnings: list[str]) -> dict[str, Any] | None:
    candidates = [
        root / "generation-quality" / "generation_quality.json",
        root / "eval_suite" / "generation-quality" / "generation_quality.json",
    ]
    for path in candidates:
        payload = _read_json(path, warnings, missing_ok=True)
        if isinstance(payload, dict):
            payload = dict(payload)
            payload.setdefault("source_path", str(path))
            return payload
    warnings.append("generation quality report not found")
    return None


def _read_json(path: Path, warnings: list[str], *, missing_ok: bool = False) -> dict[str, Any] | None:
    if not path.exists():
        if not missing_ok:
            warnings.append(f"missing: {path}")
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        warnings.append(f"{path} must contain a JSON object")
        return None
    return payload


def _max_abs_generated_delta(pair_batch: Any) -> float | int | None:
    values = []
    for result in _list_of_dicts(_pick(pair_batch, "results")):
        value = _number(_pick(_dict(result.get("comparison")), "generated_char_delta"))
        if value is not None:
            values.append(abs(value))
    if not values:
        return None
    value = max(values)
    return int(value) if float(value).is_integer() else value


def _status(score: float) -> str:
    if score >= 80:
        return "pass"
    if score >= 60:
        return "warn"
    return "fail"


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _component_section(components: list[dict[str, Any]]) -> str:
    rows = []
    for item in components:
        rows.append(
            "<tr>"
            f"<td><strong>{_e(item.get('title'))}</strong><br><span>{_e(item.get('key'))}</span></td>"
            f"<td><span class=\"pill {_e(item.get('status'))}\">{_e(item.get('status'))}</span></td>"
            f"<td>{_e(item.get('score'))}</td>"
            f"<td>{_e(item.get('weight'))}</td>"
            f"<td>{_e(item.get('weighted_score'))}</td>"
            f"<td>{_e(item.get('detail'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Benchmark Components</h2>'
        '<table><thead><tr><th>Component</th><th>Status</th><th>Score</th><th>Weight</th><th>Weighted</th><th>Detail</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _case_section(cases: list[dict[str, Any]]) -> str:
    if not cases:
        return '<section class="panel"><h2>Case Scores</h2><p class="muted">No case-level benchmark rows found.</p></section>'
    rows = []
    for item in cases:
        rows.append(
            "<tr>"
            f"<td><strong>{_e(item.get('name'))}</strong><br><span>{_e(item.get('task_type'))} / {_e(item.get('difficulty'))}</span></td>"
            f"<td>{_e(item.get('eval_char_count'))}<br><span>unique={_e(item.get('eval_unique_char_count'))}</span></td>"
            f"<td>{_e(item.get('generation_quality_status'))}<br><span>flags={_e(item.get('generation_flag_count'))}</span></td>"
            f"<td>{_e(item.get('pair_generated_equal'))}<br><span>delta={_e(item.get('pair_generated_char_delta'))}</span></td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Case Scores</h2>'
        '<table><thead><tr><th>Case</th><th>Eval</th><th>Generation Quality</th><th>Pair</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _registry_section(registry: dict[str, Any]) -> str:
    rows = [
        ("Available", registry.get("available")),
        ("Runs", registry.get("run_count")),
        ("Best-val rank", registry.get("best_val_loss_rank")),
        ("Pair reports", _fmt_mapping(registry.get("pair_report_counts"))),
        ("Pair delta cases", registry.get("pair_delta_cases")),
        ("Max pair delta", registry.get("pair_delta_max_generated")),
    ]
    return '<section class="panel"><h2>Registry Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def _list_section(title: str, values: Any, *, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["None"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:920px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:58px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _as_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value))


def _csv_value(value: Any) -> Any:
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return value


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
