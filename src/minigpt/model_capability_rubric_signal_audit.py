from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from minigpt.model_capability_stall_diagnostic import STALL_JSON_FILENAME
from minigpt.model_capability_token_budget_stability import TOKEN_BUDGET_STABILITY_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, list_of_strs, number_or_none, utc_now


RUBRIC_SIGNAL_AUDIT_JSON_FILENAME = "model_capability_rubric_signal_audit.json"
RUBRIC_SIGNAL_AUDIT_TEXT_FILENAME = "model_capability_rubric_signal_audit.txt"
RUBRIC_SIGNAL_AUDIT_MARKDOWN_FILENAME = "model_capability_rubric_signal_audit.md"
RUBRIC_SIGNAL_AUDIT_HTML_FILENAME = "model_capability_rubric_signal_audit.html"


def locate_token_budget_stability_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TOKEN_BUDGET_STABILITY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def build_model_capability_rubric_signal_audit(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    search_base: str | Path | None = None,
    target_token_cap: int | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base_dir = _base_dir(source_path, search_base)
    seeds = [
        _seed_rubric_signal(row, base_dir=base_dir, target_token_cap=target_token_cap)
        for row in list_of_dicts(stability_report.get("rows"))
    ]
    cases = [_case_with_source(case, seed) for seed in seeds for case in list_of_dicts(seed.get("cases"))]
    issues = _issues(stability_report, seeds, cases)
    status = "pass" if not issues else "fail"
    summary = summarize_rubric_signal(cases, seeds)
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability rubric signal audit",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "rubric_signal_audit_ready" if status == "pass" else "fix_rubric_signal_audit",
        "issue_count": len(issues),
        "issues": issues,
        "source_token_budget_stability": str(source_path) if source_path else None,
        "out_dir": str(Path(out_dir)),
        "target_token_cap": summary.get("target_token_cap"),
        "seed_count": len(seeds),
        "case_count": len(cases),
        "seeds": seeds,
        "summary": summary,
        "cases": cases,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(summary),
            "next_action": _next_action(summary),
        },
    }


def summarize_rubric_signal(cases: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> dict[str, Any]:
    failed_check_counts = _count_values(check for case in cases for check in list_of_strs(case.get("last_failed_checks")))
    missing_term_counts = _count_values(term for case in cases for term in list_of_strs(case.get("last_missing_terms")))
    reason_counts = _count_values(case.get("stall_reason") for case in cases)
    score_deltas = [float(value) for value in (number_or_none(case.get("score_delta")) for case in cases) if value is not None]
    token_caps = sorted({int(cap) for cap in (number_or_none(seed.get("token_cap"), int) for seed in seeds) if cap is not None})
    score_improved = sum(1 for value in score_deltas if value > 0)
    pass_transitions = sum(1 for case in cases if case.get("first_status") != "pass" and case.get("last_status") == "pass")
    return {
        "target_token_cap": token_caps[-1] if token_caps else None,
        "seed_count": len(seeds),
        "diagnostic_success_count": sum(1 for seed in seeds if seed.get("status") == "pass"),
        "case_count": len(cases),
        "persistent_fail_count": sum(1 for case in cases if case.get("first_status") == "fail" and case.get("last_status") == "fail"),
        "pass_transition_count": pass_transitions,
        "score_improved_count": score_improved,
        "score_degraded_count": sum(1 for value in score_deltas if value < 0),
        "score_unchanged_count": sum(1 for value in score_deltas if value == 0),
        "preview_changed_count": sum(1 for case in cases if case.get("preview_changed")),
        "avg_score_delta": _mean(score_deltas),
        "dominant_stall_reasons": reason_counts,
        "dominant_failed_checks": failed_check_counts,
        "dominant_missing_terms": dict(list(missing_term_counts.items())[:12]),
        "cross_seed_failed_checks": _cross_seed_keys(seeds, "dominant_failed_checks"),
        "cross_seed_stall_reasons": _cross_seed_keys(seeds, "dominant_stall_reasons"),
        "decision": _summary_decision(failed_check_counts, reason_counts, score_improved, pass_transitions),
    }


def _seed_rubric_signal(row: dict[str, Any], *, base_dir: Path, target_token_cap: int | None) -> dict[str, Any]:
    probe_path = _resolve_file(row.get("report_path"), base_dir)
    probe = read_json_report(probe_path) if probe_path else {}
    token_row = _select_token_row(list_of_dicts(probe.get("rows")), target_token_cap)
    token_cap = number_or_none(token_row.get("case_token_cap"), int)
    diagnostic_path = _resolve_file(token_row.get("source_diagnostic"), base_dir, filename=STALL_JSON_FILENAME)
    diagnostic = read_json_report(diagnostic_path) if diagnostic_path else {}
    summary = as_dict(diagnostic.get("summary"))
    return {
        "seed": row.get("seed"),
        "token_cap": token_cap,
        "status": "pass" if probe and diagnostic and list_of_dicts(diagnostic.get("cases")) else "fail",
        "probe_path": str(probe_path) if probe_path else None,
        "diagnostic_path": str(diagnostic_path) if diagnostic_path else None,
        "case_count": summary.get("case_count"),
        "score_improved_count": summary.get("score_improved_count"),
        "persistent_fail_count": summary.get("persistent_fail_count"),
        "pass_transition_count": summary.get("pass_transition_count"),
        "preview_changed_count": summary.get("preview_changed_count"),
        "token_budget_or_shape_limit_count": summary.get("token_budget_or_shape_limit_count"),
        "dominant_stall_reasons": as_dict(summary.get("dominant_stall_reasons")),
        "dominant_failed_checks": as_dict(summary.get("dominant_failed_checks")),
        "dominant_missing_terms": as_dict(summary.get("dominant_missing_terms")),
        "cases": list_of_dicts(diagnostic.get("cases")),
    }


def _case_with_source(case: dict[str, Any], seed: dict[str, Any]) -> dict[str, Any]:
    row = dict(case)
    row["token_cap"] = seed.get("token_cap")
    row["source_diagnostic"] = seed.get("diagnostic_path")
    return row


def _select_token_row(rows: list[dict[str, Any]], target_token_cap: int | None) -> dict[str, Any]:
    valid = [row for row in rows if number_or_none(row.get("case_token_cap"), int) is not None]
    if target_token_cap is not None:
        return next((row for row in valid if number_or_none(row.get("case_token_cap"), int) == target_token_cap), {})
    if not valid:
        return {}
    return sorted(valid, key=lambda row: int(number_or_none(row.get("case_token_cap"), int) or 0))[-1]


def _issues(stability_report: dict[str, Any], seeds: list[dict[str, Any]], cases: list[dict[str, Any]]) -> list[str]:
    issues = []
    if not stability_report:
        issues.append("source token budget stability report is missing or invalid")
    if not seeds:
        issues.append("no seed probe rows found")
    for seed in seeds:
        if seed.get("status") != "pass":
            issues.append(f"seed-{seed.get('seed')} rubric signal inputs are incomplete")
    if not cases:
        issues.append("no stall diagnostic cases found for rubric signal audit")
    return issues


def _summary_decision(
    failed_checks: dict[str, int],
    reasons: dict[str, int],
    score_improved: int,
    pass_transitions: int,
) -> str:
    if score_improved > 0 or pass_transitions > 0:
        return "some_rubric_progress_visible"
    if failed_checks.get("must_include", 0) >= max(1, sum(failed_checks.values()) // 2):
        return "rubric_required_terms_dominate_flat_scores"
    if reasons.get("generation_unchanged", 0) >= max(1, sum(reasons.values()) // 2):
        return "generation_unchanged_dominate_flat_scores"
    if reasons.get("token_budget_or_shape_limit", 0) > 0:
        return "token_shape_still_blocks_some_cases"
    return "rubric_signal_needs_manual_review"


def _interpretation_reason(summary: dict[str, Any]) -> str:
    decision = summary.get("decision")
    if decision == "rubric_required_terms_dominate_flat_scores":
        return "After cap-12 relief, flat scores are dominated by required-term rubric failures rather than token budget alone."
    if decision == "generation_unchanged_dominate_flat_scores":
        return "After cap-12 relief, many prompt generations are unchanged across tiny training rungs."
    if decision == "some_rubric_progress_visible":
        return "At least one case now shows score or pass-transition progress, but the sample is still tiny."
    if decision == "token_shape_still_blocks_some_cases":
        return "Some token or task-shape blockers remain even at the larger evaluation budget."
    return "The audit found rubric blockers but cannot rank a single dominant cause confidently."


def _next_action(summary: dict[str, Any]) -> str:
    if summary.get("decision") == "rubric_required_terms_dominate_flat_scores":
        return "inspect required terms and tiny corpus coverage before increasing model size"
    if summary.get("decision") == "generation_unchanged_dominate_flat_scores":
        return "compare generated previews and training data before spending a larger training budget"
    if summary.get("decision") == "some_rubric_progress_visible":
        return "repeat the progressing cases with more seeds and a slightly larger training budget"
    return "review remaining case-level failures before changing model or benchmark settings"


def _resolve_file(value: Any, base_dir: Path, *, filename: str | None = None) -> Path | None:
    if not value:
        return None
    raw = Path(str(value).replace("\\", "/"))
    candidates = [raw, base_dir / raw, Path.cwd() / raw]
    for anchor in (base_dir, *base_dir.parents, Path.cwd()):
        candidates.append(anchor / raw)
    expanded = []
    for candidate in candidates:
        expanded.append(candidate)
        if filename:
            expanded.append(candidate / filename)
    for candidate in expanded:
        if candidate.is_file():
            return candidate
    return None


def _base_dir(source_path: str | Path | None, search_base: str | Path | None) -> Path:
    if search_base is not None:
        return Path(search_base)
    if source_path is not None:
        return Path(source_path).parent
    return Path.cwd()


def _cross_seed_keys(seeds: list[dict[str, Any]], key: str) -> list[str]:
    key_sets = [set(as_dict(seed.get(key)).keys()) for seed in seeds if as_dict(seed.get(key))]
    if not key_sets:
        return []
    return sorted(set.intersection(*key_sets))


def _count_values(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value).strip()
        if key:
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)
