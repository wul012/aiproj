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
    read_json_report as read_json_report,
)
from minigpt.model_capability_required_term_pair_rebalance_seed_stability import (
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_capacity_sweep_summary import (
    capacity_sweep_decision as _decision,
    interpretation_reason as _interpretation_reason,
    model_quality_claim as _model_quality_claim,
    next_action as _next_action,
    source_baseline as _source_baseline,
    summarize_capacity_variant_probe_rows,
    summarize_pair_capacity_sweep,
    summarize_required_term_pair_capacity_sweep,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


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
