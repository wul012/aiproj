from __future__ import annotations

from typing import Any


def summarize_required_term_pair_capacity_sweep(
    pairs: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    capacity_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    variant_pair_summaries: list[dict[str, Any]],
    pair_capacity_summaries: list[dict[str, Any]],
    *,
    source_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_summary or {}
    run_count = len(capacity_rows)
    training_pass_count = sum(1 for row in capacity_rows if row.get("training_status") == "pass")
    checkpoint_count = sum(1 for row in capacity_rows if row.get("checkpoint_exists"))
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in probe_rows)
    probe_hits = sum(1 for row in probe_rows if int(row.get("continuation_hit_count") or 0) > 0)
    full_variant_pairs = sum(1 for row in variant_pair_summaries if row.get("pair_full_hit"))
    partial_variant_pairs = sum(1 for row in variant_pair_summaries if row.get("pair_partial_hit"))
    full_pairs = sum(1 for row in pair_capacity_summaries if row.get("capacity_full_hit_observed"))
    best = _best_variant_pair_summary(variant_pair_summaries)
    return {
        "pair_capacity_sweep_decision": _capacity_sweep_decision(
            pairs,
            variants,
            capacity_rows,
            probe_rows,
            training_pass_count,
            full_variant_pairs,
            partial_variant_pairs,
        ),
        "source_pair_rebalance_seed_stability_decision": source.get("pair_rebalance_seed_stability_decision"),
        "source_stable_pair_count": int(source.get("stable_pair_count") or 0),
        "source_pair_seed_full_hit_count": int(source.get("pair_seed_full_hit_count") or 0),
        "source_pair_seed_full_hit_rate": source.get("pair_seed_full_hit_rate"),
        "selected_pair_count": len(pairs),
        "variant_count": len(variants),
        "variant_run_count": run_count,
        "probe_count": len(probe_rows),
        "training_pass_count": training_pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "continuation_hit_count": continuation_hits,
        "probe_hit_count": probe_hits,
        "probe_success_rate": round(probe_hits / len(probe_rows), 4) if probe_rows else 0.0,
        "variant_pair_full_hit_count": full_variant_pairs,
        "variant_pair_partial_hit_count": partial_variant_pairs,
        "variant_pair_zero_hit_count": max(0, len(variant_pair_summaries) - full_variant_pairs - partial_variant_pairs),
        "variant_pair_full_hit_rate": round(full_variant_pairs / len(variant_pair_summaries), 4)
        if variant_pair_summaries
        else 0.0,
        "capacity_full_hit_pair_count": full_pairs,
        "capacity_full_hit_observed": full_pairs > 0,
        "best_variant_id": best.get("variant_id"),
        "best_variant_label": best.get("variant_label"),
        "best_variant_hit_count": best.get("hit_count"),
        "best_variant_pair_full_hit": best.get("pair_full_hit"),
        "capacity_sweep_improved": full_pairs > 0,
    }


def summarize_capacity_variant_probe_rows(
    pairs: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        term_names = [str(term) for term in pair.get("term_names") or []]
        for variant in variants:
            variant_id = str(variant.get("variant_id") or "")
            probes = [
                row
                for row in probe_rows
                if str(row.get("pair_id") or "") == pair_id and str(row.get("variant_id") or "") == variant_id
            ]
            hit_terms = [str(row.get("term") or "") for row in probes if int(row.get("continuation_hit_count") or 0) > 0]
            rows.append(
                {
                    "pair_id": pair_id,
                    "variant_id": variant_id,
                    "variant_label": variant.get("label"),
                    "term_names": term_names,
                    "hit_terms": hit_terms,
                    "missed_terms": [term for term in term_names if term not in hit_terms],
                    "hit_count": len(hit_terms),
                    "hit_rate": round(len(hit_terms) / len(term_names), 4) if term_names else 0.0,
                    "pair_full_hit": bool(term_names) and len(hit_terms) == len(term_names),
                    "pair_partial_hit": 0 < len(hit_terms) < len(term_names),
                }
            )
    return rows


def summarize_pair_capacity_sweep(
    pairs: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    variant_pair_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        pair_rows = [row for row in variant_pair_summaries if str(row.get("pair_id") or "") == pair_id]
        full_hit_variants = [str(row.get("variant_id") or "") for row in pair_rows if row.get("pair_full_hit")]
        partial_hit_variants = [str(row.get("variant_id") or "") for row in pair_rows if row.get("pair_partial_hit")]
        best = _best_variant_pair_summary(pair_rows)
        rows.append(
            {
                "pair_id": pair_id,
                "term_names": pair.get("term_names") or [],
                "variant_count": len(variants),
                "full_hit_variant_count": len(full_hit_variants),
                "full_hit_variants": full_hit_variants,
                "partial_hit_variants": partial_hit_variants,
                "capacity_full_hit_observed": bool(full_hit_variants),
                "best_variant_id": best.get("variant_id"),
                "best_variant_label": best.get("variant_label"),
                "best_variant_hit_count": best.get("hit_count"),
                "best_variant_pair_full_hit": best.get("pair_full_hit"),
            }
        )
    return rows


def capacity_sweep_decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_capacity_sweep"
    if summary.get("capacity_full_hit_observed"):
        return "required_term_pair_capacity_sweep_recovered"
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "required_term_pair_capacity_sweep_partial"
    return "required_term_pair_capacity_sweep_not_recovered"


def source_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_rebalance_seed_stability_decision": summary.get("pair_rebalance_seed_stability_decision"),
        "source_pair_rebalance_decision": summary.get("source_pair_rebalance_decision"),
        "selected_pair_count": summary.get("selected_pair_count"),
        "seed_count": summary.get("seed_count"),
        "pair_seed_full_hit_count": summary.get("pair_seed_full_hit_count"),
        "stable_pair_count": summary.get("stable_pair_count"),
        "pair_rebalance_seed_stable": summary.get("pair_rebalance_seed_stable"),
    }


def model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("capacity_full_hit_observed"):
        return "pair_capacity_sweep_recovered_signal_only"
    return "not_claimed"


def interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "At least one capacity sweep input or training run failed, so no capacity conclusion is available."
    if summary.get("capacity_full_hit_observed"):
        return "At least one capacity variant recovered a full-hit pair for the fragile v496 target."
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "The sweep still produced only partial pair hits; capacity changes did not recover the v495 full-hit."
    return "The sweep produced no required-term continuation hits for the selected fragile pair."


def next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed capacity sweep inputs or training runs before changing curriculum size"
    if summary.get("capacity_full_hit_observed"):
        return "repeat the recovered capacity variant across seeds before using it as a bridge to three-term curricula"
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "inspect corpus prompts and generation decoding before adding more terms to the checkpoint"
    return "step back to single-pair corpus design before increasing model size"


def _capacity_sweep_decision(
    pairs: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    capacity_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    training_pass_count: int,
    full_variant_pair_count: int,
    partial_variant_pair_count: int,
) -> str:
    if not pairs:
        return "no_fragile_pairs_selected"
    if not variants:
        return "no_capacity_variants_configured"
    if training_pass_count != len(capacity_rows):
        return "pair_capacity_sweep_training_failed"
    if not probe_rows:
        return "pair_capacity_sweep_generation_missing"
    if full_variant_pair_count > 0:
        return "pair_capacity_sweep_full_hit_recovered"
    if partial_variant_pair_count > 0:
        return "pair_capacity_sweep_partial_only"
    return "pair_capacity_sweep_not_recovered"


def _best_variant_pair_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return sorted(
        rows,
        key=lambda row: (
            int(bool(row.get("pair_full_hit"))),
            int(row.get("hit_count") or 0),
            str(row.get("variant_id") or ""),
        ),
        reverse=True,
    )[0]


__all__ = [
    "capacity_sweep_decision",
    "interpretation_reason",
    "model_quality_claim",
    "next_action",
    "source_baseline",
    "summarize_capacity_variant_probe_rows",
    "summarize_pair_capacity_sweep",
    "summarize_required_term_pair_capacity_sweep",
]
