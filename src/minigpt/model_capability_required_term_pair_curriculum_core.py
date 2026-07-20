"""Execution and aggregation core for required-term pair curriculum runs."""

from __future__ import annotations

from itertools import combinations
import re
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.report_utils import as_dict, list_of_dicts
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code

REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME = "model_capability_required_term_pair_curriculum.json"
REQUIRED_TERM_PAIR_CURRICULUM_TEXT_FILENAME = "model_capability_required_term_pair_curriculum.txt"
REQUIRED_TERM_PAIR_CURRICULUM_MARKDOWN_FILENAME = "model_capability_required_term_pair_curriculum.md"
REQUIRED_TERM_PAIR_CURRICULUM_HTML_FILENAME = "model_capability_required_term_pair_curriculum.html"


def select_pair_curriculum_terms(
    seed_stability_report: dict[str, Any],
    *,
    include_partial_terms: bool = False,
    term_limit: int | None = None,
) -> list[dict[str, Any]]:
    source_rows = {str(row.get("term") or ""): row for row in list_of_dicts(seed_stability_report.get("term_rows"))}
    selected: list[dict[str, Any]] = []
    for summary in list_of_dicts(seed_stability_report.get("term_seed_summaries")):
        term = str(summary.get("term") or "").strip()
        if not term:
            continue
        stable = bool(summary.get("stable_across_seeds"))
        partial = bool(summary.get("partial_across_seeds"))
        if not stable and not (include_partial_terms and partial):
            continue
        source = source_rows.get(term, {})
        selected.append(
            {
                "case": summary.get("case") or source.get("case"),
                "term": term,
                "scaffold_prompt": str(source.get("scaffold_prompt") or f"{term}:"),
                "source_hit_seed_count": int(summary.get("hit_seed_count") or 0),
                "source_seed_count": int(summary.get("seed_count") or 0),
                "source_hit_rate": summary.get("hit_rate"),
                "source_hit_seeds": summary.get("hit_seeds") or [],
                "source_missed_seeds": summary.get("missed_seeds") or [],
                "source_stable_across_seeds": stable,
                "source_partial_across_seeds": partial,
            }
        )
    selected.sort(key=lambda row: (str(row.get("case") or ""), str(row.get("term") or "")))
    if term_limit is not None and term_limit >= 0:
        return selected[:term_limit]
    return selected


def build_pair_curriculum_pairs(
    terms: list[dict[str, Any]],
    *,
    pair_limit: int | None = None,
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for index, pair_terms in enumerate(combinations(terms, 2)):
        pair_id = f"{index + 1:02d}-" + "-".join(_slug(str(term["term"])) for term in pair_terms)
        pairs.append(
            {
                "pair_id": pair_id,
                "pair_index": index,
                "terms": [dict(term) for term in pair_terms],
                "term_names": [str(term["term"]) for term in pair_terms],
                "case_names": [str(term.get("case") or "") for term in pair_terms],
            }
        )
    if pair_limit is not None and pair_limit >= 0:
        return pairs[:pair_limit]
    return pairs


def build_required_term_pair_curriculum_corpus(pair: dict[str, Any], *, repeat: int) -> str:
    repeat_count = max(1, int(repeat))
    terms = list_of_dicts(pair.get("terms"))
    lines = [
        "MiniGPT required-term pair curriculum corpus.",
        "Two seed-stable one-term targets are trained in the same file to inspect interference.",
    ]
    for _ in range(repeat_count):
        for term_row in terms:
            term = str(term_row.get("term") or "")
            prompt = str(term_row.get("scaffold_prompt") or f"{term}:")
            lines.append(f"{prompt}{term}")
            lines.append(f"{prompt} {term}")
    return "\n".join(lines) + "\n"


def summarize_required_term_pair_curriculum(
    selected_terms: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    pair_summaries: list[dict[str, Any]],
    *,
    previous_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    previous = previous_summary or {}
    pair_count = len(pairs)
    probe_count = len(probe_rows)
    training_pass_count = sum(1 for row in pair_rows if row.get("training_status") == "pass")
    checkpoint_count = sum(1 for row in pair_rows if row.get("checkpoint_exists"))
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in probe_rows)
    probe_hits = sum(1 for row in probe_rows if int(row.get("continuation_hit_count") or 0) > 0)
    full_pairs = sum(1 for row in pair_summaries if row.get("pair_full_hit"))
    partial_pairs = sum(1 for row in pair_summaries if row.get("pair_partial_hit"))
    return {
        "pair_curriculum_decision": _pair_curriculum_decision(
            selected_terms,
            pairs,
            pair_rows,
            probe_rows,
            training_pass_count,
            full_pairs,
            probe_hits,
        ),
        "source_stable_term_count": int(previous.get("stable_term_count") or 0),
        "source_term_seed_hit_count": int(previous.get("term_seed_hit_count") or 0),
        "selected_term_count": len(selected_terms),
        "pair_count": pair_count,
        "pair_run_count": len(pair_rows),
        "probe_count": probe_count,
        "training_pass_count": training_pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "continuation_hit_count": continuation_hits,
        "probe_hit_count": probe_hits,
        "probe_success_rate": round(probe_hits / probe_count, 4) if probe_count else 0.0,
        "pair_full_hit_count": full_pairs,
        "pair_partial_hit_count": partial_pairs,
        "pair_zero_hit_count": max(0, pair_count - full_pairs - partial_pairs),
        "pair_full_success_rate": round(full_pairs / pair_count, 4) if pair_count else 0.0,
        "multi_target_pair_capacity_observed": full_pairs > 0,
        "all_pairs_full_hit": bool(pairs) and full_pairs == pair_count,
    }


def summarize_pair_probe_rows(pairs: list[dict[str, Any]], probe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        rows = [row for row in probe_rows if str(row.get("pair_id") or "") == pair_id]
        hit_terms = [str(row.get("term") or "") for row in rows if int(row.get("continuation_hit_count") or 0) > 0]
        term_names = [str(term) for term in pair.get("term_names") or []]
        hit_count = len(hit_terms)
        summaries.append(
            {
                "pair_id": pair_id,
                "term_names": term_names,
                "probe_count": len(rows),
                "hit_count": hit_count,
                "hit_terms": hit_terms,
                "missed_terms": [term for term in term_names if term not in hit_terms],
                "hit_rate": round(hit_count / len(term_names), 4) if term_names else 0.0,
                "pair_full_hit": bool(term_names) and hit_count == len(term_names),
                "pair_partial_hit": 0 < hit_count < len(term_names),
            }
        )
    return summaries


def _run_pair(
    root: Path,
    pair: dict[str, Any],
    *,
    pair_index: int,
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
    generation_seed: int,
    device: str,
    train_func: TrainFunc | None,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    pair_id = str(pair.get("pair_id") or f"pair-{pair_index + 1}")
    corpus_text = build_required_term_pair_curriculum_corpus(pair, repeat=repeat)
    corpus_path = root / "pair-corpora" / f"{pair_id}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "pair-runs" / pair_id
    seed = generation_seed + pair_index
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
                    "pair_terms": pair.get("term_names") or [],
                    "pair_corpus_path": str(corpus_path),
                    "pair_repeat": max(1, int(repeat)),
                },
                training,
                index=term_index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=seed,
                device=device,
                generate_func=generate_func,
            )
            probe_rows.append(
                {
                    **generation,
                    "pair_id": pair_id,
                    "pair_terms": pair.get("term_names") or [],
                    "training_status": training.get("status"),
                    "checkpoint_path": training.get("checkpoint_path"),
                    "checkpoint_exists": bool(training.get("checkpoint_exists")),
                }
            )
    return {
        "pair_row": {
            "pair_id": pair_id,
            "pair_terms": pair.get("term_names") or [],
            "pair_corpus_path": str(corpus_path),
            "pair_corpus_exists": corpus_path.is_file(),
            "pair_line_count": len(corpus_text.splitlines()) - 2,
            "pair_repeat": max(1, int(repeat)),
            "training_seed": seed,
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


def _input_issues(report: dict[str, Any], selected_terms: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source one-term seed stability report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source one-term seed stability report is not pass")
    if report and as_dict(report.get("summary")).get("single_term_capacity_stable") is not True:
        issues.append("source one-term seed stability did not observe stable single-target capacity")
    if len(selected_terms) < 2:
        issues.append("at least two stable terms are required for pair curriculum")
    if not pairs:
        issues.append("no pair curriculum combinations were selected")
    return issues


def _pair_curriculum_decision(
    selected_terms: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    training_pass_count: int,
    full_pair_count: int,
    probe_hit_count: int,
) -> str:
    if len(selected_terms) < 2:
        return "not_enough_stable_terms"
    if not pairs:
        return "no_pair_curriculum_pairs"
    if training_pass_count != len(pair_rows):
        return "pair_curriculum_training_failed"
    if not probe_rows:
        return "pair_curriculum_generation_missing"
    if full_pair_count == len(pairs):
        return "all_pairs_preserve_required_terms"
    if full_pair_count > 0:
        return "some_pairs_preserve_required_terms"
    if probe_hit_count > 0:
        return "pair_curriculum_partial_only"
    return "pair_curriculum_no_uptake"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_curriculum"
    if summary.get("multi_target_pair_capacity_observed"):
        return "required_term_pair_curriculum_capacity_observed"
    if int(summary.get("probe_hit_count") or 0) > 0:
        return "required_term_pair_curriculum_partial"
    return "required_term_pair_curriculum_not_reproduced"


def _previous_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "one_term_seed_stability_decision": summary.get("one_term_seed_stability_decision"),
        "stable_term_count": summary.get("stable_term_count"),
        "partial_stable_term_count": summary.get("partial_stable_term_count"),
        "term_seed_hit_count": summary.get("term_seed_hit_count"),
        "term_seed_success_rate": summary.get("term_seed_success_rate"),
        "single_term_capacity_stable": summary.get("single_term_capacity_stable"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("multi_target_pair_capacity_observed"):
        return "pair_curriculum_capacity_signal_only"
    if int(summary.get("probe_hit_count") or 0) > 0:
        return "pair_curriculum_partial_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The pair curriculum source or at least one training run failed, so no multi-target conclusion is available."
    if summary.get("all_pairs_full_hit"):
        return "Every selected two-term curriculum preserved both required terms in short continuations."
    if summary.get("multi_target_pair_capacity_observed"):
        return "At least one two-term checkpoint emitted both required terms, showing limited multi-target capacity."
    if int(summary.get("probe_hit_count") or 0) > 0:
        return "Some probes hit their required term, but no pair preserved both targets together."
    return "The stable one-term targets did not survive the two-term curriculum probe."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed pair runs before expanding curriculum size"
    if summary.get("multi_target_pair_capacity_observed"):
        return "repeat the strongest pair across seeds before moving to three-term curriculum"
    if int(summary.get("probe_hit_count") or 0) > 0:
        return "inspect partially successful pairs and rebalance pair corpus before adding more targets"
    return "reduce pair size pressure with more iterations or stronger prompt separation before trying larger groups"


def _sample_prompt(pair: dict[str, Any]) -> str:
    for term in list_of_dicts(pair.get("terms")):
        prompt = str(term.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "fixed:"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "term"


__all__ = [
    "REQUIRED_TERM_PAIR_CURRICULUM_HTML_FILENAME",
    "REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME",
    "REQUIRED_TERM_PAIR_CURRICULUM_MARKDOWN_FILENAME",
    "REQUIRED_TERM_PAIR_CURRICULUM_TEXT_FILENAME",
    "build_pair_curriculum_pairs",
    "build_required_term_pair_curriculum_corpus",
    "resolve_exit_code",
    "select_pair_curriculum_terms",
    "summarize_pair_probe_rows",
    "summarize_required_term_pair_curriculum",
]
