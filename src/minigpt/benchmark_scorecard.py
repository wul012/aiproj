from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .benchmark_scorecard_artifacts import (
    render_benchmark_scorecard_html as _artifact_render_benchmark_scorecard_html,
    render_benchmark_scorecard_markdown as _artifact_render_benchmark_scorecard_markdown,
    write_benchmark_scorecard_csv as _artifact_write_benchmark_scorecard_csv,
    write_benchmark_scorecard_drilldown_csv as _artifact_write_benchmark_scorecard_drilldown_csv,
    write_benchmark_scorecard_html as _artifact_write_benchmark_scorecard_html,
    write_benchmark_scorecard_json as _artifact_write_benchmark_scorecard_json,
    write_benchmark_scorecard_markdown as _artifact_write_benchmark_scorecard_markdown,
    write_benchmark_scorecard_outputs as _artifact_write_benchmark_scorecard_outputs,
    write_benchmark_scorecard_rubric_csv as _artifact_write_benchmark_scorecard_rubric_csv,
)


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

    case_scores = _case_scores(eval_suite, generation_quality, pair_batch)
    rubric_scores = _rubric_scores(case_scores)
    case_scores = _case_scores_with_rubric(case_scores, rubric_scores)
    components = [
        _eval_coverage_component(eval_suite, root / "eval_suite" / "eval_suite.json"),
        _generation_quality_component(generation_quality),
        _rubric_correctness_component(rubric_scores),
        _pair_consistency_component(pair_batch, root / "pair_batch" / "pair_generation_batch.json"),
        _pair_delta_stability_component(pair_batch, root / "pair_batch" / "pair_generation_batch.json"),
        _evidence_completeness_component(root),
    ]
    drilldowns = _benchmark_drilldowns(case_scores)
    summary = _score_summary(components, eval_suite, generation_quality, pair_batch, drilldowns, rubric_scores)
    return {
        "schema_version": 3,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "run_dir": str(root),
        "registry_path": str(registry_path) if registry_path is not None else None,
        "summary": summary,
        "components": components,
        "rubric_scores": rubric_scores,
        "drilldowns": drilldowns,
        "case_scores": case_scores,
        "registry_context": _registry_context(registry, root),
        "recommendations": _recommendations(summary, components, drilldowns),
        "warnings": warnings,
    }


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def write_benchmark_scorecard_json(scorecard: dict[str, Any], path: str | Path) -> None:
    _artifact_write_benchmark_scorecard_json(scorecard, path)


def write_benchmark_scorecard_csv(scorecard: dict[str, Any], path: str | Path) -> None:
    _artifact_write_benchmark_scorecard_csv(scorecard, path)


def write_benchmark_scorecard_drilldown_csv(scorecard: dict[str, Any], path: str | Path) -> None:
    _artifact_write_benchmark_scorecard_drilldown_csv(scorecard, path)


def write_benchmark_scorecard_rubric_csv(scorecard: dict[str, Any], path: str | Path) -> None:
    _artifact_write_benchmark_scorecard_rubric_csv(scorecard, path)


def render_benchmark_scorecard_markdown(scorecard: dict[str, Any]) -> str:
    return _artifact_render_benchmark_scorecard_markdown(scorecard)


def write_benchmark_scorecard_markdown(scorecard: dict[str, Any], path: str | Path) -> None:
    _artifact_write_benchmark_scorecard_markdown(scorecard, path)


def render_benchmark_scorecard_html(scorecard: dict[str, Any]) -> str:
    return _artifact_render_benchmark_scorecard_html(scorecard)


def write_benchmark_scorecard_html(scorecard: dict[str, Any], path: str | Path) -> None:
    _artifact_write_benchmark_scorecard_html(scorecard, path)


def write_benchmark_scorecard_outputs(scorecard: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return _artifact_write_benchmark_scorecard_outputs(scorecard, out_dir)


def _eval_coverage_component(eval_suite: Any, path: Path) -> dict[str, Any]:
    case_count = _number(_pick(eval_suite, "case_count")) or 0
    score = min(100.0, case_count * 20.0)
    status = _status(score)
    return _component(
        "eval_coverage",
        "Eval Suite Coverage",
        score,
        0.15,
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
        0.2,
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


def _rubric_correctness_component(rubric_scores: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(rubric_scores.get("summary"))
    case_count = _number(summary.get("case_count")) or 0
    avg_score = _number(summary.get("avg_score")) or 0
    return _component(
        "rubric_correctness",
        "Rubric Correctness",
        avg_score,
        0.25,
        _status(avg_score) if case_count else "fail",
        "benchmark_scorecard.rubric_scores",
        f"{int(summary.get('pass_count') or 0)} pass / {int(summary.get('warn_count') or 0)} warn / {int(summary.get('fail_count') or 0)} fail.",
        {
            "case_count": int(case_count),
            "avg_score": round(avg_score, 2),
            "weakest_case": summary.get("weakest_case"),
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
        0.15,
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
        0.15,
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


def _score_summary(
    components: list[dict[str, Any]],
    eval_suite: Any,
    generation_quality: Any,
    pair_batch: Any,
    drilldowns: dict[str, Any],
    rubric_scores: dict[str, Any],
) -> dict[str, Any]:
    total_weight = sum(float(item.get("weight") or 0) for item in components)
    overall = 0.0 if total_weight == 0 else sum(float(item.get("weighted_score") or 0) for item in components) / total_weight
    weakest_task_type = _dict(_pick(drilldowns, "weakest_task_type"))
    weakest_difficulty = _dict(_pick(drilldowns, "weakest_difficulty"))
    rubric_summary = _dict(rubric_scores.get("summary"))
    return {
        "overall_score": round(overall, 2),
        "overall_status": _status(overall),
        "component_count": len(components),
        "eval_suite_cases": _pick(eval_suite, "case_count"),
        "generation_quality_status": _pick(_dict(_pick(generation_quality, "summary")), "overall_status"),
        "generation_quality_cases": _pick(_dict(_pick(generation_quality, "summary")), "case_count"),
        "rubric_status": rubric_summary.get("overall_status"),
        "rubric_avg_score": rubric_summary.get("avg_score"),
        "rubric_pass_count": rubric_summary.get("pass_count"),
        "rubric_warn_count": rubric_summary.get("warn_count"),
        "rubric_fail_count": rubric_summary.get("fail_count"),
        "weakest_rubric_case": rubric_summary.get("weakest_case"),
        "weakest_rubric_score": rubric_summary.get("weakest_score"),
        "pair_batch_cases": _pick(pair_batch, "case_count"),
        "pair_generated_differences": _pick(pair_batch, "generated_difference_count"),
        "max_abs_generated_delta": _max_abs_generated_delta(pair_batch),
        "task_type_group_count": len(_list_of_dicts(_pick(drilldowns, "task_type"))),
        "difficulty_group_count": len(_list_of_dicts(_pick(drilldowns, "difficulty"))),
        "weakest_task_type": weakest_task_type.get("key"),
        "weakest_task_type_score": weakest_task_type.get("score"),
        "weakest_difficulty": weakest_difficulty.get("key"),
        "weakest_difficulty_score": weakest_difficulty.get("score"),
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


def _rubric_scores(case_scores: list[dict[str, Any]]) -> dict[str, Any]:
    cases = [_rubric_case_score(case) for case in case_scores]
    scores = [_number(case.get("score")) or 0 for case in cases]
    avg_score = 0.0 if not scores else round(sum(scores) / len(scores), 2)
    weakest = min(cases, key=lambda item: (_number(item.get("score")) or 0, str(item.get("name"))), default={})
    return {
        "schema_version": 1,
        "summary": {
            "case_count": len(cases),
            "avg_score": avg_score,
            "overall_status": _status(avg_score) if cases else "fail",
            "pass_count": sum(1 for case in cases if case.get("status") == "pass"),
            "warn_count": sum(1 for case in cases if case.get("status") == "warn"),
            "fail_count": sum(1 for case in cases if case.get("status") == "fail"),
            "weakest_case": weakest.get("name"),
            "weakest_score": weakest.get("score"),
        },
        "cases": cases,
    }


def _case_scores_with_rubric(case_scores: list[dict[str, Any]], rubric_scores: dict[str, Any]) -> list[dict[str, Any]]:
    rubric_by_name = {str(item.get("name")): item for item in _list_of_dicts(rubric_scores.get("cases"))}
    rows = []
    for case in case_scores:
        row = dict(case)
        rubric = rubric_by_name.get(str(case.get("name")))
        if rubric:
            row["rubric_score"] = rubric.get("score")
            row["rubric_status"] = rubric.get("status")
            row["rubric_failed_checks"] = rubric.get("failed_checks")
            row["rubric_missing_terms"] = rubric.get("missing_terms")
        rows.append(row)
    return rows


def _rubric_case_score(case: dict[str, Any]) -> dict[str, Any]:
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
        "status": _status(score),
        "score": score,
        "passed_checks": len(checks) - len(failed_checks),
        "total_checks": len(checks),
        "matched_terms": _matched_terms(text, must_include),
        "missing_terms": _missing_terms(text, must_include),
        "failed_checks": failed_checks,
        "expected_behavior": case.get("expected_behavior"),
        "checks": checks,
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


def _benchmark_drilldowns(case_scores: list[dict[str, Any]]) -> dict[str, Any]:
    task_type_rows = _group_drilldowns(case_scores, "task_type")
    difficulty_rows = _group_drilldowns(case_scores, "difficulty")
    return {
        "task_type": task_type_rows,
        "difficulty": difficulty_rows,
        "weakest_task_type": _weakest_drilldown(task_type_rows),
        "weakest_difficulty": _weakest_drilldown(difficulty_rows),
    }


def _group_drilldowns(case_scores: list[dict[str, Any]], group_by: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for case in case_scores:
        key = str(case.get(group_by) or "unknown")
        groups.setdefault(key, []).append(case)
    rows = [_build_drilldown_row(group_by, key, rows) for key, rows in groups.items()]
    return sorted(rows, key=lambda item: (-int(item.get("case_count") or 0), str(item.get("key"))))


def _build_drilldown_row(group_by: str, key: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    generation_counts = {"pass": 0, "warn": 0, "fail": 0}
    generation_case_count = 0
    for case in cases:
        status = str(case.get("generation_quality_status") or "")
        if status in generation_counts:
            generation_counts[status] += 1
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

    rubric_scores = [_number(case.get("rubric_score")) for case in cases]
    rubric_scores = [value for value in rubric_scores if value is not None]
    rubric_score = 0.0 if not rubric_scores else sum(rubric_scores) / len(rubric_scores)
    rubric_counts = {"pass": 0, "warn": 0, "fail": 0}
    for case in cases:
        status = str(case.get("rubric_status") or "")
        if status in rubric_counts:
            rubric_counts[status] += 1

    coverage_score = min(100.0, len(cases) * 50.0)
    score = rubric_score * 0.3 + generation_score * 0.25 + pair_score * 0.2 + delta_score * 0.15 + coverage_score * 0.1
    return {
        "group_by": group_by,
        "key": key,
        "status": _status(score),
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


def _weakest_drilldown(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    weakest = min(rows, key=lambda item: (float(item.get("score") or 0), -int(item.get("case_count") or 0), str(item.get("key"))))
    return {
        "key": weakest.get("key"),
        "status": weakest.get("status"),
        "score": weakest.get("score"),
        "case_count": weakest.get("case_count"),
    }


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


def _recommendations(summary: dict[str, Any], components: list[dict[str, Any]], drilldowns: dict[str, Any] | None = None) -> list[str]:
    recs = []
    if summary.get("overall_status") == "pass":
        recs.append("Use this scorecard as the single benchmark entry point for the current run.")
    else:
        recs.append("Treat low scoring components as the next benchmark hardening targets.")
    weak = [item for item in components if item.get("status") != "pass"]
    if weak:
        recs.append("Improve weak components: " + ", ".join(str(item.get("title")) for item in weak) + ".")
    if summary.get("weakest_rubric_case"):
        recs.append(
            f"Review weakest rubric case `{summary.get('weakest_rubric_case')}` at score {summary.get('weakest_rubric_score')} before trusting benchmark gains."
        )
    drilldowns = _dict(drilldowns)
    weakest_task = _dict(drilldowns.get("weakest_task_type"))
    weakest_difficulty = _dict(drilldowns.get("weakest_difficulty"))
    if weakest_task:
        recs.append(
            f"Review weakest task type `{weakest_task.get('key')}` at score {weakest_task.get('score')} before expanding the suite."
        )
    if weakest_difficulty:
        recs.append(
            f"Review weakest difficulty `{weakest_difficulty.get('key')}` at score {weakest_difficulty.get('score')} before comparing runs."
        )
    recs.append("Next step: compare rubric score changes across runs so correctness regressions are visible in the registry.")
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
