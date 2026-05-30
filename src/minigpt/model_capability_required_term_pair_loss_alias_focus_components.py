from __future__ import annotations

from typing import Any


def case_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if str(row.get("expected_term") or "").casefold() != "loss":
        return None
    case_id = str(row.get("case_id") or "")
    prompt = str(row.get("prompt") or "")
    if not case_id or not prompt:
        return None
    return {
        "case_id": case_id,
        "case_type": str(row.get("case_type") or "unknown"),
        "alias_group": str(row.get("alias_group") or "unknown"),
        "prompt": prompt,
        "expected_term": "loss",
    }


def case_lines(case: dict[str, Any], label: str) -> list[str]:
    prompt = str(case.get("prompt") or "")
    term = str(case.get("expected_term") or "loss")
    return [f"{prompt}{term}", f"{prompt} {term}", f"{label} alias {prompt} means {term}", f"{label} continue {prompt}{term}"]


def sorted_cases(cases: Any) -> list[dict[str, Any]]:
    order = {"source": 0, "heldout": 1}
    return sorted([dict(case) for case in cases], key=lambda row: (order.get(str(row.get("case_type")), 9), str(row.get("case_id"))))


def clean_seeds(seeds: tuple[int, ...] | list[int]) -> list[int]:
    clean: list[int] = []
    for seed in seeds:
        value = int(seed)
        if value not in clean:
            clean.append(value)
    return clean


def preview(value: Any, limit: int = 90) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 1] + "..."


def focus_decision(seed_count: int, pass_count: int, focus_full_count: int, support_full_count: int) -> str:
    if seed_count == 0:
        return "loss_alias_focus_no_seeds"
    if pass_count < seed_count:
        return "loss_alias_focus_structural_failures"
    if support_full_count == seed_count:
        return "loss_alias_focus_support_full_hit"
    if focus_full_count == seed_count:
        return "loss_alias_focus_missed_rows_repaired"
    if focus_full_count > 0:
        return "loss_alias_focus_seed_dependent_repair"
    return "loss_alias_focus_no_repair"


def focus_metric_decision(
    strict_decision: str,
    seed_count: int,
    focus_normalized_full_count: int,
    support_normalized_full_count: int,
    normalization_gain_count: int,
) -> str:
    if strict_decision != "loss_alias_focus_no_repair":
        return strict_decision
    if seed_count > 0 and support_normalized_full_count == seed_count and normalization_gain_count > 0:
        return "loss_alias_focus_strict_miss_normalized_support_full_signal"
    if seed_count > 0 and focus_normalized_full_count == seed_count and normalization_gain_count > 0:
        return "loss_alias_focus_strict_miss_normalized_focus_signal"
    if normalization_gain_count > 0:
        return "loss_alias_focus_strict_miss_normalized_partial_signal"
    return strict_decision


def focus_surface_decision(
    strict_decision: str,
    seed_count: int,
    focus_newline_cleanup_full_count: int,
    support_newline_cleanup_full_count: int,
    newline_cleanup_gain_count: int,
) -> str:
    if strict_decision != "loss_alias_focus_no_repair":
        return strict_decision
    if seed_count > 0 and support_newline_cleanup_full_count == seed_count and newline_cleanup_gain_count > 0:
        return "loss_alias_focus_strict_miss_newline_cleanup_support_full_signal"
    if seed_count > 0 and focus_newline_cleanup_full_count == seed_count and newline_cleanup_gain_count > 0:
        return "loss_alias_focus_strict_miss_newline_cleanup_focus_signal"
    if newline_cleanup_gain_count > 0:
        return "loss_alias_focus_strict_miss_newline_cleanup_partial_signal"
    return strict_decision
