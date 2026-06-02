from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_coexistence_refresh import _train_refresh_checkpoint
from minigpt.model_capability_required_term_pair_generation_profile_replay import (
    DEFAULT_PROFILE_IDS,
    build_model_capability_required_term_pair_generation_profile_replay,
)
from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import (
    PAIR_READINESS_CORPUS_MATERIALIZATION_JSON_FILENAME,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_TRAINING_RUN_JSON_FILENAME = "model_capability_required_term_pair_readiness_training_run.json"
PAIR_READINESS_TRAINING_RUN_CSV_FILENAME = "model_capability_required_term_pair_readiness_training_run.csv"
PAIR_READINESS_TRAINING_RUN_TEXT_FILENAME = "model_capability_required_term_pair_readiness_training_run.txt"
PAIR_READINESS_TRAINING_RUN_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_training_run.md"
PAIR_READINESS_TRAINING_RUN_HTML_FILENAME = "model_capability_required_term_pair_readiness_training_run.html"

TrainFunc = Callable[[dict[str, Any]], dict[str, Any]]
GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_pair_readiness_training_run_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_CORPUS_MATERIALIZATION_JSON_FILENAME
    return source


def build_pair_readiness_training_run(
    materialization_report: dict[str, Any],
    *,
    out_dir: str | Path,
    seed: int = 3535,
    max_iters: int = 1400,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 16,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    paths = as_dict(materialization_report.get("materialized_paths"))
    corpus_path = Path(str(paths.get("training_corpus") or ""))
    train_dir = root / "pair-readiness-training-run"
    issues: list[str] = []
    if materialization_report.get("status") != "pass":
        issues.append("pair-readiness corpus materialization did not pass")
    if not corpus_path.is_file():
        issues.append("pair-readiness training corpus is missing")
    training: dict[str, Any] = {}
    replay_report: dict[str, Any] = {}
    if not issues:
        training = _train_refresh_checkpoint(
            {
                "corpus_path": str(corpus_path),
                "train_dir": str(train_dir),
                "resume_checkpoint": "",
                "seed": seed,
                "max_iters": max_iters,
                "eval_iters": eval_iters,
                "batch_size": batch_size,
                "block_size": block_size,
                "n_layer": n_layer,
                "n_head": n_head,
                "n_embd": n_embd,
                "learning_rate": learning_rate,
                "device": device,
            },
            train_func,
        )
        if training.get("status") != "pass":
            issues.append("pair-readiness training failed")
        else:
            replay_report = build_model_capability_required_term_pair_generation_profile_replay(
                _source_report(materialization_report, training, seed=seed),
                out_dir=root / "heldout-direct-replay",
                profiles=DEFAULT_PROFILE_IDS,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                device=device,
                generated_at=generated_at,
                generate_func=generate_func,
            )
            if replay_report.get("status") != "pass":
                issues.append("pair-readiness heldout replay failed")
    summary = _summary(materialization_report, training, replay_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair-readiness training run",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "out_dir": str(root),
        "settings": {
            "seed": seed,
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
            "experiment_boundary": "train on materialized pair-readiness corpus and replay heldout direct probes",
        },
        "source_materialization": {
            "status": materialization_report.get("status"),
            "decision": materialization_report.get("decision"),
            "summary": as_dict(materialization_report.get("summary")),
            "training_corpus": str(corpus_path),
        },
        "training": training,
        "replay_report": replay_report,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _source_report(materialization_report: dict[str, Any], training: dict[str, Any], *, seed: int) -> dict[str, Any]:
    probes = list_of_dicts(as_dict(materialization_report.get("heldout_eval_fixture")).get("probes"))
    terms = [
        {
            "case": str(probe.get("id") or probe.get("expected_term")),
            "term": str(probe.get("expected_term")),
            "scaffold_prompt": str(probe.get("prompt")),
            "source_hit_rate": 1.0,
        }
        for probe in probes
        if probe.get("expected_term") in {"fixed", "loss"}
    ]
    return {
        "targets": [{"pair_id": "01-fixed-loss", "terms": terms}],
        "training_rows": [
            {
                "branch_retention_run_id": "01-fixed-loss-pair-readiness",
                "pair_id": "01-fixed-loss",
                "variant_id": "pair-readiness-materialized",
                "seed": seed,
                "checkpoint_path": training.get("checkpoint_path"),
                "tokenizer_path": training.get("tokenizer_path"),
            }
        ],
        "probe_rows": [
            {"variant_id": "pair-readiness-materialized", "term": "fixed", "generation_seed": seed},
            {"variant_id": "pair-readiness-materialized", "term": "loss", "generation_seed": seed + 1},
        ],
    }


def _summary(materialization_report: dict[str, Any], training: dict[str, Any], replay_report: dict[str, Any]) -> dict[str, Any]:
    replay_summary = as_dict(replay_report.get("summary"))
    pair_full = int(replay_summary.get("default_pair_full_variant_count") or 0) > 0 or int(
        replay_summary.get("suppression_pair_full_variant_count") or 0
    ) > 0
    return {
        "materialization_status": materialization_report.get("status"),
        "training_status": training.get("status", ""),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "default_pair_full_variant_count": replay_summary.get("default_pair_full_variant_count", 0),
        "suppression_pair_full_variant_count": replay_summary.get("suppression_pair_full_variant_count", 0),
        "default_continuation_hit_count": replay_summary.get("default_continuation_hit_count", 0),
        "suppression_continuation_hit_count": replay_summary.get("suppression_continuation_hit_count", 0),
        "pair_full_observed": pair_full,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_training_run"
    if summary.get("pair_full_observed") is True:
        return "pair_readiness_training_pair_full_observed"
    return "pair_readiness_training_no_pair_full"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Training or heldout replay failed before model quality could be assessed.",
            "next_action": "repair pair-readiness training run",
        }
    if summary.get("pair_full_observed") is True:
        return {
            "model_quality_claim": "direct_pair_probe_hit",
            "reason": "The materialized pair-readiness training run hit both heldout direct probes.",
            "next_action": "run heldout pair-probe replay before promoting the checkpoint",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "The materialized corpus trained successfully but did not hit both heldout direct probes.",
        "next_action": "inspect heldout direct failures before changing corpus",
    }


__all__ = [
    "PAIR_READINESS_TRAINING_RUN_CSV_FILENAME",
    "PAIR_READINESS_TRAINING_RUN_HTML_FILENAME",
    "PAIR_READINESS_TRAINING_RUN_JSON_FILENAME",
    "PAIR_READINESS_TRAINING_RUN_MARKDOWN_FILENAME",
    "PAIR_READINESS_TRAINING_RUN_TEXT_FILENAME",
    "build_pair_readiness_training_run",
    "locate_pair_readiness_training_run_source",
    "read_json_report",
    "resolve_exit_code",
]
