from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    number_or_default,
    number_or_none,
    string_list as _string_list,
    utc_now,
)
from minigpt.benchmark_scorecard_decision_artifacts import (
    render_benchmark_scorecard_decision_html,
    render_benchmark_scorecard_decision_markdown,
    write_benchmark_scorecard_decision_csv,
    write_benchmark_scorecard_decision_html,
    write_benchmark_scorecard_decision_json,
    write_benchmark_scorecard_decision_markdown,
    write_benchmark_scorecard_decision_outputs,
    write_benchmark_scorecard_remediation_csv,
)


BLOCKER_CATEGORY_PRIORITY = {
    "threshold": 60,
    "missing_rubric": 50,
    "rubric_regression": 40,
    "overall_regression": 30,
    "baseline_candidate": 20,
    "other_blocker": 10,
}

REVIEW_CATEGORY_PRIORITY = {
    "suite_design_not_ready": 65,
    "eval_suite_not_ready": 60,
    "rubric_fail_regression": 50,
    "generation_quality_flag_regression": 40,
    "case_regression": 30,
    "generation_quality_flag_shift": 20,
    "generation_quality_case_shift": 10,
    "other_review": 0,
}

BLOCKER_REMEDIATION_ACTIONS = {
    "threshold": "Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change.",
    "missing_rubric": "Regenerate the benchmark scorecard with rubric outputs before making a promotion decision.",
    "rubric_regression": "Inspect rubric-regressed cases against the baseline and fix task correctness before promotion.",
    "overall_regression": "Review the overall score components and keep the baseline unless the regression is understood.",
    "baseline_candidate": "Keep the baseline row as reference evidence, not as a promotable candidate.",
    "other_blocker": "Inspect uncategorized blocker text and add a stable category if it recurs.",
}

REVIEW_REMEDIATION_ACTIONS = {
    "suite_design_not_ready": "Make the prompt-suite design comparison-ready before treating this decision as clean promotion evidence.",
    "eval_suite_not_ready": "Make the eval suite comparison-ready before treating this decision as clean promotion evidence.",
    "rubric_fail_regression": "Inspect newly failing rubric cases and decide whether the run needs retraining or prompt/data fixes.",
    "generation_quality_flag_regression": "Open the generation-quality report and inspect the prompts that increased flags.",
    "case_regression": "Review case-level deltas to distinguish wording drift from true task failure.",
    "generation_quality_flag_shift": "Compare dominant generation-quality flags to see whether the failure mode changed materially.",
    "generation_quality_case_shift": "Inspect the new worst generation-quality case before promoting the candidate.",
    "other_review": "Inspect uncategorized review text and add a stable category if it recurs.",
}

BLOCKER_REMEDIATION_METADATA = {
    "threshold": ("raise_candidate_rubric_or_change_policy", "blocker", "model-eval", ["benchmark_scorecard_decision", "benchmark_scorecard"]),
    "missing_rubric": ("regenerate_scorecard_rubric", "blocker", "eval-artifact", ["benchmark_scorecard"]),
    "rubric_regression": ("inspect_rubric_regressions", "blocker", "model-eval", ["benchmark_scorecard_comparison", "benchmark_scorecard"]),
    "overall_regression": ("review_overall_score_components", "blocker", "model-eval", ["benchmark_scorecard_comparison"]),
    "baseline_candidate": ("keep_baseline_as_reference", "info", "release-evidence", ["benchmark_scorecard_comparison"]),
    "other_blocker": ("inspect_uncategorized_blocker", "blocker", "decision-maintenance", ["benchmark_scorecard_decision"]),
}

REVIEW_REMEDIATION_METADATA = {
    "suite_design_not_ready": ("make_suite_design_comparison_ready", "review", "eval-artifact", ["eval_suite", "benchmark_scorecard", "benchmark_scorecard_comparison"]),
    "eval_suite_not_ready": ("make_eval_suite_comparison_ready", "review", "eval-artifact", ["eval_suite", "benchmark_scorecard_comparison"]),
    "rubric_fail_regression": ("inspect_rubric_failures", "review", "model-eval", ["benchmark_scorecard", "eval_suite"]),
    "generation_quality_flag_regression": ("inspect_generation_quality_flags", "review", "generation-quality", ["generation_quality"]),
    "case_regression": ("inspect_case_deltas", "review", "model-eval", ["benchmark_scorecard_comparison"]),
    "generation_quality_flag_shift": ("review_generation_quality_flag_shift", "review", "generation-quality", ["generation_quality"]),
    "generation_quality_case_shift": ("review_generation_quality_worst_case", "review", "generation-quality", ["generation_quality"]),
    "other_review": ("inspect_uncategorized_review", "review", "decision-maintenance", ["benchmark_scorecard_decision"]),
}


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


def _case_delta_counts(comparison: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in _list_of_dicts(comparison.get("case_deltas")):
        if row.get("is_baseline"):
            continue
        name = str(row.get("run_name") or "")
        bucket = counts.setdefault(name, {"regressed": 0, "improved": 0})
        if row.get("relation") == "regressed":
            bucket["regressed"] += 1
        elif row.get("relation") == "improved":
            bucket["improved"] += 1
    return counts


def _evaluate_run(
    run: dict[str, Any],
    delta: dict[str, Any],
    case_counts: dict[str, dict[str, int]],
    min_rubric_score: float,
) -> dict[str, Any]:
    name = run.get("name")
    is_baseline = bool(delta.get("is_baseline"))
    blockers: list[str] = []
    review_items: list[str] = []
    rubric_score = _number(run.get("rubric_avg_score"))
    if is_baseline:
        blockers.append("baseline run is not a promotion candidate")
    if rubric_score is None:
        blockers.append("rubric_avg_score is missing")
    elif rubric_score < float(min_rubric_score):
        blockers.append(f"rubric_avg_score below {float(min_rubric_score):.1f}")
    if delta.get("rubric_relation") == "regressed":
        blockers.append("rubric score regressed from baseline")
    if delta.get("overall_relation") == "regressed":
        blockers.append("overall score regressed from baseline")
    if _int(delta.get("rubric_fail_count_delta")) > 0:
        review_items.append("rubric fail count increased")
    flag_delta = _int_or_none(delta.get("generation_quality_total_flags_delta"))
    if flag_delta is not None and flag_delta > 0:
        review_items.append(f"generation-quality flags increased by {flag_delta}")
    if delta.get("generation_quality_dominant_flag_changed"):
        review_items.append("dominant generation-quality flag changed")
    if delta.get("generation_quality_worst_case_changed"):
        review_items.append("worst generation-quality case changed")
    eval_comparison_status = run.get("eval_suite_comparison_status")
    if eval_comparison_status not in {None, "pass"}:
        review_items.append(f"eval-suite comparison readiness is {eval_comparison_status}")
    suite_design_comparison_status = run.get("eval_suite_design_comparison_status")
    if suite_design_comparison_status not in {None, "pass"}:
        review_items.append(f"suite-design comparison readiness is {suite_design_comparison_status}")
    counts = case_counts.get(str(name), {"regressed": 0, "improved": 0})
    if counts.get("regressed"):
        review_items.append(f"{counts.get('regressed')} case regression(s)")
    blocker_categories = _categorize_blockers(blockers)
    review_categories = _categorize_review_items(review_items)
    relation = "baseline" if is_baseline else "blocked" if blockers else "review" if review_items else "promote"
    return {
        "name": name,
        "source_path": run.get("source_path"),
        "run_dir": run.get("run_dir"),
        "is_baseline": is_baseline,
        "decision_relation": relation,
        "overall_score": _number(run.get("overall_score")),
        "rubric_avg_score": rubric_score,
        "overall_score_delta": _number(delta.get("overall_score_delta")),
        "rubric_avg_score_delta": _number(delta.get("rubric_avg_score_delta")),
        "generation_quality_total_flags": _int_or_none(run.get("generation_quality_total_flags")),
        "generation_quality_total_flags_delta": flag_delta,
        "generation_quality_flag_relation": delta.get("generation_quality_flag_relation"),
        "generation_quality_dominant_flag": run.get("generation_quality_dominant_flag"),
        "generation_quality_worst_case": run.get("generation_quality_worst_case"),
        "eval_suite_coverage_status": run.get("eval_suite_coverage_status"),
        "eval_suite_comparison_status": eval_comparison_status,
        "eval_suite_design_coverage_status": run.get("eval_suite_design_coverage_status"),
        "eval_suite_design_comparison_status": suite_design_comparison_status,
        "eval_suite_design_duplicate_seed_count": _int_or_none(run.get("eval_suite_design_duplicate_seed_count")),
        "eval_suite_design_expected_behavior_complete": run.get("eval_suite_design_expected_behavior_complete"),
        "case_regression_count": int(counts.get("regressed") or 0),
        "case_improvement_count": int(counts.get("improved") or 0),
        "blockers": blockers,
        "review_items": review_items,
        "blocker_categories": blocker_categories,
        "review_categories": review_categories,
    }


def _select_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    return dict(
        max(
            candidates,
            key=lambda row: (
                _number(row.get("rubric_avg_score")) or 0.0,
                _number(row.get("overall_score")) or 0.0,
                -(_int_or_none(row.get("generation_quality_total_flags")) or 0),
                str(row.get("name") or ""),
            ),
        )
    )


def _decision_status(selected: dict[str, Any] | None) -> str:
    if not selected:
        return "blocked"
    if selected.get("review_items"):
        return "review"
    return "promote"


def _recommended_action(status: str) -> str:
    return {
        "promote": "promote_selected_scorecard",
        "review": "review_generation_flags_and_case_deltas",
        "blocked": "keep_baseline_or_fix_candidate",
    }.get(status, "review_generation_flags_and_case_deltas")


def _summary(
    comparison: dict[str, Any],
    evaluations: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    clean_candidates: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    decision_status: str,
    min_rubric_score: float,
) -> dict[str, Any]:
    nonbaseline = [row for row in evaluations if not row.get("is_baseline")]
    comparison_summary = _dict(comparison.get("summary"))
    non_ready = [row for row in nonbaseline if row.get("eval_suite_comparison_status") not in {None, "pass"}]
    non_design_ready = [row for row in nonbaseline if row.get("eval_suite_design_comparison_status") not in {None, "pass"}]
    threshold_blocks = _threshold_blocks(nonbaseline, min_rubric_score)
    threshold_profile = _threshold_profile(threshold_blocks)
    blocker_category_counts = _category_counts(nonbaseline, "blocker_categories")
    review_category_counts = _category_counts(nonbaseline, "review_categories")
    return {
        "decision_status": decision_status,
        "comparison_scorecard_count": comparison.get("scorecard_count"),
        "candidate_count": len(candidates),
        "clean_candidate_count": len(clean_candidates),
        "review_candidate_count": sum(1 for row in nonbaseline if row.get("review_items") and not row.get("blockers")),
        "blocked_candidate_count": sum(1 for row in nonbaseline if row.get("blockers")),
        "non_comparison_ready_candidate_count": len(non_ready),
        "non_comparison_ready_candidates": [row.get("name") for row in non_ready],
        "non_design_comparison_ready_candidate_count": len(non_design_ready),
        "non_design_comparison_ready_candidates": [row.get("name") for row in non_design_ready],
        "selected_name": None if selected is None else selected.get("name"),
        "selected_relation": None if selected is None else selected.get("decision_relation"),
        "selected_rubric_avg_score": None if selected is None else selected.get("rubric_avg_score"),
        "selected_generation_quality_total_flags_delta": None if selected is None else selected.get("generation_quality_total_flags_delta"),
        "comparison_case_regression_count": comparison_summary.get("case_regression_count"),
        "comparison_non_comparison_ready_count": comparison_summary.get("non_comparison_ready_count"),
        "comparison_non_comparison_ready_runs": comparison_summary.get("non_comparison_ready_runs")
        if isinstance(comparison_summary.get("non_comparison_ready_runs"), list)
        else [],
        "comparison_non_design_comparison_ready_count": comparison_summary.get("non_design_comparison_ready_count"),
        "comparison_non_design_comparison_ready_runs": comparison_summary.get("non_design_comparison_ready_runs")
        if isinstance(comparison_summary.get("non_design_comparison_ready_runs"), list)
        else [],
        "comparison_baseline_eval_suite_comparison_status": comparison_summary.get("baseline_eval_suite_comparison_status"),
        "comparison_baseline_eval_suite_design_comparison_status": comparison_summary.get(
            "baseline_eval_suite_design_comparison_status"
        ),
        "comparison_design_comparison_changed_count": comparison_summary.get("design_comparison_changed_count"),
        "comparison_generation_quality_flag_regression_count": comparison_summary.get("generation_quality_flag_regression_count"),
        "comparison_generation_quality_dominant_flag_change_count": comparison_summary.get("generation_quality_dominant_flag_change_count"),
        "blocker_category_counts": blocker_category_counts,
        "dominant_blocker_category": _dominant_category(blocker_category_counts, BLOCKER_CATEGORY_PRIORITY),
        "review_category_counts": review_category_counts,
        "dominant_review_category": _dominant_category(review_category_counts, REVIEW_CATEGORY_PRIORITY),
        "first_threshold_blocked_candidate": threshold_profile.get("first_threshold_blocked_candidate"),
        "first_threshold_blocker": threshold_profile.get("first_threshold_blocker"),
        "first_threshold_rubric_score": threshold_profile.get("first_threshold_rubric_score"),
        "first_threshold_min_rubric_score": threshold_profile.get("first_threshold_min_rubric_score"),
        "first_threshold_margin": threshold_profile.get("first_threshold_margin"),
        "threshold_blocked_candidate_count": threshold_profile.get("threshold_blocked_candidate_count"),
        "threshold_blocked_candidate_names": threshold_profile.get("threshold_blocked_candidate_names"),
        "threshold_closest_candidate": threshold_profile.get("threshold_closest_candidate"),
        "threshold_closest_margin": threshold_profile.get("threshold_closest_margin"),
        "threshold_largest_gap_candidate": threshold_profile.get("threshold_largest_gap_candidate"),
        "threshold_largest_gap_margin": threshold_profile.get("threshold_largest_gap_margin"),
    }


def _categorize_blockers(blockers: list[str]) -> list[str]:
    categories = []
    for blocker in blockers:
        text = str(blocker)
        if text == "baseline run is not a promotion candidate":
            categories.append("baseline_candidate")
        elif text == "rubric_avg_score is missing":
            categories.append("missing_rubric")
        elif text.startswith("rubric_avg_score below"):
            categories.append("threshold")
        elif text == "rubric score regressed from baseline":
            categories.append("rubric_regression")
        elif text == "overall score regressed from baseline":
            categories.append("overall_regression")
        else:
            categories.append("other_blocker")
    return categories


def _categorize_review_items(review_items: list[str]) -> list[str]:
    categories = []
    for item in review_items:
        text = str(item)
        if text == "rubric fail count increased":
            categories.append("rubric_fail_regression")
        elif text.startswith("generation-quality flags increased"):
            categories.append("generation_quality_flag_regression")
        elif text == "dominant generation-quality flag changed":
            categories.append("generation_quality_flag_shift")
        elif text == "worst generation-quality case changed":
            categories.append("generation_quality_case_shift")
        elif text.startswith("eval-suite comparison readiness is"):
            categories.append("eval_suite_not_ready")
        elif text.startswith("suite-design comparison readiness is"):
            categories.append("suite_design_not_ready")
        elif text.endswith("case regression(s)"):
            categories.append("case_regression")
        else:
            categories.append("other_review")
    return categories


def _category_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        values = row.get(key)
        if not isinstance(values, list):
            continue
        for value in values:
            category = str(value)
            counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def _dominant_category(counts: dict[str, int], priority: dict[str, int]) -> str | None:
    if not counts:
        return None
    return max(counts.items(), key=lambda item: (item[1], priority.get(item[0], -1), item[0]))[0]


def _remediation_plan(summary: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for category, count in _dict(summary.get("blocker_category_counts")).items():
        action_code, severity, owner_scope, target_artifacts = BLOCKER_REMEDIATION_METADATA.get(str(category), BLOCKER_REMEDIATION_METADATA["other_blocker"])
        items.append(
            {
                "kind": "blocker",
                "category": str(category),
                "count": _int(count),
                "priority": BLOCKER_CATEGORY_PRIORITY.get(str(category), -1),
                "action_code": action_code,
                "severity": severity,
                "owner_scope": owner_scope,
                "target_artifacts": list(target_artifacts),
                "action": BLOCKER_REMEDIATION_ACTIONS.get(str(category), BLOCKER_REMEDIATION_ACTIONS["other_blocker"]),
            }
        )
    for category, count in _dict(summary.get("review_category_counts")).items():
        action_code, severity, owner_scope, target_artifacts = REVIEW_REMEDIATION_METADATA.get(str(category), REVIEW_REMEDIATION_METADATA["other_review"])
        items.append(
            {
                "kind": "review",
                "category": str(category),
                "count": _int(count),
                "priority": REVIEW_CATEGORY_PRIORITY.get(str(category), -1),
                "action_code": action_code,
                "severity": severity,
                "owner_scope": owner_scope,
                "target_artifacts": list(target_artifacts),
                "action": REVIEW_REMEDIATION_ACTIONS.get(str(category), REVIEW_REMEDIATION_ACTIONS["other_review"]),
            }
        )
    return sorted(items, key=lambda item: (-_int(item.get("count")), -_int(item.get("priority")), str(item.get("kind")), str(item.get("category"))))


def _remediation_summary(remediation_plan: list[dict[str, Any]]) -> dict[str, Any]:
    blocker_count = sum(1 for item in remediation_plan if str(item.get("kind")) == "blocker")
    review_count = sum(1 for item in remediation_plan if str(item.get("kind")) == "review")
    top_item = remediation_plan[0] if remediation_plan else {}
    return {
        "remediation_plan_count": len(remediation_plan),
        "remediation_blocker_count": blocker_count,
        "remediation_review_count": review_count,
        "dominant_remediation_kind": None if not top_item else top_item.get("kind"),
        "dominant_remediation_category": None if not top_item else top_item.get("category"),
        "dominant_remediation_action": None if not top_item else top_item.get("action"),
    }


def _threshold_blocks(rows: list[dict[str, Any]], min_rubric_score: float) -> list[dict[str, Any]]:
    blocks = []
    threshold = float(min_rubric_score)
    for row in rows:
        if row.get("is_baseline"):
            continue
        blocker = _first_matching_list_item(row, "blockers", "rubric_avg_score below")
        if blocker is None:
            continue
        rubric_score = _number(row.get("rubric_avg_score"))
        margin = None if rubric_score is None else round(float(rubric_score) - threshold, 4)
        blocks.append(
            {
                "name": None if row.get("name") is None else str(row.get("name")),
                "blocker": blocker,
                "rubric_avg_score": rubric_score,
                "min_rubric_score": threshold,
                "margin": margin,
            }
        )
    return blocks


def _threshold_profile(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if not blocks:
        return {
            "first_threshold_blocked_candidate": None,
            "first_threshold_blocker": None,
            "first_threshold_rubric_score": None,
            "first_threshold_min_rubric_score": None,
            "first_threshold_margin": None,
            "threshold_blocked_candidate_count": 0,
            "threshold_blocked_candidate_names": [],
            "threshold_closest_candidate": None,
            "threshold_closest_margin": None,
            "threshold_largest_gap_candidate": None,
            "threshold_largest_gap_margin": None,
        }
    with_margin = [row for row in blocks if row.get("margin") is not None]
    closest = max(with_margin, key=lambda row: float(row.get("margin") or 0.0)) if with_margin else {}
    largest_gap = min(with_margin, key=lambda row: float(row.get("margin") or 0.0)) if with_margin else {}
    first = blocks[0]
    return {
        "first_threshold_blocked_candidate": first.get("name"),
        "first_threshold_blocker": first.get("blocker"),
        "first_threshold_rubric_score": first.get("rubric_avg_score"),
        "first_threshold_min_rubric_score": first.get("min_rubric_score"),
        "first_threshold_margin": first.get("margin"),
        "threshold_blocked_candidate_count": len(blocks),
        "threshold_blocked_candidate_names": [str(row.get("name")) for row in blocks if row.get("name") is not None],
        "threshold_closest_candidate": closest.get("name"),
        "threshold_closest_margin": closest.get("margin"),
        "threshold_largest_gap_candidate": largest_gap.get("name"),
        "threshold_largest_gap_margin": largest_gap.get("margin"),
    }


def _first_matching_list_item(row: dict[str, Any], key: str, prefix: str) -> str | None:
    values = row.get(key)
    if not isinstance(values, list):
        return None
    for item in values:
        text = str(item)
        if text.startswith(prefix):
            return text
    return None


def _recommendations(
    decision_status: str,
    selected: dict[str, Any] | None,
    evaluations: list[dict[str, Any]],
    comparison: dict[str, Any],
    remediation_plan: list[dict[str, Any]],
) -> list[str]:
    recommendations: list[str] = []
    if decision_status == "promote":
        recommendations.append("Promote the selected scorecard only as benchmark evidence, not as proof of broad model quality.")
    elif decision_status == "review":
        recommendations.append("Review generation-quality flags and case deltas before promoting the selected scorecard.")
    else:
        recommendations.append("Keep the baseline or fix candidate scorecard regressions before promotion.")
    if selected and selected.get("review_items"):
        recommendations.append("Selected review item(s): " + "; ".join(_string_list(selected.get("review_items"))) + ".")
    if selected and selected.get("eval_suite_comparison_status") not in {None, "pass"}:
        recommendations.append("Do not treat the selected scorecard as clean model-quality evidence until its eval suite is comparison-ready.")
    if selected and selected.get("eval_suite_design_comparison_status") not in {None, "pass"}:
        recommendations.append("Do not treat the selected scorecard as clean model-quality evidence until its prompt suite design is comparison-ready.")
    if any(row.get("blockers") for row in evaluations if not row.get("is_baseline")):
        recommendations.append("Blocked candidates should stay in the comparison as evidence for why they were not promoted.")
    summary = _dict(comparison.get("summary"))
    non_ready = _string_list(summary.get("non_comparison_ready_runs"))
    if non_ready:
        recommendations.append("Scorecard comparison includes non-comparison-ready eval suites: " + ", ".join(non_ready) + ".")
    if summary.get("baseline_eval_suite_comparison_status") not in {None, "pass"}:
        recommendations.append("Baseline eval suite is not comparison-ready; choose a cleaner baseline before promotion decisions.")
    non_design_ready = _string_list(summary.get("non_design_comparison_ready_runs"))
    if non_design_ready:
        recommendations.append("Scorecard comparison includes non-suite-design-ready runs: " + ", ".join(non_design_ready) + ".")
    if summary.get("baseline_eval_suite_design_comparison_status") not in {None, "pass"}:
        recommendations.append("Baseline prompt-suite design is not comparison-ready; choose a cleaner baseline before promotion decisions.")
    if _int(summary.get("generation_quality_flag_regression_count")):
        recommendations.append("At least one compared scorecard increased generation-quality flags; inspect raw generation-quality reports.")
    if _int(summary.get("case_regression_count")):
        recommendations.append("Case regressions are present; verify whether they are wording drift or true task failures.")
    if remediation_plan:
        top_item = remediation_plan[0]
        recommendations.append(f"Top remediation: {top_item.get('category')} -> {top_item.get('action')}")
    return recommendations



def _number(value: Any) -> float | None:
    number = number_or_none(value, float)
    return float(number) if number is not None else None


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


def _int_or_none(value: Any) -> int | None:
    number = number_or_none(value, int)
    return int(number) if number is not None else None
