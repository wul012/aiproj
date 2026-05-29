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
    REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME,
    build_required_term_pair_rebalance_corpus,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_JSON_FILENAME = (
    "model_capability_required_term_pair_rebalance_seed_stability.json"
)
REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_TEXT_FILENAME = (
    "model_capability_required_term_pair_rebalance_seed_stability.txt"
)
REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_rebalance_seed_stability.md"
)
REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_HTML_FILENAME = (
    "model_capability_required_term_pair_rebalance_seed_stability.html"
)

DEFAULT_PAIR_REBALANCE_STABILITY_SEEDS = (496, 1496, 2496)


def locate_model_capability_required_term_pair_rebalance_seed_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_rebalance_seed_stability(
    pair_rebalance_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = DEFAULT_PAIR_REBALANCE_STABILITY_SEEDS,
    pair_limit: int | None = None,
    repeat: int = 240,
    isolated_repeat: int = 2,
    max_iters: int = 1600,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 8,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int | None = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_summary = as_dict(pair_rebalance_report.get("summary"))
    selected_pairs = select_rebalance_seed_stability_pairs(pair_rebalance_report, pair_limit=pair_limit)
    resolved_seeds = _clean_seeds(seeds)
    issues = _input_issues(pair_rebalance_report, selected_pairs, resolved_seeds)

    pair_seed_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for pair_index, pair in enumerate(selected_pairs):
            for seed_index, seed in enumerate(resolved_seeds):
                seed_result = _run_pair_seed(
                    root,
                    pair,
                    pair_index=pair_index,
                    seed_index=seed_index,
                    seed=seed,
                    repeat=repeat,
                    isolated_repeat=isolated_repeat,
                    max_iters=max_iters,
                    eval_iters=eval_iters,
                    batch_size=batch_size,
                    block_size=block_size,
                    n_layer=n_layer,
                    n_head=n_head,
                    n_embd=n_embd,
                    learning_rate=learning_rate,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    device=device,
                    train_func=train_func,
                    generate_func=generate_func,
                )
                pair_seed_rows.append(seed_result["pair_seed_row"])
                probe_rows.extend(seed_result["probe_rows"])

    training_failures = [row for row in pair_seed_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} pair rebalance seed-stability runs did not complete successfully")

    seed_pair_summaries = summarize_seed_pair_probe_rows(selected_pairs, probe_rows, resolved_seeds)
    pair_seed_summaries = summarize_pair_seed_stability(selected_pairs, seed_pair_summaries, resolved_seeds)
    summary = summarize_required_term_pair_rebalance_seed_stability(
        selected_pairs,
        pair_seed_rows,
        probe_rows,
        seed_pair_summaries,
        pair_seed_summaries,
        resolved_seeds,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair rebalance seed stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_rebalance": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seeds": resolved_seeds,
            "seed_count": len(resolved_seeds),
            "pair_limit": pair_limit,
            "repeat": max(1, int(repeat)),
            "isolated_repeat": max(1, int(isolated_repeat)),
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "repeat v495 full-hit rebalance pairs across seeds before expanding curriculum size",
        },
        "previous_baseline": _previous_baseline(source_summary),
        "summary": summary,
        "selected_pair_count": len(selected_pairs),
        "pairs": selected_pairs,
        "pair_seed_run_count": len(pair_seed_rows),
        "pair_seed_rows": pair_seed_rows,
        "seed_pair_summaries": seed_pair_summaries,
        "pair_seed_summaries": pair_seed_summaries,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def select_rebalance_seed_stability_pairs(
    pair_rebalance_report: dict[str, Any],
    *,
    pair_limit: int | None = None,
) -> list[dict[str, Any]]:
    source_pairs = {str(row.get("pair_id") or ""): row for row in list_of_dicts(pair_rebalance_report.get("pairs"))}
    selected: list[dict[str, Any]] = []
    for row in list_of_dicts(pair_rebalance_report.get("compare_rows")):
        if not row.get("rebalance_pair_full_hit"):
            continue
        if int(row.get("hit_count_delta") or 0) <= 0:
            continue
        pair_id = str(row.get("pair_id") or "")
        source_pair = source_pairs.get(pair_id)
        if not source_pair:
            continue
        selected.append(
            {
                "pair_id": pair_id,
                "pair_index": int(source_pair.get("pair_index") or len(selected)),
                "terms": list_of_dicts(source_pair.get("terms")),
                "term_names": [str(term) for term in source_pair.get("term_names") or row.get("term_names") or []],
                "v494_hit_terms": [str(term) for term in row.get("source_hit_terms") or []],
                "v494_missed_terms": [str(term) for term in row.get("source_missed_terms") or []],
                "v495_hit_terms": [str(term) for term in row.get("rebalance_hit_terms") or []],
                "v495_missed_terms": [str(term) for term in row.get("rebalance_missed_terms") or []],
                "v495_hit_count_delta": int(row.get("hit_count_delta") or 0),
                "v495_rebalance_pair_full_hit": bool(row.get("rebalance_pair_full_hit")),
            }
        )
    selected.sort(key=lambda item: str(item.get("pair_id") or ""))
    if pair_limit is not None and pair_limit >= 0:
        return selected[:pair_limit]
    return selected


def summarize_required_term_pair_rebalance_seed_stability(
    pairs: list[dict[str, Any]],
    pair_seed_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    seed_pair_summaries: list[dict[str, Any]],
    pair_seed_summaries: list[dict[str, Any]],
    seeds: list[int],
    *,
    source_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_summary or {}
    run_count = len(pair_seed_rows)
    pass_count = sum(1 for row in pair_seed_rows if row.get("training_status") == "pass")
    checkpoint_count = sum(1 for row in pair_seed_rows if row.get("checkpoint_exists"))
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in probe_rows)
    probe_hits = sum(1 for row in probe_rows if int(row.get("continuation_hit_count") or 0) > 0)
    full_seed_pairs = sum(1 for row in seed_pair_summaries if row.get("pair_full_hit"))
    partial_seed_pairs = sum(1 for row in seed_pair_summaries if row.get("pair_partial_hit"))
    stable_pairs = sum(1 for row in pair_seed_summaries if row.get("stable_full_hit_across_seeds"))
    partial_pairs = sum(1 for row in pair_seed_summaries if row.get("partial_full_hit_across_seeds"))
    return {
        "pair_rebalance_seed_stability_decision": _seed_stability_decision(
            pairs,
            pair_seed_rows,
            seeds,
            pass_count,
            stable_pairs,
            full_seed_pairs,
        ),
        "source_pair_rebalance_decision": source.get("pair_rebalance_decision"),
        "source_pair_full_hit_count": int(source.get("pair_full_hit_count") or 0),
        "source_pair_full_hit_delta": int(source.get("pair_full_hit_delta") or 0),
        "selected_pair_count": len(pairs),
        "seed_count": len(seeds),
        "pair_seed_run_count": run_count,
        "probe_count": len(probe_rows),
        "training_pass_count": pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "continuation_hit_count": continuation_hits,
        "probe_hit_count": probe_hits,
        "probe_success_rate": round(probe_hits / len(probe_rows), 4) if probe_rows else 0.0,
        "pair_seed_full_hit_count": full_seed_pairs,
        "pair_seed_partial_hit_count": partial_seed_pairs,
        "pair_seed_zero_hit_count": max(0, len(seed_pair_summaries) - full_seed_pairs - partial_seed_pairs),
        "pair_seed_full_hit_rate": round(full_seed_pairs / len(seed_pair_summaries), 4) if seed_pair_summaries else 0.0,
        "stable_pair_count": stable_pairs,
        "partial_stable_pair_count": partial_pairs,
        "no_full_hit_pair_count": max(0, len(pairs) - stable_pairs - partial_pairs),
        "stable_pair_rate": round(stable_pairs / len(pairs), 4) if pairs else 0.0,
        "pair_rebalance_seed_stable": stable_pairs > 0,
        "all_selected_pairs_seed_stable": bool(pairs) and stable_pairs == len(pairs),
        "seed_success_rates": _seed_success_rates(seed_pair_summaries, seeds, len(pairs)),
    }


def summarize_seed_pair_probe_rows(
    pairs: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    seeds: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        term_names = [str(term) for term in pair.get("term_names") or []]
        for seed in seeds:
            probes = [
                row
                for row in probe_rows
                if str(row.get("pair_id") or "") == pair_id and int(row.get("seed") or 0) == seed
            ]
            hit_terms = [str(row.get("term") or "") for row in probes if int(row.get("continuation_hit_count") or 0) > 0]
            rows.append(
                {
                    "pair_id": pair_id,
                    "seed": seed,
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


def summarize_pair_seed_stability(
    pairs: list[dict[str, Any]],
    seed_pair_summaries: list[dict[str, Any]],
    seeds: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        seed_rows = [row for row in seed_pair_summaries if str(row.get("pair_id") or "") == pair_id]
        full_hit_seeds = [int(row.get("seed") or 0) for row in seed_rows if row.get("pair_full_hit")]
        rows.append(
            {
                "pair_id": pair_id,
                "term_names": pair.get("term_names") or [],
                "v495_hit_terms": pair.get("v495_hit_terms") or [],
                "seed_count": len(seeds),
                "run_count": len(seed_rows),
                "full_hit_seed_count": len(full_hit_seeds),
                "full_hit_seeds": full_hit_seeds,
                "missed_full_hit_seeds": [seed for seed in seeds if seed not in full_hit_seeds],
                "full_hit_rate": round(len(full_hit_seeds) / len(seeds), 4) if seeds else 0.0,
                "stable_full_hit_across_seeds": bool(seeds) and len(full_hit_seeds) == len(seeds),
                "partial_full_hit_across_seeds": 0 < len(full_hit_seeds) < len(seeds),
            }
        )
    return rows


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_pair_seed(
    root: Path,
    pair: dict[str, Any],
    *,
    pair_index: int,
    seed_index: int,
    seed: int,
    repeat: int,
    isolated_repeat: int,
    max_iters: int,
    eval_iters: int,
    batch_size: int,
    block_size: int,
    n_layer: int,
    n_head: int,
    n_embd: int,
    learning_rate: float,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    device: str,
    train_func: TrainFunc | None,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    pair_id = str(pair.get("pair_id") or f"pair-{pair_index + 1}")
    run_id = f"{pair_id}-seed-{seed}"
    corpus_text = build_required_term_pair_rebalance_corpus(pair, repeat=repeat, isolated_repeat=isolated_repeat)
    corpus_path = root / "seed-corpora" / f"{_slug(run_id)}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "seed-runs" / run_id
    training = _train_micro_checkpoint(
        {
            "corpus_path": str(corpus_path),
            "train_dir": str(train_dir),
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "seed": seed,
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
                    "pair_seed_run_id": run_id,
                    "pair_terms": pair.get("term_names") or [],
                    "pair_seed_corpus_path": str(corpus_path),
                    "pair_seed": seed,
                    "rebalance_repeat": max(1, int(repeat)),
                    "isolated_repeat": max(1, int(isolated_repeat)),
                },
                training,
                index=term_index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=seed + term_index,
                device=device,
                generate_func=generate_func,
            )
            probe_rows.append(
                {
                    **generation,
                    "pair_id": pair_id,
                    "pair_seed_run_id": run_id,
                    "seed": seed,
                    "pair_terms": pair.get("term_names") or [],
                    "training_status": training.get("status"),
                    "checkpoint_path": training.get("checkpoint_path"),
                    "checkpoint_exists": bool(training.get("checkpoint_exists")),
                }
            )
    return {
        "pair_seed_row": {
            "pair_seed_run_id": run_id,
            "pair_id": pair_id,
            "pair_terms": pair.get("term_names") or [],
            "seed": seed,
            "seed_index": seed_index,
            "pair_seed_corpus_path": str(corpus_path),
            "pair_seed_corpus_exists": corpus_path.is_file(),
            "pair_seed_line_count": len(corpus_text.splitlines()) - 2,
            "rebalance_repeat": max(1, int(repeat)),
            "isolated_repeat": max(1, int(isolated_repeat)),
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


def _input_issues(report: dict[str, Any], pairs: list[dict[str, Any]], seeds: list[int]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source pair rebalance report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source pair rebalance report is not pass")
    if report and as_dict(report.get("summary")).get("pair_rebalance_decision") != "pair_rebalance_full_hit_gain":
        issues.append("source pair rebalance did not produce a full-hit gain")
    if not pairs:
        issues.append("source pair rebalance has no improved full-hit pairs to repeat")
    if not seeds:
        issues.append("at least one seed is required")
    return issues


def _seed_stability_decision(
    pairs: list[dict[str, Any]],
    pair_seed_rows: list[dict[str, Any]],
    seeds: list[int],
    pass_count: int,
    stable_pair_count: int,
    full_seed_pair_count: int,
) -> str:
    if not pairs:
        return "no_improved_full_hit_pairs"
    if not seeds:
        return "no_seeds_configured"
    if pass_count != len(pair_seed_rows):
        return "pair_rebalance_seed_training_failed"
    if not pair_seed_rows:
        return "pair_rebalance_seed_stability_missing"
    if stable_pair_count == len(pairs):
        return "all_rebalance_full_pairs_seed_stable"
    if stable_pair_count > 0:
        return "some_rebalance_full_pairs_seed_stable"
    if full_seed_pair_count > 0:
        return "pair_rebalance_seed_stability_partial_only"
    return "rebalance_full_pairs_not_reproduced_across_seeds"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_rebalance_seed_stability"
    if summary.get("pair_rebalance_seed_stable"):
        return "required_term_pair_rebalance_seed_stability_observed"
    if int(summary.get("pair_seed_full_hit_count") or 0) > 0:
        return "required_term_pair_rebalance_seed_stability_partial"
    return "required_term_pair_rebalance_seed_stability_not_reproduced"


def _previous_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_rebalance_decision": summary.get("pair_rebalance_decision"),
        "source_pair_full_hit_count": summary.get("source_pair_full_hit_count"),
        "pair_full_hit_count": summary.get("pair_full_hit_count"),
        "pair_full_hit_delta": summary.get("pair_full_hit_delta"),
        "probe_hit_count": summary.get("probe_hit_count"),
        "probe_hit_delta": summary.get("probe_hit_delta"),
        "rebalance_improved": summary.get("rebalance_improved"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("pair_rebalance_seed_stable"):
        return "pair_rebalance_seed_stable_capacity_signal_only"
    if int(summary.get("pair_seed_full_hit_count") or 0) > 0:
        return "pair_rebalance_seed_partial_capacity_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "At least one pair seed-stability input or training run failed, so no stability claim is available."
    if summary.get("pair_rebalance_seed_stable"):
        return "At least one v495 full-hit pair reproduced full-hit behavior across every configured seed."
    if int(summary.get("pair_seed_full_hit_count") or 0) > 0:
        return "The v495 full-hit pair reproduced under some seeds, but none were stable across every configured seed."
    return "The v495 full-hit pair did not reproduce full-hit behavior under the configured seed repeat."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed seed-stability runs before changing pair curriculum design"
    if summary.get("pair_rebalance_seed_stable"):
        return "use the seed-stable pair as a candidate bridge before trying a three-term curriculum"
    if int(summary.get("pair_seed_full_hit_count") or 0) > 0:
        return "increase seed count or training budget to separate fragile pair capacity from stable uptake"
    return "treat v495 full-hit as fragile and inspect corpus/model capacity before expanding target groups"


def _seed_success_rates(seed_pair_summaries: list[dict[str, Any]], seeds: list[int], pair_count: int) -> dict[str, float]:
    rates: dict[str, float] = {}
    for seed in seeds:
        full_hits = sum(
            1
            for row in seed_pair_summaries
            if int(row.get("seed") or 0) == seed and bool(row.get("pair_full_hit"))
        )
        rates[str(seed)] = round(full_hits / pair_count, 4) if pair_count else 0.0
    return rates


def _sample_prompt(pair: dict[str, Any]) -> str:
    for term in list_of_dicts(pair.get("terms")):
        prompt = str(term.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "fixed:"


def _clean_seeds(seeds: tuple[int, ...] | list[int]) -> list[int]:
    cleaned: list[int] = []
    for raw_seed in seeds:
        seed = int(raw_seed)
        if seed not in cleaned:
            cleaned.append(seed)
    return cleaned


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "pair-seed"
