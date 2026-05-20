from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_decision_artifacts import (
    render_promoted_training_scale_decision_html,
    render_promoted_training_scale_decision_markdown,
    write_promoted_training_scale_decision_csv,
    write_promoted_training_scale_decision_html,
    write_promoted_training_scale_decision_json,
    write_promoted_training_scale_decision_markdown,
    write_promoted_training_scale_decision_outputs,
)
from minigpt.promoted_training_scale_decision_review import (
    append_decision_handoff_batch_recommendations,
    append_decision_handoff_clean_batch_recommendations,
    build_decision_handoff_review_summary,
)
from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    number_or_default,
    string_list as _string_list,
    utc_now,
)


GATE_ORDER = {"fail": 0, "warn": 1, "pass": 2}
BATCH_ORDER = {"skipped": 0, None: 0, "failed": 1, "planned": 2, "completed": 3}


def load_promoted_training_scale_comparison(path: str | Path) -> dict[str, Any]:
    comparison_path = _resolve_comparison_path(Path(path))
    payload = json.loads(comparison_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted training scale comparison must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(comparison_path)
    return payload


def build_promoted_training_scale_decision(
    comparison_path: str | Path,
    *,
    min_readiness: int = 70,
    require_gate_pass: bool = False,
    require_batch_completed: bool = True,
    require_suite_consistency: bool = False,
    title: str = "MiniGPT promoted training scale baseline decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    comparison = load_promoted_training_scale_comparison(comparison_path)
    comparison_file = Path(str(comparison.get("_source_path")))
    comparison_dir = comparison_file.parent
    comparison_summary = _dict(comparison.get("summary"))
    suite_reasons = _suite_consistency_reasons(comparison_summary, require_suite_consistency)
    promotions = _promotion_rows(comparison, comparison_dir)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    report_compared = comparison.get("comparison_status") == "compared"
    for row in promotions:
        reasons = ["comparison report is not compared"] if not report_compared else _rejection_reasons(
            row,
            min_readiness=min_readiness,
            require_gate_pass=require_gate_pass,
            require_batch_completed=require_batch_completed,
        )
        reasons.extend(suite_reasons)
        if reasons:
            rejected.append({**row, "reasons": reasons})
        else:
            candidates.append(row)
    selected = _select_candidate(candidates)
    decision_status = _decision_status(comparison, selected, rejected)
    summary = _summary(
        comparison_summary,
        promotions,
        candidates,
        rejected,
        selected,
        decision_status,
        require_suite_consistency=require_suite_consistency,
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "comparison_path": str(comparison_file),
        "comparison_status": comparison.get("comparison_status"),
        "promotions": promotions,
        "selected_baseline": selected,
        "rejected_runs": rejected,
        "summary": summary,
        "decision_status": decision_status,
        "recommendations": _recommendations(
            decision_status,
            selected,
            rejected,
            comparison_summary=comparison_summary,
            require_suite_consistency=require_suite_consistency,
        ),
    }


def _resolve_comparison_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "promoted_training_scale_comparison.json",
                path / "comparison" / "promoted_training_scale_comparison.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _promotion_rows(comparison: dict[str, Any], comparison_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for row in _list_of_dicts(comparison.get("promotions")):
        resolved_path = _resolve_path(row.get("training_scale_run_path"), comparison_dir)
        rows.append(
            {
                "name": row.get("name"),
                "promotion_status": row.get("promotion_status"),
                "promoted_for_comparison": bool(row.get("promoted_for_comparison")),
                "comparison_status": row.get("comparison_status") or comparison.get("comparison_status"),
                "gate_status": row.get("gate_status"),
                "batch_status": row.get("batch_status"),
                "readiness_score": row.get("readiness_score"),
                "suite_path": row.get("suite_path"),
                "handoff_require_suite_consistency": bool(row.get("handoff_require_suite_consistency")),
                "handoff_suite_consistency": row.get("handoff_suite_consistency"),
                "handoff_suite_mismatch_count": row.get("handoff_suite_mismatch_count"),
                "handoff_selected_suite_path": row.get("handoff_selected_suite_path"),
                "handoff_require_clean_batch_review": bool(row.get("handoff_require_clean_batch_review")),
                "handoff_clean_batch_review_status": row.get("handoff_clean_batch_review_status"),
                "handoff_batch_maturity_ci_regression_count": _int(
                    row.get("handoff_batch_maturity_ci_regression_count")
                ),
                "handoff_batch_maturity_ci_regression_names": _string_list(
                    row.get("handoff_batch_maturity_ci_regression_names")
                ),
                "handoff_selected_batch_maturity_ci_regression_count": _int(
                    row.get("handoff_selected_batch_maturity_ci_regression_count")
                ),
                "comparison_exclusion_reasons": _string_list(row.get("comparison_exclusion_reasons")),
                "handoff_selected_batch_review_status": row.get("handoff_selected_batch_review_status"),
                "handoff_selected_batch_comparison_review_action_count": row.get(
                    "handoff_selected_batch_comparison_review_action_count"
                ),
                "handoff_selected_batch_comparison_blocker_action_count": row.get(
                    "handoff_selected_batch_comparison_blocker_action_count"
                ),
                "handoff_selected_batch_maturity_coverage_regression_count": row.get(
                    "handoff_selected_batch_maturity_coverage_regression_count"
                ),
                "handoff_batch_comparison_review_action_count": row.get("handoff_batch_comparison_review_action_count"),
                "handoff_batch_comparison_blocker_action_count": row.get(
                    "handoff_batch_comparison_blocker_action_count"
                ),
                "handoff_batch_comparison_blocker_reasons": _string_list(
                    row.get("handoff_batch_comparison_blocker_reasons")
                ),
                "training_scale_run_path": str(resolved_path),
                "source_path": row.get("source_path"),
            }
        )
    return rows


def _rejection_reasons(
    row: dict[str, Any],
    *,
    min_readiness: int,
    require_gate_pass: bool,
    require_batch_completed: bool,
) -> list[str]:
    reasons: list[str] = []
    if not row.get("promoted_for_comparison"):
        reasons.append("run was not promoted for comparison")
        reasons.extend(reason for reason in _string_list(row.get("comparison_exclusion_reasons")) if reason not in reasons)
    if row.get("handoff_require_clean_batch_review") and row.get("handoff_clean_batch_review_status") != "clean":
        reasons.append("clean batch-review requirement is not clean")
    if row.get("handoff_require_clean_batch_review") and _int(row.get("handoff_batch_maturity_ci_regression_count")) > 0:
        reason = "handoff batch CI regression count is " f"{row.get('handoff_batch_maturity_ci_regression_count')}"
        if reason not in reasons:
            reasons.append(reason)
    if row.get("gate_status") == "fail":
        reasons.append("gate failed")
    elif require_gate_pass and row.get("gate_status") != "pass":
        reasons.append("gate is not pass")
    if require_batch_completed and row.get("batch_status") != "completed":
        reasons.append("batch did not complete")
    if _int(row.get("readiness_score")) < int(min_readiness):
        reasons.append(f"readiness_score below {int(min_readiness)}")
    if not row.get("training_scale_run_path") or not Path(str(row.get("training_scale_run_path"))).exists():
        reasons.append("training_scale_run.json is missing")
    return reasons


def _suite_consistency_reasons(comparison_summary: dict[str, Any], require_suite_consistency: bool) -> list[str]:
    if not require_suite_consistency:
        return []
    suite_consistency = str(comparison_summary.get("suite_consistency") or "")
    if suite_consistency == "consistent":
        return []
    return [f"benchmark suite consistency is {suite_consistency or 'missing'}"]


def _select_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    return dict(
        max(
            candidates,
            key=lambda row: (
                _int(row.get("readiness_score")),
                GATE_ORDER.get(str(row.get("gate_status")), -1),
                BATCH_ORDER.get(row.get("batch_status"), 0),
            ),
        )
    )


def _decision_status(
    comparison: dict[str, Any],
    selected: dict[str, Any] | None,
    rejected: list[dict[str, Any]],
) -> str:
    if _string_list(comparison.get("blockers")):
        return "blocked"
    if not selected:
        return "blocked"
    if selected.get("gate_status") == "warn" or rejected:
        return "review"
    return "accepted"


def _summary(
    comparison_summary: dict[str, Any],
    promotions: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    decision_status: str,
    *,
    require_suite_consistency: bool,
) -> dict[str, Any]:
    summary = {
        "decision_status": decision_status,
        "comparison_status": comparison_summary.get("comparison_status"),
        "promotion_index_status": comparison_summary.get("promotion_index_status"),
        "promotion_count": len(promotions),
        "candidate_count": len(candidates),
        "rejected_count": len(rejected),
        "selected_name": None if selected is None else selected.get("name"),
        "selected_gate_status": None if selected is None else selected.get("gate_status"),
        "selected_batch_status": None if selected is None else selected.get("batch_status"),
        "selected_readiness_score": None if selected is None else selected.get("readiness_score"),
        "selected_suite_path": None if selected is None else selected.get("suite_path"),
        "require_suite_consistency": bool(require_suite_consistency),
        "selected_promotion_status": None if selected is None else selected.get("promotion_status"),
        "suite_consistency": comparison_summary.get("suite_consistency"),
        "suite_paths": comparison_summary.get("suite_paths"),
        "suite_mismatch_count": comparison_summary.get("suite_mismatch_count"),
    }
    summary.update(build_decision_handoff_review_summary(comparison_summary, promotions, selected))
    return summary


def _recommendations(
    decision_status: str,
    selected: dict[str, Any] | None,
    rejected: list[dict[str, Any]],
    *,
    comparison_summary: dict[str, Any],
    require_suite_consistency: bool,
) -> list[str]:
    if decision_status == "accepted":
        recommendations = [
            "Use the selected promoted baseline for the next training-scale planning cycle.",
            "Keep the rejected promoted runs around as comparison evidence so the baseline choice stays explainable.",
        ]
        if selected and selected.get("suite_path"):
            recommendations.append(f"Carry `{selected.get('suite_path')}` into the next promoted seed so later comparisons stay suite-consistent.")
        if require_suite_consistency and comparison_summary.get("suite_consistency") != "consistent":
            recommendations.append("Fix benchmark suite consistency before using this promoted baseline as clean model-quality evidence.")
        elif comparison_summary.get("suite_consistency") == "mixed":
            recommendations.append("Promoted runs use different benchmark suites; treat this baseline as governance triage, not clean model-quality evidence.")
        append_decision_handoff_clean_batch_recommendations(recommendations, selected, comparison_summary)
        append_decision_handoff_batch_recommendations(recommendations, selected, comparison_summary)
        return recommendations
    if decision_status == "review":
        recommendations = [
            "Review the remaining promoted runs before turning this baseline into the next run seed.",
            "Gate warnings can be accepted for review, but they should be justified before larger training.",
        ]
        if require_suite_consistency and comparison_summary.get("suite_consistency") != "consistent":
            recommendations.append("Fix benchmark suite consistency before using this promoted baseline as clean model-quality evidence.")
        elif comparison_summary.get("suite_consistency") == "mixed":
            recommendations.append("Promoted runs use different benchmark suites; treat this baseline as governance triage, not clean model-quality evidence.")
        append_decision_handoff_clean_batch_recommendations(recommendations, selected, comparison_summary)
        append_decision_handoff_batch_recommendations(recommendations, selected, comparison_summary)
        return recommendations
    recommendations = [
        "Fix the promoted comparison or promote more runs before selecting a new baseline.",
    ]
    if require_suite_consistency and comparison_summary.get("suite_consistency") != "consistent":
        recommendations.append("Fix benchmark suite consistency before using this promoted baseline as clean model-quality evidence.")
    elif comparison_summary.get("suite_consistency") == "mixed":
        recommendations.append("Promoted runs use different benchmark suites; treat this baseline as governance triage, not clean model-quality evidence.")
    append_decision_handoff_clean_batch_recommendations(recommendations, selected, comparison_summary)
    append_decision_handoff_batch_recommendations(recommendations, selected, comparison_summary)
    return recommendations


def _resolve_path(value: Any, base_dir: Path) -> Path:
    if value is None:
        return base_dir
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidates = [base_dir / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))
