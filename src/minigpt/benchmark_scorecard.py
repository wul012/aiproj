from __future__ import annotations

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
from .benchmark_scorecard_components import (
    _eval_coverage_component,
    _evidence_completeness_component,
    _generation_quality_component,
    _pair_consistency_component,
    _pair_delta_stability_component,
    _recommendations,
    _registry_context,
    _rubric_correctness_component,
    _score_summary,
)
from .benchmark_scorecard_scoring import (
    benchmark_drilldowns as _benchmark_drilldowns,
    case_scores as _case_scores,
    case_scores_with_rubric as _case_scores_with_rubric,
    rubric_scores as _rubric_scores,
)
from .report_utils import utc_now


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


def _read_generation_quality(root: Path, warnings: list[str]) -> dict[str, Any] | None:
    candidates = [
        root / "generation_quality" / "generation_quality.json",
        root / "generation-quality" / "generation_quality.json",
        root / "eval_suite" / "generation_quality" / "generation_quality.json",
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
