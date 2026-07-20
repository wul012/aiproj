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
from minigpt.model_capability_required_term_one_term_isolation import (
    REQUIRED_TERM_ONE_TERM_ISOLATION_JSON_FILENAME,
    build_required_term_one_term_corpus,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_ONE_TERM_SEED_STABILITY_JSON_FILENAME = (
    "model_capability_required_term_one_term_seed_stability.json"
)
REQUIRED_TERM_ONE_TERM_SEED_STABILITY_TEXT_FILENAME = (
    "model_capability_required_term_one_term_seed_stability.txt"
)
REQUIRED_TERM_ONE_TERM_SEED_STABILITY_MARKDOWN_FILENAME = (
    "model_capability_required_term_one_term_seed_stability.md"
)
REQUIRED_TERM_ONE_TERM_SEED_STABILITY_HTML_FILENAME = (
    "model_capability_required_term_one_term_seed_stability.html"
)

DEFAULT_ONE_TERM_STABILITY_SEEDS = (493, 1493, 2493)


def locate_model_capability_required_term_one_term_seed_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_ONE_TERM_ISOLATION_JSON_FILENAME
    return source


def build_model_capability_required_term_one_term_seed_stability(
    one_term_isolation_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = DEFAULT_ONE_TERM_STABILITY_SEEDS,
    include_all_terms: bool = False,
    term_limit: int | None = None,
    repeat: int = 200,
    max_iters: int = 1200,
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
    source_summary = as_dict(one_term_isolation_report.get("summary"))
    selected_terms = select_seed_stability_terms(
        one_term_isolation_report,
        include_all_terms=include_all_terms,
        term_limit=term_limit,
    )
    resolved_seeds = _clean_seeds(seeds)
    issues = _input_issues(one_term_isolation_report, selected_terms, resolved_seeds)

    seed_rows: list[dict[str, Any]] = []
    if not issues:
        for term_index, term_row in enumerate(selected_terms):
            for seed_index, seed in enumerate(resolved_seeds):
                seed_rows.append(
                    _run_one_term_seed(
                        root,
                        term_row,
                        term_index=term_index,
                        seed_index=seed_index,
                        seed=seed,
                        repeat=repeat,
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
                )

    training_failures = [row for row in seed_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} one-term seed stability runs did not complete successfully")

    summary = summarize_required_term_one_term_seed_stability(
        selected_terms,
        seed_rows,
        resolved_seeds,
        previous_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term one-term seed stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_one_term_isolation": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seeds": resolved_seeds,
            "seed_count": len(resolved_seeds),
            "include_all_terms": include_all_terms,
            "term_limit": term_limit,
            "repeat": max(1, int(repeat)),
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
            "experiment_boundary": (
                "retrain v492 successful one-term cases across seeds to test whether isolated uptake is stable"
            ),
        },
        "previous_baseline": _previous_baseline(source_summary),
        "summary": summary,
        "term_count": len(selected_terms),
        "term_rows": selected_terms,
        "seed_run_count": len(seed_rows),
        "seed_rows": seed_rows,
        "term_seed_summaries": _term_seed_summaries(selected_terms, seed_rows, resolved_seeds),
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def select_seed_stability_terms(
    one_term_isolation_report: dict[str, Any],
    *,
    include_all_terms: bool = False,
    term_limit: int | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in list_of_dicts(one_term_isolation_report.get("isolation_rows")):
        term = str(row.get("term") or "").strip()
        if not term or term in seen:
            continue
        source_hits = int(row.get("continuation_hit_count") or 0)
        if not include_all_terms and source_hits <= 0:
            continue
        seen.add(term)
        rows.append(
            {
                "case": row.get("case"),
                "term": term,
                "scaffold_prompt": str(row.get("scaffold_prompt") or f"{term}:"),
                "source_one_term_run_id": row.get("one_term_run_id"),
                "source_generation_seed": row.get("generation_seed"),
                "source_continuation_hit_count": source_hits,
                "source_checkpoint_path": row.get("checkpoint_path"),
                "source_continuation_preview": row.get("continuation_preview"),
            }
        )
    if term_limit is not None and term_limit >= 0:
        return rows[:term_limit]
    return rows


def summarize_required_term_one_term_seed_stability(
    term_rows: list[dict[str, Any]],
    seed_rows: list[dict[str, Any]],
    seeds: list[int],
    *,
    previous_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    previous = previous_summary or {}
    term_summaries = _term_seed_summaries(term_rows, seed_rows, seeds)
    run_count = len(seed_rows)
    pass_count = sum(1 for row in seed_rows if row.get("training_status") == "pass")
    checkpoint_count = sum(1 for row in seed_rows if row.get("checkpoint_exists"))
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in seed_rows)
    hit_runs = sum(1 for row in seed_rows if int(row.get("continuation_hit_count") or 0) > 0)
    stable_terms = sum(1 for row in term_summaries if row.get("stable_across_seeds"))
    partial_terms = sum(1 for row in term_summaries if row.get("partial_across_seeds"))
    source_successes = int(previous.get("term_with_continuation_hit_count") or 0)
    return {
        "one_term_seed_stability_decision": _one_term_seed_stability_decision(
            term_rows,
            seed_rows,
            seeds,
            pass_count,
            stable_terms,
            hit_runs,
        ),
        "source_successful_term_count": source_successes,
        "selected_term_count": len(term_rows),
        "seed_count": len(seeds),
        "seed_run_count": run_count,
        "training_pass_count": pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "continuation_hit_count": continuation_hits,
        "term_seed_hit_count": hit_runs,
        "term_seed_success_rate": round(hit_runs / run_count, 4) if run_count else 0.0,
        "stable_term_count": stable_terms,
        "partial_stable_term_count": partial_terms,
        "no_hit_term_count": max(0, len(term_rows) - stable_terms - partial_terms),
        "stable_term_rate": round(stable_terms / len(term_rows), 4) if term_rows else 0.0,
        "single_term_capacity_stable": stable_terms > 0,
        "all_selected_terms_seed_stable": bool(term_rows) and stable_terms == len(term_rows),
        "seed_success_rates": _seed_success_rates(seed_rows, seeds, len(term_rows)),
        "term_success_rates": {str(row["term"]): row["hit_rate"] for row in term_summaries},
        "previous_one_term_decision": previous.get("one_term_isolation_decision"),
        "previous_term_with_continuation_hit_count": source_successes,
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_one_term_seed(
    root: Path,
    term_row: dict[str, Any],
    *,
    term_index: int,
    seed_index: int,
    seed: int,
    repeat: int,
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
    term = str(term_row.get("term") or "").strip()
    run_id = f"{term_index + 1:02d}-{_slug(term)}-seed-{seed}"
    corpus_text = build_required_term_one_term_corpus(term_row, repeat=repeat)
    corpus_path = root / "one-term-seed-corpora" / f"{run_id}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "one-term-seed-runs" / run_id
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
            "sample_prompt": str(term_row.get("scaffold_prompt") or f"{term}:"),
        },
        train_func,
    )
    generation: dict[str, Any] = {}
    if training.get("status") == "pass":
        generation = _generation_row(
            {
                **term_row,
                "one_term_seed_run_id": run_id,
                "one_term_seed_corpus_path": str(corpus_path),
                "one_term_seed": seed,
                "one_term_repeat": max(1, int(repeat)),
            },
            training,
            index=0,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            generation_seed=seed,
            device=device,
            generate_func=generate_func,
        )
    return {
        **term_row,
        "one_term_seed_run_id": run_id,
        "seed": seed,
        "seed_index": seed_index,
        "one_term_seed_corpus_path": str(corpus_path),
        "one_term_seed_corpus_exists": corpus_path.is_file(),
        "one_term_line_count": len(corpus_text.splitlines()) - 2,
        "one_term_repeat": max(1, int(repeat)),
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
        "generation_seed": generation.get("generation_seed"),
        "generated": generation.get("generated", ""),
        "continuation": generation.get("continuation", ""),
        "prompt_truncated": generation.get("prompt_truncated", False),
        "prompt_hit_count": generation.get("prompt_hit_count", 0),
        "generated_hit_count": generation.get("generated_hit_count", 0),
        "continuation_hit_count": generation.get("continuation_hit_count", 0),
        "generated_preview": generation.get("generated_preview", ""),
        "continuation_preview": generation.get("continuation_preview", ""),
    }


def _term_seed_summaries(
    term_rows: list[dict[str, Any]],
    seed_rows: list[dict[str, Any]],
    seeds: list[int],
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for term_row in term_rows:
        term = str(term_row.get("term") or "")
        rows = [row for row in seed_rows if str(row.get("term") or "") == term]
        hit_seeds = [int(row.get("seed") or 0) for row in rows if int(row.get("continuation_hit_count") or 0) > 0]
        hit_count = len(hit_seeds)
        summaries.append(
            {
                "case": term_row.get("case"),
                "term": term,
                "source_continuation_hit_count": term_row.get("source_continuation_hit_count"),
                "seed_count": len(seeds),
                "run_count": len(rows),
                "hit_seed_count": hit_count,
                "hit_seeds": hit_seeds,
                "missed_seeds": [seed for seed in seeds if seed not in hit_seeds],
                "hit_rate": round(hit_count / len(seeds), 4) if seeds else 0.0,
                "stable_across_seeds": bool(seeds) and hit_count == len(seeds),
                "partial_across_seeds": 0 < hit_count < len(seeds),
            }
        )
    return summaries


def _seed_success_rates(seed_rows: list[dict[str, Any]], seeds: list[int], term_count: int) -> dict[str, float]:
    rates: dict[str, float] = {}
    for seed in seeds:
        hits = sum(
            1
            for row in seed_rows
            if int(row.get("seed") or 0) == seed and int(row.get("continuation_hit_count") or 0) > 0
        )
        rates[str(seed)] = round(hits / term_count, 4) if term_count else 0.0
    return rates


def _input_issues(report: dict[str, Any], term_rows: list[dict[str, Any]], seeds: list[int]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source one-term isolation report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source one-term isolation report is not pass")
    if report and as_dict(report.get("summary")).get("single_term_capacity_observed") is not True:
        issues.append("source one-term isolation did not observe any successful term")
    if not term_rows:
        issues.append("source one-term isolation has no selected successful term rows")
    if not seeds:
        issues.append("at least one seed is required")
    return issues


def _one_term_seed_stability_decision(
    term_rows: list[dict[str, Any]],
    seed_rows: list[dict[str, Any]],
    seeds: list[int],
    pass_count: int,
    stable_term_count: int,
    hit_run_count: int,
) -> str:
    if not term_rows:
        return "no_successful_source_terms"
    if not seeds:
        return "no_seeds_configured"
    if pass_count != len(seed_rows):
        return "one_term_seed_training_run_failed"
    if not seed_rows:
        return "one_term_seed_stability_missing"
    if stable_term_count == len(term_rows):
        return "all_successful_terms_seed_stable"
    if stable_term_count > 0:
        return "some_successful_terms_seed_stable"
    if hit_run_count > 0:
        return "one_term_seed_stability_partial_only"
    return "successful_terms_not_reproduced_across_seeds"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_one_term_seed_stability"
    if summary.get("single_term_capacity_stable"):
        return "required_term_one_term_seed_stability_observed"
    if int(summary.get("term_seed_hit_count") or 0) > 0:
        return "required_term_one_term_seed_stability_partial"
    return "required_term_one_term_seed_stability_not_reproduced"


def _previous_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "one_term_isolation_decision": summary.get("one_term_isolation_decision"),
        "term_count": summary.get("term_count"),
        "term_with_continuation_hit_count": summary.get("term_with_continuation_hit_count"),
        "continuation_hit_count": summary.get("continuation_hit_count"),
        "single_term_capacity_observed": summary.get("single_term_capacity_observed"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("single_term_capacity_stable"):
        return "one_term_seed_stable_capacity_signal_only"
    if int(summary.get("term_seed_hit_count") or 0) > 0:
        return "one_term_seed_partial_capacity_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "At least one seed-stability input or training run failed, so no stability claim is available."
    if summary.get("single_term_capacity_stable"):
        return "At least one v492 successful one-term case reproduced continuation uptake across all configured seeds."
    if int(summary.get("term_seed_hit_count") or 0) > 0:
        return "Some v492 successful one-term cases still hit under another seed, but none were stable across every seed."
    return "The v492 successful one-term cases did not reproduce required-term continuation uptake under the configured seed repeat."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed seed-stability runs before changing corpus design"
    if summary.get("single_term_capacity_stable"):
        return "use stable one-term cases as a small curriculum before reintroducing multiple terms"
    if int(summary.get("term_seed_hit_count") or 0) > 0:
        return "increase seed count or training budget to separate fragile memorization from stable uptake"
    return "inspect per-term corpus and generation settings before treating v492 hits as reusable capacity"


def _clean_seeds(seeds: tuple[int, ...] | list[int]) -> list[int]:
    cleaned: list[int] = []
    for raw_seed in seeds:
        seed = int(raw_seed)
        if seed not in cleaned:
            cleaned.append(seed)
    return cleaned


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "term"
