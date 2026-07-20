from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_pair_contrast_free_training_components import _slug
from minigpt.model_capability_required_term_pair_loss_branch_sweep import (
    REQUIRED_TERM_PAIR_LOSS_BRANCH_SWEEP_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_branch_retention_sweep_components import (
    build_required_term_pair_branch_retention_corpus,
    normalize_branch_retention_variants,
    select_branch_retention_targets,
    summarize_branch_retention_targets,
    summarize_branch_retention_variant_probe_rows,
    summarize_required_term_pair_branch_retention_sweep,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_BRANCH_RETENTION_SWEEP_JSON_FILENAME = (
    "model_capability_required_term_pair_branch_retention_sweep.json"
)
REQUIRED_TERM_PAIR_BRANCH_RETENTION_SWEEP_TEXT_FILENAME = (
    "model_capability_required_term_pair_branch_retention_sweep.txt"
)
REQUIRED_TERM_PAIR_BRANCH_RETENTION_SWEEP_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_branch_retention_sweep.md"
)
REQUIRED_TERM_PAIR_BRANCH_RETENTION_SWEEP_HTML_FILENAME = (
    "model_capability_required_term_pair_branch_retention_sweep.html"
)

DEFAULT_PAIR_BRANCH_RETENTION_SWEEP_SEED = 502


def locate_model_capability_required_term_pair_branch_retention_sweep_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_BRANCH_SWEEP_JSON_FILENAME
    return source


def default_pair_branch_retention_sweep_variants() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": "alternating-balanced",
            "label": "alternate fixed/loss order without asymmetric boost",
            "cycle_strategy": "alternating",
            "repeat": 240,
            "isolated_repeat": 2,
            "term_weight": 1,
            "symmetric_anchor_repeat": 0,
            "max_iters": 2200,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "symmetric-boost",
            "label": "equal double copies for both pair branches",
            "cycle_strategy": "alternating",
            "repeat": 180,
            "isolated_repeat": 2,
            "term_weight": 2,
            "symmetric_anchor_repeat": 0,
            "max_iters": 2400,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
        {
            "variant_id": "symmetric-anchor",
            "label": "alternating cycles plus symmetric terminal anchors",
            "cycle_strategy": "alternating",
            "repeat": 160,
            "isolated_repeat": 2,
            "term_weight": 1,
            "symmetric_anchor_repeat": 100,
            "max_iters": 2600,
            "n_embd": 64,
            "learning_rate": 0.02,
        },
    ]


def build_model_capability_required_term_pair_branch_retention_sweep(
    loss_branch_sweep: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seed: int = DEFAULT_PAIR_BRANCH_RETENTION_SWEEP_SEED,
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
    source_summary = as_dict(loss_branch_sweep.get("summary"))
    targets = select_branch_retention_targets(loss_branch_sweep, pair_limit=pair_limit)
    variant_rows = normalize_branch_retention_variants(
        default_pair_branch_retention_sweep_variants() if variants is None else variants
    )
    issues = _input_issues(loss_branch_sweep, targets, variant_rows)

    training_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for target_index, target in enumerate(targets):
            for variant_index, variant in enumerate(variant_rows):
                result = _run_branch_retention_variant(
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
        issues.append(f"{len(training_failures)} branch-retention sweep training runs did not complete successfully")

    variant_summaries = summarize_branch_retention_variant_probe_rows(targets, variant_rows, probe_rows)
    target_summaries = summarize_branch_retention_targets(targets, variant_summaries)
    summary = summarize_required_term_pair_branch_retention_sweep(
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
        "title": "MiniGPT model capability required-term pair branch-retention sweep",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_loss_branch_sweep": str(source_path) if source_path else None,
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
            "experiment_boundary": "restore branch retention after v501 tradeoff without adding negative contrast leakage",
        },
        "source_baseline": _source_baseline(source_summary),
        "target_count": len(targets),
        "targets": targets,
        "branch_retention_variants": variant_rows,
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


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_branch_retention_variant(
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
    corpus_text = build_required_term_pair_branch_retention_corpus(target, variant)
    corpus_path = root / "branch-retention-corpora" / f"{_slug(run_id)}.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "branch-retention-runs" / run_id
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
                    "branch_retention_run_id": run_id,
                    "pair_terms": target.get("term_names") or [],
                    "focus_missed_term": target.get("focus_missed_term"),
                    "source_hit_terms": target.get("source_hit_terms") or [],
                    "branch_retention_corpus_path": str(corpus_path),
                    "branch_retention_seed": seed,
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
                    "branch_retention_run_id": run_id,
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
            "branch_retention_run_id": run_id,
            "pair_id": pair_id,
            "pair_terms": target.get("term_names") or [],
            "focus_missed_term": target.get("focus_missed_term"),
            "variant_id": variant_id,
            "variant_label": variant.get("label"),
            "seed": int(seed),
            "branch_retention_corpus_path": str(corpus_path),
            "branch_retention_corpus_exists": corpus_path.is_file(),
            "branch_retention_line_count": len(corpus_text.splitlines()) - 2,
            "cycle_strategy": variant.get("cycle_strategy"),
            "repeat": int(variant["repeat"]),
            "isolated_repeat": int(variant["isolated_repeat"]),
            "term_weight": int(variant["term_weight"]),
            "symmetric_anchor_repeat": int(variant["symmetric_anchor_repeat"]),
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
        issues.append("source loss-branch sweep report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source loss-branch sweep report is not pass")
    if report and int(source_summary.get("branch_tradeoff_variant_count") or 0) <= 0:
        issues.append("source loss-branch sweep has no branch tradeoff to retain")
    if report and int(source_summary.get("pair_full_hit_variant_count") or 0) > 0:
        issues.append("source loss-branch sweep already has a full-hit variant; retention sweep is not needed")
    if not targets:
        issues.append("source loss-branch sweep has no eligible branch-retention target")
    if not variants:
        issues.append("at least one branch-retention variant is required")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_branch_retention_sweep"
    decision = str(summary.get("branch_retention_sweep_decision") or "")
    if decision == "branch_retention_sweep_full_hit_recovered":
        return "required_term_pair_branch_retention_recovered"
    if decision in {"branch_retention_sweep_balanced_partial", "branch_retention_sweep_tradeoff_remains"}:
        return "required_term_pair_branch_retention_partial"
    return "required_term_pair_branch_retention_not_recovered"


def _source_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "loss_branch_sweep_decision": summary.get("loss_branch_sweep_decision"),
        "branch_tradeoff_variant_count": summary.get("branch_tradeoff_variant_count"),
        "pair_full_hit_variant_count": summary.get("pair_full_hit_variant_count"),
        "best_variant_id": summary.get("best_variant_id"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("pair_full_hit_variant_count") or 0) > 0:
        return "branch_retention_pair_signal_only"
    if int(summary.get("balanced_retention_variant_count") or 0) > 0:
        return "branch_retention_partial_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The loss-branch source or at least one branch-retention training run failed."
    if int(summary.get("pair_full_hit_variant_count") or 0) > 0:
        return "At least one balanced clean variant emitted both pair terms under their own prompts."
    if int(summary.get("retention_tradeoff_variant_count") or 0) > 0:
        return "Balanced clean variants still produced a branch tradeoff instead of retaining both branches."
    return "Balanced clean variants did not recover the pair branch signal."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair branch-retention inputs before adding more variants"
    if int(summary.get("pair_full_hit_variant_count") or 0) > 0:
        return "repeat the recovered retention variant across seeds before expanding pair count"
    if int(summary.get("retention_tradeoff_variant_count") or 0) > 0:
        return "try a smaller supervised decoding/evaluation diagnostic before more corpus weighting"
    return "return to one-branch diagnostics or tokenizer/context probes before expanding model claims"


def _sample_prompt(target: dict[str, Any]) -> str:
    for term in list_of_dicts(target.get("terms")):
        prompt = str(term.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "fixed:"
