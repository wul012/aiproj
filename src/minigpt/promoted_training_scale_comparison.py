from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    format_mapping as _fmt_mapping,
    first_present,
    list_of_dicts as _list_of_dicts,
    number_or_default,
    positive_int_mapping as _int_mapping,
    string_list as _string_list,
    utc_now,
)
from minigpt.promoted_training_scale_comparison_artifacts import (
    render_promoted_training_scale_comparison_html,
    render_promoted_training_scale_comparison_markdown,
    write_promoted_training_scale_comparison_csv,
    write_promoted_training_scale_comparison_html,
    write_promoted_training_scale_comparison_json,
    write_promoted_training_scale_comparison_markdown,
    write_promoted_training_scale_comparison_outputs,
)
from minigpt.training_scale_run_comparison import build_training_scale_run_comparison


def load_training_scale_promotion_index(path: str | Path) -> dict[str, Any]:
    index_path = _resolve_index_path(Path(path))
    payload = json.loads(index_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale promotion index must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(index_path)
    return payload


def build_promoted_training_scale_comparison(
    promotion_index_path: str | Path,
    *,
    baseline: str | int | None = None,
    generated_at: str | None = None,
    title: str = "MiniGPT promoted training scale comparison",
) -> dict[str, Any]:
    index = load_training_scale_promotion_index(promotion_index_path)
    index_file = Path(str(index.get("_source_path")))
    index_dir = index_file.parent
    index_summary = _dict(index.get("summary"))
    index_comparison = _dict(index.get("comparison_inputs"))
    promotions = _promotion_rows(index, index_dir)
    compare_rows = [row for row in promotions if row.get("promoted_for_comparison")]
    comparison_inputs = _comparison_inputs(index_comparison, compare_rows, index_dir)
    blocked_reason = None
    comparison_report: dict[str, Any] = {}
    comparison_status = "blocked"
    if len(comparison_inputs["resolved_paths"]) < 2:
        blocked_reason = "at least two promoted runs are required to compare"
    elif comparison_inputs["missing_paths"]:
        blocked_reason = "missing promoted run paths: " + ", ".join(comparison_inputs["missing_paths"])
    else:
        try:
            comparison_report = build_training_scale_run_comparison(
                comparison_inputs["resolved_paths"],
                names=comparison_inputs["names"],
                baseline=baseline if baseline is not None else comparison_inputs["baseline_name"],
                title=title,
                generated_at=generated_at,
            )
            comparison_status = "compared"
        except Exception as exc:  # pragma: no cover - converted into report data
            blocked_reason = str(exc)
    promotions = _merge_comparison_rows(promotions, comparison_report)
    summary = _summary(index_summary, promotions, comparison_inputs, comparison_report, comparison_status, blocked_reason)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "promotion_index_path": str(index_file),
        "promotion_index_summary": index_summary,
        "promotions": promotions,
        "comparison_inputs": comparison_inputs,
        "comparison_status": comparison_status,
        "comparison": comparison_report,
        "summary": summary,
        "blockers": _blockers(blocked_reason, comparison_inputs, comparison_status),
        "recommendations": _recommendations(summary),
    }



def _resolve_index_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "training_scale_promotion_index.json",
                path / "promotion-index" / "training_scale_promotion_index.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _promotion_rows(index: dict[str, Any], index_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for row in _list_of_dicts(index.get("promotions")):
        run_path = row.get("training_scale_run_path")
        resolved_run_path = _resolve_path(run_path, index_dir)
        clean_guard = _clean_batch_review_guard(row)
        index_marked_compare_ready = bool(row.get("promoted_for_comparison"))
        exclusion_reasons = _comparison_exclusion_reasons(row, resolved_run_path, clean_guard, index_marked_compare_ready)
        promoted_for_comparison = index_marked_compare_ready and not exclusion_reasons
        if (
            clean_guard.get("handoff_require_clean_batch_review")
            and clean_guard.get("handoff_clean_batch_review_status") != "clean"
        ):
            promoted_for_comparison = False
        rows.append(
            {
                "name": row.get("name"),
                "promotion_status": row.get("promotion_status"),
                "promoted_for_comparison": promoted_for_comparison,
                "comparison_exclusion_reasons": exclusion_reasons,
                "training_scale_run_path": str(resolved_run_path),
                "training_scale_run_exists": resolved_run_path.exists(),
                "gate_status": row.get("gate_status"),
                "batch_status": row.get("batch_status"),
                "readiness_score": row.get("readiness_score"),
                "handoff_require_suite_consistency": bool(row.get("handoff_require_suite_consistency")),
                "handoff_suite_consistency": row.get("handoff_suite_consistency"),
                "handoff_suite_mismatch_count": row.get("handoff_suite_mismatch_count"),
                "handoff_selected_suite_path": row.get("handoff_selected_suite_path"),
                "handoff_require_clean_batch_review": clean_guard.get("handoff_require_clean_batch_review"),
                "handoff_clean_batch_review_status": clean_guard.get("handoff_clean_batch_review_status"),
                "handoff_batch_maturity_ci_regression_count": clean_guard.get(
                    "handoff_batch_maturity_ci_regression_count"
                ),
                "handoff_batch_maturity_ci_regression_reason_counts": clean_guard.get(
                    "handoff_batch_maturity_ci_regression_reason_counts"
                ),
                "handoff_batch_maturity_ci_regression_names": clean_guard.get(
                    "handoff_batch_maturity_ci_regression_names"
                ),
                "handoff_selected_batch_maturity_ci_regression_count": clean_guard.get(
                    "handoff_selected_batch_maturity_ci_regression_count"
                ),
                "handoff_selected_batch_maturity_ci_regression_reason_counts": clean_guard.get(
                    "handoff_selected_batch_maturity_ci_regression_reason_counts"
                ),
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
                "handoff_batch_comparison_blocker_action_count": row.get("handoff_batch_comparison_blocker_action_count"),
                "handoff_batch_comparison_blocker_reasons": _string_list(row.get("handoff_batch_comparison_blocker_reasons")),
            }
        )
    return rows


def _comparison_inputs(
    index_comparison: dict[str, Any],
    compare_rows: list[dict[str, Any]],
    index_dir: Path,
) -> dict[str, Any]:
    names = [str(row.get("name")) for row in compare_rows if row.get("name")]
    paths = [str(row.get("training_scale_run_path")) for row in compare_rows if row.get("training_scale_run_path")]
    resolved_paths = [_resolve_path(path, index_dir) for path in paths]
    missing_paths = [str(path) for path in resolved_paths if not path.exists()]
    baseline_name = index_comparison.get("baseline_name")
    if baseline_name and baseline_name not in names and names:
        baseline_name = names[0]
    return {
        "run_count": len(compare_rows),
        "names": names,
        "training_scale_run_paths": paths,
        "resolved_paths": [str(path) for path in resolved_paths],
        "missing_paths": missing_paths,
        "baseline_name": baseline_name,
        "compare_command_ready": len(compare_rows) >= 2 and not missing_paths,
    }


def _merge_comparison_rows(promotions: list[dict[str, Any]], comparison_report: dict[str, Any]) -> list[dict[str, Any]]:
    runs = {row.get("name"): row for row in _list_of_dicts(comparison_report.get("runs"))}
    merged = []
    for row in promotions:
        updated = dict(row)
        run = runs.get(row.get("name"))
        if run:
            updated.update(
                {
                    "comparison_status": run.get("status"),
                    "allowed": run.get("allowed"),
                    "gate_status": run.get("gate_status"),
                    "batch_status": run.get("batch_status"),
                    "suite_path": run.get("suite_path"),
                    "readiness_score": run.get("readiness_score"),
                }
            )
        merged.append(updated)
    return merged


def _summary(
    index_summary: dict[str, Any],
    promotions: list[dict[str, Any]],
    comparison_inputs: dict[str, Any],
    comparison_report: dict[str, Any],
    comparison_status: str,
    blocked_reason: str | None,
) -> dict[str, Any]:
    compared = _dict(comparison_report.get("summary"))
    return {
        "comparison_status": comparison_status,
        "promotion_index_status": _index_status(index_summary),
        "promotion_count": len(promotions),
        "promoted_count": sum(1 for row in promotions if row.get("promotion_status") == "promoted"),
        "comparison_ready_count": comparison_inputs.get("run_count"),
        "compared_run_count": _dict(comparison_report.get("summary")).get("run_count"),
        "baseline_name": compared.get("baseline_name") or comparison_inputs.get("baseline_name"),
        "best_by_readiness": _dict(comparison_report.get("best_by_readiness")).get("name"),
        "suite_consistency": compared.get("suite_consistency"),
        "suite_path_count": compared.get("suite_path_count"),
        "suite_paths": compared.get("suite_paths"),
        "suite_mismatch_count": compared.get("suite_mismatch_count"),
        "handoff_require_suite_consistency_count": sum(1 for row in promotions if row.get("handoff_require_suite_consistency")),
        "handoff_suite_consistent_count": sum(1 for row in promotions if row.get("handoff_suite_consistency") == "consistent"),
        "handoff_suite_mismatch_total": sum(_int(row.get("handoff_suite_mismatch_count")) for row in promotions),
        "handoff_selected_suite_path_count": sum(1 for row in promotions if row.get("handoff_selected_suite_path")),
        "handoff_require_clean_batch_review_count": sum(1 for row in promotions if row.get("handoff_require_clean_batch_review")),
        "handoff_clean_batch_review_count": sum(
            1
            for row in promotions
            if row.get("handoff_require_clean_batch_review")
            and row.get("handoff_clean_batch_review_status") == "clean"
            and _int(row.get("handoff_batch_maturity_ci_regression_count")) == 0
        ),
        "handoff_unclean_batch_review_count": sum(
            1
            for row in promotions
            if row.get("handoff_require_clean_batch_review")
            and (
                row.get("handoff_clean_batch_review_status") != "clean"
                or _int(row.get("handoff_batch_maturity_ci_regression_count")) > 0
            )
        ),
        "handoff_batch_maturity_ci_regression_count": sum(
            _int(row.get("handoff_batch_maturity_ci_regression_count")) for row in promotions
        ),
        "handoff_selected_batch_maturity_ci_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_ci_regression_count")) for row in promotions
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _sum_reason_counts(
            row.get("handoff_selected_batch_maturity_ci_regression_reason_counts") for row in promotions
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": _sum_reason_counts(
            row.get("handoff_batch_maturity_ci_regression_reason_counts") for row in promotions
        ),
        "handoff_batch_maturity_ci_regression_names": sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_batch_maturity_ci_regression_names"))
            }
        ),
        "comparison_ready_handoff_selected_batch_review_count": sum(
            1
            for row in promotions
            if row.get("promoted_for_comparison") and row.get("handoff_selected_batch_review_status") == "review"
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": sum(
            1
            for row in promotions
            if row.get("promoted_for_comparison") and row.get("handoff_selected_batch_review_status") == "blocker"
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": sum(
            _int(row.get("handoff_selected_batch_comparison_review_action_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": sum(
            _int(row.get("handoff_selected_batch_comparison_blocker_action_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_comparison_review_action_total": sum(
            _int(row.get("handoff_batch_comparison_review_action_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_comparison_blocker_action_total": sum(
            _int(row.get("handoff_batch_comparison_blocker_action_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": sorted(
            {
                reason
                for row in promotions
                if row.get("promoted_for_comparison")
                for reason in _string_list(row.get("handoff_batch_comparison_blocker_reasons"))
            }
        ),
        "comparison_ready_handoff_require_clean_batch_review_count": sum(
            1 for row in promotions if row.get("promoted_for_comparison") and row.get("handoff_require_clean_batch_review")
        ),
        "comparison_ready_handoff_clean_batch_review_count": sum(
            1
            for row in promotions
            if row.get("promoted_for_comparison")
            and row.get("handoff_require_clean_batch_review")
            and row.get("handoff_clean_batch_review_status") == "clean"
            and _int(row.get("handoff_batch_maturity_ci_regression_count")) == 0
        ),
        "comparison_ready_handoff_unclean_batch_review_count": sum(
            1
            for row in promotions
            if row.get("promoted_for_comparison")
            and row.get("handoff_require_clean_batch_review")
            and (
                row.get("handoff_clean_batch_review_status") != "clean"
                or _int(row.get("handoff_batch_maturity_ci_regression_count")) > 0
            )
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_count": sum(
            _int(row.get("handoff_batch_maturity_ci_regression_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_ci_regression_count"))
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": _sum_reason_counts(
            row.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": _sum_reason_counts(
            row.get("handoff_batch_maturity_ci_regression_reason_counts")
            for row in promotions
            if row.get("promoted_for_comparison")
        ),
        "comparison_ready_handoff_batch_maturity_ci_regression_names": sorted(
            {
                name
                for row in promotions
                if row.get("promoted_for_comparison")
                for name in _string_list(row.get("handoff_batch_maturity_ci_regression_names"))
            }
        ),
        "comparison_ready_handoff_suite_mismatch_total": sum(
            _int(row.get("handoff_suite_mismatch_count")) for row in promotions if row.get("promoted_for_comparison")
        ),
        "allowed_count": compared.get("allowed_count"),
        "blocked_count": compared.get("blocked_count"),
        "gate_warn_count": compared.get("gate_warn_count"),
        "gate_fail_count": compared.get("gate_fail_count"),
        "blocked_reason": blocked_reason,
    }


def _blockers(blocked_reason: str | None, comparison_inputs: dict[str, Any], comparison_status: str) -> list[str]:
    if comparison_status == "compared":
        return []
    blockers = []
    if blocked_reason:
        blockers.append(blocked_reason)
    if comparison_inputs.get("run_count", 0) < 2:
        blockers.append("need at least two promoted runs for comparison")
    if comparison_inputs.get("missing_paths"):
        blockers.append("missing promoted run paths: " + ", ".join(_string_list(comparison_inputs.get("missing_paths"))))
    return blockers


def _index_status(index_summary: dict[str, Any]) -> str:
    if not index_summary:
        return "unknown"
    if index_summary.get("compare_command_ready"):
        return "compare_ready"
    return "insufficient"


def _recommendations(summary: dict[str, Any]) -> list[str]:
    if summary.get("comparison_status") == "compared":
        recommendations = [
            "Use the compared promoted runs as the baseline for the next training-scale decision.",
            "Keep review and blocked promotions in the index, but do not feed them into comparison runs.",
        ]
        if _int(summary.get("comparison_ready_handoff_unclean_batch_review_count")):
            recommendations.append(
                "Comparison-ready promoted inputs still include unclean clean-required handoffs; resolve them before treating this comparison as clean model-quality evidence."
            )
        elif _int(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")):
            detail = _fmt_mapping(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"))
            suffix = f" Observed reasons: {detail}." if detail != "none" else ""
            recommendations.append(
                "Comparison-ready promoted inputs still include handoff batch CI regressions; resolve them before treating this comparison as clean model-quality evidence."
                + suffix
            )
        elif _int(summary.get("comparison_ready_handoff_selected_batch_blocker_count")):
            recommendations.append(
                "Comparison-ready promoted inputs still carry selected handoff batch blocker actions; resolve them before treating this comparison as clean model-quality evidence."
            )
        elif _int(summary.get("handoff_batch_maturity_ci_regression_count")):
            detail = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
            suffix = f" Observed reasons: {detail}." if detail != "none" else ""
            recommendations.append(
                "CI-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
                + suffix
            )
        if _int(summary.get("handoff_batch_maturity_ci_regression_count")) and not any(
            "CI-regressed handoff batch evidence remains visible" in item for item in recommendations
        ):
            detail = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
            suffix = f" Observed reasons: {detail}." if detail != "none" else ""
            recommendations.append(
                "CI-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
                + suffix
            )
        reasons = _string_list(summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons"))
        if reasons:
            recommendations.append("Comparison-ready batch blocker reasons: " + ", ".join(reasons))
        elif _int(summary.get("comparison_ready_handoff_selected_batch_review_count")):
            recommendations.append(
                "Comparison-ready promoted inputs still carry selected handoff batch review actions; review them before treating this comparison as clean model-quality evidence."
            )
        if summary.get("suite_consistency") == "mixed":
            recommendations.append("Compared promoted runs use different benchmark suites; review suite paths before treating readiness deltas as clean model-quality deltas.")
        return recommendations
    recommendations = [
        "Add another promoted run or fix the blocked baseline before comparing promoted results.",
        "Use the promotion index to keep review and blocked evidence visible without mixing it into model comparison.",
    ]
    if _int(summary.get("comparison_ready_handoff_unclean_batch_review_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still include unclean clean-required handoffs; clean them before treating later comparisons as baseline evidence."
        )
    elif _int(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_count")):
        detail = _fmt_mapping(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail != "none" else ""
        recommendations.append(
            "Comparison-ready promoted inputs still include handoff batch CI regressions; clean them before treating later comparisons as baseline evidence."
            + suffix
        )
    elif _int(summary.get("comparison_ready_handoff_selected_batch_blocker_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still carry selected handoff batch blocker actions; clean them before treating later comparisons as baseline evidence."
        )
    elif _int(summary.get("comparison_ready_handoff_selected_batch_review_count")):
        recommendations.append(
            "Comparison-ready promoted inputs still carry selected handoff batch review actions; review them before treating later comparisons as baseline evidence."
        )
    elif _int(summary.get("handoff_batch_maturity_ci_regression_count")):
        detail = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail != "none" else ""
        recommendations.append(
            "CI-regressed handoff batch evidence remains visible in the promotion list but is kept out of clean-required promoted comparisons."
            + suffix
        )
    return recommendations



def _comparison_exclusion_reasons(
    row: dict[str, Any],
    resolved_run_path: Path,
    clean_guard: dict[str, Any],
    index_marked_compare_ready: bool,
) -> list[str]:
    reasons = []
    if row.get("promotion_status") != "promoted":
        reasons.append("not promoted")
    if not resolved_run_path.exists():
        reasons.append("missing training scale run path")
    if clean_guard.get("handoff_require_clean_batch_review"):
        if clean_guard.get("handoff_clean_batch_review_status") != "clean":
            reasons.append(f"clean batch review status is {clean_guard.get('handoff_clean_batch_review_status')}")
        if _int(clean_guard.get("handoff_batch_maturity_ci_regression_count")) > 0:
            reasons.append(
                "handoff batch CI regression count is "
                f"{clean_guard.get('handoff_batch_maturity_ci_regression_count')}"
            )
    if not index_marked_compare_ready and not reasons:
        reasons.append("not marked compare-ready by promotion index")
    return reasons


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


def _sum_reason_counts(values: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        for reason, count in _int_mapping(value).items():
            result[reason] = result.get(reason, 0) + count
    return dict(sorted(result.items()))


def _clean_batch_review_guard(row: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(row.get("summary"))
    guard = _dict(row.get("clean_batch_review_guard"))
    required = first_present(
        row.get("handoff_require_clean_batch_review"),
        row.get("decision_require_clean_batch_review"),
        row.get("require_clean_batch_review"),
        guard.get("handoff_require_clean_batch_review"),
        guard.get("decision_require_clean_batch_review"),
        guard.get("require_clean_batch_review"),
        summary.get("handoff_require_clean_batch_review"),
        summary.get("decision_require_clean_batch_review"),
        summary.get("require_clean_batch_review"),
    )
    return {
        "handoff_require_clean_batch_review": bool(required),
        "handoff_clean_batch_review_status": first_present(
            row.get("handoff_clean_batch_review_status"),
            guard.get("handoff_clean_batch_review_status"),
            guard.get("clean_batch_review_status"),
            summary.get("handoff_clean_batch_review_status"),
            summary.get("clean_batch_review_status"),
        ),
        "handoff_batch_maturity_ci_regression_count": first_present(
            row.get("handoff_batch_maturity_ci_regression_count"),
            guard.get("handoff_batch_maturity_ci_regression_count"),
            guard.get("batch_maturity_ci_regression_count"),
            summary.get("handoff_batch_maturity_ci_regression_count"),
            summary.get("batch_maturity_ci_regression_count"),
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": _int_mapping(
            first_present(
                row.get("handoff_batch_maturity_ci_regression_reason_counts"),
                guard.get("handoff_batch_maturity_ci_regression_reason_counts"),
                guard.get("batch_maturity_ci_regression_reason_counts"),
                summary.get("handoff_batch_maturity_ci_regression_reason_counts"),
                summary.get("batch_maturity_ci_regression_reason_counts"),
            )
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(
            first_present(
                row.get("handoff_batch_maturity_ci_regression_names"),
                guard.get("handoff_batch_maturity_ci_regression_names"),
                guard.get("batch_maturity_ci_regression_names"),
                summary.get("handoff_batch_maturity_ci_regression_names"),
                summary.get("batch_maturity_ci_regression_names"),
            )
        ),
        "handoff_selected_batch_maturity_ci_regression_count": first_present(
            row.get("handoff_selected_batch_maturity_ci_regression_count"),
            guard.get("handoff_selected_batch_maturity_ci_regression_count"),
            guard.get("selected_batch_maturity_ci_regression_count"),
            summary.get("handoff_selected_batch_maturity_ci_regression_count"),
            summary.get("selected_batch_maturity_ci_regression_count"),
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _int_mapping(
            first_present(
                row.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
                guard.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
                guard.get("selected_batch_maturity_ci_regression_reason_counts"),
                summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
                summary.get("selected_batch_maturity_ci_regression_reason_counts"),
            )
        ),
    }
