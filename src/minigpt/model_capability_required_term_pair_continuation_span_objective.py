from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_pair_continuation_span_objective_core import (
    PrefixSweepFunc,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_CORPUS_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_HTML_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_JSON_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_OBJECTIVE_TEXT_FILENAME,
    _candidate_prefix_rows,
    _decision,
    _generation_rows,
    _input_issues,
    _model_quality_claim,
    _next_action,
    _reason,
    _sample_prompt,
    _source_prefix_completion_path,
    build_continuation_span_corpus,
    compare_span_prefix_summaries,
    refresh_training_artifact_status,
    resolve_exit_code,
    select_continuation_span_examples,
    summarize_continuation_span_objective,
    summarize_source_prefix_completion,
)
from minigpt.model_capability_required_term_pair_diagnostic_rollup import (
    REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_prefix_completion_sweep_components import (
    summarize_prefix_completion_probe_rows,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import utc_now


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


# Execution and aggregation helpers are re-exported from the core module.
