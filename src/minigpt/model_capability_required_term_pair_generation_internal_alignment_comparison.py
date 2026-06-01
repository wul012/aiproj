from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import TARGET_TERMS
from minigpt.model_capability_required_term_pair_refresh_forced_choice_diagnostic import (
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_comparison.json"
)
PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_CSV_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_comparison.csv"
)
PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_TEXT_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_comparison.txt"
)
PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_comparison.md"
)
PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_HTML_FILENAME = (
    "model_capability_required_term_pair_generation_internal_alignment_comparison.html"
)


def locate_generation_internal_alignment_refresh_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def locate_generation_internal_alignment_forced_choice_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_generation_internal_alignment_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("generation/internal alignment input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_generation_internal_alignment_comparison(
    sources: Sequence[dict[str, Any]],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_rows = [_source_row(index, source) for index, source in enumerate(sources)]
    issues = _issues(source_rows)
    summary = _summary(source_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair generation/internal alignment comparison",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_rows": source_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def make_generation_internal_alignment_source(
    *,
    label: str,
    refresh_report: dict[str, Any],
    forced_choice_report: dict[str, Any],
    refresh_path: str | Path = "",
    forced_choice_path: str | Path = "",
) -> dict[str, Any]:
    return {
        "label": label,
        "refresh_report": refresh_report,
        "forced_choice_report": forced_choice_report,
        "refresh_path": str(refresh_path),
        "forced_choice_path": str(forced_choice_path),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _source_row(index: int, source: dict[str, Any]) -> dict[str, Any]:
    label = str(source.get("label") or f"alignment-source-{index + 1}")
    refresh = as_dict(source.get("refresh_report"))
    forced = as_dict(source.get("forced_choice_report"))
    refresh_summary = as_dict(refresh.get("summary"))
    refresh_settings = as_dict(refresh.get("settings"))
    generation_terms = _generation_hit_terms(refresh)
    internal_terms = _internal_expected_best_terms(forced, label)
    generation_pair_full = set(TARGET_TERMS).issubset(generation_terms)
    internal_pair_full = set(TARGET_TERMS).issubset(internal_terms)
    return {
        "index": index,
        "source_label": label,
        "refresh_path": str(source.get("refresh_path") or ""),
        "forced_choice_path": str(source.get("forced_choice_path") or ""),
        "refresh_status": refresh.get("status"),
        "refresh_decision": refresh.get("decision"),
        "forced_choice_status": forced.get("status"),
        "forced_choice_decision": forced.get("decision"),
        "corpus_mode": refresh_settings.get("corpus_mode"),
        "seed": refresh_settings.get("seed"),
        "training_status": refresh_summary.get("training_status"),
        "checkpoint_exists": bool(refresh_summary.get("checkpoint_exists")),
        "generation_hit_terms": sorted(generation_terms),
        "generation_missed_terms": _missed_terms(generation_terms),
        "generation_pair_full": generation_pair_full,
        "internal_expected_best_terms": sorted(internal_terms),
        "internal_missed_terms": _missed_terms(internal_terms),
        "internal_pair_full": internal_pair_full,
        "generation_internal_disagreement_terms": _disagreement_terms(generation_terms, internal_terms),
        "alignment_class": _alignment_class(generation_terms, internal_terms),
    }


def _generation_hit_terms(refresh_report: dict[str, Any]) -> set[str]:
    replay = as_dict(refresh_report.get("replay_report"))
    return {
        str(row.get("term"))
        for row in list_of_dicts(replay.get("case_rows"))
        if row.get("continuation_hit") and str(row.get("term")) in TARGET_TERMS
    }


def _internal_expected_best_terms(forced_choice_report: dict[str, Any], label: str) -> set[str]:
    prompt_rows = [
        row
        for row in list_of_dicts(forced_choice_report.get("prompt_summaries"))
        if str(row.get("source_label") or "") == label
    ]
    if not prompt_rows and len(list_of_dicts(forced_choice_report.get("source_summaries"))) == 1:
        prompt_rows = list_of_dicts(forced_choice_report.get("prompt_summaries"))
    return {
        str(row.get("prompt_term"))
        for row in prompt_rows
        if row.get("expected_best") and str(row.get("prompt_term")) in TARGET_TERMS
    }


def _missed_terms(hit_terms: set[str]) -> list[str]:
    return [term for term in TARGET_TERMS if term not in hit_terms]


def _disagreement_terms(generation_terms: set[str], internal_terms: set[str]) -> list[str]:
    return sorted(generation_terms.symmetric_difference(internal_terms))


def _alignment_class(generation_terms: set[str], internal_terms: set[str]) -> str:
    generation_pair_full = set(TARGET_TERMS).issubset(generation_terms)
    internal_pair_full = set(TARGET_TERMS).issubset(internal_terms)
    if generation_pair_full and internal_pair_full:
        return "generation_internal_pair_full"
    if generation_pair_full:
        return "generation_pair_full_internal_partial"
    if not generation_terms and internal_pair_full:
        return "internal_pair_full_generation_none"
    if not generation_terms and internal_terms:
        return "internal_partial_generation_none"
    if not generation_terms:
        return "generation_none"
    if internal_pair_full:
        return "internal_pair_full_generation_gap"
    if generation_terms == {"fixed"} and internal_terms == {"fixed"}:
        return "fixed_only_aligned_partial"
    if generation_terms == {"loss"} and internal_terms == {"loss"}:
        return "loss_only_aligned_partial"
    return "partial_tradeoff"


def _issues(source_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not source_rows:
        issues.append("at least one generation/internal source is required")
    for row in source_rows:
        label = row.get("source_label")
        if row.get("refresh_status") != "pass":
            issues.append(f"{label} refresh status is not pass")
        if row.get("training_status") != "pass":
            issues.append(f"{label} training status is not pass")
        if not row.get("checkpoint_exists"):
            issues.append(f"{label} checkpoint is missing")
        if row.get("forced_choice_status") != "pass":
            issues.append(f"{label} forced-choice status is not pass")
    return issues


def _summary(source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    aligned = [row for row in source_rows if row.get("alignment_class") == "generation_internal_pair_full"]
    generation_only = [
        row for row in source_rows if row.get("alignment_class") == "generation_pair_full_internal_partial"
    ]
    internal_only = [
        row
        for row in source_rows
        if row.get("alignment_class") in {"internal_pair_full_generation_gap", "internal_pair_full_generation_none"}
    ]
    best_rows = _best_rows(source_rows)
    return {
        "compared_source_count": len(source_rows),
        "generation_pair_full_count": sum(1 for row in source_rows if row.get("generation_pair_full")),
        "internal_pair_full_count": sum(1 for row in source_rows if row.get("internal_pair_full")),
        "aligned_pair_full_count": len(aligned),
        "generation_only_pair_full_count": len(generation_only),
        "internal_only_pair_full_count": len(internal_only),
        "alignment_classes": _class_counts(source_rows),
        "best_source_labels": [str(row.get("source_label") or "") for row in best_rows],
        "best_alignment_class": str(best_rows[0].get("alignment_class") or "") if best_rows else "",
    }


def _best_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = [(row, _score(row)) for row in source_rows]
    best = max([score for _, score in scored] or [0])
    return [row for row, score in scored if score == best]


def _score(row: dict[str, Any]) -> int:
    score = 0
    if row.get("generation_pair_full"):
        score += 4
    score += len(row.get("generation_hit_terms", []))
    if row.get("internal_pair_full"):
        score += 4
    score += len(row.get("internal_expected_best_terms", []))
    return score


def _class_counts(source_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in source_rows:
        key = str(row.get("alignment_class") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_generation_internal_alignment_inputs"
    if int(summary.get("aligned_pair_full_count") or 0) > 0:
        return "select_aligned_generation_internal_pair_full_candidate"
    if int(summary.get("generation_only_pair_full_count") or 0) > 0:
        return "keep_generation_pair_full_and_repair_internal_preference"
    if int(summary.get("internal_only_pair_full_count") or 0) > 0:
        return "use_internal_pair_full_to_repair_generation"
    return "continue_required_term_pair_objective_search"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The generation/internal alignment inputs are incomplete.",
            "next_action": "repair input reports before route selection",
        }
    if int(summary.get("aligned_pair_full_count") or 0) > 0:
        return {
            "model_quality_claim": "targeted_pair_alignment_candidate",
            "reason": "At least one route has both generation pair-full and internal pair-full.",
            "next_action": "repeat the aligned candidate across seeds before promotion",
        }
    if int(summary.get("generation_only_pair_full_count") or 0) > 0:
        return {
            "model_quality_claim": "generation_pair_full_internal_partial",
            "reason": "A route generates both terms but still has partial forced-choice internal preference.",
            "next_action": "repair internal preference while preserving generation pair-full",
        }
    if int(summary.get("internal_only_pair_full_count") or 0) > 0:
        return {
            "model_quality_claim": "internal_pair_full_generation_gap",
            "reason": "A route has internal pair match but cannot release both terms in generation.",
            "next_action": "bridge generation without destroying internal preference",
        }
    return {
        "model_quality_claim": "comparison_only",
        "reason": "No compared route has pair-full evidence in either complete alignment view.",
        "next_action": "design a new objective",
    }


__all__ = [
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_CSV_FILENAME",
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_HTML_FILENAME",
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_JSON_FILENAME",
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_GENERATION_INTERNAL_ALIGNMENT_COMPARISON_TEXT_FILENAME",
    "build_model_capability_required_term_pair_generation_internal_alignment_comparison",
    "locate_generation_internal_alignment_forced_choice_report",
    "locate_generation_internal_alignment_refresh_report",
    "make_generation_internal_alignment_source",
    "read_generation_internal_alignment_report",
    "resolve_exit_code",
]
