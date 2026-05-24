from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    first_present,
    format_mapping as _fmt_mapping,
    list_of_dicts as _list_of_dicts,
    number_or_default,
    positive_int_mapping as _int_mapping,
    string_list as _string_list,
)


def _resolve_names(reports: list[dict[str, Any]], names: list[str] | None) -> list[str]:
    if names is not None:
        resolved = [str(name).strip() for name in names]
    else:
        resolved = []
        for index, report in enumerate(reports):
            source = Path(str(report.get("_source_path") or f"promotion-{index + 1}"))
            parent = source.parent
            if parent.name in {"promotion", "training-scale-promotion"} and parent.parent.name:
                resolved.append(parent.parent.name)
            else:
                resolved.append(str(parent.name or source.stem or f"promotion-{index + 1}"))
    if any(not name for name in resolved):
        raise ValueError("promotion names cannot be empty")
    if len(set(resolved)) != len(resolved):
        raise ValueError("promotion names must be unique")
    return resolved


def _promotion_row(report: dict[str, Any], name: str, index: int) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    suite_guard = _suite_guard(report)
    variants = _list_of_dicts(report.get("variants"))
    primary = _primary_variant(variants)
    artifacts = _artifact_map(primary)
    scale_run_path = str(report.get("training_scale_run_path") or "")
    scale_run_exists = bool(scale_run_path and Path(scale_run_path).is_file())
    promotion_status = str(summary.get("promotion_status") or "missing")
    clean_batch_review = _clean_batch_review_guard(report)
    clean_requirement_satisfied = (
        not clean_batch_review.get("handoff_require_clean_batch_review")
        or (
            clean_batch_review.get("handoff_clean_batch_review_status") == "clean"
            and _int(clean_batch_review.get("handoff_batch_maturity_ci_regression_count")) == 0
            and _int(clean_batch_review.get("handoff_batch_maturity_suite_design_regression_count")) == 0
        )
    )
    promoted_for_comparison = promotion_status == "promoted" and scale_run_exists and clean_requirement_satisfied
    return {
        "index": index + 1,
        "name": name,
        "promotion_source_path": report.get("_source_path"),
        "promotion_status": promotion_status,
        "promoted_for_comparison": promoted_for_comparison,
        "handoff_path": report.get("handoff_path"),
        "project_root": report.get("project_root"),
        "out_root": report.get("out_root"),
        "training_scale_run_path": scale_run_path,
        "training_scale_run_exists": scale_run_exists,
        "batch_path": report.get("batch_path"),
        "handoff_status": summary.get("handoff_status"),
        "scale_run_status": summary.get("scale_run_status"),
        "batch_status": summary.get("batch_status"),
        "variant_count": summary.get("variant_count") or len(variants),
        "ready_variant_count": summary.get("ready_variant_count") or sum(1 for row in variants if row.get("promotion_status") == "ready"),
        "checkpoint_count": summary.get("checkpoint_count"),
        "registry_count": summary.get("registry_count"),
        "maturity_narrative_count": summary.get("maturity_narrative_count"),
        "required_artifact_count": summary.get("required_artifact_count"),
        "available_required_artifact_count": summary.get("available_required_artifact_count"),
        "blocker_count": summary.get("blocker_count") or len(_string_list(report.get("blockers"))),
        "review_item_count": summary.get("review_item_count") or len(_string_list(report.get("review_items"))),
        "handoff_require_suite_consistency": suite_guard.get("handoff_require_suite_consistency"),
        "handoff_suite_consistency": suite_guard.get("handoff_suite_consistency"),
        "handoff_suite_mismatch_count": suite_guard.get("handoff_suite_mismatch_count"),
        "handoff_selected_suite_path": suite_guard.get("handoff_selected_suite_path"),
        "handoff_require_clean_batch_review": clean_batch_review.get("handoff_require_clean_batch_review"),
        "handoff_clean_batch_review_status": clean_batch_review.get("handoff_clean_batch_review_status"),
        "handoff_batch_maturity_ci_regression_count": clean_batch_review.get("handoff_batch_maturity_ci_regression_count"),
        "handoff_batch_maturity_ci_regression_reason_counts": clean_batch_review.get(
            "handoff_batch_maturity_ci_regression_reason_counts"
        ),
        "handoff_batch_maturity_ci_regression_names": clean_batch_review.get("handoff_batch_maturity_ci_regression_names"),
        "handoff_batch_maturity_suite_design_regression_count": clean_batch_review.get(
            "handoff_batch_maturity_suite_design_regression_count"
        ),
        "handoff_batch_maturity_suite_design_regression_names": clean_batch_review.get(
            "handoff_batch_maturity_suite_design_regression_names"
        ),
        "handoff_selected_batch_review_status": summary.get("handoff_selected_batch_review_status"),
        "handoff_selected_batch_comparison_review_action_count": summary.get(
            "handoff_selected_batch_comparison_review_action_count"
        ),
        "handoff_selected_batch_comparison_blocker_action_count": summary.get(
            "handoff_selected_batch_comparison_blocker_action_count"
        ),
        "handoff_selected_batch_maturity_coverage_regression_count": summary.get(
            "handoff_selected_batch_maturity_coverage_regression_count"
        ),
        "handoff_selected_batch_maturity_suite_design_regression_count": summary.get(
            "handoff_selected_batch_maturity_suite_design_regression_count"
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": _string_list(
            summary.get("handoff_selected_batch_maturity_suite_design_regression_names")
        ),
        "handoff_selected_batch_maturity_ci_regression_count": summary.get(
            "handoff_selected_batch_maturity_ci_regression_count"
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _int_mapping(
            summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_batch_comparison_review_action_count": summary.get("handoff_batch_comparison_review_action_count"),
        "handoff_batch_comparison_blocker_action_count": summary.get("handoff_batch_comparison_blocker_action_count"),
        "handoff_batch_comparison_blocker_reasons": _string_list(summary.get("handoff_batch_comparison_blocker_reasons")),
        "primary_variant": primary.get("name"),
        "primary_variant_status": primary.get("promotion_status"),
        "primary_portfolio_json": primary.get("portfolio_json"),
        "primary_checkpoint": artifacts.get("checkpoint"),
        "primary_registry": artifacts.get("registry"),
        "primary_maturity_narrative": artifacts.get("maturity_narrative"),
        "missing_required": _string_list(primary.get("missing_required")),
        "blockers": _string_list(report.get("blockers")),
        "review_items": _string_list(report.get("review_items")),
    }


def _primary_variant(variants: list[dict[str, Any]]) -> dict[str, Any]:
    for row in variants:
        if row.get("promotion_status") == "ready":
            return row
    return variants[0] if variants else {}


def _artifact_map(variant: dict[str, Any]) -> dict[str, str]:
    rows = _list_of_dicts(variant.get("artifact_rows"))
    result = {}
    for row in rows:
        if row.get("exists"):
            result[str(row.get("key"))] = str(row.get("path") or "")
    return result


def _comparison_inputs(promotions: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    ready = [row for row in promotions if row.get("promoted_for_comparison")]
    baseline_row = _select_baseline(ready, baseline)
    paths = [str(row.get("training_scale_run_path")) for row in ready]
    names = [str(row.get("name")) for row in ready]
    command = []
    if len(ready) >= 2:
        command = ["python", "scripts/compare_training_scale_runs.py"]
        command.extend(paths)
        for name in names:
            command.extend(["--name", name])
        if baseline_row:
            command.extend(["--baseline", str(baseline_row.get("name"))])
    return {
        "run_count": len(ready),
        "names": names,
        "training_scale_run_paths": paths,
        "baseline_name": baseline_row.get("name") if baseline_row else None,
        "compare_command_ready": len(command) > 0,
        "compare_command": command,
    }


def _select_baseline(rows: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    if not rows:
        if baseline is not None:
            raise ValueError("baseline cannot be selected without promoted comparison inputs")
        return {}
    if baseline is None:
        return rows[0]
    if isinstance(baseline, int) or (isinstance(baseline, str) and str(baseline).isdigit()):
        index = int(baseline)
        if index < 0 or index >= len(rows):
            raise ValueError("baseline index out of range")
        return rows[index]
    for row in rows:
        if row.get("name") == baseline:
            return row
    raise ValueError(f"baseline is not promoted for comparison: {baseline}")


def _summary(promotions: list[dict[str, Any]], comparison_inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "promotion_count": len(promotions),
        "promoted_count": sum(1 for row in promotions if row.get("promotion_status") == "promoted"),
        "review_count": sum(1 for row in promotions if row.get("promotion_status") == "review"),
        "blocked_count": sum(1 for row in promotions if row.get("promotion_status") == "blocked"),
        "missing_count": sum(1 for row in promotions if row.get("promotion_status") == "missing"),
        "comparison_ready_count": comparison_inputs.get("run_count"),
        "compare_command_ready": comparison_inputs.get("compare_command_ready"),
        "non_comparable_count": sum(1 for row in promotions if not row.get("promoted_for_comparison")),
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
            and _int(row.get("handoff_batch_maturity_suite_design_regression_count")) == 0
        ),
        "handoff_unclean_batch_review_count": sum(
            1
            for row in promotions
            if row.get("handoff_require_clean_batch_review")
            and (
                row.get("handoff_clean_batch_review_status") != "clean"
                or _int(row.get("handoff_batch_maturity_ci_regression_count")) > 0
                or _int(row.get("handoff_batch_maturity_suite_design_regression_count")) > 0
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
        "handoff_batch_maturity_suite_design_regression_count": sum(
            _int(row.get("handoff_batch_maturity_suite_design_regression_count")) for row in promotions
        ),
        "handoff_selected_batch_maturity_suite_design_regression_total": sum(
            _int(row.get("handoff_selected_batch_maturity_suite_design_regression_count")) for row in promotions
        ),
        "handoff_batch_maturity_suite_design_regression_names": sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_batch_maturity_suite_design_regression_names"))
            }
        ),
        "handoff_selected_batch_maturity_suite_design_regression_names": sorted(
            {
                name
                for row in promotions
                for name in _string_list(row.get("handoff_selected_batch_maturity_suite_design_regression_names"))
            }
        ),
        "handoff_selected_batch_review_count": sum(
            1 for row in promotions if row.get("handoff_selected_batch_review_status") == "review"
        ),
        "handoff_selected_batch_blocker_count": sum(
            1 for row in promotions if row.get("handoff_selected_batch_review_status") == "blocker"
        ),
        "handoff_selected_batch_comparison_review_action_total": sum(
            _int(row.get("handoff_selected_batch_comparison_review_action_count")) for row in promotions
        ),
        "handoff_selected_batch_comparison_blocker_action_total": sum(
            _int(row.get("handoff_selected_batch_comparison_blocker_action_count")) for row in promotions
        ),
        "handoff_batch_comparison_review_action_total": sum(
            _int(row.get("handoff_batch_comparison_review_action_count")) for row in promotions
        ),
        "handoff_batch_comparison_blocker_action_total": sum(
            _int(row.get("handoff_batch_comparison_blocker_action_count")) for row in promotions
        ),
        "handoff_batch_comparison_blocker_reasons": sorted(
            {
                reason
                for row in promotions
                for reason in _string_list(row.get("handoff_batch_comparison_blocker_reasons"))
            }
        ),
    }


def _recommendations(summary: dict[str, Any]) -> list[str]:
    ready_count = _int(summary.get("comparison_ready_count"))
    blocked_count = _int(summary.get("blocked_count"))
    review_count = _int(summary.get("review_count"))
    batch_blockers = _int(summary.get("handoff_selected_batch_blocker_count"))
    batch_reviews = _int(summary.get("handoff_selected_batch_review_count"))
    unclean_required = _int(summary.get("handoff_unclean_batch_review_count"))
    ci_regressions = _int(summary.get("handoff_batch_maturity_ci_regression_count"))
    suite_design_regressions = _int(summary.get("handoff_batch_maturity_suite_design_regression_count"))
    if ready_count >= 2:
        items = [
            "Run the generated compare command to compare only promoted training scale runs.",
            "Keep review and blocked promotions out of baseline selection until their evidence is fixed.",
        ]
        if ci_regressions:
            detail = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
            suffix = f" Observed reasons: {detail}." if detail != "none" else ""
            items.append(
                "Resolve handoff batch CI regression evidence before treating promoted compare inputs as clean evidence."
                + suffix
            )
        if suite_design_regressions:
            names = ", ".join(_string_list(summary.get("handoff_batch_maturity_suite_design_regression_names")))
            suffix = f" Affected promotions: {names}." if names else ""
            items.append(
                "Resolve handoff batch suite-design regression evidence before treating promoted compare inputs as clean evidence."
                + suffix
            )
        elif unclean_required and not ci_regressions:
            items.append("Resolve handoff clean batch-review requirements before treating promoted compare inputs as clean evidence.")
        elif batch_blockers:
            items.append("Resolve selected handoff batch blocker actions before treating promoted compare inputs as clean evidence.")
        elif batch_reviews:
            items.append("Review selected handoff batch actions before treating promoted compare inputs as clean evidence.")
        return items
    if ready_count == 1:
        items = [
            "Use the single promoted run as the baseline candidate and add another promoted run before comparison.",
            "Do not compare review or blocked promotions against the baseline as model capability evidence.",
        ]
        if ci_regressions:
            detail = _fmt_mapping(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
            suffix = f" Observed reasons: {detail}." if detail != "none" else ""
            items.append("Resolve handoff batch CI regression evidence before using this single promoted run as baseline evidence." + suffix)
        if suite_design_regressions:
            names = ", ".join(_string_list(summary.get("handoff_batch_maturity_suite_design_regression_names")))
            suffix = f" Affected promotions: {names}." if names else ""
            items.append("Resolve handoff batch suite-design regression evidence before using this single promoted run as baseline evidence." + suffix)
        elif unclean_required and not ci_regressions:
            items.append("Resolve handoff clean batch-review requirements before using this single promoted run as baseline evidence.")
        elif batch_blockers:
            items.append("Resolve selected handoff batch blocker actions before using this single promoted run as baseline evidence.")
        elif batch_reviews:
            items.append("Review selected handoff batch actions before using this single promoted run as baseline evidence.")
        return items
    if blocked_count or review_count:
        return ["Resolve review or blocked promotions before building a training scale comparison."]
    return ["Create at least one promoted training scale promotion before building the index."]


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


def _sum_reason_counts(values: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        for reason, count in _int_mapping(value).items():
            result[reason] = result.get(reason, 0) + count
    return dict(sorted(result.items()))


def _suite_guard(report: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    guard = _dict(report.get("suite_guard"))
    required = guard.get("handoff_require_suite_consistency")
    if required is None:
        required = guard.get("require_suite_consistency")
    if required is None:
        required = summary.get("handoff_require_suite_consistency")
    if required is None:
        required = summary.get("require_suite_consistency")
    return {
        "handoff_require_suite_consistency": bool(required),
        "handoff_suite_consistency": first_present(
            guard.get("handoff_suite_consistency"),
            guard.get("suite_consistency"),
            summary.get("handoff_suite_consistency"),
            summary.get("suite_consistency"),
        ),
        "handoff_suite_mismatch_count": first_present(
            guard.get("handoff_suite_mismatch_count"),
            guard.get("suite_mismatch_count"),
            summary.get("handoff_suite_mismatch_count"),
            summary.get("suite_mismatch_count"),
        ),
        "handoff_selected_suite_path": first_present(
            guard.get("handoff_selected_suite_path"),
            guard.get("selected_suite_path"),
            summary.get("handoff_selected_suite_path"),
            summary.get("selected_suite_path"),
        ),
    }


def _clean_batch_review_guard(report: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    guard = _dict(report.get("clean_batch_review_guard"))
    required = first_present(
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
            guard.get("handoff_clean_batch_review_status"),
            guard.get("clean_batch_review_status"),
            summary.get("handoff_clean_batch_review_status"),
            summary.get("clean_batch_review_status"),
        ),
        "handoff_batch_maturity_ci_regression_count": first_present(
            guard.get("handoff_batch_maturity_ci_regression_count"),
            guard.get("batch_maturity_ci_regression_count"),
            summary.get("handoff_batch_maturity_ci_regression_count"),
            summary.get("batch_maturity_ci_regression_count"),
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": _int_mapping(
            first_present(
                guard.get("handoff_batch_maturity_ci_regression_reason_counts"),
                guard.get("batch_maturity_ci_regression_reason_counts"),
                summary.get("handoff_batch_maturity_ci_regression_reason_counts"),
                summary.get("batch_maturity_ci_regression_reason_counts"),
            )
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(
            first_present(
                guard.get("handoff_batch_maturity_ci_regression_names"),
                guard.get("batch_maturity_ci_regression_names"),
                summary.get("handoff_batch_maturity_ci_regression_names"),
                summary.get("batch_maturity_ci_regression_names"),
            )
        ),
        "handoff_batch_maturity_suite_design_regression_count": first_present(
            guard.get("handoff_batch_maturity_suite_design_regression_count"),
            guard.get("batch_maturity_suite_design_regression_count"),
            summary.get("handoff_batch_maturity_suite_design_regression_count"),
            summary.get("batch_maturity_suite_design_regression_count"),
        ),
        "handoff_batch_maturity_suite_design_regression_names": _string_list(
            first_present(
                guard.get("handoff_batch_maturity_suite_design_regression_names"),
                guard.get("batch_maturity_suite_design_regression_names"),
                summary.get("handoff_batch_maturity_suite_design_regression_names"),
                summary.get("batch_maturity_suite_design_regression_names"),
            )
        ),
    }
