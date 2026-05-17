from __future__ import annotations

from typing import Any


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
