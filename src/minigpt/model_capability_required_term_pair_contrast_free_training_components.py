from __future__ import annotations

import re
from typing import Any

from minigpt.report_utils import list_of_dicts


def select_contrast_free_pairs(report: dict[str, Any], *, pair_limit: int | None = 1) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for target in list_of_dicts(report.get("targets")):
        pair_id = str(target.get("pair_id") or "")
        terms = list_of_dicts(target.get("terms"))
        if not pair_id or pair_id in seen or len(terms) < 2:
            continue
        seen.add(pair_id)
        rows.append(
            {
                "pair_id": pair_id,
                "source_target_id": target.get("target_id"),
                "source_variant_id": target.get("variant_id"),
                "source_capacity_run_id": target.get("capacity_run_id"),
                "term_names": [str(term) for term in target.get("term_names") or []],
                "terms": terms,
            }
        )
    rows.sort(key=lambda row: str(row.get("pair_id") or ""))
    if pair_limit is not None and pair_limit >= 0:
        return rows[:pair_limit]
    return rows


def normalize_contrast_free_variants(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(variants):
        variant_id = _slug(str(item.get("variant_id") or item.get("id") or f"variant-{index + 1}"))
        if not variant_id or variant_id in seen:
            continue
        seen.add(variant_id)
        normalized.append(
            {
                "variant_id": variant_id,
                "label": str(item.get("label") or variant_id),
                "repeat": max(1, int(item.get("repeat") or 240)),
                "isolated_repeat": max(1, int(item.get("isolated_repeat") or 2)),
                "max_iters": max(1, int(item.get("max_iters") or 1600)),
                "n_embd": max(1, int(item.get("n_embd") or 64)),
                "learning_rate": float(item.get("learning_rate") or 0.02),
            }
        )
    return normalized


def build_required_term_pair_contrast_free_corpus(pair: dict[str, Any], *, repeat: int, isolated_repeat: int) -> str:
    terms = list_of_dicts(pair.get("terms"))
    repeat_count = max(1, int(repeat))
    isolated_count = max(1, int(isolated_repeat))
    lines = [
        "MiniGPT required-term pair contrast-free corpus.",
        "Each scaffold prompt is followed only by its own target term.",
    ]
    for _ in range(repeat_count):
        for term_row in terms:
            lines.extend(_contrast_free_term_rows(term_row, isolated_count))
    return "\n".join(lines) + "\n"


def summarize_required_term_pair_contrast_free_training(
    pairs: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    variant_summaries: list[dict[str, Any]],
    pair_summaries: list[dict[str, Any]],
    *,
    source_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_summary or {}
    training_pass_count = sum(1 for row in training_rows if row.get("training_status") == "pass")
    checkpoint_count = sum(1 for row in training_rows if row.get("checkpoint_exists"))
    probe_hits = sum(1 for row in probe_rows if int(row.get("continuation_hit_count") or 0) > 0)
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in probe_rows)
    full_variants = sum(1 for row in variant_summaries if row.get("pair_full_hit"))
    partial_variants = sum(1 for row in variant_summaries if row.get("pair_partial_hit"))
    full_pairs = sum(1 for row in pair_summaries if row.get("contrast_free_full_hit_observed"))
    best = _best_variant_summary(variant_summaries)
    return {
        "contrast_free_training_decision": _training_decision(
            pairs,
            variants,
            training_rows,
            probe_rows,
            training_pass_count,
            full_variants,
            partial_variants,
        ),
        "source_prompt_separation_audit_decision": source.get("prompt_separation_audit_decision"),
        "source_corpus_revision_recommended": bool(source.get("corpus_revision_recommended")),
        "source_direct_prompt_other_term_leak_count": int(source.get("direct_prompt_other_term_leak_count") or 0),
        "selected_pair_count": len(pairs),
        "variant_count": len(variants),
        "training_run_count": len(training_rows),
        "training_pass_count": training_pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "probe_count": len(probe_rows),
        "probe_hit_count": probe_hits,
        "continuation_hit_count": continuation_hits,
        "probe_success_rate": round(probe_hits / len(probe_rows), 4) if probe_rows else 0.0,
        "variant_pair_full_hit_count": full_variants,
        "variant_pair_partial_hit_count": partial_variants,
        "variant_pair_zero_hit_count": max(0, len(variant_summaries) - full_variants - partial_variants),
        "variant_pair_full_hit_rate": round(full_variants / len(variant_summaries), 4) if variant_summaries else 0.0,
        "contrast_free_full_hit_pair_count": full_pairs,
        "contrast_free_full_hit_observed": full_pairs > 0,
        "best_variant_id": best.get("variant_id"),
        "best_variant_hit_count": best.get("hit_count"),
        "best_variant_pair_full_hit": best.get("pair_full_hit"),
    }


def summarize_contrast_free_variant_probe_rows(
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


def summarize_contrast_free_pairs(
    pairs: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    variant_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        pair_rows = [row for row in variant_summaries if str(row.get("pair_id") or "") == pair_id]
        full_hit_variants = [str(row.get("variant_id") or "") for row in pair_rows if row.get("pair_full_hit")]
        partial_hit_variants = [str(row.get("variant_id") or "") for row in pair_rows if row.get("pair_partial_hit")]
        best = _best_variant_summary(pair_rows)
        rows.append(
            {
                "pair_id": pair_id,
                "term_names": pair.get("term_names") or [],
                "variant_count": len(variants),
                "full_hit_variant_count": len(full_hit_variants),
                "partial_hit_variant_count": len(partial_hit_variants),
                "full_hit_variants": full_hit_variants,
                "partial_hit_variants": partial_hit_variants,
                "contrast_free_full_hit_observed": bool(full_hit_variants),
                "best_variant_id": best.get("variant_id"),
                "best_variant_hit_count": best.get("hit_count"),
                "best_variant_pair_full_hit": best.get("pair_full_hit"),
            }
        )
    return rows


def _contrast_free_term_rows(term_row: dict[str, Any], isolated_count: int) -> list[str]:
    term = str(term_row.get("term") or "")
    prompt = str(term_row.get("scaffold_prompt") or f"{term}:")
    case = str(term_row.get("case") or "unknown-case")
    rows: list[str] = []
    for _ in range(isolated_count):
        rows.append(f"{prompt}{term}")
        rows.append(f"{prompt} {term}")
        rows.append(f"{case}|{prompt}{term}")
    return rows


def _training_decision(
    pairs: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    training_pass_count: int,
    full_variant_count: int,
    partial_variant_count: int,
) -> str:
    if not pairs:
        return "contrast_free_training_no_pairs"
    if not variants:
        return "contrast_free_training_no_variants"
    if training_pass_count != len(training_rows):
        return "contrast_free_training_failed"
    if not probe_rows:
        return "contrast_free_generation_missing"
    if full_variant_count > 0:
        return "contrast_free_training_full_hit_recovered"
    if partial_variant_count > 0:
        return "contrast_free_training_partial_only"
    return "contrast_free_training_not_recovered"


def _best_variant_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            bool(row.get("pair_full_hit")),
            int(row.get("hit_count") or 0),
            str(row.get("variant_id") or ""),
        ),
    )


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "contrast-free"
