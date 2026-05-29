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
from minigpt.model_capability_required_term_pair_curriculum import (
    REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME = "model_capability_required_term_pair_rebalance.json"
REQUIRED_TERM_PAIR_REBALANCE_TEXT_FILENAME = "model_capability_required_term_pair_rebalance.txt"
REQUIRED_TERM_PAIR_REBALANCE_MARKDOWN_FILENAME = "model_capability_required_term_pair_rebalance.md"
REQUIRED_TERM_PAIR_REBALANCE_HTML_FILENAME = "model_capability_required_term_pair_rebalance.html"


def locate_model_capability_required_term_pair_rebalance_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_rebalance(
    pair_curriculum_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
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
    generation_seed: int = 495,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_summary = as_dict(pair_curriculum_report.get("summary"))
    pairs = select_rebalance_pairs(pair_curriculum_report, pair_limit=pair_limit)
    issues = _input_issues(pair_curriculum_report, pairs)

    pair_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for pair_index, pair in enumerate(pairs):
            pair_result = _run_rebalance_pair(
                root,
                pair,
                pair_index=pair_index,
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
                generation_seed=generation_seed,
                device=device,
                train_func=train_func,
                generate_func=generate_func,
            )
            pair_rows.append(pair_result["pair_row"])
            probe_rows.extend(pair_result["probe_rows"])

    training_failures = [row for row in pair_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} pair rebalance training runs did not complete successfully")

    pair_summaries = summarize_rebalance_probe_rows(pairs, probe_rows)
    compare_rows = compare_rebalance_pairs(pairs, pair_summaries)
    summary = summarize_required_term_pair_rebalance(
        pairs,
        pair_rows,
        probe_rows,
        pair_summaries,
        compare_rows,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair rebalance",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_curriculum": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
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
            "generation_seed": generation_seed,
            "device": device,
            "experiment_boundary": "rebalance partial two-term curricula before expanding to larger target groups",
        },
        "previous_baseline": _previous_baseline(source_summary),
        "summary": summary,
        "selected_pair_count": len(pairs),
        "pairs": pairs,
        "pair_rows": pair_rows,
        "pair_summaries": pair_summaries,
        "compare_rows": compare_rows,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def select_rebalance_pairs(
    pair_curriculum_report: dict[str, Any],
    *,
    pair_limit: int | None = None,
) -> list[dict[str, Any]]:
    source_pairs = {str(row.get("pair_id") or ""): row for row in list_of_dicts(pair_curriculum_report.get("pairs"))}
    selected: list[dict[str, Any]] = []
    for summary in list_of_dicts(pair_curriculum_report.get("pair_summaries")):
        if summary.get("pair_full_hit"):
            continue
        if not summary.get("pair_partial_hit"):
            continue
        pair_id = str(summary.get("pair_id") or "")
        source_pair = source_pairs.get(pair_id)
        if not source_pair:
            continue
        selected.append(
            {
                "pair_id": pair_id,
                "pair_index": int(source_pair.get("pair_index") or len(selected)),
                "terms": list_of_dicts(source_pair.get("terms")),
                "term_names": [str(term) for term in source_pair.get("term_names") or []],
                "source_hit_terms": [str(term) for term in summary.get("hit_terms") or []],
                "source_missed_terms": [str(term) for term in summary.get("missed_terms") or []],
                "source_hit_rate": summary.get("hit_rate"),
                "source_pair_full_hit": bool(summary.get("pair_full_hit")),
                "source_pair_partial_hit": bool(summary.get("pair_partial_hit")),
            }
        )
    selected.sort(key=lambda row: str(row.get("pair_id") or ""))
    if pair_limit is not None and pair_limit >= 0:
        return selected[:pair_limit]
    return selected


def build_required_term_pair_rebalance_corpus(
    pair: dict[str, Any],
    *,
    repeat: int,
    isolated_repeat: int,
) -> str:
    terms = list_of_dicts(pair.get("terms"))
    repeat_count = max(1, int(repeat))
    isolated_count = max(1, int(isolated_repeat))
    lines = [
        "MiniGPT required-term pair rebalance corpus.",
        "Each prompt must keep its own target even when two targets share one checkpoint.",
    ]
    for _ in range(repeat_count):
        for term_row in terms:
            lines.extend(_term_rows(term_row, isolated_count))
        lines.extend(_paired_rows(terms))
    return "\n".join(lines) + "\n"


def summarize_required_term_pair_rebalance(
    pairs: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    pair_summaries: list[dict[str, Any]],
    compare_rows: list[dict[str, Any]],
    *,
    source_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_summary or {}
    selected_source_probe_hits = sum(len(pair.get("source_hit_terms") or []) for pair in pairs)
    selected_source_full_pairs = sum(1 for pair in pairs if pair.get("source_pair_full_hit"))
    pair_count = len(pairs)
    probe_count = len(probe_rows)
    training_pass_count = sum(1 for row in pair_rows if row.get("training_status") == "pass")
    checkpoint_count = sum(1 for row in pair_rows if row.get("checkpoint_exists"))
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in probe_rows)
    probe_hits = sum(1 for row in probe_rows if int(row.get("continuation_hit_count") or 0) > 0)
    full_pairs = sum(1 for row in pair_summaries if row.get("pair_full_hit"))
    partial_pairs = sum(1 for row in pair_summaries if row.get("pair_partial_hit"))
    improved_pairs = sum(1 for row in compare_rows if int(row.get("hit_count_delta") or 0) > 0)
    regressed_pairs = sum(1 for row in compare_rows if int(row.get("hit_count_delta") or 0) < 0)
    return {
        "pair_rebalance_decision": _rebalance_decision(
            pairs,
            pair_rows,
            probe_rows,
            training_pass_count,
            full_pairs,
            probe_hits,
            selected_source_full_pairs,
            selected_source_probe_hits,
        ),
        "source_pair_curriculum_decision": source.get("pair_curriculum_decision"),
        "source_pair_count": int(source.get("pair_count") or 0),
        "source_probe_hit_count": selected_source_probe_hits,
        "source_pair_full_hit_count": selected_source_full_pairs,
        "selected_pair_count": pair_count,
        "pair_run_count": len(pair_rows),
        "probe_count": probe_count,
        "training_pass_count": training_pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "continuation_hit_count": continuation_hits,
        "probe_hit_count": probe_hits,
        "probe_hit_delta": probe_hits - selected_source_probe_hits,
        "probe_success_rate": round(probe_hits / probe_count, 4) if probe_count else 0.0,
        "pair_full_hit_count": full_pairs,
        "pair_full_hit_delta": full_pairs - selected_source_full_pairs,
        "pair_partial_hit_count": partial_pairs,
        "pair_zero_hit_count": max(0, pair_count - full_pairs - partial_pairs),
        "pair_full_success_rate": round(full_pairs / pair_count, 4) if pair_count else 0.0,
        "pair_improved_count": improved_pairs,
        "pair_regressed_count": regressed_pairs,
        "multi_target_pair_capacity_observed": full_pairs > 0,
        "rebalance_improved": full_pairs > selected_source_full_pairs or probe_hits > selected_source_probe_hits,
    }


def summarize_rebalance_probe_rows(pairs: list[dict[str, Any]], probe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        probes = [row for row in probe_rows if str(row.get("pair_id") or "") == pair_id]
        hit_terms = [str(row.get("term") or "") for row in probes if int(row.get("continuation_hit_count") or 0) > 0]
        term_names = [str(term) for term in pair.get("term_names") or []]
        hit_count = len(hit_terms)
        rows.append(
            {
                "pair_id": pair_id,
                "term_names": term_names,
                "source_hit_terms": pair.get("source_hit_terms") or [],
                "source_missed_terms": pair.get("source_missed_terms") or [],
                "hit_count": hit_count,
                "hit_terms": hit_terms,
                "missed_terms": [term for term in term_names if term not in hit_terms],
                "hit_rate": round(hit_count / len(term_names), 4) if term_names else 0.0,
                "pair_full_hit": bool(term_names) and hit_count == len(term_names),
                "pair_partial_hit": 0 < hit_count < len(term_names),
            }
        )
    return rows


def compare_rebalance_pairs(pairs: list[dict[str, Any]], pair_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = {str(row.get("pair_id") or ""): row for row in pair_summaries}
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        summary = summaries.get(pair_id, {})
        source_hits = [str(term) for term in pair.get("source_hit_terms") or []]
        rebalance_hits = [str(term) for term in summary.get("hit_terms") or []]
        rows.append(
            {
                "pair_id": pair_id,
                "term_names": pair.get("term_names") or [],
                "source_hit_terms": source_hits,
                "source_missed_terms": pair.get("source_missed_terms") or [],
                "rebalance_hit_terms": rebalance_hits,
                "rebalance_missed_terms": summary.get("missed_terms") or [],
                "source_hit_count": len(source_hits),
                "rebalance_hit_count": len(rebalance_hits),
                "hit_count_delta": len(rebalance_hits) - len(source_hits),
                "source_pair_full_hit": bool(pair.get("source_pair_full_hit")),
                "rebalance_pair_full_hit": bool(summary.get("pair_full_hit")),
            }
        )
    return rows


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_rebalance_pair(
    root: Path,
    pair: dict[str, Any],
    *,
    pair_index: int,
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
    generation_seed: int,
    device: str,
    train_func: TrainFunc | None,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    pair_id = str(pair.get("pair_id") or f"pair-{pair_index + 1}")
    corpus_text = build_required_term_pair_rebalance_corpus(pair, repeat=repeat, isolated_repeat=isolated_repeat)
    corpus_path = root / "rebalance-corpora" / f"{_slug(pair_id)}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "rebalance-runs" / pair_id
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
                    "rebalance_corpus_path": str(corpus_path),
                    "rebalance_repeat": max(1, int(repeat)),
                    "isolated_repeat": max(1, int(isolated_repeat)),
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
            "rebalance_corpus_path": str(corpus_path),
            "rebalance_corpus_exists": corpus_path.is_file(),
            "rebalance_line_count": len(corpus_text.splitlines()) - 2,
            "rebalance_repeat": max(1, int(repeat)),
            "isolated_repeat": max(1, int(isolated_repeat)),
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


def _term_rows(term_row: dict[str, Any], isolated_count: int) -> list[str]:
    term = str(term_row.get("term") or "")
    prompt = str(term_row.get("scaffold_prompt") or f"{term}:")
    rows: list[str] = []
    for _ in range(isolated_count):
        rows.append(f"{prompt}{term}")
        rows.append(f"{prompt} {term}")
        rows.append(f"{term} prompt keeps {term}")
    return rows


def _paired_rows(terms: list[dict[str, Any]]) -> list[str]:
    rows: list[str] = []
    names = [str(term.get("term") or "") for term in terms]
    for term_row in terms:
        term = str(term_row.get("term") or "")
        prompt = str(term_row.get("scaffold_prompt") or f"{term}:")
        other_terms = [name for name in names if name != term]
        rows.append(f"{prompt}{term}")
        rows.append(f"pair {' '.join(names)} prompt {prompt} target {term}")
        for other in other_terms:
            rows.append(f"{prompt}{term} not {other}")
    return rows


def _input_issues(report: dict[str, Any], pairs: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source pair curriculum report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source pair curriculum report is not pass")
    if report and as_dict(report.get("summary")).get("pair_curriculum_decision") != "pair_curriculum_partial_only":
        issues.append("source pair curriculum is not a partial-only rebalance target")
    if not pairs:
        issues.append("no partial pair curriculum rows were selected for rebalance")
    return issues


def _rebalance_decision(
    pairs: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    training_pass_count: int,
    full_pair_count: int,
    probe_hit_count: int,
    source_full_pair_count: int,
    source_probe_hit_count: int,
) -> str:
    if not pairs:
        return "no_partial_pairs_selected"
    if training_pass_count != len(pair_rows):
        return "pair_rebalance_training_failed"
    if not probe_rows:
        return "pair_rebalance_generation_missing"
    if full_pair_count > source_full_pair_count:
        return "pair_rebalance_full_hit_gain"
    if probe_hit_count > source_probe_hit_count:
        return "pair_rebalance_probe_hit_gain"
    if probe_hit_count == 0:
        return "pair_rebalance_no_uptake"
    return "pair_rebalance_no_gain"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_rebalance"
    if int(summary.get("pair_full_hit_delta") or 0) > 0:
        return "required_term_pair_rebalance_capacity_gain"
    if int(summary.get("probe_hit_delta") or 0) > 0:
        return "required_term_pair_rebalance_probe_gain"
    return "required_term_pair_rebalance_no_gain"


def _previous_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_curriculum_decision": summary.get("pair_curriculum_decision"),
        "pair_count": summary.get("pair_count"),
        "probe_hit_count": summary.get("probe_hit_count"),
        "pair_full_hit_count": summary.get("pair_full_hit_count"),
        "pair_partial_hit_count": summary.get("pair_partial_hit_count"),
        "pair_full_success_rate": summary.get("pair_full_success_rate"),
        "multi_target_pair_capacity_observed": summary.get("multi_target_pair_capacity_observed"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("pair_full_hit_delta") or 0) > 0:
        return "pair_rebalance_capacity_signal_only"
    if int(summary.get("probe_hit_delta") or 0) > 0:
        return "pair_rebalance_probe_gain_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The rebalance source or at least one pair training run failed, so no capacity claim is available."
    if int(summary.get("pair_full_hit_delta") or 0) > 0:
        return "At least one previously partial pair emitted both required terms after rebalance training."
    if int(summary.get("probe_hit_delta") or 0) > 0:
        return "The rebalance increased individual probe hits but still did not preserve both terms in a pair."
    return "The rebalance did not improve on the v494 partial-only pair curriculum boundary."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed rebalance inputs or training runs before changing model scale"
    if int(summary.get("pair_full_hit_delta") or 0) > 0:
        return "repeat the improved pairs across seeds before attempting three-term curricula"
    if int(summary.get("probe_hit_delta") or 0) > 0:
        return "keep pair rebalance but tune prompt separation before increasing target count"
    return "move from corpus-only rebalance to capacity changes such as more iterations or wider embeddings"


def _sample_prompt(pair: dict[str, Any]) -> str:
    missed = pair.get("source_missed_terms") or []
    for term in list_of_dicts(pair.get("terms")):
        if term.get("term") in missed:
            return str(term.get("scaffold_prompt") or f"{term.get('term')}:")
    for term in list_of_dicts(pair.get("terms")):
        prompt = str(term.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "fixed:"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "pair"
