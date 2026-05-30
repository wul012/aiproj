from __future__ import annotations

from typing import Any

from minigpt.model_capability_required_term_pair_contrast_free_training_components import _slug
from minigpt.report_utils import list_of_dicts


def select_branch_retention_targets(report: dict[str, Any], *, pair_limit: int | None = 1) -> list[dict[str, Any]]:
    targets_by_pair = {str(row.get("pair_id") or ""): row for row in list_of_dicts(report.get("targets"))}
    summaries = [
        row
        for row in list_of_dicts(report.get("target_summaries"))
        if int(row.get("branch_tradeoff_variant_count") or 0) > 0
    ]
    rows: list[dict[str, Any]] = []
    for summary in summaries:
        pair_id = str(summary.get("pair_id") or "")
        source = targets_by_pair.get(pair_id)
        if not source:
            continue
        term_names = [str(term) for term in source.get("term_names") or []]
        focus = str(source.get("focus_missed_term") or summary.get("focus_missed_term") or "")
        source_hit_terms = [str(term) for term in source.get("hit_term_names") or summary.get("source_hit_terms") or []]
        if not term_names or not focus or not source_hit_terms:
            continue
        rows.append(
            {
                "pair_id": pair_id,
                "term_names": term_names,
                "terms": list_of_dicts(source.get("terms")),
                "focus_missed_term": focus,
                "source_hit_terms": source_hit_terms,
                "source_missed_terms": [str(term) for term in source.get("missed_term_names") or []],
                "source_tradeoff_variant_count": int(summary.get("branch_tradeoff_variant_count") or 0),
                "source_focus_hit_variant_count": int(summary.get("focus_term_hit_variant_count") or 0),
                "source_pair_full_hit_variant_count": int(summary.get("pair_full_hit_variant_count") or 0),
                "source_best_variant_id": summary.get("best_variant_id"),
            }
        )
    rows.sort(key=lambda row: str(row.get("pair_id") or ""))
    if pair_limit is not None and pair_limit >= 0:
        return rows[:pair_limit]
    return rows


def normalize_branch_retention_variants(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(variants):
        variant_id = _slug(str(item.get("variant_id") or item.get("id") or f"variant-{index + 1}"))
        if not variant_id or variant_id in seen:
            continue
        seen.add(variant_id)
        cycle_strategy = str(item.get("cycle_strategy") or "alternating")
        if cycle_strategy not in {"source-order", "reverse-order", "alternating"}:
            cycle_strategy = "alternating"
        normalized.append(
            {
                "variant_id": variant_id,
                "label": str(item.get("label") or variant_id),
                "cycle_strategy": cycle_strategy,
                "repeat": max(1, int(item.get("repeat") or 220)),
                "isolated_repeat": max(1, int(item.get("isolated_repeat") or 2)),
                "term_weight": max(1, int(item.get("term_weight") or 1)),
                "symmetric_anchor_repeat": max(0, int(item.get("symmetric_anchor_repeat") or 0)),
                "max_iters": max(1, int(item.get("max_iters") or 2200)),
                "n_embd": max(1, int(item.get("n_embd") or 64)),
                "learning_rate": float(item.get("learning_rate") or 0.02),
            }
        )
    return normalized


def build_required_term_pair_branch_retention_corpus(target: dict[str, Any], variant: dict[str, Any]) -> str:
    repeat_count = max(1, int(variant.get("repeat") or 1))
    isolated_count = max(1, int(variant.get("isolated_repeat") or 1))
    term_weight = max(1, int(variant.get("term_weight") or 1))
    lines = [
        "MiniGPT required-term pair branch-retention sweep corpus.",
        "The corpus balances both pair branches and keeps each scaffold tied only to its own term.",
    ]
    for cycle in range(repeat_count):
        for term_row in _cycle_terms(target, variant, cycle):
            for _ in range(term_weight):
                lines.extend(_retention_term_rows(term_row, isolated_count))
    anchor_count = max(0, int(variant.get("symmetric_anchor_repeat") or 0))
    for _ in range(anchor_count):
        for term_row in list_of_dicts(target.get("terms")):
            lines.extend(_retention_term_rows(term_row, isolated_count))
    return "\n".join(lines) + "\n"


def summarize_branch_retention_variant_probe_rows(
    targets: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        pair_id = str(target.get("pair_id") or "")
        term_names = [str(term) for term in target.get("term_names") or []]
        focus = str(target.get("focus_missed_term") or "")
        source_hit_terms = [str(term) for term in target.get("source_hit_terms") or []]
        for variant in variants:
            variant_id = str(variant.get("variant_id") or "")
            probes = [
                row
                for row in probe_rows
                if str(row.get("pair_id") or "") == pair_id and str(row.get("variant_id") or "") == variant_id
            ]
            hit_terms = [str(row.get("term") or "") for row in probes if int(row.get("continuation_hit_count") or 0) > 0]
            missed_terms = [term for term in term_names if term not in hit_terms]
            retained_source_terms = [term for term in source_hit_terms if term in hit_terms]
            dropped_source_terms = [term for term in source_hit_terms if term not in hit_terms]
            focus_hit = focus in hit_terms
            source_retained = len(retained_source_terms) == len(source_hit_terms)
            rows.append(
                {
                    "pair_id": pair_id,
                    "variant_id": variant_id,
                    "variant_label": variant.get("label"),
                    "term_names": term_names,
                    "focus_missed_term": focus,
                    "source_hit_terms": source_hit_terms,
                    "hit_terms": hit_terms,
                    "missed_terms": missed_terms,
                    "retained_source_hit_terms": retained_source_terms,
                    "dropped_source_hit_terms": dropped_source_terms,
                    "hit_count": len(hit_terms),
                    "hit_rate": round(len(hit_terms) / len(term_names), 4) if term_names else 0.0,
                    "focus_missed_term_hit": focus_hit,
                    "source_hit_terms_retained": source_retained,
                    "pair_full_hit": bool(term_names) and len(hit_terms) == len(term_names),
                    "balanced_retention": focus_hit and source_retained,
                    "retention_tradeoff": focus_hit != source_retained,
                }
            )
    return rows


def summarize_branch_retention_targets(
    targets: list[dict[str, Any]],
    variant_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        pair_id = str(target.get("pair_id") or "")
        variants = [row for row in variant_summaries if str(row.get("pair_id") or "") == pair_id]
        best = _best_variant_summary(variants)
        rows.append(
            {
                "pair_id": pair_id,
                "term_names": target.get("term_names") or [],
                "focus_missed_term": target.get("focus_missed_term"),
                "source_hit_terms": target.get("source_hit_terms") or [],
                "source_tradeoff_variant_count": target.get("source_tradeoff_variant_count"),
                "variant_count": len(variants),
                "balanced_retention_variant_count": sum(1 for row in variants if row.get("balanced_retention")),
                "pair_full_hit_variant_count": sum(1 for row in variants if row.get("pair_full_hit")),
                "retention_tradeoff_variant_count": sum(1 for row in variants if row.get("retention_tradeoff")),
                "focus_term_hit_variant_count": sum(1 for row in variants if row.get("focus_missed_term_hit")),
                "source_retained_variant_count": sum(1 for row in variants if row.get("source_hit_terms_retained")),
                "best_variant_id": best.get("variant_id"),
                "best_variant_hit_count": best.get("hit_count"),
                "best_variant_balanced_retention": best.get("balanced_retention"),
                "best_variant_pair_full_hit": best.get("pair_full_hit"),
            }
        )
    return rows


def summarize_required_term_pair_branch_retention_sweep(
    targets: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    variant_summaries: list[dict[str, Any]],
    target_summaries: list[dict[str, Any]],
    *,
    source_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_summary or {}
    training_pass_count = sum(1 for row in training_rows if row.get("training_status") == "pass")
    checkpoint_count = sum(1 for row in training_rows if row.get("checkpoint_exists"))
    probe_hits = sum(1 for row in probe_rows if int(row.get("continuation_hit_count") or 0) > 0)
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in probe_rows)
    balanced = sum(1 for row in variant_summaries if row.get("balanced_retention"))
    full_hits = sum(1 for row in variant_summaries if row.get("pair_full_hit"))
    tradeoffs = sum(1 for row in variant_summaries if row.get("retention_tradeoff"))
    focus_hits = sum(1 for row in variant_summaries if row.get("focus_missed_term_hit"))
    source_retained = sum(1 for row in variant_summaries if row.get("source_hit_terms_retained"))
    best = _best_variant_summary(variant_summaries)
    return {
        "branch_retention_sweep_decision": _retention_decision(
            targets,
            variants,
            training_rows,
            probe_rows,
            training_pass_count,
            balanced,
            full_hits,
            tradeoffs,
        ),
        "source_loss_branch_sweep_decision": source.get("loss_branch_sweep_decision"),
        "source_branch_tradeoff_variant_count": int(source.get("branch_tradeoff_variant_count") or 0),
        "source_pair_full_hit_variant_count": int(source.get("pair_full_hit_variant_count") or 0),
        "source_best_variant_id": source.get("best_variant_id"),
        "target_count": len(targets),
        "variant_count": len(variants),
        "training_run_count": len(training_rows),
        "training_pass_count": training_pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "probe_count": len(probe_rows),
        "probe_hit_count": probe_hits,
        "continuation_hit_count": continuation_hits,
        "focus_term_hit_variant_count": focus_hits,
        "source_retained_variant_count": source_retained,
        "balanced_retention_variant_count": balanced,
        "pair_full_hit_variant_count": full_hits,
        "retention_tradeoff_variant_count": tradeoffs,
        "best_variant_id": best.get("variant_id"),
        "best_variant_hit_count": best.get("hit_count"),
        "best_variant_balanced_retention": best.get("balanced_retention"),
        "best_variant_pair_full_hit": best.get("pair_full_hit"),
    }


def _cycle_terms(target: dict[str, Any], variant: dict[str, Any], cycle: int) -> list[dict[str, Any]]:
    terms = list_of_dicts(target.get("terms"))
    strategy = str(variant.get("cycle_strategy") or "alternating")
    if strategy == "source-order":
        return terms
    if strategy == "reverse-order":
        return list(reversed(terms))
    return terms if cycle % 2 == 0 else list(reversed(terms))


def _retention_term_rows(term_row: dict[str, Any], isolated_count: int) -> list[str]:
    term = str(term_row.get("term") or "")
    prompt = str(term_row.get("scaffold_prompt") or f"{term}:")
    case = str(term_row.get("case") or "unknown-case")
    rows: list[str] = []
    for _ in range(isolated_count):
        rows.append(f"{prompt}{term}")
        rows.append(f"{prompt} {term}")
        rows.append(f"{case}|{prompt}{term}")
    return rows


def _best_variant_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            bool(row.get("pair_full_hit")),
            bool(row.get("balanced_retention")),
            int(row.get("hit_count") or 0),
            bool(row.get("focus_missed_term_hit")),
            bool(row.get("source_hit_terms_retained")),
            str(row.get("variant_id") or ""),
        ),
    )


def _retention_decision(
    targets: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    training_pass_count: int,
    balanced_count: int,
    full_hit_count: int,
    tradeoff_count: int,
) -> str:
    if not targets:
        return "branch_retention_sweep_no_targets"
    if not variants:
        return "branch_retention_sweep_no_variants"
    if training_pass_count != len(training_rows):
        return "branch_retention_sweep_training_failed"
    if not probe_rows:
        return "branch_retention_sweep_generation_missing"
    if full_hit_count > 0:
        return "branch_retention_sweep_full_hit_recovered"
    if balanced_count > 0:
        return "branch_retention_sweep_balanced_partial"
    if tradeoff_count > 0:
        return "branch_retention_sweep_tradeoff_remains"
    return "branch_retention_sweep_not_recovered"
