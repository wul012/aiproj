from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from minigpt.report_utils import (
    as_dict,
    list_of_dicts,
    list_of_strs,
    number_or_none,
    resolve_archived_reference_path,
    utc_now,
)


STALL_JSON_FILENAME = "model_capability_stall_diagnostic.json"
STALL_TEXT_FILENAME = "model_capability_stall_diagnostic.txt"
STALL_MARKDOWN_FILENAME = "model_capability_stall_diagnostic.md"
STALL_HTML_FILENAME = "model_capability_stall_diagnostic.html"


def locate_stability_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / "model_capability_ladder_stability.json"
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def build_model_capability_stall_diagnostic(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    search_base: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base_dir = _base_dir(source_path, search_base)
    seed_rows = [_seed_diagnostic(row, base_dir=base_dir) for row in list_of_dicts(stability_report.get("rows"))]
    case_rows = [case for seed in seed_rows for case in list_of_dicts(seed.get("cases"))]
    issue_list = _issues(stability_report, seed_rows, case_rows)
    status = "pass" if not issue_list else "fail"
    summary = summarize_stall_cases(case_rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability stall diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "capability_stall_diagnostic_ready" if status == "pass" else "fix_capability_stall_diagnostic",
        "issue_count": len(issue_list),
        "issues": issue_list,
        "source_stability_report": str(source_path) if source_path else None,
        "out_dir": str(Path(out_dir)),
        "seed_count": len(seed_rows),
        "case_count": len(case_rows),
        "summary": summary,
        "seeds": seed_rows,
        "cases": case_rows,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(summary),
            "next_action": _next_action(summary),
        },
    }


def summarize_stall_cases(case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    score_deltas = [float(value) for value in (_score_delta(row) for row in case_rows) if value is not None]
    improved = sum(1 for value in score_deltas if value > 0)
    degraded = sum(1 for value in score_deltas if value < 0)
    unchanged = sum(1 for value in score_deltas if value == 0)
    reason_counts = _count_values(row.get("stall_reason") for row in case_rows)
    failed_check_counts = _count_values(check for row in case_rows for check in list_of_strs(row.get("last_failed_checks")))
    missing_term_counts = _count_values(term for row in case_rows for term in list_of_strs(row.get("last_missing_terms")))
    return {
        "case_count": len(case_rows),
        "score_improved_count": improved,
        "score_degraded_count": degraded,
        "score_unchanged_count": unchanged,
        "persistent_fail_count": sum(1 for row in case_rows if row.get("first_status") == "fail" and row.get("last_status") == "fail"),
        "pass_transition_count": sum(1 for row in case_rows if row.get("first_status") != "pass" and row.get("last_status") == "pass"),
        "preview_changed_count": sum(1 for row in case_rows if row.get("preview_changed")),
        "token_budget_or_shape_limit_count": reason_counts.get("token_budget_or_shape_limit", 0),
        "avg_score_delta": _mean(score_deltas),
        "dominant_stall_reasons": reason_counts,
        "dominant_failed_checks": failed_check_counts,
        "dominant_missing_terms": dict(list(missing_term_counts.items())[:10]),
        "decision": _summary_decision(improved, degraded, reason_counts),
    }


def _seed_diagnostic(row: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    report_path = _resolve_file(row.get("report_path"), base_dir)
    ladder = read_json_report(report_path) if report_path else {}
    ladder_rows = sorted(list_of_dicts(ladder.get("rows")), key=lambda item: int(item.get("max_iters") or 0))
    first = ladder_rows[0] if ladder_rows else {}
    last = ladder_rows[-1] if ladder_rows else {}
    first_bundle = _load_rung_bundle(first, base_dir=base_dir)
    last_bundle = _load_rung_bundle(last, base_dir=base_dir)
    cases = _case_rows(row, first, last, first_bundle, last_bundle)
    return {
        "seed": row.get("seed"),
        "status": "pass" if report_path and ladder and first_bundle.get("scorecard") and last_bundle.get("scorecard") else "fail",
        "report_path": str(report_path) if report_path else None,
        "first_max_iters": first.get("max_iters"),
        "last_max_iters": last.get("max_iters"),
        "best_val_loss_delta": row.get("best_val_loss_delta"),
        "score_delta": row.get("score_delta"),
        "generation_flags_delta": row.get("generation_flags_delta"),
        "case_count": len(cases),
        "cases": cases,
    }


def _load_rung_bundle(row: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    run_dir = _resolve_dir(row.get("run_dir"), base_dir)
    scorecard = read_json_report(run_dir / "benchmark-scorecard" / "benchmark_scorecard.json") if run_dir else {}
    generation = read_json_report(run_dir / "generation-quality" / "generation_quality.json") if run_dir else {}
    return {"run_dir": str(run_dir) if run_dir else None, "scorecard": scorecard, "generation": generation}


def _case_rows(
    seed_row: dict[str, Any],
    first_rung: dict[str, Any],
    last_rung: dict[str, Any],
    first_bundle: dict[str, Any],
    last_bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    first_cases = _rubric_cases(first_bundle.get("scorecard"))
    last_cases = _rubric_cases(last_bundle.get("scorecard"))
    first_gen = _generation_cases(first_bundle.get("generation"))
    last_gen = _generation_cases(last_bundle.get("generation"))
    names = sorted(set(first_cases) | set(last_cases))
    return [
        _case_row(
            seed_row,
            first_rung,
            last_rung,
            first_cases.get(name, {}),
            last_cases.get(name, {}),
            first_gen.get(name, {}),
            last_gen.get(name, {}),
        )
        for name in names
    ]


def _case_row(
    seed_row: dict[str, Any],
    first_rung: dict[str, Any],
    last_rung: dict[str, Any],
    first_case: dict[str, Any],
    last_case: dict[str, Any],
    first_generation: dict[str, Any],
    last_generation: dict[str, Any],
) -> dict[str, Any]:
    score_delta = _delta(last_case.get("score"), first_case.get("score"))
    first_preview = first_generation.get("continuation_preview")
    last_preview = last_generation.get("continuation_preview")
    preview_changed = first_preview != last_preview
    fixed_checks = sorted(set(list_of_strs(first_case.get("failed_checks"))) - set(list_of_strs(last_case.get("failed_checks"))))
    new_checks = sorted(set(list_of_strs(last_case.get("failed_checks"))) - set(list_of_strs(first_case.get("failed_checks"))))
    return {
        "seed": seed_row.get("seed"),
        "case": first_case.get("name") or last_case.get("name"),
        "task_type": first_case.get("task_type") or last_case.get("task_type"),
        "difficulty": first_case.get("difficulty") or last_case.get("difficulty"),
        "first_max_iters": first_rung.get("max_iters"),
        "last_max_iters": last_rung.get("max_iters"),
        "first_status": first_case.get("status"),
        "last_status": last_case.get("status"),
        "first_score": number_or_none(first_case.get("score")),
        "last_score": number_or_none(last_case.get("score")),
        "score_delta": score_delta,
        "first_failed_checks": list_of_strs(first_case.get("failed_checks")),
        "last_failed_checks": list_of_strs(last_case.get("failed_checks")),
        "fixed_failed_checks": fixed_checks,
        "new_failed_checks": new_checks,
        "first_missing_terms": list_of_strs(first_case.get("missing_terms")),
        "last_missing_terms": list_of_strs(last_case.get("missing_terms")),
        "first_preview": first_preview,
        "last_preview": last_preview,
        "preview_changed": preview_changed,
        "first_flag_count": number_or_none(first_generation.get("flag_count"), int),
        "last_flag_count": number_or_none(last_generation.get("flag_count"), int),
        "flag_delta": _delta(last_generation.get("flag_count"), first_generation.get("flag_count")),
        "stall_reason": _stall_reason(last_case, score_delta, preview_changed),
    }


def _rubric_cases(scorecard: Any) -> dict[str, dict[str, Any]]:
    cases = list_of_dicts(as_dict(as_dict(scorecard).get("rubric_scores")).get("cases"))
    return {str(case.get("name")): case for case in cases if case.get("name")}


def _generation_cases(report: Any) -> dict[str, dict[str, Any]]:
    cases = list_of_dicts(as_dict(report).get("cases"))
    return {str(case.get("name")): case for case in cases if case.get("name")}


def _stall_reason(last_case: dict[str, Any], score_delta: float | None, preview_changed: bool) -> str:
    failed = set(list_of_strs(last_case.get("failed_checks")))
    if last_case.get("status") == "pass":
        return "case_passed"
    if "length_bounds" in failed or "task_shape" in failed:
        return "token_budget_or_shape_limit"
    if score_delta is not None and score_delta > 0:
        return "partial_rubric_progress"
    if not preview_changed:
        return "generation_unchanged"
    if list_of_strs(last_case.get("missing_terms")):
        return "required_terms_missing"
    return "rubric_failure_persists"


def _issues(stability_report: dict[str, Any], seed_rows: list[dict[str, Any]], case_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not stability_report:
        issues.append("source stability report is missing or invalid")
    if not seed_rows:
        issues.append("no seed ladder rows found")
    for row in seed_rows:
        if row.get("status") != "pass":
            issues.append(f"seed-{row.get('seed')} diagnostic inputs are incomplete")
    if not case_rows:
        issues.append("no rubric cases found for first/last ladder comparison")
    return issues


def _summary_decision(improved: int, degraded: int, reason_counts: dict[str, int]) -> str:
    if improved > degraded:
        return "partial_eval_progress_detected"
    if reason_counts.get("token_budget_or_shape_limit", 0) > 0:
        return "token_budget_or_shape_limits_block_eval_signal"
    return "capability_stall_explained"


def _interpretation_reason(summary: dict[str, Any]) -> str:
    if summary.get("decision") == "token_budget_or_shape_limits_block_eval_signal":
        return "The tiny ladder lowers loss, but the prompt-level rubric remains blocked by short outputs and task-shape failures."
    if summary.get("decision") == "partial_eval_progress_detected":
        return "Some prompt-level rubric scores moved, but the evidence is still too small for a model-quality claim."
    return "The diagnostic explains the current stall without claiming model quality improvement."


def _next_action(summary: dict[str, Any]) -> str:
    if summary.get("token_budget_or_shape_limit_count", 0) > 0:
        return "run a longer-token capability ladder before interpreting rubric scores as model ability"
    if summary.get("score_improved_count", 0) > summary.get("score_degraded_count", 0):
        return "repeat the improved cases with more seeds and a larger training budget"
    return "inspect required-term failures and decide whether data, token budget, or rubric design is the limiting factor"


def _base_dir(source_path: str | Path | None, search_base: str | Path | None) -> Path:
    if search_base is not None:
        return Path(search_base)
    if source_path is not None:
        return Path(source_path).parent
    return Path.cwd()


def _resolve_file(value: Any, base_dir: Path) -> Path | None:
    resolved = resolve_archived_reference_path(value, base_dir)
    if resolved and resolved.is_file():
        return resolved
    if value:
        candidate = Path.cwd() / Path(str(value).replace("\\", "/"))
        if candidate.is_file():
            return candidate
    return resolved if resolved and resolved.is_file() else None


def _resolve_dir(value: Any, base_dir: Path) -> Path | None:
    if not value:
        return None
    candidate = Path(str(value).replace("\\", "/"))
    if candidate.is_dir() or candidate.is_absolute():
        return candidate
    for anchor in (base_dir, *base_dir.parents, Path.cwd()):
        based = anchor / candidate
        if based.is_dir():
            return based
    return candidate


def _delta(candidate: Any, baseline: Any) -> float | None:
    left = number_or_none(candidate)
    right = number_or_none(baseline)
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 4)


def _score_delta(row: dict[str, Any]) -> float | None:
    return number_or_none(row.get("score_delta"))


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _count_values(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value).strip()
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
