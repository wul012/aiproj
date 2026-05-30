from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict, list_of_dicts


def select_decoding_path_trace_targets(
    decoding_gap_probe: dict[str, Any],
    *,
    variant_limit: int | None = 1,
) -> list[dict[str, Any]]:
    best_variant = str(as_dict(decoding_gap_probe.get("summary")).get("best_variant_id") or "")
    rows = [
        row
        for row in list_of_dicts(decoding_gap_probe.get("probe_rows"))
        if not best_variant or str(row.get("variant_id") or "") == best_variant
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("variant_id") or ""), []).append(row)
    targets = [
        {
            "variant_id": variant_id,
            "probe_count": len(probes),
            "probes": probes,
        }
        for variant_id, probes in sorted(grouped.items())
        if variant_id and probes
    ]
    if variant_limit is not None and variant_limit >= 0:
        return targets[:variant_limit]
    return targets


def summarize_decoding_path_probe_rows(probe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for row in probe_rows:
        first_match = bool(row.get("first_sample_matches_expected_first_token"))
        continuation_hit = bool(row.get("continuation_hit"))
        summaries.append(
            {
                "variant_id": row.get("variant_id"),
                "profile_id": row.get("profile_id"),
                "prompt_term": row.get("prompt_term"),
                "expected_term": row.get("expected_term"),
                "continuation_hit": continuation_hit,
                "first_expected_token_rank": row.get("first_expected_token_rank"),
                "first_sample_text": row.get("first_sample_text"),
                "first_sample_matches_expected_first_token": first_match,
                "late_hit_after_first_miss": continuation_hit and not first_match,
                "expected_first_token_seen_step": row.get("expected_first_token_seen_step"),
                "continuation_preview": row.get("continuation_preview"),
            }
        )
    return summaries


def summarize_required_term_pair_decoding_path_trace(
    targets: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    probe_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    continuation_hits = sum(1 for row in probe_summaries if row.get("continuation_hit"))
    first_matches = sum(1 for row in probe_summaries if row.get("first_sample_matches_expected_first_token"))
    late_hits = sum(1 for row in probe_summaries if row.get("late_hit_after_first_miss"))
    rank_le_5 = sum(1 for row in probe_summaries if _rank_le(row.get("first_expected_token_rank"), 5))
    return {
        "decoding_path_trace_decision": _trace_decision(probe_summaries, first_matches, late_hits),
        "target_count": len(targets),
        "probe_count": len(probe_summaries),
        "trace_step_count": sum(len(list_of_dicts(row.get("steps"))) for row in probe_rows),
        "continuation_hit_count": continuation_hits,
        "first_sample_match_count": first_matches,
        "late_hit_after_first_miss_count": late_hits,
        "first_expected_rank_le_5_count": rank_le_5,
        "first_sample_miss_count": max(0, len(probe_summaries) - first_matches),
    }


def _trace_decision(probe_summaries: list[dict[str, Any]], first_matches: int, late_hits: int) -> str:
    if not probe_summaries:
        return "decoding_path_trace_no_probes"
    if late_hits > 0:
        return "decoding_path_trace_late_expression_after_first_miss"
    if first_matches > 0:
        return "decoding_path_trace_first_token_expression_observed"
    return "decoding_path_trace_first_token_miss"


def _rank_le(value: Any, limit: int) -> bool:
    try:
        return int(value) <= limit
    except (TypeError, ValueError):
        return False
