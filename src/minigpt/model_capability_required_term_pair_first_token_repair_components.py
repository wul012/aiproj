from __future__ import annotations

from typing import Any

from minigpt.report_utils import list_of_dicts


def select_first_token_repair_targets(path_trace_report: dict[str, Any], *, variant_limit: int | None = 1) -> list[dict[str, Any]]:
    rows = [
        row
        for row in list_of_dicts(path_trace_report.get("probe_rows"))
        if row.get("first_expected_token_id") is not None and not row.get("first_sample_matches_expected_first_token")
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("variant_id") or ""), []).append(row)
    targets = [
        {"variant_id": variant_id, "probe_count": len(probes), "probes": probes}
        for variant_id, probes in sorted(grouped.items())
        if variant_id and probes
    ]
    if variant_limit is not None and variant_limit >= 0:
        return targets[:variant_limit]
    return targets


def summarize_first_token_repair_profiles(
    targets: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant_id in sorted({str(row.get("variant_id") or "") for row in repair_rows if row.get("variant_id")}):
        profile_ids = sorted({str(row.get("profile_id") or "") for row in repair_rows if str(row.get("variant_id") or "") == variant_id})
        for profile_id in profile_ids:
            group = [
                row
                for row in repair_rows
                if str(row.get("variant_id") or "") == variant_id and str(row.get("profile_id") or "") == profile_id
            ]
            hit_count = sum(1 for row in group if row.get("repaired_continuation_hit"))
            prompt_count = len(group)
            rows.append(
                {
                    "variant_id": variant_id,
                    "profile_id": profile_id,
                    "prompt_count": prompt_count,
                    "repair_count": len(group),
                    "repaired_hit_count": hit_count,
                    "repaired_profile_full_hit": bool(group) and hit_count == prompt_count,
                    "hit_terms": [str(row.get("prompt_term")) for row in group if row.get("repaired_continuation_hit")],
                    "missed_terms": [str(row.get("prompt_term")) for row in group if not row.get("repaired_continuation_hit")],
                }
            )
    return rows


def summarize_required_term_pair_first_token_repair(
    targets: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    profile_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    hit_count = sum(1 for row in repair_rows if row.get("repaired_continuation_hit"))
    source_hits = sum(1 for row in repair_rows if row.get("source_continuation_hit"))
    improved = sum(1 for row in repair_rows if row.get("repaired_continuation_hit") and not row.get("source_continuation_hit"))
    full_count = sum(1 for row in profile_summaries if row.get("repaired_profile_full_hit"))
    best = _best_profile(profile_summaries)
    return {
        "first_token_repair_decision": _repair_decision(targets, repair_rows, full_count, improved, hit_count),
        "target_count": len(targets),
        "repair_count": len(repair_rows),
        "source_continuation_hit_count": source_hits,
        "repaired_continuation_hit_count": hit_count,
        "improved_prompt_count": improved,
        "repaired_profile_full_hit_count": full_count,
        "best_variant_id": best.get("variant_id"),
        "best_profile_id": best.get("profile_id"),
        "best_profile_repaired_hit_count": best.get("repaired_hit_count"),
    }


def _best_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            bool(row.get("repaired_profile_full_hit")),
            int(row.get("repaired_hit_count") or 0),
            str(row.get("profile_id") or ""),
        ),
    )


def _repair_decision(
    targets: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    full_count: int,
    improved: int,
    hit_count: int,
) -> str:
    if not targets:
        return "first_token_repair_no_targets"
    if not repair_rows:
        return "first_token_repair_no_rows"
    if full_count > 0:
        return "first_token_repair_full_expression_recovered"
    if improved > 0:
        return "first_token_repair_improved_partial_expression"
    if hit_count > 0:
        return "first_token_repair_preserved_partial_expression"
    return "first_token_repair_no_expression"
