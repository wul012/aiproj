from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    utc_now,
)
from minigpt.benchmark_scorecard_decision_logic import (
    _case_delta_counts,
    _decision_status,
    _evaluate_run,
    _recommendations,
    _recommended_action,
    _remediation_plan,
    _remediation_summary,
    _select_candidate,
    _summary,
)
from minigpt.benchmark_scorecard_decision_artifacts import (
    render_benchmark_scorecard_decision_html,  # noqa: F401
    render_benchmark_scorecard_decision_markdown,  # noqa: F401
    write_benchmark_scorecard_decision_csv,  # noqa: F401
    write_benchmark_scorecard_decision_html,  # noqa: F401
    write_benchmark_scorecard_decision_json,  # noqa: F401
    write_benchmark_scorecard_decision_markdown,  # noqa: F401
    write_benchmark_scorecard_decision_outputs,  # noqa: F401
    write_benchmark_scorecard_remediation_csv,  # noqa: F401
)


def load_benchmark_scorecard_comparison(path: str | Path) -> dict[str, Any]:
    comparison_path = _resolve_comparison_path(Path(path))
    payload = json.loads(comparison_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("benchmark scorecard comparison must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(comparison_path)
    return payload


def build_benchmark_scorecard_decision(
    comparison_path: str | Path,
    *,
    min_rubric_score: float = 80.0,
    title: str = "MiniGPT benchmark scorecard promotion decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    comparison = load_benchmark_scorecard_comparison(comparison_path)
    runs = _list_of_dicts(comparison.get("runs"))
    if not runs:
        raise ValueError("comparison must contain at least one run")
    deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
    case_counts = _case_delta_counts(comparison)
    evaluations = [_evaluate_run(run, deltas.get(run.get("name"), {}), case_counts, min_rubric_score) for run in runs]
    candidates = [row for row in evaluations if not row.get("is_baseline") and not row.get("blockers")]
    clean_candidates = [row for row in candidates if not row.get("review_items")]
    selected = _select_candidate(clean_candidates or candidates)
    decision_status = _decision_status(selected)
    summary = _summary(comparison, evaluations, candidates, clean_candidates, selected, decision_status, min_rubric_score)
    remediation_plan = _remediation_plan(summary)
    remediation_summary = _remediation_summary(remediation_plan)
    summary = {**summary, **remediation_summary}
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "comparison_path": str(comparison.get("_source_path")),
        "comparison_title": comparison.get("title"),
        "baseline_name": _dict(comparison.get("baseline")).get("name") or _dict(comparison.get("summary")).get("baseline_name"),
        "min_rubric_score": float(min_rubric_score),
        "decision_status": decision_status,
        "recommended_action": _recommended_action(decision_status),
        "selected_run": selected,
        "candidate_evaluations": evaluations,
        "summary": summary,
        "remediation_plan": remediation_plan,
        "recommendations": _recommendations(decision_status, selected, evaluations, comparison, remediation_plan),
    }



def _resolve_comparison_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "benchmark_scorecard_comparison.json",
                path / "benchmark-scorecard-comparison" / "benchmark_scorecard_comparison.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)
