from __future__ import annotations

from typing import Any

from minigpt.report_utils import list_of_dicts


def select_prefix_completion_targets(path_trace_report: dict[str, Any], *, variant_limit: int | None = 1) -> list[dict[str, Any]]:
    rows = [
        row
        for row in list_of_dicts(path_trace_report.get("probe_rows"))
        if row.get("checkpoint_path") and row.get("tokenizer_path") and row.get("expected_term")
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("variant_id") or ""), []).append(row)
    targets = [{"variant_id": key, "probe_count": len(value), "probes": value} for key, value in sorted(grouped.items()) if key]
    if variant_limit is not None and variant_limit >= 0:
        return targets[:variant_limit]
    return targets


def summarize_prefix_completion_probe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            str(row.get("variant_id") or ""),
            str(row.get("profile_id") or ""),
            str(row.get("prompt_term") or ""),
        )
        grouped.setdefault(key, []).append(row)
    for (_variant, _profile, _prompt), group in sorted(grouped.items()):
        group.sort(key=lambda row: int(row.get("forced_prefix_token_count") or 0))
        hits = [row for row in group if row.get("prefix_completion_hit")]
        first_hit = hits[0] if hits else {}
        full_prefix = group[-1] if group else {}
        summaries.append(
            {
                "variant_id": full_prefix.get("variant_id"),
                "profile_id": full_prefix.get("profile_id"),
                "prompt_term": full_prefix.get("prompt_term"),
                "expected_term": full_prefix.get("expected_term"),
                "expected_token_count": full_prefix.get("expected_token_count"),
                "tested_prefix_count": len(group),
                "hit_prefix_count": len(hits),
                "minimum_hit_prefix_token_count": first_hit.get("forced_prefix_token_count"),
                "full_prefix_hit": bool(full_prefix.get("prefix_completion_hit")),
                "one_token_prefix_hit": any(int(row.get("forced_prefix_token_count") or 0) == 1 and row.get("prefix_completion_hit") for row in group),
                "best_completion_preview": (first_hit or full_prefix).get("completion_preview"),
            }
        )
    return summaries


def summarize_required_term_pair_prefix_completion_sweep(
    targets: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    probe_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    full_prefix_hits = sum(1 for row in probe_summaries if row.get("full_prefix_hit"))
    one_token_hits = sum(1 for row in probe_summaries if row.get("one_token_prefix_hit"))
    any_hits = sum(1 for row in probe_summaries if int(row.get("hit_prefix_count") or 0) > 0)
    return {
        "prefix_completion_sweep_decision": _decision(probe_summaries, full_prefix_hits, one_token_hits),
        "target_count": len(targets),
        "prefix_row_count": len(rows),
        "probe_summary_count": len(probe_summaries),
        "any_prefix_hit_probe_count": any_hits,
        "one_token_prefix_hit_probe_count": one_token_hits,
        "full_prefix_hit_probe_count": full_prefix_hits,
        "span_completion_gap_probe_count": max(0, len(probe_summaries) - one_token_hits),
    }


def _decision(summaries: list[dict[str, Any]], full_prefix_hits: int, one_token_hits: int) -> str:
    if not summaries:
        return "prefix_completion_no_probes"
    if one_token_hits == len(summaries):
        return "prefix_completion_one_token_sufficient"
    if full_prefix_hits == len(summaries):
        return "prefix_completion_requires_longer_prefix"
    if full_prefix_hits > 0:
        return "prefix_completion_partial_span_repair"
    return "prefix_completion_not_recovered"
