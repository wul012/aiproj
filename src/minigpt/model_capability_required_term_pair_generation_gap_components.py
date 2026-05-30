from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict, list_of_dicts


def build_generation_gap_rows(
    forced_choice_report: dict[str, Any],
    branch_retention_report: dict[str, Any],
) -> list[dict[str, Any]]:
    probe_index = _probe_index(branch_retention_report)
    rows: list[dict[str, Any]] = []
    for prompt in list_of_dicts(forced_choice_report.get("prompt_summaries")):
        key = (
            str(prompt.get("run_id") or ""),
            str(prompt.get("prompt_term") or ""),
        )
        probe = probe_index.get(key, {})
        forced_expected = bool(prompt.get("expected_is_best"))
        generation_hit = int(probe.get("continuation_hit_count") or 0) > 0
        rows.append(
            {
                "run_id": prompt.get("run_id"),
                "pair_id": prompt.get("pair_id"),
                "variant_id": prompt.get("variant_id"),
                "variant_label": prompt.get("variant_label"),
                "prompt_term": prompt.get("prompt_term"),
                "expected_term": prompt.get("expected_term"),
                "forced_best_candidate_term": prompt.get("best_candidate_term"),
                "forced_expected_is_best": forced_expected,
                "forced_expected_rank": prompt.get("expected_rank"),
                "forced_expected_avg_nll": prompt.get("expected_avg_nll"),
                "forced_expected_margin_vs_best": prompt.get("expected_margin_vs_best"),
                "generation_continuation_hit": generation_hit,
                "generation_continuation_hit_count": int(probe.get("continuation_hit_count") or 0),
                "generation_generated_hit_count": int(probe.get("generated_hit_count") or 0),
                "generation_continuation_preview": probe.get("continuation_preview"),
                "generation_generated_preview": probe.get("generated_preview"),
                "gap_class": classify_generation_gap(forced_expected, generation_hit),
            }
        )
    return rows


def summarize_generation_gap_variants(
    forced_choice_report: dict[str, Any],
    branch_retention_report: dict[str, Any],
    gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forced_index = {str(row.get("run_id") or ""): row for row in list_of_dicts(forced_choice_report.get("variant_summaries"))}
    generation_index = {
        str(row.get("variant_id") or ""): row for row in list_of_dicts(branch_retention_report.get("variant_summaries"))
    }
    variant_ids = sorted({str(row.get("variant_id") or "") for row in gap_rows if row.get("variant_id")})
    rows: list[dict[str, Any]] = []
    for variant_id in variant_ids:
        prompts = [row for row in gap_rows if str(row.get("variant_id") or "") == variant_id]
        forced = _forced_for_variant(forced_index, prompts)
        generation = generation_index.get(variant_id, {})
        counts = _gap_counts(prompts)
        rows.append(
            {
                "variant_id": variant_id,
                "variant_label": prompts[0].get("variant_label") if prompts else forced.get("variant_label"),
                "run_id": forced.get("run_id") or (prompts[0].get("run_id") if prompts else None),
                "prompt_count": len(prompts),
                "forced_expected_best_count": int(forced.get("expected_best_count") or 0),
                "forced_choice_full_match": bool(forced.get("forced_choice_full_match")),
                "generation_hit_count": int(generation.get("hit_count") or 0),
                "generation_pair_full_hit": bool(generation.get("pair_full_hit")),
                "generation_hit_terms": [str(term) for term in generation.get("hit_terms") or []],
                "generation_missed_terms": [str(term) for term in generation.get("missed_terms") or []],
                "gap_counts": counts,
                "forced_generation_gap": bool(forced.get("forced_choice_full_match")) and not bool(generation.get("pair_full_hit")),
            }
        )
    return rows


def summarize_required_term_pair_generation_gap(
    forced_choice_report: dict[str, Any],
    branch_retention_report: dict[str, Any],
    gap_rows: list[dict[str, Any]],
    variant_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    forced_summary = as_dict(forced_choice_report.get("summary"))
    branch_summary = as_dict(branch_retention_report.get("summary"))
    counts = _gap_counts(gap_rows)
    forced_full = int(forced_summary.get("forced_choice_full_match_variant_count") or 0)
    generation_full = int(branch_summary.get("pair_full_hit_variant_count") or 0)
    gap_variants = sum(1 for row in variant_summaries if row.get("forced_generation_gap"))
    best_gap = _best_gap_variant(variant_summaries)
    return {
        "generation_gap_decision": _generation_gap_decision(forced_full, generation_full, counts, gap_variants),
        "source_forced_choice_decision": forced_summary.get("forced_choice_diagnostic_decision"),
        "source_branch_retention_sweep_decision": branch_summary.get("branch_retention_sweep_decision"),
        "prompt_count": len(gap_rows),
        "variant_count": len(variant_summaries),
        "forced_choice_full_match_variant_count": forced_full,
        "generation_full_match_variant_count": generation_full,
        "forced_generation_gap_variant_count": gap_variants,
        "aligned_hit_prompt_count": counts.get("aligned_hit", 0),
        "internal_only_prompt_count": counts.get("internal_only", 0),
        "generation_only_prompt_count": counts.get("generation_only", 0),
        "aligned_miss_prompt_count": counts.get("aligned_miss", 0),
        "best_gap_variant_id": best_gap.get("variant_id"),
        "best_gap_variant_internal_only_count": as_dict(best_gap.get("gap_counts")).get("internal_only"),
    }


def classify_generation_gap(forced_expected: bool, generation_hit: bool) -> str:
    if forced_expected and generation_hit:
        return "aligned_hit"
    if forced_expected and not generation_hit:
        return "internal_only"
    if not forced_expected and generation_hit:
        return "generation_only"
    return "aligned_miss"


def _probe_index(report: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for row in list_of_dicts(report.get("probe_rows")):
        rows[(str(row.get("branch_retention_run_id") or ""), str(row.get("term") or ""))] = row
    return rows


def _forced_for_variant(forced_index: dict[str, dict[str, Any]], prompts: list[dict[str, Any]]) -> dict[str, Any]:
    for prompt in prompts:
        row = forced_index.get(str(prompt.get("run_id") or ""))
        if row:
            return row
    return {}


def _gap_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"aligned_hit": 0, "internal_only": 0, "generation_only": 0, "aligned_miss": 0}
    for row in rows:
        gap_class = str(row.get("gap_class") or "")
        if gap_class in counts:
            counts[gap_class] += 1
    return {key: value for key, value in counts.items() if value}


def _best_gap_variant(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            int(as_dict(row.get("gap_counts")).get("internal_only") or 0),
            bool(row.get("forced_generation_gap")),
            int(row.get("forced_expected_best_count") or 0),
            str(row.get("variant_id") or ""),
        ),
    )


def _generation_gap_decision(
    forced_full: int,
    generation_full: int,
    counts: dict[str, int],
    gap_variants: int,
) -> str:
    if forced_full <= 0:
        return "generation_gap_no_internal_full_match"
    if generation_full > 0:
        return "generation_gap_generation_aligned"
    if gap_variants > 0 or counts.get("internal_only", 0) > 0:
        return "generation_gap_internal_signal_not_expressed"
    return "generation_gap_no_expression_delta"
