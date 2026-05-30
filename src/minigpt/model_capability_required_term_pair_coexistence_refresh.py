from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_generation_profile_replay import (
    DEFAULT_PROFILE_IDS,
    build_model_capability_required_term_pair_generation_profile_replay,
    resolve_exit_code as _replay_exit_code,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_COEXISTENCE_REFRESH_JSON_FILENAME = "model_capability_required_term_pair_coexistence_refresh.json"
PAIR_COEXISTENCE_REFRESH_TEXT_FILENAME = "model_capability_required_term_pair_coexistence_refresh.txt"
PAIR_COEXISTENCE_REFRESH_MARKDOWN_FILENAME = "model_capability_required_term_pair_coexistence_refresh.md"
PAIR_COEXISTENCE_REFRESH_HTML_FILENAME = "model_capability_required_term_pair_coexistence_refresh.html"
PAIR_COEXISTENCE_REFRESH_CORPUS_FILENAME = "required_term_pair_coexistence_refresh_corpus.txt"
PAIR_COEXISTENCE_CORPUS_MODES = ("spaced_answer", "colon_immediate", "colon_immediate_first_token_boost")

ROOT = Path(__file__).resolve().parents[2]
TrainFunc = Callable[[dict[str, Any]], dict[str, Any]]
GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def build_model_capability_required_term_pair_coexistence_refresh(
    *,
    out_dir: str | Path,
    seed: int = 533,
    corpus_mode: str = "spaced_answer",
    repeat: int = 260,
    bridge_repeat: int = 20,
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
    corpus_text = build_pair_coexistence_refresh_corpus(repeat=repeat, bridge_repeat=bridge_repeat, corpus_mode=corpus_mode)
    corpus_path = root / PAIR_COEXISTENCE_REFRESH_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    train_dir = root / "pair-coexistence-refresh-run"
    training = _train_refresh_checkpoint(
        {
            "corpus_path": str(corpus_path),
            "train_dir": str(train_dir),
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
    replay_report: dict[str, Any] = {}
    issues: list[str] = []
    if training.get("status") != "pass":
        issues.append("pair coexistence refresh training failed")
    else:
        replay_report = build_model_capability_required_term_pair_generation_profile_replay(
            _source_report(training, seed=seed),
            out_dir=root / "pair-generation-profile-replay",
            profiles=DEFAULT_PROFILE_IDS,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            device=device,
            generated_at=generated_at,
            generate_func=generate_func,
        )
        if replay_report.get("status") != "pass":
            issues.append("pair coexistence refresh replay failed")
    summary = _summary(training, replay_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair coexistence refresh",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "out_dir": str(root),
        "settings": {
            "seed": seed,
            "corpus_mode": corpus_mode,
            "repeat": repeat,
            "bridge_repeat": bridge_repeat,
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
            "experiment_boundary": "train a tiny direct fixed/loss coexistence corpus after generation profiles failed to repair archived pair checkpoints",
        },
        "corpus": {
            "path": str(corpus_path),
            "char_count": len(corpus_text),
            "line_count": len(corpus_text.splitlines()),
            "repeat": repeat,
            "bridge_repeat": bridge_repeat,
        },
        "training": training,
        "replay_report": replay_report,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def build_pair_coexistence_refresh_corpus(*, repeat: int, bridge_repeat: int, corpus_mode: str = "spaced_answer") -> str:
    lines = [
        "MiniGPT fixed/loss pair coexistence refresh corpus.",
        "The prompt before the colon selects the exact continuation term.",
    ]
    if corpus_mode == "spaced_answer":
        for _ in range(max(1, repeat)):
            lines.extend(
                [
                    "fixed: fixed",
                    "loss: loss",
                    "comparison-baseline|fixed: fixed",
                    "factual-val-loss|loss: loss",
                    "term=fixed prompt=fixed: answer=fixed",
                    "term=loss prompt=loss: answer=loss",
                ]
            )
        for _ in range(max(0, bridge_repeat)):
            lines.extend(
                [
                    "fixed and loss are separate branches.",
                    "fixed: fixed ; loss: loss",
                    "When the prefix is fixed:, continue fixed.",
                    "When the prefix is loss:, continue loss.",
                ]
            )
    elif corpus_mode == "colon_immediate":
        for _ in range(max(1, repeat)):
            lines.extend(
                [
                    "fixed:fixed",
                    "loss:loss",
                    "comparison-baseline|fixed:fixed",
                    "factual-val-loss|loss:loss",
                    "prompt=fixed:target=fixed",
                    "prompt=loss:target=loss",
                    "select fixed:fixed",
                    "select loss:loss",
                ]
            )
        for _ in range(max(0, bridge_repeat)):
            lines.extend(
                [
                    "fixed/loss are separate branches.",
                    "fixed:fixed;loss:loss",
                    "prefix fixed:fixed",
                    "prefix loss:loss",
                ]
            )
    elif corpus_mode == "colon_immediate_first_token_boost":
        for _ in range(max(1, repeat)):
            lines.extend(
                [
                    "fixed:fixed",
                    "loss:loss",
                    "fixed:f",
                    "loss:l",
                    "fixed:fi",
                    "loss:lo",
                    "fixed:fix",
                    "loss:los",
                    "prompt=fixed:target=fixed",
                    "prompt=loss:target=loss",
                    "prefix=fixed:next=fixed",
                    "prefix=loss:next=loss",
                ]
            )
        for _ in range(max(0, bridge_repeat)):
            lines.extend(
                [
                    "fixed:fixed",
                    "loss:loss",
                    "fixed branch starts with f.",
                    "loss branch starts with l.",
                ]
            )
    else:
        raise ValueError(f"unknown corpus_mode: {corpus_mode}")
    return "\n".join(lines) + "\n"


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    replay = as_dict(report.get("replay_report"))
    if replay:
        return _replay_exit_code(replay, require_pass=require_pass)
    return 0


def _train_refresh_checkpoint(context: dict[str, Any], train_func: TrainFunc | None) -> dict[str, Any]:
    if train_func is not None:
        return train_func(context)
    train_dir = Path(str(context["train_dir"]))
    logs_dir = train_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "train.py"),
        "--data",
        str(context["corpus_path"]),
        "--out-dir",
        str(train_dir),
        "--device",
        str(context["device"]),
        "--tokenizer",
        "char",
        "--max-iters",
        str(context["max_iters"]),
        "--eval-interval",
        str(max(1, int(context["max_iters"]) // 4)),
        "--eval-iters",
        str(context["eval_iters"]),
        "--batch-size",
        str(context["batch_size"]),
        "--block-size",
        str(context["block_size"]),
        "--n-layer",
        str(context["n_layer"]),
        "--n-head",
        str(context["n_head"]),
        "--n-embd",
        str(context["n_embd"]),
        "--learning-rate",
        str(context["learning_rate"]),
        "--seed",
        str(context["seed"]),
        "--sample-prompt",
        "fixed:",
        "--sample-tokens",
        "8",
        "--sample-temperature",
        "0.2",
        "--sample-top-k",
        "1",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    stdout_path = logs_dir / "train_stdout.txt"
    stderr_path = logs_dir / "train_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return _training_result(train_dir, command, completed.returncode, stdout_path, stderr_path)


def _training_result(train_dir: Path, command: list[str], returncode: int, stdout_path: Path | None, stderr_path: Path | None) -> dict[str, Any]:
    checkpoint_path = train_dir / "checkpoint.pt"
    tokenizer_path = train_dir / "tokenizer.json"
    metrics_path = train_dir / "metrics.jsonl"
    train_config_path = train_dir / "train_config.json"
    return {
        "status": "pass" if returncode == 0 and checkpoint_path.is_file() and tokenizer_path.is_file() else "fail",
        "returncode": returncode,
        "command": command,
        "command_text": " ".join(command),
        "stdout": "" if stdout_path is None else str(stdout_path),
        "stderr": "" if stderr_path is None else str(stderr_path),
        "run_dir": str(train_dir),
        "checkpoint_path": str(checkpoint_path),
        "tokenizer_path": str(tokenizer_path),
        "metrics_path": str(metrics_path),
        "train_config_path": str(train_config_path),
        "checkpoint_exists": checkpoint_path.is_file(),
        "tokenizer_exists": tokenizer_path.is_file(),
        "metrics_exists": metrics_path.is_file(),
        "train_config_exists": train_config_path.is_file(),
    }


def _source_report(training: dict[str, Any], *, seed: int) -> dict[str, Any]:
    return {
        "targets": [
            {
                "pair_id": "01-fixed-loss",
                "terms": [
                    {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:", "source_hit_rate": 1.0},
                    {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:", "source_hit_rate": 1.0},
                ],
            }
        ],
        "training_rows": [
            {
                "branch_retention_run_id": "01-fixed-loss-coexistence-refresh",
                "pair_id": "01-fixed-loss",
                "variant_id": "coexistence-refresh",
                "seed": seed,
                "checkpoint_path": training.get("checkpoint_path"),
                "tokenizer_path": training.get("tokenizer_path"),
            }
        ],
        "probe_rows": [
            {"variant_id": "coexistence-refresh", "term": "fixed", "generation_seed": seed},
            {"variant_id": "coexistence-refresh", "term": "loss", "generation_seed": seed + 1},
        ],
    }


def _summary(training: dict[str, Any], replay_report: dict[str, Any]) -> dict[str, Any]:
    replay_summary = as_dict(replay_report.get("summary"))
    default_full = int(replay_summary.get("default_pair_full_variant_count") or 0)
    suppression_full = int(replay_summary.get("suppression_pair_full_variant_count") or 0)
    return {
        "training_status": training.get("status"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "default_pair_full_variant_count": default_full,
        "suppression_pair_full_variant_count": suppression_full,
        "best_pair_full_variant_count": max(default_full, suppression_full),
        "suppression_hit_delta": replay_summary.get("suppression_hit_delta", 0),
        "pair_full_observed": max(default_full, suppression_full) > 0,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_coexistence_refresh"
    if summary.get("pair_full_observed"):
        return "required_term_pair_coexistence_refresh_pair_full_observed"
    return "required_term_pair_coexistence_refresh_no_pair_full"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The pair coexistence refresh did not complete, so no model capability conclusion is available."
        next_action = "repair the refresh run before changing corpus shape"
    elif summary.get("pair_full_observed"):
        reason = "A direct fixed/loss refresh corpus produced at least one profile with full pair continuation coverage."
        next_action = "repeat the refresh across seeds before promoting it as stable pair coexistence"
    else:
        reason = "The refresh run completed but still did not produce full fixed/loss continuation coverage."
        next_action = "increase pair objective diversity or inspect first-token preference before more training"
    return {
        "model_quality_claim": "targeted_pair_refresh_signal_only" if summary.get("pair_full_observed") else "not_claimed",
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_COEXISTENCE_CORPUS_MODES",
    "PAIR_COEXISTENCE_REFRESH_CORPUS_FILENAME",
    "PAIR_COEXISTENCE_REFRESH_HTML_FILENAME",
    "PAIR_COEXISTENCE_REFRESH_JSON_FILENAME",
    "PAIR_COEXISTENCE_REFRESH_MARKDOWN_FILENAME",
    "PAIR_COEXISTENCE_REFRESH_TEXT_FILENAME",
    "build_model_capability_required_term_pair_coexistence_refresh",
    "build_pair_coexistence_refresh_corpus",
    "resolve_exit_code",
]
