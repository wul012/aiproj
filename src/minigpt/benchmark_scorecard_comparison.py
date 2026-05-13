from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any


def load_benchmark_scorecard(path: str | Path) -> dict[str, Any]:
    scorecard_path = _resolve_scorecard_path(Path(path))
    payload = json.loads(scorecard_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("benchmark scorecard must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(scorecard_path)
    return payload


def build_benchmark_scorecard_comparison(
    scorecard_paths: list[str | Path],
    *,
    names: list[str] | None = None,
    baseline: str | int | None = None,
    title: str = "MiniGPT benchmark scorecard comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not scorecard_paths:
        raise ValueError("at least one benchmark scorecard is required")
    if names is not None and len(names) != len(scorecard_paths):
        raise ValueError("names length must match scorecard_paths length")

    scorecards = [load_benchmark_scorecard(path) for path in scorecard_paths]
    resolved_names = _resolve_names(scorecards, names)
    runs = [_scorecard_run_summary(scorecard, resolved_names[index], index) for index, scorecard in enumerate(scorecards)]
    baseline_run = _select_baseline(runs, baseline)
    deltas = [_run_delta(run, baseline_run) for run in runs]
    case_deltas = _case_deltas(scorecards, resolved_names, baseline_run)
    task_deltas = _group_deltas(scorecards, resolved_names, baseline_run, group_name="task_type")
    difficulty_deltas = _group_deltas(scorecards, resolved_names, baseline_run, group_name="difficulty")
    summary = _comparison_summary(runs, baseline_run, deltas, case_deltas, task_deltas, difficulty_deltas)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or _utc_now(),
        "scorecard_count": len(scorecards),
        "baseline": baseline_run,
        "runs": runs,
        "baseline_deltas": deltas,
        "case_deltas": case_deltas,
        "task_type_deltas": task_deltas,
        "difficulty_deltas": difficulty_deltas,
        "summary": summary,
        "best_by_overall_score": _best_run(runs, "overall_score"),
        "best_by_rubric_avg_score": _best_run(runs, "rubric_avg_score"),
        "recommendations": _recommendations(summary, deltas, case_deltas, task_deltas, difficulty_deltas),
    }


def write_benchmark_scorecard_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_benchmark_scorecard_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "source_path",
        "run_dir",
        "overall_status",
        "overall_score",
        "rubric_status",
        "rubric_avg_score",
        "rubric_pass_count",
        "rubric_warn_count",
        "rubric_fail_count",
        "weakest_rubric_case",
        "weakest_rubric_score",
        "case_count",
        "component_count",
        "task_type_count",
        "difficulty_count",
        "baseline_name",
        "is_baseline",
        "overall_score_delta",
        "rubric_avg_score_delta",
        "rubric_pass_count_delta",
        "rubric_warn_count_delta",
        "rubric_fail_count_delta",
        "weakest_case_changed",
        "overall_relation",
        "rubric_relation",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for run in _list_of_dicts(report.get("runs")):
            row = dict(run)
            row.update(deltas.get(run.get("name"), {}))
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def write_benchmark_scorecard_case_delta_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case",
        "run_name",
        "baseline_name",
        "task_type",
        "difficulty",
        "baseline_rubric_score",
        "rubric_score",
        "rubric_score_delta",
        "baseline_rubric_status",
        "rubric_status",
        "relation",
        "status_changed",
        "added_missing_terms",
        "removed_missing_terms",
        "added_failed_checks",
        "removed_failed_checks",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("case_deltas")):
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_benchmark_scorecard_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    lines = [
        f"# {report.get('title', 'MiniGPT benchmark scorecard comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Scorecards: `{report.get('scorecard_count')}`",
        f"- Baseline: `{baseline.get('name')}`",
        f"- Best overall: `{_pick(_dict(report.get('best_by_overall_score')), 'name') or 'missing'}`",
        f"- Best rubric: `{_pick(_dict(report.get('best_by_rubric_avg_score')), 'name') or 'missing'}`",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Improved overall | {_md(summary.get('improved_overall_count'))} |",
        f"| Regressed overall | {_md(summary.get('regressed_overall_count'))} |",
        f"| Improved rubric | {_md(summary.get('improved_rubric_count'))} |",
        f"| Regressed rubric | {_md(summary.get('regressed_rubric_count'))} |",
        f"| Case regressions | {_md(summary.get('case_regression_count'))} |",
        f"| Case improvements | {_md(summary.get('case_improvement_count'))} |",
        f"| Weakest regression case | {_md(summary.get('weakest_case_regression'))} |",
        "",
        "## Runs",
        "",
        "| Run | Overall | Rubric | Case Count | Weakest Case | Relation | Explanation |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("name"), {})
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(run.get("name")),
                    _md(f"{_fmt(run.get('overall_score'))} ({_fmt_signed(delta.get('overall_score_delta'))})"),
                    _md(f"{_fmt(run.get('rubric_avg_score'))} ({_fmt_signed(delta.get('rubric_avg_score_delta'))})"),
                    _md(run.get("case_count")),
                    _md(f"{run.get('weakest_rubric_case')}:{_fmt(run.get('weakest_rubric_score'))}"),
                    _md(delta.get("rubric_relation")),
                    _md(delta.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Case Deltas",
            "",
            "| Case | Run | Task | Rubric Delta | Relation | Missing Terms Delta | Failed Checks Delta | Explanation |",
            "| --- | --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in _list_of_dicts(report.get("case_deltas")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("case")),
                    _md(row.get("run_name")),
                    _md(f"{row.get('task_type')}/{row.get('difficulty')}"),
                    _md(_fmt_signed(row.get("rubric_score_delta"))),
                    _md(row.get("relation")),
                    _md(_terms_delta(row, "missing_terms")),
                    _md(_terms_delta(row, "failed_checks")),
                    _md(row.get("explanation")),
                ]
            )
            + " |"
        )
    lines.extend(_markdown_group_section("Task Type Deltas", report.get("task_type_deltas")))
    lines.extend(_markdown_group_section("Difficulty Deltas", report.get("difficulty_deltas")))
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_benchmark_scorecard_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_comparison_markdown(report), encoding="utf-8")


def render_benchmark_scorecard_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    stats = [
        ("Baseline", baseline.get("name")),
        ("Scorecards", report.get("scorecard_count")),
        ("Best overall", _pick(_dict(report.get("best_by_overall_score")), "name")),
        ("Best rubric", _pick(_dict(report.get("best_by_rubric_avg_score")), "name")),
        ("Rubric regressions", summary.get("regressed_rubric_count")),
        ("Case regressions", summary.get("case_regression_count")),
        ("Weakest case", summary.get("weakest_case_regression")),
        ("Generated", report.get("generated_at")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT benchmark scorecard comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT benchmark scorecard comparison'))}</h1><p>Baseline: {_e(baseline.get('name'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _run_section(report),
            _case_delta_section(report),
            _group_delta_section("Task Type Deltas", report.get("task_type_deltas")),
            _group_delta_section("Difficulty Deltas", report.get("difficulty_deltas")),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT benchmark scorecard comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_benchmark_scorecard_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_scorecard_comparison_html(report), encoding="utf-8")


def write_benchmark_scorecard_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "benchmark_scorecard_comparison.json",
        "csv": root / "benchmark_scorecard_comparison.csv",
        "case_delta_csv": root / "benchmark_scorecard_case_deltas.csv",
        "markdown": root / "benchmark_scorecard_comparison.md",
        "html": root / "benchmark_scorecard_comparison.html",
    }
    write_benchmark_scorecard_comparison_json(report, paths["json"])
    write_benchmark_scorecard_comparison_csv(report, paths["csv"])
    write_benchmark_scorecard_case_delta_csv(report, paths["case_delta_csv"])
    write_benchmark_scorecard_comparison_markdown(report, paths["markdown"])
    write_benchmark_scorecard_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_scorecard_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates = [
            path / "benchmark-scorecard" / "benchmark_scorecard.json",
            path / "benchmark_scorecard.json",
        ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"benchmark scorecard not found: {path}")


def _resolve_names(scorecards: list[dict[str, Any]], names: list[str] | None) -> list[str]:
    if names is not None:
        return [str(name) for name in names]
    resolved = []
    for index, scorecard in enumerate(scorecards, start=1):
        run_dir = _as_str(scorecard.get("run_dir"))
        source_path = _as_str(scorecard.get("_source_path"))
        if run_dir:
            resolved.append(Path(run_dir).name or f"scorecard-{index}")
        elif source_path:
            path = Path(source_path)
            resolved.append(path.parent.parent.name if path.parent.name == "benchmark-scorecard" else path.stem)
        else:
            resolved.append(f"scorecard-{index}")
    return resolved


def _scorecard_run_summary(scorecard: dict[str, Any], name: str, index: int) -> dict[str, Any]:
    summary = _dict(scorecard.get("summary"))
    rubric = _dict(scorecard.get("rubric_scores"))
    rubric_summary = _dict(rubric.get("summary"))
    drilldowns = _dict(scorecard.get("drilldowns"))
    return {
        "index": index,
        "name": name,
        "source_path": scorecard.get("_source_path"),
        "run_dir": scorecard.get("run_dir"),
        "generated_at": scorecard.get("generated_at"),
        "overall_status": summary.get("overall_status"),
        "overall_score": _number(summary.get("overall_score")),
        "component_count": _as_int(summary.get("component_count")),
        "case_count": len(_list_of_dicts(scorecard.get("case_scores"))) or _as_int(rubric_summary.get("case_count")),
        "task_type_count": len(_list_of_dicts(drilldowns.get("task_type"))),
        "difficulty_count": len(_list_of_dicts(drilldowns.get("difficulty"))),
        "rubric_status": summary.get("rubric_status") or rubric_summary.get("overall_status"),
        "rubric_avg_score": _number(_first_present(summary, rubric_summary, "rubric_avg_score", "avg_score")),
        "rubric_pass_count": _as_int(_first_present(summary, rubric_summary, "rubric_pass_count", "pass_count")),
        "rubric_warn_count": _as_int(_first_present(summary, rubric_summary, "rubric_warn_count", "warn_count")),
        "rubric_fail_count": _as_int(_first_present(summary, rubric_summary, "rubric_fail_count", "fail_count")),
        "weakest_rubric_case": _first_present(summary, rubric_summary, "weakest_rubric_case", "weakest_case"),
        "weakest_rubric_score": _number(_first_present(summary, rubric_summary, "weakest_rubric_score", "weakest_score")),
        "weakest_task_type": summary.get("weakest_task_type"),
        "weakest_task_type_score": _number(summary.get("weakest_task_type_score")),
        "weakest_difficulty": summary.get("weakest_difficulty"),
        "weakest_difficulty_score": _number(summary.get("weakest_difficulty_score")),
    }


def _select_baseline(runs: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    if baseline is None:
        return runs[0]
    if isinstance(baseline, int):
        if baseline < 0 or baseline >= len(runs):
            raise ValueError(f"baseline index out of range: {baseline}")
        return runs[baseline]
    wanted = baseline.strip()
    if not wanted:
        raise ValueError("baseline cannot be empty")
    if wanted.isdigit():
        index = int(wanted) - 1
        if 0 <= index < len(runs):
            return runs[index]
    for run in runs:
        if wanted in {str(run.get("name")), str(run.get("source_path")), str(run.get("run_dir")), Path(str(run.get("run_dir") or "")).name}:
            return run
    raise ValueError(f"baseline did not match a scorecard name, path, run_dir, or 1-based index: {baseline}")


def _run_delta(run: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    overall_delta = _delta(run.get("overall_score"), baseline.get("overall_score"))
    rubric_delta = _delta(run.get("rubric_avg_score"), baseline.get("rubric_avg_score"))
    row = {
        "name": run.get("name"),
        "source_path": run.get("source_path"),
        "baseline_name": baseline.get("name"),
        "is_baseline": run.get("source_path") == baseline.get("source_path") and run.get("name") == baseline.get("name"),
        "overall_score_delta": overall_delta,
        "rubric_avg_score_delta": rubric_delta,
        "rubric_pass_count_delta": _int_delta(run.get("rubric_pass_count"), baseline.get("rubric_pass_count")),
        "rubric_warn_count_delta": _int_delta(run.get("rubric_warn_count"), baseline.get("rubric_warn_count")),
        "rubric_fail_count_delta": _int_delta(run.get("rubric_fail_count"), baseline.get("rubric_fail_count")),
        "weakest_case_changed": _changed(run.get("weakest_rubric_case"), baseline.get("weakest_rubric_case")),
        "overall_relation": _score_relation(overall_delta, is_baseline=run.get("name") == baseline.get("name")),
        "rubric_relation": _score_relation(rubric_delta, is_baseline=run.get("name") == baseline.get("name")),
    }
    row["explanation"] = _run_explanation(row, run, baseline)
    return row


def _case_deltas(scorecards: list[dict[str, Any]], names: list[str], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_index = int(baseline.get("index") or 0)
    baseline_cases = _case_map(scorecards[baseline_index])
    rows: list[dict[str, Any]] = []
    for index, scorecard in enumerate(scorecards):
        name = names[index]
        for case_name in sorted(set(baseline_cases) | set(_case_map(scorecard))):
            baseline_case = baseline_cases.get(case_name, {"name": case_name})
            case = _case_map(scorecard).get(case_name, {"name": case_name})
            row = _case_delta(case_name, name, str(baseline.get("name")), case, baseline_case, is_baseline=index == baseline_index)
            rows.append(row)
    return rows


def _case_delta(
    case_name: str,
    run_name: str,
    baseline_name: str,
    case: dict[str, Any],
    baseline: dict[str, Any],
    *,
    is_baseline: bool,
) -> dict[str, Any]:
    rubric_delta = _delta(
        _first_present(case, case, "rubric_score", "score"),
        _first_present(baseline, baseline, "rubric_score", "score"),
    )
    added_missing = _list_delta(case.get("rubric_missing_terms") or case.get("missing_terms"), baseline.get("rubric_missing_terms") or baseline.get("missing_terms"))
    removed_missing = _list_delta(baseline.get("rubric_missing_terms") or baseline.get("missing_terms"), case.get("rubric_missing_terms") or case.get("missing_terms"))
    added_failed = _list_delta(case.get("rubric_failed_checks") or case.get("failed_checks"), baseline.get("rubric_failed_checks") or baseline.get("failed_checks"))
    removed_failed = _list_delta(baseline.get("rubric_failed_checks") or baseline.get("failed_checks"), case.get("rubric_failed_checks") or case.get("failed_checks"))
    row = {
        "case": case_name,
        "run_name": run_name,
        "baseline_name": baseline_name,
        "is_baseline": is_baseline,
        "task_type": case.get("task_type") or baseline.get("task_type"),
        "difficulty": case.get("difficulty") or baseline.get("difficulty"),
        "baseline_rubric_score": _number(_first_present(baseline, baseline, "rubric_score", "score")),
        "rubric_score": _number(_first_present(case, case, "rubric_score", "score")),
        "rubric_score_delta": rubric_delta,
        "baseline_rubric_status": _first_present(baseline, baseline, "rubric_status", "status"),
        "rubric_status": _first_present(case, case, "rubric_status", "status"),
        "relation": _score_relation(rubric_delta, is_baseline=is_baseline),
        "status_changed": _changed(case.get("rubric_status") or case.get("status"), baseline.get("rubric_status") or baseline.get("status")),
        "added_missing_terms": added_missing,
        "removed_missing_terms": removed_missing,
        "added_failed_checks": added_failed,
        "removed_failed_checks": removed_failed,
    }
    row["explanation"] = _case_explanation(row)
    return row


def _case_map(scorecard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for case in _list_of_dicts(scorecard.get("case_scores")):
        name = str(case.get("name") or f"case-{len(rows) + 1}")
        rows[name] = dict(case)
    for rubric in _list_of_dicts(_dict(scorecard.get("rubric_scores")).get("cases")):
        name = str(rubric.get("name") or f"case-{len(rows) + 1}")
        rows.setdefault(name, {"name": name})
        rows[name].update(
            {
                "task_type": rows[name].get("task_type") or rubric.get("task_type"),
                "difficulty": rows[name].get("difficulty") or rubric.get("difficulty"),
                "rubric_status": rubric.get("status"),
                "rubric_score": rubric.get("score"),
                "rubric_missing_terms": rubric.get("missing_terms"),
                "rubric_failed_checks": rubric.get("failed_checks"),
            }
        )
    return rows


def _group_deltas(scorecards: list[dict[str, Any]], names: list[str], baseline: dict[str, Any], *, group_name: str) -> list[dict[str, Any]]:
    baseline_index = int(baseline.get("index") or 0)
    baseline_groups = _group_map(scorecards[baseline_index], group_name)
    rows = []
    for index, scorecard in enumerate(scorecards):
        groups = _group_map(scorecard, group_name)
        for key in sorted(set(baseline_groups) | set(groups)):
            group = groups.get(key, {"key": key})
            base = baseline_groups.get(key, {"key": key})
            score_delta = _delta(group.get("score"), base.get("score"))
            rubric_delta = _delta(group.get("rubric_score"), base.get("rubric_score"))
            row = {
                "group_by": group_name,
                "key": key,
                "run_name": names[index],
                "baseline_name": baseline.get("name"),
                "is_baseline": index == baseline_index,
                "case_count": group.get("case_count"),
                "baseline_case_count": base.get("case_count"),
                "score": _number(group.get("score")),
                "baseline_score": _number(base.get("score")),
                "score_delta": score_delta,
                "rubric_score": _number(group.get("rubric_score")),
                "baseline_rubric_score": _number(base.get("rubric_score")),
                "rubric_score_delta": rubric_delta,
                "relation": _score_relation(score_delta, is_baseline=index == baseline_index),
                "rubric_relation": _score_relation(rubric_delta, is_baseline=index == baseline_index),
                "cases": group.get("cases") if isinstance(group.get("cases"), list) else [],
            }
            row["explanation"] = _group_explanation(row)
            rows.append(row)
    return rows


def _group_map(scorecard: dict[str, Any], group_name: str) -> dict[str, dict[str, Any]]:
    drilldowns = _dict(scorecard.get("drilldowns"))
    rows = _list_of_dicts(drilldowns.get(group_name))
    return {str(row.get("key") or "unknown"): row for row in rows}


def _comparison_summary(
    runs: list[dict[str, Any]],
    baseline: dict[str, Any],
    deltas: list[dict[str, Any]],
    case_deltas: list[dict[str, Any]],
    task_deltas: list[dict[str, Any]],
    difficulty_deltas: list[dict[str, Any]],
) -> dict[str, Any]:
    comparable_cases = [row for row in case_deltas if not row.get("is_baseline") and row.get("rubric_score_delta") is not None]
    regressions = [row for row in comparable_cases if float(row.get("rubric_score_delta") or 0) < 0]
    improvements = [row for row in comparable_cases if float(row.get("rubric_score_delta") or 0) > 0]
    weakest = min(regressions, key=lambda row: (float(row.get("rubric_score_delta") or 0), str(row.get("case"))), default={})
    return {
        "baseline_name": baseline.get("name"),
        "baseline_source_path": baseline.get("source_path"),
        "scorecard_count": len(runs),
        "improved_overall_count": sum(1 for row in deltas if row.get("overall_relation") == "improved"),
        "regressed_overall_count": sum(1 for row in deltas if row.get("overall_relation") == "regressed"),
        "improved_rubric_count": sum(1 for row in deltas if row.get("rubric_relation") == "improved"),
        "regressed_rubric_count": sum(1 for row in deltas if row.get("rubric_relation") == "regressed"),
        "case_delta_count": len(case_deltas),
        "case_regression_count": len(regressions),
        "case_improvement_count": len(improvements),
        "weakest_case_regression": weakest.get("case"),
        "weakest_case_regression_run": weakest.get("run_name"),
        "weakest_case_regression_delta": weakest.get("rubric_score_delta"),
        "task_type_delta_count": len(task_deltas),
        "difficulty_delta_count": len(difficulty_deltas),
    }


def _recommendations(
    summary: dict[str, Any],
    deltas: list[dict[str, Any]],
    case_deltas: list[dict[str, Any]],
    task_deltas: list[dict[str, Any]],
    difficulty_deltas: list[dict[str, Any]],
) -> list[str]:
    recs: list[str] = []
    if int(summary.get("regressed_rubric_count") or 0):
        recs.append("Review runs with rubric regressions before promoting them in the registry.")
    elif int(summary.get("improved_rubric_count") or 0):
        recs.append("Rubric correctness improved for at least one run; inspect case deltas before treating the gain as robust.")
    else:
        recs.append("No rubric average change was detected; use case-level rows to check whether individual prompts moved in opposite directions.")
    weakest_case = summary.get("weakest_case_regression")
    if weakest_case:
        recs.append(
            f"Start regression review from case `{weakest_case}` in run `{summary.get('weakest_case_regression_run')}` with delta {_fmt_signed(summary.get('weakest_case_regression_delta'))}."
        )
    weak_tasks = [row for row in task_deltas if not row.get("is_baseline") and row.get("relation") == "regressed"]
    if weak_tasks:
        recs.append("Task-type regressions are present: " + ", ".join(sorted({str(row.get("key")) for row in weak_tasks})) + ".")
    weak_difficulties = [row for row in difficulty_deltas if not row.get("is_baseline") and row.get("relation") == "regressed"]
    if weak_difficulties:
        recs.append("Difficulty regressions are present: " + ", ".join(sorted({str(row.get("key")) for row in weak_difficulties})) + ".")
    if any(row.get("added_missing_terms") or row.get("added_failed_checks") for row in case_deltas if not row.get("is_baseline")):
        recs.append("Inspect added missing terms and failed checks to separate wording drift from true task failure.")
    return recs


def _best_run(runs: list[dict[str, Any]], field: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if _number(run.get(field)) is not None]
    if not candidates:
        return None
    best = max(candidates, key=lambda run: (_number(run.get(field)) or 0.0, str(run.get("name"))))
    return {"name": best.get("name"), "source_path": best.get("source_path"), field: best.get(field)}


def _run_explanation(delta: dict[str, Any], run: dict[str, Any], baseline: dict[str, Any]) -> str:
    if delta.get("is_baseline"):
        return "This run is the baseline for scorecard deltas."
    parts = [
        f"Overall score changed {_fmt_signed(delta.get('overall_score_delta'))} from {baseline.get('name')}.",
        f"Rubric average changed {_fmt_signed(delta.get('rubric_avg_score_delta'))}.",
    ]
    if delta.get("rubric_fail_count_delta"):
        parts.append(f"Rubric fail count changed {_fmt_signed(delta.get('rubric_fail_count_delta'))}.")
    if delta.get("weakest_case_changed"):
        parts.append(f"Weakest case moved from {baseline.get('weakest_rubric_case')} to {run.get('weakest_rubric_case')}.")
    return " ".join(parts)


def _case_explanation(row: dict[str, Any]) -> str:
    if row.get("is_baseline"):
        return "Baseline case row."
    parts = [f"Rubric score changed {_fmt_signed(row.get('rubric_score_delta'))}."]
    if row.get("status_changed"):
        parts.append(f"Status changed from {row.get('baseline_rubric_status')} to {row.get('rubric_status')}.")
    if row.get("added_missing_terms"):
        parts.append("New missing term(s): " + ", ".join(_string_list(row.get("added_missing_terms"))) + ".")
    if row.get("removed_missing_terms"):
        parts.append("Recovered missing term(s): " + ", ".join(_string_list(row.get("removed_missing_terms"))) + ".")
    if row.get("added_failed_checks"):
        parts.append("New failed check(s): " + ", ".join(_string_list(row.get("added_failed_checks"))) + ".")
    if row.get("removed_failed_checks"):
        parts.append("Recovered failed check(s): " + ", ".join(_string_list(row.get("removed_failed_checks"))) + ".")
    return " ".join(parts)


def _group_explanation(row: dict[str, Any]) -> str:
    if row.get("is_baseline"):
        return "Baseline group row."
    parts = [
        f"{row.get('group_by')} `{row.get('key')}` score changed {_fmt_signed(row.get('score_delta'))}.",
        f"Rubric changed {_fmt_signed(row.get('rubric_score_delta'))}.",
    ]
    if row.get("case_count") != row.get("baseline_case_count"):
        parts.append(f"Case count changed from {row.get('baseline_case_count')} to {row.get('case_count')}.")
    return " ".join(parts)


def _score_relation(delta: Any, *, is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    if delta is None:
        return "missing"
    number = float(delta)
    if number > 0:
        return "improved"
    if number < 0:
        return "regressed"
    return "tied"


def _run_section(report: dict[str, Any]) -> str:
    deltas = {row.get("name"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    rows = []
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("name"), {})
        relation = str(delta.get("rubric_relation") or "missing")
        rows.append(
            "<tr>"
            f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('run_dir') or run.get('source_path'))}</span></td>"
            f"<td>{_e(_fmt(run.get('overall_score')))}<br><span>{_e(_fmt_signed(delta.get('overall_score_delta')))}</span></td>"
            f"<td><span class=\"pill {_relation_class(relation)}\">{_e(relation)}</span><br><span>{_e(_fmt(run.get('rubric_avg_score')))} ({_e(_fmt_signed(delta.get('rubric_avg_score_delta')))})</span></td>"
            f"<td>{_e(run.get('rubric_pass_count'))} pass / {_e(run.get('rubric_warn_count'))} warn / {_e(run.get('rubric_fail_count'))} fail</td>"
            f"<td>{_e(run.get('weakest_rubric_case'))}<br><span>{_e(_fmt(run.get('weakest_rubric_score')))}</span></td>"
            f"<td>{_e(delta.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Runs</h2><table><thead><tr>'
        "<th>Run</th><th>Overall</th><th>Rubric</th><th>Rubric Counts</th><th>Weakest Case</th><th>Explanation</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _case_delta_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("case_deltas")):
        relation = str(row.get("relation") or "missing")
        rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('case'))}</strong><br><span>{_e(row.get('task_type'))} / {_e(row.get('difficulty'))}</span></td>"
            f"<td>{_e(row.get('run_name'))}</td>"
            f"<td><span class=\"pill {_relation_class(relation)}\">{_e(relation)}</span><br><span>{_e(_fmt_signed(row.get('rubric_score_delta')))}</span></td>"
            f"<td>{_e(_terms_delta(row, 'missing_terms'))}</td>"
            f"<td>{_e(_terms_delta(row, 'failed_checks'))}</td>"
            f"<td>{_e(row.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Case Deltas</h2><table><thead><tr>'
        "<th>Case</th><th>Run</th><th>Relation</th><th>Missing Terms</th><th>Failed Checks</th><th>Explanation</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _group_delta_section(title: str, rows: Any) -> str:
    html_rows = []
    for row in _list_of_dicts(rows):
        relation = str(row.get("relation") or "missing")
        html_rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('key'))}</strong><br><span>{_e(row.get('group_by'))}</span></td>"
            f"<td>{_e(row.get('run_name'))}</td>"
            f"<td><span class=\"pill {_relation_class(relation)}\">{_e(relation)}</span></td>"
            f"<td>{_e(_fmt(row.get('score')))}<br><span>{_e(_fmt_signed(row.get('score_delta')))}</span></td>"
            f"<td>{_e(_fmt(row.get('rubric_score')))}<br><span>{_e(_fmt_signed(row.get('rubric_score_delta')))}</span></td>"
            f"<td>{_e(row.get('case_count'))}</td>"
            f"<td>{_e(row.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        f'<section class="panel"><h2>{_e(title)}</h2><table><thead><tr>'
        "<th>Group</th><th>Run</th><th>Relation</th><th>Score</th><th>Rubric</th><th>Cases</th><th>Explanation</th>"
        "</tr></thead><tbody>"
        + "".join(html_rows)
        + "</tbody></table></section>"
    )


def _markdown_group_section(title: str, rows: Any) -> list[str]:
    lines = [
        "",
        f"## {title}",
        "",
        "| Group | Run | Score Delta | Rubric Delta | Relation | Explanation |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in _list_of_dicts(rows):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("key")),
                    _md(row.get("run_name")),
                    _md(_fmt_signed(row.get("score_delta"))),
                    _md(_fmt_signed(row.get("rubric_score_delta"))),
                    _md(row.get("relation")),
                    _md(row.get("explanation")),
                ]
            )
            + " |"
        )
    return lines


def _terms_delta(row: dict[str, Any], suffix: str) -> str:
    added = _string_list(row.get(f"added_{suffix}"))
    removed = _string_list(row.get(f"removed_{suffix}"))
    parts = []
    if added:
        parts.append("added: " + ", ".join(added))
    if removed:
        parts.append("removed: " + ", ".join(removed))
    return "; ".join(parts) if parts else "none"


def _list_delta(left: Any, right: Any) -> list[str]:
    right_set = set(_string_list(right))
    return sorted({item for item in _string_list(left) if item not in right_set})


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _delta(value: Any, baseline: Any) -> float | None:
    left = _number(value)
    right = _number(baseline)
    if left is None or right is None:
        return None
    return round(left - right, 4)


def _int_delta(value: Any, baseline: Any) -> int | None:
    if value is None or baseline is None:
        return None
    return int(value) - int(baseline)


def _changed(value: Any, baseline: Any) -> bool | None:
    if value is None or baseline is None:
        return None
    return value != baseline


def _first_present(primary: dict[str, Any], fallback: dict[str, Any], primary_key: str, fallback_key: str) -> Any:
    value = primary.get(primary_key) if isinstance(primary, dict) else None
    if value is not None:
        return value
    return fallback.get(fallback_key) if isinstance(fallback, dict) else None


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(value: dict[str, Any], key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_signed(value: Any) -> str:
    if value is None:
        return "missing"
    number = float(value)
    return f"{number:+.5g}"


def _md(value: Any) -> str:
    return ("missing" if value is None else str(value)).replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _stat(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e(_fmt(value))}</div></div>'


def _relation_class(relation: str) -> str:
    if relation == "improved":
        return "pass"
    if relation == "regressed":
        return "fail"
    if relation == "baseline":
        return "base"
    return "warn"


def _list_section(title: str, values: Any) -> str:
    items = _string_list(values) or ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee8; --page:#f7f7f2; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; --blue:#2563eb; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:18px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:1020px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:68px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
.pill.base { background:var(--blue); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""
