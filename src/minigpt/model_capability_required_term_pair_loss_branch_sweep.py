from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_pair_contrast_free_training import (
    REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_contrast_free_training_components import _slug
from minigpt.model_capability_required_term_pair_loss_branch_sweep_components import (
    build_required_term_pair_loss_branch_corpus,
    normalize_loss_branch_variants,
    select_loss_branch_targets,
    summarize_loss_branch_targets,
    summarize_loss_branch_variant_probe_rows,
    summarize_required_term_pair_loss_branch_sweep,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_PAIR_LOSS_BRANCH_SWEEP_JSON_FILENAME = "model_capability_required_term_pair_loss_branch_sweep.json"
REQUIRED_TERM_PAIR_LOSS_BRANCH_SWEEP_TEXT_FILENAME = "model_capability_required_term_pair_loss_branch_sweep.txt"
REQUIRED_TERM_PAIR_LOSS_BRANCH_SWEEP_MARKDOWN_FILENAME = "model_capability_required_term_pair_loss_branch_sweep.md"
REQUIRED_TERM_PAIR_LOSS_BRANCH_SWEEP_HTML_FILENAME = "model_capability_required_term_pair_loss_branch_sweep.html"

DEFAULT_PAIR_LOSS_BRANCH_SWEEP_SEED = 501


def locate_model_capability_required_term_pair_loss_branch_sweep_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_JSON_FILENAME
    return source


def default_pair_loss_branch_sweep_variants() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": "missed-first-order",
            "label": "missed branch first in every clean cycle",
            "term_order": "missed-first",
            "repeat": 240,
            "isolated_repeat": 2,
            "missed_weight": 1,
            "missed_anchor_repeat": 0,
            "max_iters": 1800,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "missed-boosted",
            "label": "missed branch receives a second clean row copy",
            "term_order": "source-order",
            "repeat": 220,
            "isolated_repeat": 2,
            "missed_weight": 2,
            "missed_anchor_repeat": 0,
            "max_iters": 1800,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "missed-anchored",
            "label": "missed branch first plus extra terminal anchors",
            "term_order": "missed-first",
            "repeat": 180,
            "isolated_repeat": 2,
            "missed_weight": 2,
            "missed_anchor_repeat": 120,
            "max_iters": 2200,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
    ]


def build_model_capability_required_term_pair_loss_branch_sweep(
    contrast_free_training: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seed: int = DEFAULT_PAIR_LOSS_BRANCH_SWEEP_SEED,
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
    source_summary = as_dict(contrast_free_training.get("summary"))
    targets = select_loss_branch_targets(contrast_free_training, pair_limit=pair_limit)
    variant_rows = normalize_loss_branch_variants(default_pair_loss_branch_sweep_variants() if variants is None else variants)
    issues = _input_issues(contrast_free_training, targets, variant_rows)

    training_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for target_index, target in enumerate(targets):
            for variant_index, variant in enumerate(variant_rows):
                result = _run_loss_branch_variant(
                    root,
                    target,
                    variant,
                    target_index=target_index,
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
        issues.append(f"{len(training_failures)} loss-branch sweep training runs did not complete successfully")

    variant_summaries = summarize_loss_branch_variant_probe_rows(targets, variant_rows, probe_rows)
    target_summaries = summarize_loss_branch_targets(targets, variant_summaries)
    summary = summarize_required_term_pair_loss_branch_sweep(
        targets,
        variant_rows,
        training_rows,
        probe_rows,
        variant_summaries,
        target_summaries,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-branch sweep",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_contrast_free_training": str(source_path) if source_path else None,
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
            "experiment_boundary": "rescue a missed contrast-free pair branch without restoring negative contrast leakage",
        },
        "source_baseline": _source_baseline(source_summary),
        "target_count": len(targets),
        "targets": targets,
        "loss_branch_variants": variant_rows,
        "training_rows": training_rows,
        "variant_summaries": variant_summaries,
        "target_summaries": target_summaries,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def _run_loss_branch_variant(
    root: Path,
    target: dict[str, Any],
    variant: dict[str, Any],
    *,
    target_index: int,
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
    pair_id = str(target.get("pair_id") or f"pair-{target_index + 1}")
    variant_id = str(variant.get("variant_id") or f"variant-{variant_index + 1}")
    run_id = f"{pair_id}-{variant_id}-seed-{seed}"
    corpus_text = build_required_term_pair_loss_branch_corpus(target, variant)
    corpus_path = root / "loss-branch-corpora" / f"{_slug(run_id)}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "loss-branch-runs" / run_id
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
            "sample_prompt": _sample_prompt(target),
        },
        train_func,
    )
    probe_rows: list[dict[str, Any]] = []
    if training.get("status") == "pass":
        for term_index, term_row in enumerate(list_of_dicts(target.get("terms"))):
            generation = _generation_row(
                {
                    **term_row,
                    "pair_id": pair_id,
                    "variant_id": variant_id,
                    "variant_label": variant.get("label"),
                    "loss_branch_run_id": run_id,
                    "pair_terms": target.get("term_names") or [],
                    "focus_missed_term": target.get("focus_missed_term"),
                    "source_hit_terms": target.get("hit_term_names") or [],
                    "loss_branch_corpus_path": str(corpus_path),
                    "loss_branch_seed": seed,
                    "repeat": int(variant["repeat"]),
                    "isolated_repeat": int(variant["isolated_repeat"]),
                    "missed_weight": int(variant["missed_weight"]),
                    "missed_anchor_repeat": int(variant["missed_anchor_repeat"]),
                },
                training,
                index=term_index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=seed + target_index * 1000 + variant_index * 100,
                device=device,
                generate_func=generate_func,
            )
            probe_rows.append(
                {
                    **generation,
                    "pair_id": pair_id,
                    "variant_id": variant_id,
                    "variant_label": variant.get("label"),
                    "loss_branch_run_id": run_id,
                    "seed": int(seed),
                    "pair_terms": target.get("term_names") or [],
                    "focus_missed_term": target.get("focus_missed_term"),
                    "training_status": training.get("status"),
                    "checkpoint_path": training.get("checkpoint_path"),
                    "checkpoint_exists": bool(training.get("checkpoint_exists")),
                }
            )
    return {
        "training_row": {
            "loss_branch_run_id": run_id,
            "pair_id": pair_id,
            "pair_terms": target.get("term_names") or [],
            "focus_missed_term": target.get("focus_missed_term"),
            "variant_id": variant_id,
            "variant_label": variant.get("label"),
            "seed": int(seed),
            "loss_branch_corpus_path": str(corpus_path),
            "loss_branch_corpus_exists": corpus_path.is_file(),
            "loss_branch_line_count": len(corpus_text.splitlines()) - 2,
            "term_order": variant.get("term_order"),
            "repeat": int(variant["repeat"]),
            "isolated_repeat": int(variant["isolated_repeat"]),
            "missed_weight": int(variant["missed_weight"]),
            "missed_anchor_repeat": int(variant["missed_anchor_repeat"]),
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


def _input_issues(report: dict[str, Any], targets: list[dict[str, Any]], variants: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    source_summary = as_dict(report.get("summary"))
    if not report:
        issues.append("source contrast-free training report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source contrast-free training report is not pass")
    if report and source_summary.get("contrast_free_full_hit_observed"):
        issues.append("source contrast-free training already has a full-hit pair; loss-branch sweep is not needed")
    if report and int(source_summary.get("variant_pair_partial_hit_count") or 0) <= 0:
        issues.append("source contrast-free training has no partial pair to diagnose")
    if not targets:
        issues.append("source contrast-free training has no eligible missed branch target")
    if not variants:
        issues.append("at least one loss-branch sweep variant is required")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_branch_sweep"
    decision = str(summary.get("loss_branch_sweep_decision") or "")
    if decision == "loss_branch_sweep_full_hit_recovered":
        return "required_term_pair_loss_branch_recovered"
    if decision in {"loss_branch_sweep_focus_term_recovered", "loss_branch_sweep_tradeoff_only"}:
        return "required_term_pair_loss_branch_tradeoff"
    return "required_term_pair_loss_branch_not_recovered"


def _source_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "contrast_free_training_decision": summary.get("contrast_free_training_decision"),
        "variant_pair_partial_hit_count": summary.get("variant_pair_partial_hit_count"),
        "variant_pair_full_hit_count": summary.get("variant_pair_full_hit_count"),
        "best_variant_id": summary.get("best_variant_id"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("pair_full_hit_variant_count") or 0) > 0:
        return "loss_branch_pair_signal_only"
    if int(summary.get("focus_term_hit_variant_count") or 0) > 0:
        return "loss_branch_tradeoff_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The contrast-free source or at least one loss-branch training run failed."
    if int(summary.get("pair_full_hit_variant_count") or 0) > 0:
        return "At least one clean sweep variant emitted both pair terms, so the missed branch can be rescued under this setup."
    if int(summary.get("focus_term_hit_variant_count") or 0) > 0:
        return "The previously missed branch can be made to appear, but the sweep did not preserve a full pair hit."
    return "Changing clean row order and weighting did not rescue the previously missed branch."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair the loss-branch sweep inputs before training another variant"
    if int(summary.get("pair_full_hit_variant_count") or 0) > 0:
        return "repeat the recovered loss-branch variant across seeds before increasing pair count"
    if int(summary.get("focus_term_hit_variant_count") or 0) > 0:
        return "compare the tradeoff variant against source-order probes and tune for retaining both branches"
    return "diagnose tokenizer/context effects or simplify to one-branch checkpoints before adding more terms"


def _sample_prompt(target: dict[str, Any]) -> str:
    focus = str(target.get("focus_missed_term") or "")
    for term in list_of_dicts(target.get("terms")):
        if str(term.get("term") or "") == focus and term.get("scaffold_prompt"):
            return str(term["scaffold_prompt"])
    for term in list_of_dicts(target.get("terms")):
        prompt = str(term.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "loss:"
