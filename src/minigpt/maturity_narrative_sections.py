from __future__ import annotations

from pathlib import Path
from typing import Any


def build_maturity_narrative_sections(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "key": "maturity",
            "title": "Project Maturity",
            "status": summary.get("maturity_status") or "missing",
            "claim": f"MiniGPT is at v{summary.get('current_version')} with maturity level {summary.get('average_maturity_level')}.",
            "evidence": "maturity_summary.json captures version coverage, archives, capability matrix, registry context, request history, and release readiness trend.",
            "boundary": "This is a learning-engineering maturity view, not a claim of production model capability.",
            "next_step": "Turn the strongest evidence into a shorter release portfolio narrative.",
        },
        {
            "key": "release_quality",
            "title": "Release Quality Trend",
            "status": summary.get("release_readiness_trend_status") or "missing",
            "claim": _release_claim(summary),
            "evidence": "Registry-level release readiness comparison deltas are carried into maturity summary and then into this narrative.",
            "boundary": "The trend explains release evidence quality; it does not prove generated text quality.",
            "next_step": "Review regressions before release handoff; preserve improvement evidence when the trend is positive.",
        },
        {
            "key": "serving_stability",
            "title": "Local Serving Stability",
            "status": summary.get("request_history_status") or "missing",
            "claim": _request_claim(summary),
            "evidence": "request_history_summary.json records request counts, timeout/bad-request/error rates, endpoints, checkpoints, and recent requests.",
            "boundary": "Request history is local playground evidence and may not represent external traffic.",
            "next_step": "Keep request logs small, reproducible, and tied to checkpoint/model-info evidence.",
        },
        {
            "key": "benchmark_quality",
            "title": "Benchmark Quality",
            "status": _status_from_counts(summary.get("benchmark_status_counts")),
            "claim": _benchmark_claim(summary),
            "evidence": "Benchmark scorecards combine eval coverage, generation quality, rubric correctness, pair consistency, and evidence completeness.",
            "boundary": "Scorecards are deterministic review aids, not a substitute for larger benchmark suites.",
            "next_step": "Expand fixed prompts and compare larger or fine-tuned models when data size grows.",
        },
        {
            "key": "benchmark_promotion",
            "title": "Benchmark Promotion Decision",
            "status": _status_from_counts(summary.get("benchmark_decision_status_counts")),
            "claim": _benchmark_decision_claim(summary),
            "evidence": "Benchmark scorecard decisions consume cross-run scorecard comparison deltas, case regressions, and generation-quality flag taxonomy shifts.",
            "boundary": "A promote decision means benchmark evidence can advance; it is not a production release approval.",
            "next_step": "Keep promoted scorecards tied to their raw comparison and generation-quality reports before claiming model improvement.",
        },
        {
            "key": "data_governance",
            "title": "Data Governance",
            "status": _status_from_counts(summary.get("dataset_status_counts")),
            "claim": _dataset_claim(summary),
            "evidence": "Dataset cards summarize dataset identity, provenance, quality status, warnings, artifacts, intended use, and limitations.",
            "boundary": "Dataset cards still require human review for licenses, consent, and domain fit.",
            "next_step": "Attach dataset cards to every meaningful training corpus before larger experiments.",
        },
        {
            "key": "portfolio_boundary",
            "title": "Portfolio Boundary",
            "status": summary.get("portfolio_status"),
            "claim": _portfolio_claim(summary),
            "evidence": "The narrative combines maturity, release trend, serving stability, benchmark scorecards, and dataset cards into one review surface.",
            "boundary": "The project remains a MiniGPT-from-scratch learning artifact, not a production LLM.",
            "next_step": "Use this narrative as the front door for demos, then link to detailed JSON/HTML evidence.",
        },
    ]


def build_maturity_narrative_evidence_matrix(
    maturity_path: Path,
    registry_path: Path,
    request_path: Path,
    scorecard_paths: list[Path],
    scorecard_decision_paths: list[Path],
    dataset_card_paths: list[Path],
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        _evidence("maturity", "project maturity", maturity_path, sections[0]),
        _evidence("release quality", "release readiness trend", registry_path, sections[1]),
        _evidence("serving", "request history stability", request_path, sections[2]),
    ]
    for path in scorecard_paths:
        rows.append(_evidence("benchmark", "benchmark scorecard", path, sections[3]))
    for path in scorecard_decision_paths:
        rows.append(_evidence("benchmark", "scorecard promotion decision", path, sections[4]))
    for path in dataset_card_paths:
        rows.append(_evidence("dataset", "dataset card", path, sections[5]))
    return rows


def _evidence(area: str, signal: str, path: Path, section: dict[str, Any]) -> dict[str, Any]:
    return {
        "area": area,
        "status": section.get("status"),
        "path": str(path),
        "exists": path.exists(),
        "signal": signal,
        "note": section.get("claim"),
    }


def _status_from_counts(counts: Any) -> str:
    values = counts if isinstance(counts, dict) else {}
    if not values:
        return "missing"
    if int(values.get("fail") or 0) > 0 or int(values.get("blocked") or 0) > 0:
        return "fail"
    if int(values.get("warn") or 0) > 0 or int(values.get("review") or 0) > 0:
        return "warn"
    if int(values.get("pass") or 0) > 0 or int(values.get("ready") or 0) > 0 or int(values.get("promote") or 0) > 0:
        return "pass"
    return sorted(values)[0]


def _release_claim(summary: dict[str, Any]) -> str:
    return (
        f"Release readiness trend is {summary.get('release_readiness_trend_status') or 'missing'} "
        f"with {summary.get('release_readiness_regressed_count') or 0} regression(s) and "
        f"{summary.get('release_readiness_improved_count') or 0} improvement(s)."
    )


def _request_claim(summary: dict[str, Any]) -> str:
    return (
        f"Request history status is {summary.get('request_history_status') or 'missing'} "
        f"across {summary.get('request_history_records') or 0} local inference records."
    )


def _benchmark_claim(summary: dict[str, Any]) -> str:
    return (
        f"{summary.get('benchmark_scorecard_count')} benchmark scorecard(s) are available; "
        f"average score is {summary.get('benchmark_avg_score') or 'missing'} and weakest case is "
        f"{summary.get('benchmark_weakest_case') or 'missing'}."
    )


def _benchmark_decision_claim(summary: dict[str, Any]) -> str:
    return (
        f"{summary.get('benchmark_decision_count')} scorecard decision report(s) are available; "
        f"selected run is {summary.get('benchmark_decision_selected_run') or 'missing'} with generation flag delta "
        f"{summary.get('benchmark_decision_selected_flag_delta') if summary.get('benchmark_decision_selected_flag_delta') is not None else 'missing'}."
    )


def _dataset_claim(summary: dict[str, Any]) -> str:
    return (
        f"{summary.get('dataset_card_count')} dataset card(s) are available with "
        f"{summary.get('dataset_warning_count') or 0} warning(s)."
    )


def _portfolio_claim(summary: dict[str, Any]) -> str:
    return f"Portfolio status is {summary.get('portfolio_status')} after combining release, serving, benchmark, data, and maturity evidence."


__all__ = [
    "build_maturity_narrative_evidence_matrix",
    "build_maturity_narrative_sections",
]
