from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_pair_prompt_separation_audit import (
    REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_contrast_free_training_components import (
    _slug,
    build_required_term_pair_contrast_free_corpus,
    normalize_contrast_free_variants,
    select_contrast_free_pairs,
    summarize_contrast_free_pairs,
    summarize_contrast_free_variant_probe_rows,
    summarize_required_term_pair_contrast_free_training,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_JSON_FILENAME = (
    "model_capability_required_term_pair_contrast_free_training.json"
)
REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_TEXT_FILENAME = (
    "model_capability_required_term_pair_contrast_free_training.txt"
)
REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_contrast_free_training.md"
)
REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_HTML_FILENAME = (
    "model_capability_required_term_pair_contrast_free_training.html"
)

DEFAULT_PAIR_CONTRAST_FREE_TRAINING_SEED = 500


def locate_model_capability_required_term_pair_contrast_free_training_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_JSON_FILENAME
    return source


def default_pair_contrast_free_training_variants() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": "contrast-baseline",
            "label": "contrast-free baseline",
            "repeat": 240,
            "isolated_repeat": 2,
            "max_iters": 1600,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "contrast-longer",
            "label": "contrast-free longer training",
            "repeat": 240,
            "isolated_repeat": 2,
            "max_iters": 2400,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "contrast-denser",
            "label": "contrast-free denser corpus",
            "repeat": 360,
            "isolated_repeat": 2,
            "max_iters": 1600,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
    ]


def build_model_capability_required_term_pair_contrast_free_training(
    prompt_separation_audit: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seed: int = DEFAULT_PAIR_CONTRAST_FREE_TRAINING_SEED,
    pair_limit: int | None = 1,
    variants: list[dict[str, Any]] | None = None,
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
    source_summary = as_dict(prompt_separation_audit.get("summary"))
    selected_pairs = select_contrast_free_pairs(prompt_separation_audit, pair_limit=pair_limit)
    variant_rows = normalize_contrast_free_variants(
        default_pair_contrast_free_training_variants() if variants is None else variants
    )
    issues = _input_issues(prompt_separation_audit, selected_pairs, variant_rows)

    training_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for pair_index, pair in enumerate(selected_pairs):
            for variant_index, variant in enumerate(variant_rows):
                result = _run_contrast_free_variant(
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
                training_rows.append(result["training_row"])
                probe_rows.extend(result["probe_rows"])

    training_failures = [row for row in training_rows if row.get("training_status") != "pass"]
    if training_failures:
        issues.append(f"{len(training_failures)} contrast-free training runs did not complete successfully")

    variant_summaries = summarize_contrast_free_variant_probe_rows(selected_pairs, variant_rows, probe_rows)
    pair_summaries = summarize_contrast_free_pairs(selected_pairs, variant_rows, variant_summaries)
    summary = summarize_required_term_pair_contrast_free_training(
        selected_pairs,
        variant_rows,
        training_rows,
        probe_rows,
        variant_summaries,
        pair_summaries,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair contrast-free training",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_prompt_separation_audit": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seed": int(seed),
            "pair_limit": pair_limit,
            "variant_count": len(variant_rows),
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "remove prompt-target leakage before adding new target groups",
        },
        "source_baseline": _source_baseline(source_summary),
        "selected_pair_count": len(selected_pairs),
        "pairs": selected_pairs,
        "contrast_free_variants": variant_rows,
        "training_rows": training_rows,
        "variant_summaries": variant_summaries,
        "pair_summaries": pair_summaries,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_contrast_free_variant(
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
    corpus_text = build_required_term_pair_contrast_free_corpus(
        pair,
        repeat=int(variant["repeat"]),
        isolated_repeat=int(variant["isolated_repeat"]),
    )
    corpus_path = root / "contrast-free-corpora" / f"{_slug(run_id)}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "contrast-free-runs" / run_id
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
                    "contrast_free_run_id": run_id,
                    "pair_terms": pair.get("term_names") or [],
                    "contrast_free_corpus_path": str(corpus_path),
                    "contrast_free_seed": seed,
                    "contrast_free_repeat": int(variant["repeat"]),
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
                    "contrast_free_run_id": run_id,
                    "seed": int(seed),
                    "pair_terms": pair.get("term_names") or [],
                    "training_status": training.get("status"),
                    "checkpoint_path": training.get("checkpoint_path"),
                    "checkpoint_exists": bool(training.get("checkpoint_exists")),
                }
            )
    return {
        "training_row": {
            "contrast_free_run_id": run_id,
            "pair_id": pair_id,
            "pair_terms": pair.get("term_names") or [],
            "variant_id": variant_id,
            "variant_label": variant.get("label"),
            "seed": int(seed),
            "contrast_free_corpus_path": str(corpus_path),
            "contrast_free_corpus_exists": corpus_path.is_file(),
            "contrast_free_line_count": len(corpus_text.splitlines()) - 2,
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
        issues.append("source prompt separation audit report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source prompt separation audit report is not pass")
    if report and not source_summary.get("corpus_revision_recommended"):
        issues.append("source prompt separation audit does not recommend corpus revision")
    if not pairs:
        issues.append("source prompt separation audit has no eligible pair targets")
    if not variants:
        issues.append("at least one contrast-free variant is required")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_contrast_free_training"
    if summary.get("contrast_free_full_hit_observed"):
        return "required_term_pair_contrast_free_training_recovered"
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "required_term_pair_contrast_free_training_partial"
    return "required_term_pair_contrast_free_training_not_recovered"


def _source_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt_separation_audit_decision": summary.get("prompt_separation_audit_decision"),
        "corpus_revision_recommended": summary.get("corpus_revision_recommended"),
        "direct_prompt_other_term_leak_count": summary.get("direct_prompt_other_term_leak_count"),
        "negative_contrast_leak_count": summary.get("negative_contrast_leak_count"),
        "pair_header_shared_context_count": summary.get("pair_header_shared_context_count"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("contrast_free_full_hit_observed"):
        return "contrast_free_pair_signal_only"
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "contrast_free_pair_partial_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The prompt-separation audit input or at least one contrast-free training run failed."
    if summary.get("contrast_free_full_hit_observed"):
        return "At least one contrast-free pair checkpoint emitted both required terms under the fixed probes."
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "The contrast-free corpus removed direct leakage, but the tiny pair checkpoint still only preserved part of the pair."
    return "The contrast-free corpus did not produce required-term continuation uptake for this pair."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair contrast-free training inputs before changing model scale"
    if summary.get("contrast_free_full_hit_observed"):
        return "repeat the recovered contrast-free pair across seeds before adding three-term groups"
    if int(summary.get("variant_pair_partial_hit_count") or 0) > 0:
        return "inspect contrast-free generations and consider seed stability before adding more corpus templates"
    return "increase corpus clarity or model capacity after confirming the contrast-free rows are correct"


def _sample_prompt(pair: dict[str, Any]) -> str:
    for term in list_of_dicts(pair.get("terms")):
        prompt = str(term.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "fixed:"
