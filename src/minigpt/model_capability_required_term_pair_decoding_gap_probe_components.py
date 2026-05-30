from __future__ import annotations

from typing import Any

from minigpt.report_utils import list_of_dicts


def default_decoding_gap_profiles() -> list[dict[str, Any]]:
    return [
        {"profile_id": "greedy-12", "max_new_tokens": 12, "temperature": 0.2, "top_k": 1, "seed": 505},
        {"profile_id": "greedy-24", "max_new_tokens": 24, "temperature": 0.2, "top_k": 1, "seed": 505},
        {"profile_id": "top2-24", "max_new_tokens": 24, "temperature": 0.35, "top_k": 2, "seed": 1505},
    ]


def select_decoding_gap_targets(
    generation_gap_report: dict[str, Any],
    forced_choice_report: dict[str, Any],
    *,
    variant_limit: int | None = 1,
) -> list[dict[str, Any]]:
    gap_variants = [
        row for row in list_of_dicts(generation_gap_report.get("variant_summaries")) if row.get("forced_generation_gap")
    ]
    gap_variants.sort(
        key=lambda row: (
            -int(row.get("forced_expected_best_count") or 0),
            str(row.get("variant_id") or ""),
        )
    )
    run_index = {str(row.get("variant_id") or ""): row for row in list_of_dicts(forced_choice_report.get("runs"))}
    rows: list[dict[str, Any]] = []
    for variant in gap_variants:
        variant_id = str(variant.get("variant_id") or "")
        run = run_index.get(variant_id, {})
        if not run:
            continue
        prompts = [
            row
            for row in list_of_dicts(generation_gap_report.get("gap_rows"))
            if str(row.get("variant_id") or "") == variant_id and row.get("forced_expected_is_best")
        ]
        if not prompts:
            continue
        rows.append(
            {
                "variant_id": variant_id,
                "variant_label": variant.get("variant_label"),
                "run_id": run.get("run_id"),
                "pair_id": run.get("pair_id"),
                "checkpoint_path": run.get("checkpoint_path"),
                "tokenizer_path": run.get("tokenizer_path"),
                "prompts": prompts,
            }
        )
    if variant_limit is not None and variant_limit >= 0:
        return rows[:variant_limit]
    return rows


def summarize_decoding_gap_profiles(
    targets: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target_prompt_counts = {str(row.get("variant_id") or ""): len(list_of_dicts(row.get("prompts"))) for row in targets}
    for variant_id in sorted({str(row.get("variant_id") or "") for row in probe_rows if row.get("variant_id")}):
        for profile in profiles:
            profile_id = str(profile.get("profile_id") or "")
            group = [
                row
                for row in probe_rows
                if str(row.get("variant_id") or "") == variant_id and str(row.get("profile_id") or "") == profile_id
            ]
            hit_count = sum(1 for row in group if row.get("continuation_hit"))
            prompt_count = target_prompt_counts.get(variant_id, len(group))
            rows.append(
                {
                    "variant_id": variant_id,
                    "profile_id": profile_id,
                    "prompt_count": prompt_count,
                    "probe_count": len(group),
                    "continuation_hit_count": hit_count,
                    "profile_full_hit": bool(group) and hit_count == prompt_count,
                    "hit_terms": [str(row.get("prompt_term")) for row in group if row.get("continuation_hit")],
                    "missed_terms": [str(row.get("prompt_term")) for row in group if not row.get("continuation_hit")],
                }
            )
    return rows


def summarize_required_term_pair_decoding_gap_probe(
    targets: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    profile_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    full_count = sum(1 for row in profile_summaries if row.get("profile_full_hit"))
    hit_count = sum(1 for row in probe_rows if row.get("continuation_hit"))
    best = _best_profile(profile_summaries)
    return {
        "decoding_gap_probe_decision": _probe_decision(targets, probe_rows, full_count, hit_count),
        "target_count": len(targets),
        "profile_count": len(profiles),
        "probe_count": len(probe_rows),
        "continuation_hit_count": hit_count,
        "profile_full_hit_count": full_count,
        "best_variant_id": best.get("variant_id"),
        "best_profile_id": best.get("profile_id"),
        "best_profile_hit_count": best.get("continuation_hit_count"),
    }


def _best_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            bool(row.get("profile_full_hit")),
            int(row.get("continuation_hit_count") or 0),
            str(row.get("profile_id") or ""),
        ),
    )


def _probe_decision(targets: list[dict[str, Any]], probe_rows: list[dict[str, Any]], full_count: int, hit_count: int) -> str:
    if not targets:
        return "decoding_gap_probe_no_targets"
    if not probe_rows:
        return "decoding_gap_probe_no_generation_rows"
    if full_count > 0:
        return "decoding_gap_probe_generation_expression_found"
    if hit_count > 0:
        return "decoding_gap_probe_partial_expression_only"
    return "decoding_gap_probe_no_expression"
