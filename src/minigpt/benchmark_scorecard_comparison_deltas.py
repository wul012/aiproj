from __future__ import annotations

from typing import Any


def summarize_benchmark_scorecard_run(scorecard: dict[str, Any], name: str, index: int) -> dict[str, Any]:
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
        "generation_quality_total_flags": _as_int(summary.get("generation_quality_total_flags")),
        "generation_quality_dominant_flag": summary.get("generation_quality_dominant_flag"),
        "generation_quality_worst_case": summary.get("generation_quality_worst_case"),
        "generation_quality_worst_case_status": summary.get("generation_quality_worst_case_status"),
        "weakest_task_type": summary.get("weakest_task_type"),
        "weakest_task_type_score": _number(summary.get("weakest_task_type_score")),
        "weakest_difficulty": summary.get("weakest_difficulty"),
        "weakest_difficulty_score": _number(summary.get("weakest_difficulty_score")),
    }


def build_benchmark_scorecard_run_delta(run: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    overall_delta = _delta(run.get("overall_score"), baseline.get("overall_score"))
    rubric_delta = _delta(run.get("rubric_avg_score"), baseline.get("rubric_avg_score"))
    flag_delta = _int_delta(run.get("generation_quality_total_flags"), baseline.get("generation_quality_total_flags"))
    is_baseline = run.get("source_path") == baseline.get("source_path") and run.get("name") == baseline.get("name")
    row = {
        "name": run.get("name"),
        "source_path": run.get("source_path"),
        "baseline_name": baseline.get("name"),
        "is_baseline": is_baseline,
        "overall_score_delta": overall_delta,
        "rubric_avg_score_delta": rubric_delta,
        "rubric_pass_count_delta": _int_delta(run.get("rubric_pass_count"), baseline.get("rubric_pass_count")),
        "rubric_warn_count_delta": _int_delta(run.get("rubric_warn_count"), baseline.get("rubric_warn_count")),
        "rubric_fail_count_delta": _int_delta(run.get("rubric_fail_count"), baseline.get("rubric_fail_count")),
        "weakest_case_changed": _changed(run.get("weakest_rubric_case"), baseline.get("weakest_rubric_case")),
        "generation_quality_total_flags_delta": flag_delta,
        "generation_quality_flag_relation": _flag_relation(flag_delta, is_baseline=is_baseline),
        "generation_quality_dominant_flag_changed": _changed(run.get("generation_quality_dominant_flag"), baseline.get("generation_quality_dominant_flag")),
        "generation_quality_worst_case_changed": _changed(run.get("generation_quality_worst_case"), baseline.get("generation_quality_worst_case")),
        "overall_relation": _score_relation(overall_delta, is_baseline=is_baseline),
        "rubric_relation": _score_relation(rubric_delta, is_baseline=is_baseline),
    }
    row["explanation"] = _run_explanation(row, run, baseline)
    return row


def build_benchmark_scorecard_case_deltas(scorecards: list[dict[str, Any]], names: list[str], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_index = int(baseline.get("index") or 0)
    case_maps = [_case_map(scorecard) for scorecard in scorecards]
    baseline_cases = case_maps[baseline_index]
    rows: list[dict[str, Any]] = []
    for index, case_map in enumerate(case_maps):
        name = names[index]
        for case_name in sorted(set(baseline_cases) | set(case_map)):
            baseline_case = baseline_cases.get(case_name, {"name": case_name})
            case = case_map.get(case_name, {"name": case_name})
            row = _case_delta(case_name, name, str(baseline.get("name")), case, baseline_case, is_baseline=index == baseline_index)
            rows.append(row)
    return rows


def build_benchmark_scorecard_group_deltas(
    scorecards: list[dict[str, Any]],
    names: list[str],
    baseline: dict[str, Any],
    *,
    group_name: str,
) -> list[dict[str, Any]]:
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


def build_benchmark_scorecard_summary(
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
    flag_rows = [row for row in deltas if not row.get("is_baseline") and row.get("generation_quality_total_flags_delta") is not None]
    flag_regressions = [row for row in flag_rows if int(row.get("generation_quality_total_flags_delta") or 0) > 0]
    flag_improvements = [row for row in flag_rows if int(row.get("generation_quality_total_flags_delta") or 0) < 0]
    worst_flag_regression = max(flag_regressions, key=lambda row: (int(row.get("generation_quality_total_flags_delta") or 0), str(row.get("name"))), default={})
    return {
        "baseline_name": baseline.get("name"),
        "baseline_source_path": baseline.get("source_path"),
        "baseline_generation_quality_total_flags": baseline.get("generation_quality_total_flags"),
        "baseline_generation_quality_dominant_flag": baseline.get("generation_quality_dominant_flag"),
        "baseline_generation_quality_worst_case": baseline.get("generation_quality_worst_case"),
        "scorecard_count": len(runs),
        "improved_overall_count": sum(1 for row in deltas if row.get("overall_relation") == "improved"),
        "regressed_overall_count": sum(1 for row in deltas if row.get("overall_relation") == "regressed"),
        "improved_rubric_count": sum(1 for row in deltas if row.get("rubric_relation") == "improved"),
        "regressed_rubric_count": sum(1 for row in deltas if row.get("rubric_relation") == "regressed"),
        "generation_quality_flag_delta_count": len(flag_rows),
        "generation_quality_flag_improvement_count": len(flag_improvements),
        "generation_quality_flag_regression_count": len(flag_regressions),
        "generation_quality_dominant_flag_change_count": sum(1 for row in flag_rows if row.get("generation_quality_dominant_flag_changed")),
        "generation_quality_worst_case_change_count": sum(1 for row in flag_rows if row.get("generation_quality_worst_case_changed")),
        "worst_generation_quality_flag_regression_run": worst_flag_regression.get("name"),
        "worst_generation_quality_flag_regression_delta": worst_flag_regression.get("generation_quality_total_flags_delta"),
        "case_delta_count": len(case_deltas),
        "case_regression_count": len(regressions),
        "case_improvement_count": len(improvements),
        "weakest_case_regression": weakest.get("case"),
        "weakest_case_regression_run": weakest.get("run_name"),
        "weakest_case_regression_delta": weakest.get("rubric_score_delta"),
        "task_type_delta_count": len(task_deltas),
        "difficulty_delta_count": len(difficulty_deltas),
    }


def build_benchmark_scorecard_recommendations(
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
    if int(summary.get("generation_quality_flag_regression_count") or 0):
        recs.append(
            "Generation-quality flags increased in at least one compared scorecard; inspect dominant flag and worst generation case before promotion."
        )
    elif int(summary.get("generation_quality_flag_improvement_count") or 0):
        recs.append("Generation-quality flags decreased in at least one compared scorecard; confirm the improvement also holds at case and rubric level.")
    if int(summary.get("generation_quality_dominant_flag_change_count") or 0):
        recs.append("Dominant generation-quality flag changed for at least one run; treat the comparison as a taxonomy shift, not just a score delta.")
    if any(row.get("added_missing_terms") or row.get("added_failed_checks") for row in case_deltas if not row.get("is_baseline")):
        recs.append("Inspect added missing terms and failed checks to separate wording drift from true task failure.")
    return recs


def select_best_benchmark_scorecard_run(runs: list[dict[str, Any]], field: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if _number(run.get(field)) is not None]
    if not candidates:
        return None
    best = max(candidates, key=lambda run: (_number(run.get(field)) or 0.0, str(run.get("name"))))
    return {"name": best.get("name"), "source_path": best.get("source_path"), field: best.get(field)}


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


def _group_map(scorecard: dict[str, Any], group_name: str) -> dict[str, dict[str, Any]]:
    drilldowns = _dict(scorecard.get("drilldowns"))
    rows = _list_of_dicts(drilldowns.get(group_name))
    return {str(row.get("key") or "unknown"): row for row in rows}


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
    if delta.get("generation_quality_total_flags_delta") is not None:
        parts.append(f"Generation-quality flags changed {_fmt_signed(delta.get('generation_quality_total_flags_delta'))}.")
    if delta.get("generation_quality_dominant_flag_changed"):
        parts.append(
            f"Dominant generation flag moved from {baseline.get('generation_quality_dominant_flag')} to {run.get('generation_quality_dominant_flag')}."
        )
    if delta.get("generation_quality_worst_case_changed"):
        parts.append(
            f"Worst generation case moved from {baseline.get('generation_quality_worst_case')} to {run.get('generation_quality_worst_case')}."
        )
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


def _flag_relation(delta: Any, *, is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    if delta is None:
        return "missing"
    number = int(delta)
    if number < 0:
        return "improved"
    if number > 0:
        return "regressed"
    return "tied"


def _list_delta(left: Any, right: Any) -> list[str]:
    right_set = set(_string_list(right))
    return sorted({item for item in _string_list(left) if item not in right_set})


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


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]


def _fmt_signed(value: Any) -> str:
    if value is None:
        return "missing"
    number = float(value)
    return f"{number:+.5g}"


__all__ = [
    "build_benchmark_scorecard_case_deltas",
    "build_benchmark_scorecard_group_deltas",
    "build_benchmark_scorecard_recommendations",
    "build_benchmark_scorecard_run_delta",
    "build_benchmark_scorecard_summary",
    "select_best_benchmark_scorecard_run",
    "summarize_benchmark_scorecard_run",
]
