from __future__ import annotations

from typing import Any


def case_scores(eval_suite: Any, generation_quality: Any, pair_batch: Any) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for result in _list_of_dicts(_pick(eval_suite, "results")):
        name = str(result.get("name") or f"case-{len(rows) + 1}")
        rows.setdefault(name, {"name": name})
        rows[name].update(
            {
                "task_type": result.get("task_type"),
                "difficulty": result.get("difficulty"),
                "prompt": result.get("prompt"),
                "generated": result.get("generated"),
                "continuation": result.get("continuation"),
                "expected_behavior": result.get("expected_behavior"),
                "tags": result.get("tags") if isinstance(result.get("tags"), list) else [],
                "rubric": _dict(result.get("rubric")),
                "max_new_tokens": result.get("max_new_tokens"),
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


def rubric_scores(case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    cases = [rubric_case_score(case) for case in case_rows]
    scores = [_number(case.get("score")) or 0 for case in cases]
    avg_score = 0.0 if not scores else round(sum(scores) / len(scores), 2)
    weakest = min(cases, key=lambda item: (_number(item.get("score")) or 0, str(item.get("name"))), default={})
    return {
        "schema_version": 1,
        "summary": {
            "case_count": len(cases),
            "avg_score": avg_score,
            "overall_status": status(avg_score) if cases else "fail",
            "pass_count": sum(1 for case in cases if case.get("status") == "pass"),
            "warn_count": sum(1 for case in cases if case.get("status") == "warn"),
            "fail_count": sum(1 for case in cases if case.get("status") == "fail"),
            "weakest_case": weakest.get("name"),
            "weakest_score": weakest.get("score"),
        },
        "cases": cases,
    }


def case_scores_with_rubric(case_rows: list[dict[str, Any]], rubric_report: dict[str, Any]) -> list[dict[str, Any]]:
    rubric_by_name = {str(item.get("name")): item for item in _list_of_dicts(rubric_report.get("cases"))}
    rows = []
    for case in case_rows:
        row = dict(case)
        rubric = rubric_by_name.get(str(case.get("name")))
        if rubric:
            row["rubric_score"] = rubric.get("score")
            row["rubric_status"] = rubric.get("status")
            row["rubric_failed_checks"] = rubric.get("failed_checks")
            row["rubric_missing_terms"] = rubric.get("missing_terms")
        rows.append(row)
    return rows


def rubric_case_score(case: dict[str, Any]) -> dict[str, Any]:
    name = str(case.get("name") or "unknown")
    rubric = _dict(case.get("rubric"))
    text = _case_text(case)
    char_count = _number(case.get("eval_char_count"))
    if char_count is None:
        char_count = len(str(case.get("continuation") or ""))
    min_chars = int(_number(rubric.get("min_chars")) or _default_min_chars(case))
    max_chars = _number(rubric.get("max_chars"))
    must_include = _rubric_terms(case, rubric)
    must_avoid = _term_list(_first_present(rubric, ["must_avoid", "forbidden_terms", "avoid_terms"]))

    checks = [
        _rubric_check("has_output", "Output is present", 0.2, bool(text.strip()), "Generated text is non-empty."),
        _rubric_check(
            "length_bounds",
            "Length fits prompt bounds",
            0.2,
            char_count >= min_chars and (max_chars is None or char_count <= max_chars),
            f"char_count={_fmt(char_count)}, min={min_chars}, max={_fmt(max_chars)}.",
        ),
        _term_check("must_include", "Required terms appear", 0.25, text, must_include),
        _forbidden_term_check("must_avoid", "Forbidden terms are absent", 0.15, text, must_avoid),
        _task_shape_check(case, text, char_count, min_chars),
    ]
    weighted = sum(float(check["weight"]) * float(check["score"]) for check in checks)
    total_weight = sum(float(check["weight"]) for check in checks)
    score = 0.0 if total_weight == 0 else round(weighted / total_weight * 100.0, 2)
    failed_checks = [str(check["id"]) for check in checks if float(check.get("score") or 0) < 1.0]
    return {
        "name": name,
        "task_type": case.get("task_type"),
        "difficulty": case.get("difficulty"),
        "status": status(score),
        "score": score,
        "passed_checks": len(checks) - len(failed_checks),
        "total_checks": len(checks),
        "matched_terms": _matched_terms(text, must_include),
        "missing_terms": _missing_terms(text, must_include),
        "failed_checks": failed_checks,
        "expected_behavior": case.get("expected_behavior"),
        "checks": checks,
    }


def benchmark_drilldowns(case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    task_type_rows = group_drilldowns(case_rows, "task_type")
    difficulty_rows = group_drilldowns(case_rows, "difficulty")
    return {
        "task_type": task_type_rows,
        "difficulty": difficulty_rows,
        "weakest_task_type": weakest_drilldown(task_type_rows),
        "weakest_difficulty": weakest_drilldown(difficulty_rows),
    }


def group_drilldowns(case_rows: list[dict[str, Any]], group_by: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for case in case_rows:
        key = str(case.get(group_by) or "unknown")
        groups.setdefault(key, []).append(case)
    rows = [_build_drilldown_row(group_by, key, rows) for key, rows in groups.items()]
    return sorted(rows, key=lambda item: (-int(item.get("case_count") or 0), str(item.get("key"))))


def weakest_drilldown(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    weakest = min(rows, key=lambda item: (float(item.get("score") or 0), -int(item.get("case_count") or 0), str(item.get("key"))))
    return {
        "key": weakest.get("key"),
        "status": weakest.get("status"),
        "score": weakest.get("score"),
        "case_count": weakest.get("case_count"),
    }


def status(score: float) -> str:
    if score >= 80:
        return "pass"
    if score >= 60:
        return "warn"
    return "fail"


def _build_drilldown_row(group_by: str, key: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    generation_counts = {"pass": 0, "warn": 0, "fail": 0}
    generation_case_count = 0
    for case in cases:
        generation_status = str(case.get("generation_quality_status") or "")
        if generation_status in generation_counts:
            generation_counts[generation_status] += 1
            generation_case_count += 1
    generation_score = (
        0.0
        if generation_case_count == 0
        else ((generation_counts["pass"] + generation_counts["warn"] * 0.5) / generation_case_count) * 100.0
    )

    pair_values = [case.get("pair_generated_equal") for case in cases if isinstance(case.get("pair_generated_equal"), bool)]
    pair_equal_count = sum(1 for value in pair_values if value is True)
    pair_difference_count = len(pair_values) - pair_equal_count
    pair_score = 0.0 if not pair_values else pair_equal_count / len(pair_values) * 100.0

    deltas = [_number(case.get("pair_generated_char_delta")) for case in cases]
    abs_deltas = [abs(value) for value in deltas if value is not None]
    avg_delta = None if not abs_deltas else sum(abs_deltas) / len(abs_deltas)
    max_delta = None if not abs_deltas else max(abs_deltas)
    delta_score = 0.0 if avg_delta is None else max(0.0, 100.0 - avg_delta * 10.0)

    eval_chars = [_number(case.get("eval_char_count")) for case in cases]
    eval_chars = [value for value in eval_chars if value is not None]
    avg_eval_chars = None if not eval_chars else sum(eval_chars) / len(eval_chars)

    rubric_values = [_number(case.get("rubric_score")) for case in cases]
    rubric_values = [value for value in rubric_values if value is not None]
    rubric_score = 0.0 if not rubric_values else sum(rubric_values) / len(rubric_values)
    rubric_counts = {"pass": 0, "warn": 0, "fail": 0}
    for case in cases:
        rubric_status = str(case.get("rubric_status") or "")
        if rubric_status in rubric_counts:
            rubric_counts[rubric_status] += 1

    coverage_score = min(100.0, len(cases) * 50.0)
    score = rubric_score * 0.3 + generation_score * 0.25 + pair_score * 0.2 + delta_score * 0.15 + coverage_score * 0.1
    return {
        "group_by": group_by,
        "key": key,
        "status": status(score),
        "score": round(score, 2),
        "case_count": len(cases),
        "coverage_score": round(coverage_score, 2),
        "rubric_score": round(rubric_score, 2),
        "rubric_pass_count": rubric_counts["pass"],
        "rubric_warn_count": rubric_counts["warn"],
        "rubric_fail_count": rubric_counts["fail"],
        "generation_quality_score": round(generation_score, 2),
        "pair_consistency_score": round(pair_score, 2),
        "pair_delta_stability_score": round(delta_score, 2),
        "generation_pass_count": generation_counts["pass"],
        "generation_warn_count": generation_counts["warn"],
        "generation_fail_count": generation_counts["fail"],
        "pair_equal_count": pair_equal_count,
        "pair_difference_count": pair_difference_count,
        "avg_abs_generated_delta": _round_optional(avg_delta),
        "max_abs_generated_delta": _round_optional(max_delta),
        "avg_eval_chars": _round_optional(avg_eval_chars),
        "cases": [str(case.get("name")) for case in sorted(cases, key=lambda item: str(item.get("name")))],
    }


def _rubric_check(check_id: str, title: str, weight: float, passed: bool, detail: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "title": title,
        "weight": weight,
        "score": 1.0 if passed else 0.0,
        "passed": passed,
        "detail": detail,
    }


def _term_check(check_id: str, title: str, weight: float, text: str, terms: list[str]) -> dict[str, Any]:
    if not terms:
        return _rubric_check(check_id, title, weight, True, "No explicit required terms configured.")
    matched = _matched_terms(text, terms)
    score = len(matched) / len(terms)
    return {
        "id": check_id,
        "title": title,
        "weight": weight,
        "score": round(score, 4),
        "passed": score >= 1.0,
        "detail": f"matched={len(matched)} / {len(terms)} required term(s).",
    }


def _forbidden_term_check(check_id: str, title: str, weight: float, text: str, terms: list[str]) -> dict[str, Any]:
    found = _matched_terms(text, terms)
    return {
        "id": check_id,
        "title": title,
        "weight": weight,
        "score": 0.0 if found else 1.0,
        "passed": not found,
        "detail": "found forbidden term(s): " + ", ".join(found) if found else "No forbidden terms found.",
    }


def _task_shape_check(case: dict[str, Any], text: str, char_count: float, min_chars: int) -> dict[str, Any]:
    task_type = str(case.get("task_type") or "").lower()
    if "structured" in task_type or "format" in task_type or "json" in task_type:
        passed = any(token in text for token in ["{", "}", "[", "]", ":", '"'])
        detail = "Structured task expects JSON/list-like punctuation."
    elif "summary" in task_type:
        passed = char_count >= min_chars and char_count <= 140
        detail = "Summary task expects a concise non-empty continuation."
    else:
        passed = char_count >= min_chars
        detail = "Task expects enough continuation text for review."
    return _rubric_check("task_shape", "Task shape is plausible", 0.2, passed, detail)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _round_optional(value: Any) -> float | int | None:
    number = _number(value)
    if number is None:
        return None
    rounded = round(number, 2)
    return int(rounded) if float(rounded).is_integer() else rounded


def _case_text(case: dict[str, Any]) -> str:
    generated = str(case.get("generated") or "")
    continuation = str(case.get("continuation") or "")
    return (generated + "\n" + continuation).strip()


def _default_min_chars(case: dict[str, Any]) -> int:
    task_type = str(case.get("task_type") or "").lower()
    if "structured" in task_type or "format" in task_type:
        return 4
    if "summary" in task_type:
        return 8
    return 6


def _rubric_terms(case: dict[str, Any], rubric: dict[str, Any]) -> list[str]:
    explicit = _term_list(_first_present(rubric, ["must_include", "expected_terms", "keywords", "required_terms"]))
    if explicit:
        return explicit
    explicit = _term_list(_first_present(case, ["must_include", "expected_terms", "keywords", "required_terms"]))
    if explicit:
        return explicit
    return _terms_from_expected_behavior(str(case.get("expected_behavior") or ""))


def _terms_from_expected_behavior(text: str) -> list[str]:
    stopwords = {
        "with",
        "that",
        "this",
        "the",
        "and",
        "briefly",
        "produce",
        "answer",
        "continue",
        "sentence",
        "coherent",
        "generate",
        "compact",
        "structured",
        "list",
        "fields",
        "mentions",
        "mention",
        "stay",
        "topic",
        "reject",
        "false",
        "premise",
        "explain",
        "usually",
    }
    words = []
    current = []
    for char in text.lower():
        if char.isalpha() or char in {"-", "_"}:
            current.append(char)
        else:
            if current:
                words.append("".join(current).strip("-_"))
                current = []
    if current:
        words.append("".join(current).strip("-_"))
    terms = []
    for word in words:
        if len(word) >= 4 and word not in stopwords and word not in terms:
            terms.append(word)
    return terms[:6]


def _first_present(source: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = source.get(key)
        if value not in (None, "", []):
            return value
    return None


def _term_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.replace(";", ",").split(",")
    elif isinstance(value, list):
        raw = value
    else:
        raw = [value]
    terms = []
    for item in raw:
        text = str(item).strip()
        if text and text not in terms:
            terms.append(text)
    return terms


def _matched_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return [term for term in terms if str(term).lower() in lowered]


def _missing_terms(text: str, terms: list[str]) -> list[str]:
    matched = set(_matched_terms(text, terms))
    return [term for term in terms if term not in matched]


__all__ = [
    "benchmark_drilldowns",
    "case_scores",
    "case_scores_with_rubric",
    "group_drilldowns",
    "rubric_case_score",
    "rubric_scores",
    "status",
    "weakest_drilldown",
]
