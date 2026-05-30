from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_pair_rebalance import (
    build_required_term_pair_rebalance_corpus,
    read_json_report,
)
from minigpt.model_capability_required_term_pair_rebalance_seed_stability import (
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_CAPACITY_SWEEP_JSON_FILENAME = "model_capability_required_term_pair_capacity_sweep.json"
REQUIRED_TERM_PAIR_CAPACITY_SWEEP_TEXT_FILENAME = "model_capability_required_term_pair_capacity_sweep.txt"
REQUIRED_TERM_PAIR_CAPACITY_SWEEP_MARKDOWN_FILENAME = "model_capability_required_term_pair_capacity_sweep.md"
REQUIRED_TERM_PAIR_CAPACITY_SWEEP_HTML_FILENAME = "model_capability_required_term_pair_capacity_sweep.html"

DEFAULT_PAIR_CAPACITY_SWEEP_SEED = 496


def locate_model_capability_required_term_pair_capacity_sweep_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_JSON_FILENAME
    return source


def default_pair_capacity_sweep_variants() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": "baseline-repeat",
            "label": "v496 baseline repeat",
            "repeat": 240,
            "isolated_repeat": 2,
            "max_iters": 1600,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "longer-iters",
            "label": "longer training budget",
            "repeat": 240,
            "isolated_repeat": 2,
            "max_iters": 2400,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "wider-embd",
            "label": "wider embedding",
            "repeat": 240,
            "isolated_repeat": 2,
            "max_iters": 1600,
            "n_embd": 96,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "denser-corpus",
            "label": "denser pair corpus",
            "repeat": 360,
            "isolated_repeat": 2,
            "max_iters": 1600,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
    ]


def build_model_capability_required_term_pair_capacity_sweep(
    pair_seed_stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seed: int = DEFAULT_PAIR_CAPACITY_SWEEP_SEED,
    pair_limit: int | None = 1,
    capacity_variants: list[dict[str, Any]] | None = None,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 8,
    n_layer: int = 1,
    n_head: int = 1,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int | None = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_summary = as_dict(pair_seed_stability_report.get("summary"))
    variant_source = default_pair_capacity_sweep_variants() if capacity_variants is None else capacity_variants
    variants = normalize_capacity_sweep_variants(variant_source)
    selected_pairs = select_pair_capacity_sweep_pairs(pair_seed_stability_report, pair_limit=pair_limit)
    issues = _input_issues(pair_seed_stability_report, selected_pairs, variants)

    capacity_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for pair_index, pair in enumerate(selected_pairs):
            for variant_index, variant in enumerate(variants):
                result = _run_pair_capacity_variant(
                    root,
                    pair,
                    variant,
                    pair_index=pair_index,
                    variant_index=variant_index,
                    seed=seed,
                    eval_iters=eval_iters,
                    batch_size=batch_size,
                    block_size=block_size,
                    n_layer=n_layer,
                    n_head=n_head,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    device=device,
                    train_func=train_func,
                    generate_func=generate_func,
                )
                capacity_rows.append(result["capacity_row"])
                probe_rows.extend(result["probe_rows"])

    training_failures = [row for row in capacity_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} pair capacity sweep runs did not complete successfully")

    variant_pair_summaries = summarize_capacity_variant_probe_rows(selected_pairs, variants, probe_rows)
    pair_capacity_summaries = summarize_pair_capacity_sweep(selected_pairs, variants, variant_pair_summaries)
    summary = summarize_required_term_pair_capacity_sweep(
        selected_pairs,
        variants,
        capacity_rows,
        probe_rows,
        variant_pair_summaries,
        pair_capacity_summaries,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair capacity sweep",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_rebalance_seed_stability": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seed": int(seed),
            "pair_limit": pair_limit,
            "variant_count": len(variants),
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "sweep capacity for fragile v496 pair before expanding to three-term curricula",
        },
        "source_baseline": _source_baseline(source_summary),
        "summary": summary,
        "selected_pair_count": len(selected_pairs),
        "pairs": selected_pairs,
        "capacity_variants": variants,
        "capacity_rows": capacity_rows,
        "variant_pair_summaries": variant_pair_summaries,
        "pair_capacity_summaries": pair_capacity_summaries,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def select_pair_capacity_sweep_pairs(
    pair_seed_stability_report: dict[str, Any],
    *,
    pair_limit: int | None = 1,
) -> list[dict[str, Any]]:
    source_pairs = {str(row.get("pair_id") or ""): row for row in list_of_dicts(pair_seed_stability_report.get("pairs"))}
    selected: list[dict[str, Any]] = []
    for summary in list_of_dicts(pair_seed_stability_report.get("pair_seed_summaries")):
        if summary.get("stable_full_hit_across_seeds"):
            continue
        pair_id = str(summary.get("pair_id") or "")
        source_pair = source_pairs.get(pair_id)
        if not source_pair:
            continue
        seed_count = int(summary.get("seed_count") or 0)
        full_hit_count = int(summary.get("full_hit_seed_count") or 0)
        selected.append(
            {
                "pair_id": pair_id,
                "pair_index": int(source_pair.get("pair_index") or len(selected)),
                "terms": list_of_dicts(source_pair.get("terms")),
                "term_names": [str(term) for term in source_pair.get("term_names") or summary.get("term_names") or []],
                "v495_hit_terms": [str(term) for term in source_pair.get("v495_hit_terms") or summary.get("v495_hit_terms") or []],
                "v496_seed_count": seed_count,
                "v496_full_hit_seed_count": full_hit_count,
                "v496_full_hit_rate": summary.get("full_hit_rate"),
                "v496_full_hit_seeds": [int(seed) for seed in summary.get("full_hit_seeds") or []],
                "v496_missed_full_hit_seeds": [int(seed) for seed in summary.get("missed_full_hit_seeds") or []],
                "v496_stable_full_hit_across_seeds": bool(summary.get("stable_full_hit_across_seeds")),
                "v496_fragile_pair": full_hit_count < seed_count if seed_count else True,
            }
        )
    selected.sort(key=lambda item: (int(item.get("v496_full_hit_seed_count") or 0), str(item.get("pair_id") or "")))
    if pair_limit is not None and pair_limit >= 0:
        return selected[:pair_limit]
    return selected


def normalize_capacity_sweep_variants(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_pair_capacity_variant(
    root: Path,
    pair: dict[str, Any],
    variant: dict[str, Any],
    *,
    pair_index: int,
    variant_index: int,
    seed: int,
    eval_iters: int,
    batch_size: int,
    block_size: int,
    n_layer: int,
    n_head: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    device: str,
    train_func: TrainFunc | None,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    pair_id = str(pair.get("pair_id") or f"pair-{pair_index + 1}")
    variant_id = str(variant.get("variant_id") or f"variant-{variant_index + 1}")
    run_id = f"{pair_id}-{variant_id}-seed-{seed}"
    corpus_text = build_required_term_pair_rebalance_corpus(
        pair,
        repeat=int(variant["repeat"]),
        isolated_repeat=int(variant["isolated_repeat"]),
    )
    corpus_path = root / "capacity-corpora" / f"{_slug(run_id)}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "capacity-runs" / run_id
    training = _train_micro_checkpoint(
        {
            "corpus_path": str(corpus_path),
            "train_dir": str(train_dir),
            "max_iters": int(variant["max_iters"]),
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": int(variant["n_embd"]),
            "learning_rate": float(variant["learning_rate"]),
            "seed": int(seed),
            "device": device,
            "sample_prompt": _sample_prompt(pair),
        },
        train_func,
    )
    probe_rows: list[dict[str, Any]] = []
    if training.get("status") == "pass":
        for term_index, term_row in enumerate(list_of_dicts(pair.get("terms"))):
            generation = _generation_row(
                {
                    **term_row,
                    "pair_id": pair_id,
                    "variant_id": variant_id,
                    "variant_label": variant.get("label"),
                    "capacity_run_id": run_id,
                    "pair_terms": pair.get("term_names") or [],
                    "capacity_corpus_path": str(corpus_path),
                    "capacity_seed": seed,
                    "capacity_repeat": int(variant["repeat"]),
                    "isolated_repeat": int(variant["isolated_repeat"]),
                },
                training,
                index=term_index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=seed + variant_index * 100,
                device=device,
                generate_func=generate_func,
            )
            probe_rows.append(
                {
                    **generation,
                    "pair_id": pair_id,
                    "variant_id": variant_id,
                    "variant_label": variant.get("label"),
                    "capacity_run_id": run_id,
                    "seed": int(seed),
                    "pair_terms": pair.get("term_names") or [],
                    "training_status": training.get("status"),
                    "checkpoint_path": training.get("checkpoint_path"),
                    "checkpoint_exists": bool(training.get("checkpoint_exists")),
                }
            )
    return {
        "capacity_row": {
            "capacity_run_id": run_id,
            "pair_id": pair_id,
            "pair_terms": pair.get("term_names") or [],
            "variant_id": variant_id,
            "variant_label": variant.get("label"),
            "seed": int(seed),
            "capacity_corpus_path": str(corpus_path),
            "capacity_corpus_exists": corpus_path.is_file(),
            "capacity_line_count": len(corpus_text.splitlines()) - 2,
            "repeat": int(variant["repeat"]),
            "isolated_repeat": int(variant["isolated_repeat"]),
            "max_iters": int(variant["max_iters"]),
            "n_embd": int(variant["n_embd"]),
            "learning_rate": float(variant["learning_rate"]),
            "training_status": training.get("status"),
            "training_returncode": training.get("returncode"),
            "checkpoint_path": training.get("checkpoint_path"),
            "tokenizer_path": training.get("tokenizer_path"),
            "metrics_path": training.get("metrics_path"),
            "train_config_path": training.get("train_config_path"),
            "checkpoint_exists": bool(training.get("checkpoint_exists")),
            "tokenizer_exists": bool(training.get("tokenizer_exists")),
            "metrics_exists": bool(training.get("metrics_exists")),
            "train_config_exists": bool(training.get("train_config_exists")),
            "command_text": training.get("command_text"),
        },
        "probe_rows": probe_rows,
    }


def _input_issues(report: dict[str, Any], pairs: list[dict[str, Any]], variants: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    source_summary = as_dict(report.get("summary"))
    if not report:
        issues.append("source pair rebalance seed-stability report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source pair rebalance seed-stability report is not pass")
    if report and source_summary.get("source_pair_rebalance_decision") != "pair_rebalance_full_hit_gain":
        issues.append("source seed-stability report is not tied to a v495 full-hit gain")
    if not pairs:
        issues.append("source seed-stability report has no fragile full-hit-gain pairs to sweep")
    if not variants:
        issues.append("at least one capacity variant is required")
    return issues


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


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_capacity_sweep"
    if summary.get("capacity_full_hit_observed"):
        return "required_term_pair_capacity_sweep_recovered"
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "required_term_pair_capacity_sweep_partial"
    return "required_term_pair_capacity_sweep_not_recovered"


def _source_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_rebalance_seed_stability_decision": summary.get("pair_rebalance_seed_stability_decision"),
        "source_pair_rebalance_decision": summary.get("source_pair_rebalance_decision"),
        "selected_pair_count": summary.get("selected_pair_count"),
        "seed_count": summary.get("seed_count"),
        "pair_seed_full_hit_count": summary.get("pair_seed_full_hit_count"),
        "stable_pair_count": summary.get("stable_pair_count"),
        "pair_rebalance_seed_stable": summary.get("pair_rebalance_seed_stable"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("capacity_full_hit_observed"):
        return "pair_capacity_sweep_recovered_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "At least one capacity sweep input or training run failed, so no capacity conclusion is available."
    if summary.get("capacity_full_hit_observed"):
        return "At least one capacity variant recovered a full-hit pair for the fragile v496 target."
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "The sweep still produced only partial pair hits; capacity changes did not recover the v495 full-hit."
    return "The sweep produced no required-term continuation hits for the selected fragile pair."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed capacity sweep inputs or training runs before changing curriculum size"
    if summary.get("capacity_full_hit_observed"):
        return "repeat the recovered capacity variant across seeds before using it as a bridge to three-term curricula"
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "inspect corpus prompts and generation decoding before adding more terms to the checkpoint"
    return "step back to single-pair corpus design before increasing model size"


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


def _sample_prompt(pair: dict[str, Any]) -> str:
    missed = pair.get("v496_missed_full_hit_seeds") or []
    for term in list_of_dicts(pair.get("terms")):
        prompt = str(term.get("scaffold_prompt") or "")
        if prompt and missed is not None:
            return prompt
    return "fixed:"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "capacity-sweep"
