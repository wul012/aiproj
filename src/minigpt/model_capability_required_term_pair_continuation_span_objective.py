from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_pair_diagnostic_rollup import (
    REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_prefix_completion_sweep import _sweep_with_checkpoint
from minigpt.model_capability_required_term_pair_prefix_completion_sweep_components import (
    summarize_prefix_completion_probe_rows,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, resolve_archived_reference_path, utc_now


REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_JSON_FILENAME = "model_capability_required_term_pair_continuation_span_objective.json"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_TEXT_FILENAME = "model_capability_required_term_pair_continuation_span_objective.txt"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_MARKDOWN_FILENAME = "model_capability_required_term_pair_continuation_span_objective.md"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_HTML_FILENAME = "model_capability_required_term_pair_continuation_span_objective.html"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_CORPUS_FILENAME = "required_term_pair_continuation_span_corpus.txt"

PrefixSweepFunc = Callable[[dict[str, Any]], list[dict[str, Any]]]


def locate_model_capability_required_term_pair_continuation_span_objective_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_continuation_span_objective(
    rollup_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    target_terms: tuple[str, ...] = ("fixed", "loss"),
    repeat: int = 160,
    bridge_repeat: int = 4,
    max_iters: int = 800,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 16,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int | None = 1,
    generation_seed: int = 510,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
    prefix_sweep_func: PrefixSweepFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_prefix_path = _source_prefix_completion_path(rollup_report, source_path)
    prefix_report = read_json_report(source_prefix_path) if source_prefix_path else {}
    examples = select_continuation_span_examples(prefix_report, target_terms=target_terms)
    issues = _input_issues(rollup_report, prefix_report, examples)

    corpus_text = build_continuation_span_corpus(examples, repeat=repeat, bridge_repeat=bridge_repeat)
    corpus_path = root / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")

    training: dict[str, Any] = {"status": "skipped", "reason": "input issues prevented training"}
    if not issues:
        training = _train_micro_checkpoint(
            {
                "corpus_path": str(corpus_path),
                "train_dir": str(root / "continuation-span-run"),
                "max_iters": max_iters,
                "eval_iters": eval_iters,
                "batch_size": batch_size,
                "block_size": block_size,
                "n_layer": n_layer,
                "n_head": n_head,
                "n_embd": n_embd,
                "learning_rate": learning_rate,
                "seed": generation_seed,
                "device": device,
                "sample_prompt": _sample_prompt(examples),
            },
            train_func,
        )
        if training.get("status") != "pass":
            training = refresh_training_artifact_status(training)
        if training.get("status") != "pass":
            issues.append("continuation-span training command did not complete successfully")

    generation_rows = _generation_rows(
        examples,
        training,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        generation_seed=generation_seed,
        device=device,
        generate_func=generate_func,
    )
    prefix_rows = _candidate_prefix_rows(
        examples,
        training,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        generation_seed=generation_seed,
        device=device,
        prefix_sweep_func=prefix_sweep_func,
    )
    source_prefix_summaries = summarize_source_prefix_completion(prefix_report, target_terms=target_terms)
    candidate_prefix_summaries = summarize_prefix_completion_probe_rows(prefix_rows)
    compare_rows = compare_span_prefix_summaries(source_prefix_summaries, candidate_prefix_summaries)
    summary = summarize_continuation_span_objective(
        examples,
        generation_rows,
        source_prefix_summaries,
        candidate_prefix_summaries,
        compare_rows,
        training,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair continuation-span objective",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_diagnostic_rollup": str(source_path) if source_path else None,
        "source_required_term_pair_prefix_completion": str(source_prefix_path) if source_prefix_path else None,
        "out_dir": str(root),
        "settings": {
            "target_terms": list(target_terms),
            "repeat": max(1, int(repeat)),
            "bridge_repeat": max(0, int(bridge_repeat)),
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
            "experiment_boundary": "train a tiny continuation-span target only for fixed/loss before larger data or more decoding tweaks",
        },
        "corpus": {
            "path": str(corpus_path),
            "char_count": len(corpus_text),
            "line_count": len(corpus_text.splitlines()),
        },
        "training": training,
        "examples": examples,
        "generation_rows": generation_rows,
        "source_prefix_summaries": source_prefix_summaries,
        "candidate_prefix_rows": prefix_rows,
        "candidate_prefix_summaries": candidate_prefix_summaries,
        "compare_rows": compare_rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def select_continuation_span_examples(
    prefix_report: dict[str, Any],
    *,
    target_terms: tuple[str, ...] = ("fixed", "loss"),
) -> list[dict[str, Any]]:
    wanted = {term.casefold() for term in target_terms}
    examples: dict[str, dict[str, Any]] = {}
    for target in list_of_dicts(prefix_report.get("targets")):
        for probe in list_of_dicts(target.get("probes")):
            term = str(probe.get("expected_term") or probe.get("prompt_term") or "").strip()
            if not term or term.casefold() not in wanted:
                continue
            examples.setdefault(
                term.casefold(),
                {
                    "term": term,
                    "prompt_term": str(probe.get("prompt_term") or term),
                    "scaffold_prompt": str(probe.get("prompt") or f"{term}:"),
                    "source_variant_id": probe.get("variant_id"),
                    "source_pair_id": probe.get("pair_id"),
                    "source_profile_id": probe.get("profile_id"),
                    "source_checkpoint_path": probe.get("checkpoint_path"),
                    "source_tokenizer_path": probe.get("tokenizer_path"),
                },
            )
    order = {term.casefold(): index for index, term in enumerate(target_terms)}
    return sorted(examples.values(), key=lambda row: order.get(str(row.get("term") or "").casefold(), 999))


def build_continuation_span_corpus(examples: list[dict[str, Any]], *, repeat: int, bridge_repeat: int) -> str:
    repeat_count = max(1, int(repeat))
    bridge_count = max(0, int(bridge_repeat))
    terms = [str(row.get("term") or "") for row in examples if row.get("term")]
    lines = [
        "MiniGPT required-term pair continuation-span objective corpus.",
        "Each prompt stops immediately before the target span so the model must complete the full term.",
    ]
    for _ in range(repeat_count):
        for example in examples:
            term = str(example.get("term") or "")
            prompt = str(example.get("scaffold_prompt") or f"{term}:")
            lines.append(f"{prompt}{term}")
            lines.append(f"{prompt} {term}")
            lines.append(f"continue span {prompt}{term}")
            lines.append(f"target span {term} after {prompt}")
        for _bridge in range(bridge_count):
            if len(terms) >= 2:
                lines.append(f"pair span {' '.join(terms)} keeps {terms[0]} after {terms[0]}:")
                lines.append(f"pair span {' '.join(terms)} keeps {terms[1]} after {terms[1]}:")
    return "\n".join(lines) + "\n"


def summarize_source_prefix_completion(
    prefix_report: dict[str, Any],
    *,
    target_terms: tuple[str, ...] = ("fixed", "loss"),
) -> list[dict[str, Any]]:
    wanted = {term.casefold() for term in target_terms}
    rows: list[dict[str, Any]] = []
    for term in target_terms:
        group = [
            row
            for row in list_of_dicts(prefix_report.get("probe_summaries"))
            if str(row.get("expected_term") or row.get("prompt_term") or "").casefold() == term.casefold()
        ]
        if not group and term.casefold() not in wanted:
            continue
        minimums = [int(row.get("minimum_hit_prefix_token_count") or 0) for row in group if row.get("minimum_hit_prefix_token_count")]
        rows.append(
            {
                "term": term,
                "source_profile_count": len(group),
                "source_minimum_hit_prefix_token_count": min(minimums) if minimums else None,
                "source_one_token_prefix_hit": any(row.get("one_token_prefix_hit") for row in group),
                "source_full_prefix_hit": any(row.get("full_prefix_hit") for row in group),
            }
        )
    return rows


def compare_span_prefix_summaries(source_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_by_term = {
        str(row.get("expected_term") or row.get("prompt_term") or "").casefold(): row for row in candidate_rows
    }
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        term = str(source.get("term") or "")
        candidate = candidate_by_term.get(term.casefold(), {})
        source_min = source.get("source_minimum_hit_prefix_token_count")
        candidate_min = candidate.get("minimum_hit_prefix_token_count")
        rows.append(
            {
                "term": term,
                "source_minimum_hit_prefix_token_count": source_min,
                "candidate_minimum_hit_prefix_token_count": candidate_min,
                "minimum_hit_prefix_delta": _delta(candidate_min, source_min),
                "source_one_token_prefix_hit": source.get("source_one_token_prefix_hit"),
                "candidate_one_token_prefix_hit": candidate.get("one_token_prefix_hit"),
                "source_full_prefix_hit": source.get("source_full_prefix_hit"),
                "candidate_full_prefix_hit": candidate.get("full_prefix_hit"),
                "candidate_best_completion_preview": candidate.get("best_completion_preview"),
            }
        )
    return rows


def summarize_continuation_span_objective(
    examples: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    source_prefix_summaries: list[dict[str, Any]],
    candidate_prefix_summaries: list[dict[str, Any]],
    compare_rows: list[dict[str, Any]],
    training: dict[str, Any],
) -> dict[str, Any]:
    generation_hit_terms = [str(row.get("term") or "") for row in generation_rows if int(row.get("continuation_hit_count") or 0) > 0]
    candidate_one_token_hits = sum(1 for row in candidate_prefix_summaries if row.get("one_token_prefix_hit"))
    prefix_improvements = sum(1 for row in compare_rows if (row.get("minimum_hit_prefix_delta") is not None and int(row["minimum_hit_prefix_delta"]) < 0))
    retained_one_token = sum(
        1
        for row in compare_rows
        if row.get("source_one_token_prefix_hit") and row.get("candidate_one_token_prefix_hit")
    )
    pair_full_hit = bool(examples) and len(set(generation_hit_terms)) == len(examples)
    return {
        "continuation_span_decision": _span_decision(training, generation_rows, pair_full_hit, prefix_improvements),
        "example_count": len(examples),
        "training_status": training.get("status"),
        "training_returncode": training.get("returncode"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "metrics_exists": bool(training.get("metrics_exists")),
        "source_prefix_summary_count": len(source_prefix_summaries),
        "candidate_prefix_summary_count": len(candidate_prefix_summaries),
        "generation_count": len(generation_rows),
        "generation_hit_count": len(generation_hit_terms),
        "generation_hit_terms": generation_hit_terms,
        "candidate_pair_full_generation_hit": pair_full_hit,
        "candidate_one_token_prefix_hit_count": candidate_one_token_hits,
        "prefix_minimum_improved_count": prefix_improvements,
        "source_one_token_retained_count": retained_one_token,
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def refresh_training_artifact_status(training: dict[str, Any]) -> dict[str, Any]:
    refreshed = dict(training)
    checkpoint_exists = _path_exists(refreshed.get("checkpoint_path"))
    tokenizer_exists = _path_exists(refreshed.get("tokenizer_path"))
    metrics_exists = _path_exists(refreshed.get("metrics_path"))
    train_config_exists = _path_exists(refreshed.get("train_config_path"))
    refreshed.update(
        {
            "checkpoint_exists": checkpoint_exists,
            "tokenizer_exists": tokenizer_exists,
            "metrics_exists": metrics_exists,
            "train_config_exists": train_config_exists,
        }
    )
    if int(refreshed.get("returncode") or 0) == 0 and checkpoint_exists and tokenizer_exists:
        refreshed["status"] = "pass"
    return refreshed


def _source_prefix_completion_path(rollup_report: dict[str, Any], source_path: str | Path | None) -> Path | None:
    for row in list_of_dicts(rollup_report.get("stage_rows")):
        if row.get("stage") != "prefix_completion":
            continue
        resolved = resolve_archived_reference_path(row.get("source_path"), Path(source_path).parent if source_path else None)
        if resolved and resolved.is_file():
            return resolved
    return None


def _input_issues(rollup_report: dict[str, Any], prefix_report: dict[str, Any], examples: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not rollup_report:
        issues.append("source diagnostic rollup report is missing or invalid")
    if rollup_report and rollup_report.get("status") != "pass":
        issues.append("source diagnostic rollup report is not pass")
    if as_dict(rollup_report.get("next_experiment_plan")).get("plan_id") != "continuation_span_objective_fixed_loss":
        issues.append("source rollup does not recommend continuation_span_objective_fixed_loss")
    if not prefix_report:
        issues.append("source prefix-completion report is missing or invalid")
    if prefix_report and prefix_report.get("status") != "pass":
        issues.append("source prefix-completion report is not pass")
    if not examples:
        issues.append("source prefix-completion report has no fixed/loss continuation-span examples")
    return issues


def _generation_rows(
    examples: list[dict[str, Any]],
    training: dict[str, Any],
    *,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    generation_seed: int,
    device: str,
    generate_func: GenerateFunc | None,
) -> list[dict[str, Any]]:
    if training.get("status") != "pass":
        return []
    return [
        _generation_row(
            example,
            training,
            index=index,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            generation_seed=generation_seed,
            device=device,
            generate_func=generate_func,
        )
        for index, example in enumerate(examples)
    ]


def _candidate_prefix_rows(
    examples: list[dict[str, Any]],
    training: dict[str, Any],
    *,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    generation_seed: int,
    device: str,
    prefix_sweep_func: PrefixSweepFunc | None,
) -> list[dict[str, Any]]:
    if training.get("status") != "pass":
        return []
    sweep = prefix_sweep_func or _sweep_with_checkpoint
    rows: list[dict[str, Any]] = []
    for index, example in enumerate(examples):
        rows.extend(
            sweep(
                {
                    "variant_id": "continuation-span-objective",
                    "profile_id": "candidate-greedy-12",
                    "prompt": example.get("scaffold_prompt"),
                    "prompt_term": example.get("prompt_term") or example.get("term"),
                    "expected_term": example.get("term"),
                    "checkpoint_path": training.get("checkpoint_path"),
                    "tokenizer_path": training.get("tokenizer_path"),
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    "top_k": top_k,
                    "seed": generation_seed + index,
                    "device": device,
                }
            )
        )
    return rows


def _span_decision(
    training: dict[str, Any],
    generation_rows: list[dict[str, Any]],
    pair_full_hit: bool,
    prefix_improvements: int,
) -> str:
    if training.get("status") != "pass":
        return "continuation_span_training_failed"
    if not generation_rows:
        return "continuation_span_generation_missing"
    if pair_full_hit:
        return "continuation_span_full_pair_generation_hit"
    if prefix_improvements > 0:
        return "continuation_span_prefix_minimum_improved"
    return "continuation_span_no_gain"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_continuation_span_objective"
    if summary.get("candidate_pair_full_generation_hit"):
        return "required_term_pair_continuation_span_full_hit"
    if int(summary.get("prefix_minimum_improved_count") or 0) > 0:
        return "required_term_pair_continuation_span_prefix_gain"
    return "required_term_pair_continuation_span_no_gain"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("candidate_pair_full_generation_hit"):
        return "tiny_continuation_span_pair_signal"
    if int(summary.get("prefix_minimum_improved_count") or 0) > 0:
        return "tiny_continuation_span_prefix_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The continuation-span objective could not be run cleanly."
    if summary.get("candidate_pair_full_generation_hit"):
        return "The tiny continuation-span run emitted both fixed and loss in free continuation probes."
    if int(summary.get("prefix_minimum_improved_count") or 0) > 0:
        return "The tiny continuation-span run reduced the forced-prefix length needed for at least one target term."
    return "The tiny continuation-span run completed but did not improve the fixed/loss continuation boundary."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair the continuation-span training inputs before evaluating capability"
    if summary.get("candidate_pair_full_generation_hit"):
        return "repeat the continuation-span objective across seeds before promoting this as a stable model-capability signal"
    if int(summary.get("prefix_minimum_improved_count") or 0) > 0:
        return "evaluate whether the prefix gain survives a second seed and a held-out prompt"
    return "adjust the continuation-span corpus before increasing model size"


def _sample_prompt(examples: list[dict[str, Any]]) -> str:
    for example in examples:
        prompt = str(example.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "fixed:"


def _delta(candidate: Any, source: Any) -> int | None:
    if candidate is None or source is None:
        return None
    return int(candidate) - int(source)


def _path_exists(value: Any) -> bool:
    return bool(value) and Path(str(value)).is_file()
