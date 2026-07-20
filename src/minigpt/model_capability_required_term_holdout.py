from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    REQUIRED_TERM_MICRO_TRAINING_JSON_FILENAME,
    TrainFunc,
    _generate,
    _hit_count,
    _preview,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_HOLDOUT_JSON_FILENAME = "model_capability_required_term_holdout.json"
REQUIRED_TERM_HOLDOUT_TEXT_FILENAME = "model_capability_required_term_holdout.txt"
REQUIRED_TERM_HOLDOUT_MARKDOWN_FILENAME = "model_capability_required_term_holdout.md"
REQUIRED_TERM_HOLDOUT_HTML_FILENAME = "model_capability_required_term_holdout.html"
REQUIRED_TERM_HOLDOUT_CORPUS_FILENAME = "required_term_holdout_corpus.txt"


def locate_model_capability_required_term_micro_training(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_MICRO_TRAINING_JSON_FILENAME
    return source


def build_model_capability_required_term_holdout(
    micro_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    max_iters: int = 420,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 8,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 32,
    learning_rate: float = 0.02,
    term_repeat: int = 24,
    max_new_tokens: int = 8,
    temperature: float = 0.2,
    top_k: int | None = 1,
    generation_seed: int = 484,
    holdout_terms: list[str] | None = None,
    holdout_stride: int = 3,
    holdout_offset: int = 2,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    examples = _source_examples(micro_report)
    split = split_required_term_examples(
        examples,
        holdout_terms=holdout_terms,
        holdout_stride=holdout_stride,
        holdout_offset=holdout_offset,
    )
    issues = _input_issues(micro_report, split)
    corpus_text = build_required_term_holdout_corpus(
        split["train_examples"],
        split["holdout_examples"],
        repeat=term_repeat,
    )
    corpus_path = root / REQUIRED_TERM_HOLDOUT_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")

    train_dir = root / "holdout-run"
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
            "seed": generation_seed,
            "device": device,
            "sample_prompt": _sample_prompt(split),
        },
        train_func,
    )
    if training.get("status") != "pass":
        issues.append("holdout micro-training command did not complete successfully")

    generation_rows: list[dict[str, Any]] = []
    if training.get("status") == "pass":
        generation_rows = [
            _generation_row(
                example,
                training,
                split_name="train",
                index=index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=generation_seed,
                device=device,
                generate_func=generate_func,
            )
            for index, example in enumerate(split["train_examples"])
        ]
        offset = len(generation_rows)
        generation_rows.extend(
            _generation_row(
                example,
                training,
                split_name="holdout",
                index=offset + index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=generation_seed,
                device=device,
                generate_func=generate_func,
            )
            for index, example in enumerate(split["holdout_examples"])
        )

    summary = summarize_required_term_holdout(split, generation_rows, training)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term holdout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_micro_training": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "term_repeat": term_repeat,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "generation_seed": generation_seed,
            "holdout_terms": split["holdout_terms"],
            "holdout_stride": holdout_stride,
            "holdout_offset": holdout_offset,
            "device": device,
        },
        "corpus": {
            "path": str(corpus_path),
            "char_count": len(corpus_text),
            "line_count": len(corpus_text.splitlines()),
            "repeat": term_repeat,
            "vocab_boundary": "holdout prompts are exposed for tokenizer/vocabulary coverage, but holdout prompt-to-term pairs are not repeated",
        },
        "training": training,
        "split": split,
        "summary": summary,
        "generation_count": len(generation_rows),
        "generation_rows": generation_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def split_required_term_examples(
    examples: list[dict[str, Any]],
    *,
    holdout_terms: list[str] | None,
    holdout_stride: int,
    holdout_offset: int,
) -> dict[str, Any]:
    normalized_terms = {str(term).strip() for term in holdout_terms or [] if str(term).strip()}
    unique_terms = sorted({str(row.get("term") or "").strip() for row in examples if str(row.get("term") or "").strip()})
    if not normalized_terms:
        stride = max(1, int(holdout_stride))
        offset = int(holdout_offset) % stride
        normalized_terms = {term for index, term in enumerate(unique_terms) if index % stride == offset}
    if not normalized_terms and unique_terms:
        normalized_terms = {unique_terms[-1]}
    train_examples = [row for row in examples if str(row.get("term") or "").strip() not in normalized_terms]
    holdout_examples = [row for row in examples if str(row.get("term") or "").strip() in normalized_terms]
    return {
        "source_example_count": len(examples),
        "unique_terms": unique_terms,
        "train_terms": sorted({str(row.get("term") or "") for row in train_examples if row.get("term")}),
        "holdout_terms": sorted(normalized_terms),
        "train_example_count": len(train_examples),
        "holdout_example_count": len(holdout_examples),
        "train_examples": train_examples,
        "holdout_examples": holdout_examples,
    }


def build_required_term_holdout_corpus(
    train_examples: list[dict[str, Any]],
    holdout_examples: list[dict[str, Any]],
    *,
    repeat: int,
) -> str:
    repeat_count = max(1, int(repeat))
    lines = [
        "MiniGPT required-term holdout corpus.",
        "Train rows contain scaffold-to-term pairs; holdout rows expose prompt vocabulary only.",
        "Prompt vocabulary: " + " ".join(sorted({str(row.get("scaffold_prompt") or "") for row in train_examples + holdout_examples})),
    ]
    for example in holdout_examples:
        lines.append(f"holdout-prompt-only|{example.get('case')}|{example.get('scaffold_prompt')}")
    for example in train_examples:
        term = str(example.get("term") or "")
        prompt = str(example.get("scaffold_prompt") or f"{term}:")
        case = str(example.get("case") or "unknown-case")
        for _ in range(repeat_count):
            lines.append(f"{prompt}{term}")
            lines.append(f"{prompt} {term}")
            lines.append(f"{case}|{prompt}{term}")
    return "\n".join(lines) + "\n"


def summarize_required_term_holdout(
    split: dict[str, Any],
    generation_rows: list[dict[str, Any]],
    training: dict[str, Any],
) -> dict[str, Any]:
    train_rows = [row for row in generation_rows if row.get("split") == "train"]
    holdout_rows = [row for row in generation_rows if row.get("split") == "holdout"]
    train_hits = _sum_hits(train_rows)
    holdout_hits = _sum_hits(holdout_rows)
    return {
        "holdout_decision": _holdout_decision(split, generation_rows, train_hits, holdout_hits, training),
        "source_example_count": split.get("source_example_count"),
        "train_example_count": split.get("train_example_count"),
        "holdout_example_count": split.get("holdout_example_count"),
        "train_term_count": len(split.get("train_terms") or []),
        "holdout_term_count": len(split.get("holdout_terms") or []),
        "generation_count": len(generation_rows),
        "train_generation_count": len(train_rows),
        "holdout_generation_count": len(holdout_rows),
        "train_continuation_hit_count": train_hits,
        "holdout_continuation_hit_count": holdout_hits,
        "train_case_with_hit_count": sum(1 for row in train_rows if int(row.get("continuation_hit_count") or 0) > 0),
        "holdout_case_with_hit_count": sum(1 for row in holdout_rows if int(row.get("continuation_hit_count") or 0) > 0),
        "train_hit_rate": _hit_rate(train_rows),
        "holdout_hit_rate": _hit_rate(holdout_rows),
        "training_status": training.get("status"),
        "training_returncode": training.get("returncode"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "metrics_exists": bool(training.get("metrics_exists")),
        "train_config_exists": bool(training.get("train_config_exists")),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _source_examples(micro_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in list_of_dicts(micro_report.get("examples")) if str(row.get("term") or "").strip()]


def _input_issues(micro_report: dict[str, Any], split: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not micro_report:
        issues.append("source required-term micro-training report is missing or invalid")
    if micro_report and micro_report.get("status") != "pass":
        issues.append("source required-term micro-training report is not pass")
    if not _source_examples(micro_report):
        issues.append("source required-term micro-training report has no examples")
    if not split.get("train_examples"):
        issues.append("held-out split has no training examples")
    if not split.get("holdout_examples"):
        issues.append("held-out split has no holdout examples")
    if as_dict(micro_report.get("summary")).get("continuation_hit_count") is None:
        issues.append("source required-term micro-training report has no continuation hit summary")
    return issues


def _generation_row(
    example: dict[str, Any],
    training: dict[str, Any],
    *,
    split_name: str,
    index: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    generation_seed: int,
    device: str,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    prompt = str(example.get("scaffold_prompt") or "")
    term = str(example.get("term") or "")
    request = {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "seed": generation_seed + index,
        "checkpoint_path": training.get("checkpoint_path"),
        "tokenizer_path": training.get("tokenizer_path"),
        "device": device,
    }
    response = _generate(request, generate_func)
    generated = str(response.get("generated") or "")
    prompt_truncated = not generated.startswith(prompt)
    continuation = generated[len(prompt) :] if not prompt_truncated else str(response.get("continuation") or "")
    return {
        **example,
        "split": split_name,
        "generation_seed": request["seed"],
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "generated": generated,
        "continuation": continuation,
        "prompt_truncated": prompt_truncated,
        "prompt_hit_count": _hit_count(prompt, [term]),
        "generated_hit_count": _hit_count(generated, [term]),
        "continuation_hit_count": _hit_count(continuation, [term]),
        "generated_preview": _preview(generated),
        "continuation_preview": _preview(continuation),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_holdout"
    if int(summary.get("holdout_continuation_hit_count") or 0) > 0:
        return "required_term_holdout_uptake_observed"
    return "required_term_holdout_no_uptake"


def _holdout_decision(
    split: dict[str, Any],
    generation_rows: list[dict[str, Any]],
    train_hits: int,
    holdout_hits: int,
    training: dict[str, Any],
) -> str:
    if training.get("status") != "pass":
        return "holdout_training_run_failed"
    if not split.get("train_examples") or not split.get("holdout_examples"):
        return "invalid_holdout_split"
    if not generation_rows:
        return "holdout_generation_missing"
    if holdout_hits > 0:
        return "heldout_required_term_uptake_observed"
    if train_hits > 0:
        return "training_slice_only_without_holdout_uptake"
    return "heldout_micro_training_no_required_term_uptake"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("holdout_continuation_hit_count") or 0) > 0:
        return "heldout_micro_training_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The held-out micro-training check did not complete, so no generalization conclusion is available."
    if int(summary.get("holdout_continuation_hit_count") or 0) > 0:
        return "At least one held-out required term appeared in continuation after training on other scaffold-to-term pairs."
    if int(summary.get("train_continuation_hit_count") or 0) > 0:
        return "Training-slice prompts produced required terms, but held-out terms did not, so v483's signal still looks slice-bound."
    return "Neither train nor held-out prompts produced required terms in continuation under this split."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair the held-out split or training run before making a model-capability claim"
    if int(summary.get("holdout_continuation_hit_count") or 0) > 0:
        return "repeat with a stricter case-level holdout and then compare against the standard benchmark rubric"
    if int(summary.get("train_continuation_hit_count") or 0) > 0:
        return "treat v483 as training-slice bound and improve corpus diversity before scaling"
    return "first reproduce train-slice uptake under a split before expanding benchmark scope"


def _sample_prompt(split: dict[str, Any]) -> str:
    for row in split.get("train_examples") or []:
        prompt = str(row.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "data:"


def _sum_hits(rows: list[dict[str, Any]]) -> int:
    return sum(int(row.get("continuation_hit_count") or 0) for row in rows)


def _hit_rate(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if int(row.get("continuation_hit_count") or 0) > 0) / len(rows), 4)
