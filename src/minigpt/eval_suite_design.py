from __future__ import annotations

from typing import Any

from minigpt.eval_suite import (
    COMPARISON_RECOMMENDED_DIFFICULTIES,
    MIN_COMPARISON_CASES,
    MIN_COMPARISON_TAGS,
    MIN_COMPARISON_TASK_TYPES,
    MIN_RECOMMENDED_CASES,
    MIN_RECOMMENDED_TAGS,
    PromptSuite,
    RECOMMENDED_DIFFICULTIES,
    RECOMMENDED_TASK_TYPES,
)
from minigpt.report_utils import list_of_dicts


def summarize_prompt_suite_design(suite: PromptSuite | dict[str, Any]) -> dict[str, Any]:
    payload = suite.to_dict() if isinstance(suite, PromptSuite) else dict(suite)
    cases = list_of_dicts(payload.get("cases"))
    task_type_counts = _count_by(case.get("task_type") or "general" for case in cases)
    difficulty_counts = _count_by(case.get("difficulty") or "medium" for case in cases)
    tag_counts = _count_by(tag for case in cases for tag in _string_list(case.get("tags")))
    token_budgets = [_positive_int(case.get("max_new_tokens")) for case in cases if _positive_int(case.get("max_new_tokens")) is not None]
    seed_values = [str(case.get("seed")) for case in cases if case.get("seed") not in {None, ""}]
    missing_task_types = [task_type for task_type in RECOMMENDED_TASK_TYPES if task_type not in task_type_counts]
    missing_difficulties = [difficulty for difficulty in RECOMMENDED_DIFFICULTIES if difficulty not in difficulty_counts]
    missing_comparison_difficulties = [
        difficulty for difficulty in COMPARISON_RECOMMENDED_DIFFICULTIES if difficulty not in difficulty_counts
    ]
    blockers = _coverage_blockers(
        case_count=len(cases),
        task_type_counts=task_type_counts,
        difficulty_counts=difficulty_counts,
        tag_counts=tag_counts,
        missing_task_types=missing_task_types,
        missing_difficulties=missing_difficulties,
    )
    comparison_blockers = _comparison_blockers(
        case_count=len(cases),
        task_type_counts=task_type_counts,
        tag_counts=tag_counts,
        missing_comparison_difficulties=missing_comparison_difficulties,
    )
    coverage_status = "pass" if not blockers else "warn"
    comparison_status = "pass" if coverage_status == "pass" and not comparison_blockers else "warn"
    return {
        "suite_name": payload.get("suite_name") or payload.get("name"),
        "suite_version": payload.get("suite_version") or payload.get("version"),
        "language": payload.get("language"),
        "case_count": len(cases),
        "task_type_counts": task_type_counts,
        "difficulty_counts": difficulty_counts,
        "tag_counts": tag_counts,
        "task_type_count": len(task_type_counts),
        "difficulty_count": len(difficulty_counts),
        "tag_count": len(tag_counts),
        "observed_task_types": sorted(task_type_counts),
        "observed_difficulties": sorted(difficulty_counts),
        "observed_tags": sorted(tag_counts),
        "min_new_tokens": min(token_budgets) if token_budgets else None,
        "max_new_tokens": max(token_budgets) if token_budgets else None,
        "unique_seed_count": len(set(seed_values)),
        "duplicate_seed_count": max(0, len(seed_values) - len(set(seed_values))),
        "all_cases_have_expected_behavior": all(bool(str(case.get("expected_behavior") or "").strip()) for case in cases),
        "all_cases_have_tags": all(bool(_string_list(case.get("tags"))) for case in cases),
        "coverage_status": coverage_status,
        "comparison_status": comparison_status,
        "decision": "suite_design_ready" if coverage_status == "pass" else "expand_suite_design_before_quality_claims",
        "comparison_decision": "suite_design_ready_for_repeated_checkpoint_comparison"
        if comparison_status == "pass"
        else "prefer_standard_suite_before_checkpoint_quality_claims",
        "missing_recommended_task_types": missing_task_types,
        "missing_recommended_difficulties": missing_difficulties,
        "missing_comparison_difficulties": missing_comparison_difficulties,
        "blockers": blockers,
        "comparison_blockers": comparison_blockers,
    }


def _coverage_blockers(
    *,
    case_count: int,
    task_type_counts: dict[str, int],
    difficulty_counts: dict[str, int],
    tag_counts: dict[str, int],
    missing_task_types: list[str],
    missing_difficulties: list[str],
) -> list[str]:
    blockers: list[str] = []
    if case_count < MIN_RECOMMENDED_CASES:
        blockers.append(f"only {case_count} case(s), expected at least {MIN_RECOMMENDED_CASES}")
    if missing_task_types:
        blockers.append("missing recommended task types: " + ", ".join(missing_task_types))
    if missing_difficulties:
        blockers.append("missing recommended difficulties: " + ", ".join(missing_difficulties))
    if len(tag_counts) < MIN_RECOMMENDED_TAGS:
        blockers.append(f"only {len(tag_counts)} tag(s), expected at least {MIN_RECOMMENDED_TAGS}")
    return blockers


def _comparison_blockers(
    *,
    case_count: int,
    task_type_counts: dict[str, int],
    tag_counts: dict[str, int],
    missing_comparison_difficulties: list[str],
) -> list[str]:
    blockers: list[str] = []
    if case_count < MIN_COMPARISON_CASES:
        blockers.append(f"only {case_count} case(s), expected at least {MIN_COMPARISON_CASES}")
    if len(task_type_counts) < MIN_COMPARISON_TASK_TYPES:
        blockers.append(f"only {len(task_type_counts)} task type(s), expected at least {MIN_COMPARISON_TASK_TYPES}")
    if missing_comparison_difficulties:
        blockers.append("missing comparison difficulties: " + ", ".join(missing_comparison_difficulties))
    if len(tag_counts) < MIN_COMPARISON_TAGS:
        blockers.append(f"only {len(tag_counts)} tag(s), expected at least {MIN_COMPARISON_TAGS}")
    return blockers


def _count_by(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or value in {None, ""}:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value if str(item).strip()]


__all__ = ["summarize_prompt_suite_design"]
