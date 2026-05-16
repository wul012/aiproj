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
from .benchmark_scorecard_scoring import (
    benchmark_drilldowns as _benchmark_drilldowns,
    case_scores as _case_scores,
    case_scores_with_rubric as _case_scores_with_rubric,
    rubric_scores as _rubric_scores,
    status as _status,
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
    flag_summary = _dict(summary.get("flag_summary"))
    flag_id_counts = _dict(flag_summary.get("flag_id_counts"))
    worst_cases = _list_of_dicts(flag_summary.get("worst_cases"))
    case_count = _number(_pick(summary, "case_count")) or 0
    pass_count = _number(_pick(summary, "pass_count")) or 0
    warn_count = _number(_pick(summary, "warn_count")) or 0
    fail_count = _number(_pick(summary, "fail_count")) or 0
    total_flags = _number(flag_summary.get("total_flags")) or 0
    raw_score = 0.0 if case_count == 0 else ((pass_count + warn_count * 0.5) / case_count) * 100.0
    flag_penalty = 0.0 if case_count == 0 else min(20.0, (total_flags / case_count) * 5.0)
    score = max(0.0, raw_score - flag_penalty)
    status = _status(score)
    dominant_flag = _dominant_flag(flag_id_counts)
    worst_case = worst_cases[0] if worst_cases else {}
    detail_parts = [f"{int(pass_count)} pass / {int(warn_count)} warn / {int(fail_count)} fail."]
    if total_flags:
        detail_parts.append(f"{int(total_flags)} flag(s); dominant={dominant_flag or 'missing'}.")
    return _component(
        "generation_quality",
        "Generation Quality",
        score,
        0.2,
        status,
        _as_str(_pick(report, "source_path")) or "generation_quality.json",
        " ".join(detail_parts),
        {
            "case_count": int(case_count),
            "pass_count": int(pass_count),
            "warn_count": int(warn_count),
            "fail_count": int(fail_count),
            "overall_status": _pick(summary, "overall_status"),
            "total_flags": int(total_flags),
            "dominant_flag": dominant_flag,
            "flag_id_counts": flag_id_counts,
            "worst_generation_case": worst_case.get("name"),
            "worst_generation_case_status": worst_case.get("status"),
            "worst_generation_case_flags": worst_case.get("flag_ids") if isinstance(worst_case.get("flag_ids"), list) else [],
            "raw_score": round(raw_score, 2),
            "flag_penalty": round(flag_penalty, 2),
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
    generation_summary = _dict(_pick(generation_quality, "summary"))
    flag_summary = _dict(generation_summary.get("flag_summary"))
    flag_id_counts = _dict(flag_summary.get("flag_id_counts"))
    worst_cases = _list_of_dicts(flag_summary.get("worst_cases"))
    worst_case = worst_cases[0] if worst_cases else {}
    return {
        "overall_score": round(overall, 2),
        "overall_status": _status(overall),
        "component_count": len(components),
        "eval_suite_cases": _pick(eval_suite, "case_count"),
        "generation_quality_status": _pick(generation_summary, "overall_status"),
        "generation_quality_cases": _pick(generation_summary, "case_count"),
        "generation_quality_total_flags": flag_summary.get("total_flags"),
        "generation_quality_dominant_flag": _dominant_flag(flag_id_counts),
        "generation_quality_worst_case": worst_case.get("name"),
        "generation_quality_worst_case_status": worst_case.get("status"),
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
    if summary.get("generation_quality_dominant_flag"):
        recs.append(
            f"Prioritize generation-quality flag `{summary.get('generation_quality_dominant_flag')}` before comparing this run as improved."
        )
    if summary.get("generation_quality_worst_case"):
        recs.append(
            f"Inspect worst generation-quality case `{summary.get('generation_quality_worst_case')}` ({summary.get('generation_quality_worst_case_status')})."
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


def _dominant_flag(flag_id_counts: dict[str, Any]) -> str | None:
    counts = {str(key): _number(value) or 0 for key, value in flag_id_counts.items()}
    counts = {key: value for key, value in counts.items() if key and value > 0}
    if not counts:
        return None
    return max(counts.items(), key=lambda item: (item[1], item[0]))[0]


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


def _as_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)
