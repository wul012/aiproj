from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.benchmark_history_artifacts import (
    render_benchmark_history_html,
    render_benchmark_history_markdown,
    write_benchmark_history_csv,
    write_benchmark_history_html,
    write_benchmark_history_json,
    write_benchmark_history_markdown,
    write_benchmark_history_outputs,
)
from minigpt.report_utils import as_dict, list_of_dicts, number_or_default, number_or_none, utc_now


def load_benchmark_comparison(path: str | Path) -> dict[str, Any]:
    resolved = _resolve_json_path(Path(path), "benchmark_scorecard_comparison.json")
    payload = json.loads(resolved.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("benchmark comparison must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(resolved)
    return payload


def load_benchmark_decision(path: str | Path) -> dict[str, Any]:
    resolved = _resolve_json_path(Path(path), "benchmark_scorecard_decision.json")
    payload = json.loads(resolved.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("benchmark decision must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(resolved)
    return payload


def build_benchmark_history(
    comparison_paths: list[str | Path],
    *,
    decision_paths: list[str | Path] | None = None,
    names: list[str] | None = None,
    evidence_kind: str = "real-benchmark",
    title: str = "MiniGPT benchmark history",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not comparison_paths:
        raise ValueError("at least one benchmark scorecard comparison is required")
    if names is not None and len(names) != len(comparison_paths):
        raise ValueError("names length must match comparison_paths length")
    if decision_paths is not None and len(decision_paths) != len(comparison_paths):
        raise ValueError("decision_paths length must match comparison_paths length")
    comparisons = [load_benchmark_comparison(path) for path in comparison_paths]
    decisions = [load_benchmark_decision(path) for path in decision_paths] if decision_paths is not None else [None] * len(comparisons)
    entries = [
        _entry(comparison, decisions[index], _entry_name(comparison, names, index), index, evidence_kind)
        for index, comparison in enumerate(comparisons)
    ]
    summary = _summary(entries)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "evidence_kind": evidence_kind,
        "summary": summary,
        "entries": entries,
        "recommendations": _recommendations(summary, entries),
    }


def _entry(
    comparison: dict[str, Any],
    decision: dict[str, Any] | None,
    name: str,
    index: int,
    evidence_kind: str,
) -> dict[str, Any]:
    comparison_summary = as_dict(comparison.get("summary"))
    decision_summary = as_dict(decision.get("summary")) if isinstance(decision, dict) else {}
    selected = _selected_run(comparison, decision)
    delta = _delta_for_candidate(comparison, selected)
    baseline = as_dict(comparison.get("baseline"))
    decision_status = str(decision.get("decision_status") or decision_summary.get("decision_status") or "not-provided") if isinstance(decision, dict) else "not-provided"
    model_quality_claim = "not_claimed" if evidence_kind == "tiny-smoke" else "candidate_evidence"
    return {
        "index": index,
        "name": name,
        "comparison_path": comparison.get("_source_path"),
        "decision_path": None if not isinstance(decision, dict) else decision.get("_source_path"),
        "baseline_name": baseline.get("name") or comparison_summary.get("baseline_name"),
        "candidate_name": selected.get("name"),
        "decision_status": decision_status,
        "recommended_action": None if not isinstance(decision, dict) else decision.get("recommended_action"),
        "promotion_readiness": _promotion_readiness(decision_status, selected, comparison_summary),
        "model_quality_claim": model_quality_claim,
        "overall_score": selected.get("overall_score"),
        "rubric_avg_score": selected.get("rubric_avg_score"),
        "overall_score_delta": _number(delta.get("overall_score_delta")),
        "rubric_avg_score_delta": _number(delta.get("rubric_avg_score_delta")),
        "overall_relation": delta.get("overall_relation"),
        "rubric_relation": delta.get("rubric_relation"),
        "case_regression_count": _int(first_present(selected.get("case_regression_count"), comparison_summary.get("case_regression_count"))),
        "case_improvement_count": _int(first_present(selected.get("case_improvement_count"), comparison_summary.get("case_improvement_count"))),
        "generation_quality_total_flags_delta": _int_or_none(delta.get("generation_quality_total_flags_delta")),
        "generation_quality_flag_relation": delta.get("generation_quality_flag_relation"),
        "generation_quality_dominant_flag_changed": bool(delta.get("generation_quality_dominant_flag_changed")),
        "generation_quality_worst_case_changed": bool(delta.get("generation_quality_worst_case_changed")),
        "eval_suite_comparison_status": selected.get("eval_suite_comparison_status"),
        "non_comparison_ready_count": _int(comparison_summary.get("non_comparison_ready_count")),
        "remediation_plan_count": _int(decision_summary.get("remediation_plan_count")),
        "boundary": _boundary(evidence_kind, selected, comparison_summary),
    }


def _selected_run(comparison: dict[str, Any], decision: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(decision, dict):
        selected = as_dict(decision.get("selected_run"))
        if selected:
            return selected
    best = as_dict(comparison.get("best_by_rubric_avg_score"))
    best_name = best.get("name")
    if best_name:
        for run in list_of_dicts(comparison.get("runs")):
            if run.get("name") == best_name:
                return dict(run)
    runs = [row for row in list_of_dicts(comparison.get("runs")) if not row.get("is_baseline")]
    return dict(runs[0]) if runs else {}


def _delta_for_candidate(comparison: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    selected_name = selected.get("name")
    for row in list_of_dicts(comparison.get("baseline_deltas")):
        if row.get("name") == selected_name:
            return dict(row)
    return {}


def _summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    promoted = [item for item in entries if item.get("decision_status") == "promote"]
    review = [item for item in entries if item.get("decision_status") == "review"]
    blocked = [item for item in entries if item.get("decision_status") == "blocked"]
    ready = [item for item in entries if item.get("promotion_readiness") == "ready"]
    regressions = [item for item in entries if _int(item.get("case_regression_count")) > 0]
    flag_regressions = [item for item in entries if _int_or_none(item.get("generation_quality_total_flags_delta")) is not None and int(item.get("generation_quality_total_flags_delta") or 0) > 0]
    best = max(entries, key=lambda item: (_number(item.get("rubric_avg_score_delta")) or -9999.0, _number(item.get("rubric_avg_score")) or -9999.0, str(item.get("name"))), default={})
    model_claims = sorted({str(item.get("model_quality_claim")) for item in entries if item.get("model_quality_claim")})
    return {
        "entry_count": len(entries),
        "promote_count": len(promoted),
        "review_count": len(review),
        "blocked_count": len(blocked),
        "ready_count": len(ready),
        "case_regression_entry_count": len(regressions),
        "generation_quality_flag_regression_entry_count": len(flag_regressions),
        "best_candidate_name": best.get("candidate_name"),
        "best_entry_name": best.get("name"),
        "best_rubric_avg_score_delta": best.get("rubric_avg_score_delta"),
        "model_quality_claim": "mixed" if len(model_claims) > 1 else model_claims[0] if model_claims else "not_claimed",
    }


def _recommendations(summary: dict[str, Any], entries: list[dict[str, Any]]) -> list[str]:
    if not entries:
        return ["Add at least one benchmark scorecard comparison before using benchmark history."]
    items: list[str] = []
    if _int(summary.get("ready_count")):
        items.append("Use ready benchmark entries as candidates for repeated standard-suite checkpoint evaluation.")
    if _int(summary.get("case_regression_entry_count")):
        items.append("Inspect entries with case regressions before promoting any checkpoint as improved.")
    if _int(summary.get("generation_quality_flag_regression_entry_count")):
        items.append("Review generation-quality flag regressions before treating score deltas as clean improvement.")
    if summary.get("model_quality_claim") == "not_claimed":
        items.append("Tiny-smoke history is plumbing evidence; run real benchmark candidates before claiming model quality.")
    else:
        items.append("Keep appending real benchmark comparisons so improvement evidence has history rather than one-off deltas.")
    return items


def _entry_name(comparison: dict[str, Any], names: list[str] | None, index: int) -> str:
    if names is not None:
        return str(names[index])
    source = str(comparison.get("_source_path") or "")
    return Path(source).parent.name or f"benchmark-history-{index + 1}"


def _promotion_readiness(decision_status: str, selected: dict[str, Any], comparison_summary: dict[str, Any]) -> str:
    if decision_status == "promote" and _int(comparison_summary.get("non_comparison_ready_count")) == 0:
        return "ready"
    if decision_status == "blocked":
        return "blocked"
    if selected:
        return "review"
    return "missing-decision"


def _boundary(evidence_kind: str, selected: dict[str, Any], comparison_summary: dict[str, Any]) -> str:
    if evidence_kind == "tiny-smoke":
        return "tiny-smoke-plumbing-evidence"
    if selected.get("eval_suite_comparison_status") not in {None, "pass"}:
        return "eval-suite-not-comparison-ready"
    if _int(comparison_summary.get("non_comparison_ready_count")):
        return "mixed-comparison-readiness"
    return "standard-benchmark-candidate-evidence"


def _resolve_json_path(path: Path, filename: str) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / filename,
                path / "comparison" / filename,
                path / "decision" / filename,
                path / "scorecard-comparison" / filename,
                path / "scorecard-decision" / filename,
                path / "benchmark-scorecard-comparison" / filename,
                path / "benchmark-scorecard-decision" / filename,
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _number(value: Any) -> float | None:
    number = number_or_none(value, float)
    return float(number) if number is not None else None


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


def _int_or_none(value: Any) -> int | None:
    number = number_or_none(value, int)
    return int(number) if number is not None else None


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


__all__ = [
    "build_benchmark_history",
    "load_benchmark_comparison",
    "load_benchmark_decision",
    "render_benchmark_history_html",
    "render_benchmark_history_markdown",
    "write_benchmark_history_csv",
    "write_benchmark_history_html",
    "write_benchmark_history_json",
    "write_benchmark_history_markdown",
    "write_benchmark_history_outputs",
]
