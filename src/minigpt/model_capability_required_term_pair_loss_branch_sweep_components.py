from __future__ import annotations

from typing import Any

from minigpt.model_capability_required_term_pair_contrast_free_training_components import _slug
from minigpt.report_utils import list_of_dicts


def select_loss_branch_targets(report: dict[str, Any], *, pair_limit: int | None = 1) -> list[dict[str, Any]]:
    pairs = {str(pair.get("pair_id") or ""): pair for pair in list_of_dicts(report.get("pairs"))}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in list_of_dicts(report.get("variant_summaries")):
        pair_id = str(row.get("pair_id") or "")
        if pair_id:
            grouped.setdefault(pair_id, []).append(row)

    targets: list[dict[str, Any]] = []
    for pair_id, rows in sorted(grouped.items()):
        pair = pairs.get(pair_id)
        if not pair:
            continue
        term_names = [str(term) for term in pair.get("term_names") or []]
        missed_counts = _term_counts(rows, "missed_terms")
        hit_counts = _term_counts(rows, "hit_terms")
        if not missed_counts or not hit_counts:
            continue
        missed_terms = _ordered_terms_by_count(missed_counts)
        hit_terms = _ordered_terms_by_count(hit_counts)
        stable_missed = [term for term in missed_terms if missed_counts.get(term) == len(rows)]
        focus = stable_missed[0] if stable_missed else missed_terms[0]
        targets.append(
            {
                "pair_id": pair_id,
                "source_target_id": pair.get("source_target_id"),
                "source_variant_id": pair.get("source_variant_id"),
                "source_capacity_run_id": pair.get("source_capacity_run_id"),
                "term_names": term_names,
                "terms": list_of_dicts(pair.get("terms")),
                "focus_missed_term": focus,
                "missed_term_names": missed_terms,
                "hit_term_names": hit_terms,
                "stable_missed_terms": stable_missed,
                "source_variant_count": len(rows),
                "source_missed_counts": missed_counts,
                "source_hit_counts": hit_counts,
                "source_variant_ids": [str(row.get("variant_id") or "") for row in rows],
            }
        )
    if pair_limit is not None and pair_limit >= 0:
        return targets[:pair_limit]
    return targets


def normalize_loss_branch_variants(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(variants):
        variant_id = _slug(str(item.get("variant_id") or item.get("id") or f"variant-{index + 1}"))
        if not variant_id or variant_id in seen:
            continue
        seen.add(variant_id)
        term_order = str(item.get("term_order") or "source-order")
        if term_order not in {"source-order", "missed-first"}:
            term_order = "source-order"
        normalized.append(
            {
                "variant_id": variant_id,
                "label": str(item.get("label") or variant_id),
                "term_order": term_order,
                "repeat": max(1, int(item.get("repeat") or 220)),
                "isolated_repeat": max(1, int(item.get("isolated_repeat") or 2)),
                "missed_weight": max(1, int(item.get("missed_weight") or 1)),
                "missed_anchor_repeat": max(0, int(item.get("missed_anchor_repeat") or 0)),
                "max_iters": max(1, int(item.get("max_iters") or 1800)),
                "n_embd": max(1, int(item.get("n_embd") or 64)),
                "learning_rate": float(item.get("learning_rate") or 0.02),
            }
        )
    return normalized


def build_required_term_pair_loss_branch_corpus(target: dict[str, Any], variant: dict[str, Any]) -> str:
    terms = _ordered_target_terms(target, variant)
    missed = set(str(term) for term in target.get("missed_term_names") or [])
    isolated_count = max(1, int(variant.get("isolated_repeat") or 1))
    missed_weight = max(1, int(variant.get("missed_weight") or 1))
    repeat_count = max(1, int(variant.get("repeat") or 1))
    lines = [
        "MiniGPT required-term pair loss-branch sweep corpus.",
        "Every scaffold prompt is followed only by its own target term; no negative contrast rows are used.",
    ]
    for _ in range(repeat_count):
        for term_row in terms:
            term = str(term_row.get("term") or "")
            copies = missed_weight if term in missed else 1
            for _copy in range(copies):
                lines.extend(_loss_branch_term_rows(term_row, isolated_count))
    focus_row = _term_row_for(target, str(target.get("focus_missed_term") or ""))
    for _ in range(max(0, int(variant.get("missed_anchor_repeat") or 0))):
        if focus_row:
            lines.extend(_loss_branch_term_rows(focus_row, isolated_count))
    return "\n".join(lines) + "\n"


def summarize_loss_branch_variant_probe_rows(
    targets: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        pair_id = str(target.get("pair_id") or "")
        term_names = [str(term) for term in target.get("term_names") or []]
        source_hit_terms = [str(term) for term in target.get("hit_term_names") or []]
        focus = str(target.get("focus_missed_term") or "")
        for variant in variants:
            variant_id = str(variant.get("variant_id") or "")
            probes = [
                row
                for row in probe_rows
                if str(row.get("pair_id") or "") == pair_id and str(row.get("variant_id") or "") == variant_id
            ]
            hit_terms = [str(row.get("term") or "") for row in probes if int(row.get("continuation_hit_count") or 0) > 0]
            dropped = [term for term in source_hit_terms if term not in hit_terms]
            missed_terms = [term for term in term_names if term not in hit_terms]
            focus_hit = focus in hit_terms
            rows.append(
                {
                    "pair_id": pair_id,
                    "variant_id": variant_id,
                    "variant_label": variant.get("label"),
                    "term_names": term_names,
                    "source_hit_terms": source_hit_terms,
                    "focus_missed_term": focus,
                    "hit_terms": hit_terms,
                    "missed_terms": missed_terms,
                    "dropped_source_hit_terms": dropped,
                    "hit_count": len(hit_terms),
                    "hit_rate": round(len(hit_terms) / len(term_names), 4) if term_names else 0.0,
                    "focus_missed_term_hit": focus_hit,
                    "source_hit_terms_retained": not dropped,
                    "pair_full_hit": bool(term_names) and len(hit_terms) == len(term_names),
                    "branch_tradeoff": focus_hit and bool(dropped),
                }
            )
    return rows


def summarize_loss_branch_targets(
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
                "source_hit_terms": target.get("hit_term_names") or [],
                "source_missed_counts": target.get("source_missed_counts") or {},
                "variant_count": len(variants),
                "focus_term_hit_variant_count": sum(1 for row in variants if row.get("focus_missed_term_hit")),
                "pair_full_hit_variant_count": sum(1 for row in variants if row.get("pair_full_hit")),
                "branch_tradeoff_variant_count": sum(1 for row in variants if row.get("branch_tradeoff")),
                "best_variant_id": best.get("variant_id"),
                "best_variant_hit_count": best.get("hit_count"),
                "best_variant_focus_hit": best.get("focus_missed_term_hit"),
                "best_variant_pair_full_hit": best.get("pair_full_hit"),
            }
        )
    return rows


def summarize_required_term_pair_loss_branch_sweep(
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
    focus_hits = sum(1 for row in variant_summaries if row.get("focus_missed_term_hit"))
    full_hits = sum(1 for row in variant_summaries if row.get("pair_full_hit"))
    tradeoffs = sum(1 for row in variant_summaries if row.get("branch_tradeoff"))
    best = _best_variant_summary(variant_summaries)
    return {
        "loss_branch_sweep_decision": _sweep_decision(
            targets,
            variants,
            training_rows,
            probe_rows,
            training_pass_count,
            focus_hits,
            full_hits,
            tradeoffs,
        ),
        "source_contrast_free_training_decision": source.get("contrast_free_training_decision"),
        "source_variant_pair_partial_hit_count": int(source.get("variant_pair_partial_hit_count") or 0),
        "source_variant_pair_full_hit_count": int(source.get("variant_pair_full_hit_count") or 0),
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
        "pair_full_hit_variant_count": full_hits,
        "branch_tradeoff_variant_count": tradeoffs,
        "best_variant_id": best.get("variant_id"),
        "best_variant_hit_count": best.get("hit_count"),
        "best_variant_focus_hit": best.get("focus_missed_term_hit"),
        "best_variant_pair_full_hit": best.get("pair_full_hit"),
    }


def term_row_for(target: dict[str, Any], term_name: str) -> dict[str, Any]:
    return _term_row_for(target, term_name)


def _ordered_target_terms(target: dict[str, Any], variant: dict[str, Any]) -> list[dict[str, Any]]:
    terms = list_of_dicts(target.get("terms"))
    if variant.get("term_order") != "missed-first":
        return terms
    missed = set(str(term) for term in target.get("missed_term_names") or [])
    return sorted(terms, key=lambda row: (str(row.get("term") or "") not in missed, str(row.get("term") or "")))


def _loss_branch_term_rows(term_row: dict[str, Any], isolated_count: int) -> list[str]:
    term = str(term_row.get("term") or "")
    prompt = str(term_row.get("scaffold_prompt") or f"{term}:")
    case = str(term_row.get("case") or "unknown-case")
    rows: list[str] = []
    for _ in range(isolated_count):
        rows.append(f"{prompt}{term}")
        rows.append(f"{prompt} {term}")
        rows.append(f"{case}|{prompt}{term}")
    return rows


def _term_row_for(target: dict[str, Any], term_name: str) -> dict[str, Any]:
    for row in list_of_dicts(target.get("terms")):
        if str(row.get("term") or "") == term_name:
            return row
    return {}


def _term_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for term in row.get(key) or []:
            name = str(term)
            if name:
                counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def _ordered_terms_by_count(counts: dict[str, int]) -> list[str]:
    return [term for term, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def _best_variant_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            bool(row.get("pair_full_hit")),
            bool(row.get("focus_missed_term_hit")),
            int(row.get("hit_count") or 0),
            not bool(row.get("branch_tradeoff")),
            str(row.get("variant_id") or ""),
        ),
    )


def _sweep_decision(
    targets: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    training_pass_count: int,
    focus_hit_count: int,
    full_hit_count: int,
    tradeoff_count: int,
) -> str:
    if not targets:
        return "loss_branch_sweep_no_targets"
    if not variants:
        return "loss_branch_sweep_no_variants"
    if training_pass_count != len(training_rows):
        return "loss_branch_sweep_training_failed"
    if not probe_rows:
        return "loss_branch_sweep_generation_missing"
    if full_hit_count > 0:
        return "loss_branch_sweep_full_hit_recovered"
    if focus_hit_count > 0 and tradeoff_count > 0:
        return "loss_branch_sweep_tradeoff_only"
    if focus_hit_count > 0:
        return "loss_branch_sweep_focus_term_recovered"
    return "loss_branch_sweep_still_missed"
