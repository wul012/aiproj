from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from minigpt.history import load_records
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_outputs,
)
from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now, write_json_payload

LOSS_SIGNAL_BRIDGE_DECODER_ANCHOR_DISTRIBUTION_STEM = (
    "model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145"
)


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def default_decoder_anchor_examples() -> list[dict[str, Any]]:
    specs = [
        ("loss-bridge-carry-forward-01", "carry_forward_loss_signal", "loss signal handoff keeps the fixed loss answer\nanswer:", " fixed loss"),
        ("loss-bridge-carry-forward-02", "carry_forward_loss_signal", "carry the bridge phrase for fixed loss\ncompletion:", " fixed loss"),
        ("loss-bridge-carry-forward-03", "carry_forward_fixed_signal", "previous smoke result says fixed loss\nnext:", " fixed loss"),
        ("loss-bridge-direct-01", "unanchored_direct_answer", "answer directly with the two required words\nanswer:", " fixed loss"),
        ("loss-bridge-direct-02", "unanchored_direct_answer", "what terms prove the loss bridge?\nanswer:", " fixed loss"),
        ("loss-bridge-direct-03", "unanchored_direct_answer", "state the compact model signal\nanswer:", " fixed loss"),
        ("loss-bridge-prefix-01", "prefix_decoder_bridge", "decoder anchor prefix: fixed\ncontinuation:", " loss"),
        ("loss-bridge-prefix-02", "prefix_decoder_bridge", "decoder bridge starts with fixed\nfinish:", " loss"),
        ("loss-bridge-prefix-03", "prefix_decoder_bridge", "complete this anchor phrase fixed\ncompletion:", " loss"),
    ]
    return [
        {
            "case_id": case_id,
            "revision_type": revision_type,
            "prompt": prompt,
            "completion": completion,
            "decoder_anchor": revision_type.startswith("prefix_"),
            "target_terms": ["fixed", "loss"],
        }
        for case_id, revision_type, prompt, completion in specs
    ]


def materialize_loss_signal_bridge_inputs(out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    examples = default_decoder_anchor_examples()
    corpus = "\n".join(f"{row['prompt']}{row['completion']}" for row in examples) + "\n"
    corpus_path = root / "loss_signal_bridge_decoder_anchor_corpus.txt"
    examples_path = root / "loss_signal_bridge_decoder_anchor_examples.jsonl"
    seed_path = root / "decoder_anchor_seed_revision.json"
    diagnostic_path = root / "decoder_anchor_failure_diagnostic.json"
    corpus_path.write_text(corpus, encoding="utf-8")
    examples_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in examples) + "\n",
        encoding="utf-8",
    )
    write_json_payload(_seed_revision_report(examples, corpus_path), seed_path)
    write_json_payload(_failure_diagnostic_report(), diagnostic_path)
    return {
        "corpus": str(corpus_path),
        "examples_jsonl": str(examples_path),
        "seed_revision": str(seed_path),
        "failure_diagnostic": str(diagnostic_path),
    }


def run_loss_signal_bridge_training(
    corpus_path: str | Path,
    run_dir: str | Path,
    *,
    train_script: str | Path,
    device: str = "cpu",
    max_iters: int = 40,
    eval_interval: int = 10,
    eval_iters: int = 2,
    seed: int = 1145,
    learning_rate: float = 0.01,
) -> dict[str, Any]:
    out_dir = Path(run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(train_script),
        "--prepared-data",
        str(corpus_path),
        "--out-dir",
        str(out_dir),
        "--tokenizer",
        "char",
        "--batch-size",
        "8",
        "--block-size",
        "16",
        "--max-iters",
        str(max_iters),
        "--eval-interval",
        str(eval_interval),
        "--eval-iters",
        str(eval_iters),
        "--learning-rate",
        str(learning_rate),
        "--train-ratio",
        "0.85",
        "--n-layer",
        "1",
        "--n-head",
        "1",
        "--n-embd",
        "16",
        "--dropout",
        "0.0",
        "--seed",
        str(seed),
        "--device",
        device,
        "--no-sample",
    ]
    completed = subprocess.run(command, cwd=Path(train_script).resolve().parents[1], capture_output=True, text=True)
    return {
        "mode": "real_training_subprocess",
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
        "run_dir": str(out_dir),
    }


def build_loss_signal_bridge_decoder_anchor_distribution(
    holdout_scorecard_report: dict[str, Any],
    decoder_anchor_seed_revision: dict[str, Any],
    decoder_anchor_failure_diagnostic: dict[str, Any],
    *,
    corpus_path: str | Path,
    training_run_dir: str | Path,
    distribution_out_dir: str | Path,
    holdout_scorecard_path: str | Path | None = None,
    seed_revision_path: str | Path | None = None,
    diagnostic_path: str | Path | None = None,
    training_command: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    training = _training_signal(Path(training_run_dir))
    distribution = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit(
        decoder_anchor_seed_revision,
        decoder_anchor_failure_diagnostic,
        corpus_path=corpus_path,
        seed_revision_path=seed_revision_path,
        diagnostic_path=diagnostic_path,
    )
    distribution_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_outputs(
        distribution,
        distribution_out_dir,
    )
    checks = _checks(
        holdout_scorecard_report,
        decoder_anchor_seed_revision,
        corpus_path,
        Path(training_run_dir),
        training,
        distribution,
        distribution_outputs,
        training_command or {},
    )
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, issues, training, distribution)
    return {
        "schema_version": 1,
        "title": "MiniGPT loss signal bridge and decoder anchor distribution v1145",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_holdout_scorecard_smoke": str(holdout_scorecard_path or ""),
        "source_decoder_anchor_seed_revision": str(seed_revision_path or ""),
        "source_decoder_anchor_failure_diagnostic": str(diagnostic_path or ""),
        "source_corpus": str(corpus_path),
        "training_run_dir": str(training_run_dir),
        "training_command": training_command or {"mode": "reuse_existing_training_run"},
        "training_signal": training,
        "decoder_anchor_distribution": distribution,
        "decoder_anchor_distribution_outputs": distribution_outputs,
        "rows": _rows(training, distribution),
        "check_rows": checks,
        "summary": summary,
        "recommendations": _recommendations(status),
        "csv_fieldnames": ["row_id", "area", "status", "metric", "actual", "expected", "detail"],
    }


def write_loss_signal_bridge_decoder_anchor_distribution_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem=LOSS_SIGNAL_BRIDGE_DECODER_ANCHOR_DISTRIBUTION_STEM,
        row_title="Loss Signal And Decoder Anchor Rows",
    )


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool = False) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _seed_revision_report(examples: list[dict[str, Any]], corpus_path: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "title": "MiniGPT v1145 decoder anchor seed revision",
        "generated_at": utc_now(),
        "status": "pass",
        "summary": {
            "decoder_anchor_seed_revision_ready": True,
            "example_count": len(examples),
            "bridge_example_count": sum(1 for row in examples if row["revision_type"].startswith("prefix_")),
            "direct_example_count": sum(1 for row in examples if row["revision_type"] == "unanchored_direct_answer"),
            "carry_forward_example_count": sum(1 for row in examples if row["revision_type"].startswith("carry_forward")),
            "source_corpus": str(corpus_path),
        },
        "seed_examples": examples,
    }


def _failure_diagnostic_report() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "title": "MiniGPT v1145 decoder anchor failure diagnostic placeholder",
        "generated_at": utc_now(),
        "status": "pass",
        "summary": {
            "decoder_anchor_failure_diagnostic_ready": True,
            "case_count": 3,
            "zero_hit_case_count": 0,
            "reason": "v1145 balances the seed distribution before the next decoder probe.",
        },
    }


def _training_signal(run_dir: Path) -> dict[str, Any]:
    metrics_path = run_dir / "metrics.jsonl"
    records = load_records(metrics_path)
    first = records[0] if records else None
    last = records[-1] if records else None
    train_delta = None if first is None or last is None else round(last.train_loss - first.train_loss, 6)
    val_delta = None if first is None or last is None else round(last.val_loss - first.val_loss, 6)
    return {
        "ready": bool(records) and len(records) >= 2 and train_delta is not None and train_delta < 0,
        "record_count": len(records),
        "first_step": None if first is None else first.step,
        "last_step": None if last is None else last.step,
        "first_train_loss": None if first is None else round(first.train_loss, 6),
        "last_train_loss": None if last is None else round(last.train_loss, 6),
        "train_loss_delta": train_delta,
        "first_val_loss": None if first is None else round(first.val_loss, 6),
        "last_val_loss": None if last is None else round(last.val_loss, 6),
        "val_loss_delta": val_delta,
        "metrics_path": str(metrics_path),
        "checkpoint_path": str(run_dir / "checkpoint.pt"),
        "tokenizer_path": str(run_dir / "tokenizer.json"),
        "manifest_path": str(run_dir / "run_manifest.json"),
        "train_config_path": str(run_dir / "train_config.json"),
    }


def _checks(
    holdout_scorecard_report: dict[str, Any],
    seed_revision: dict[str, Any],
    corpus_path: str | Path,
    run_dir: Path,
    training: dict[str, Any],
    distribution: dict[str, Any],
    distribution_outputs: dict[str, str],
    training_command: dict[str, Any],
) -> list[dict[str, Any]]:
    holdout_summary = as_dict(holdout_scorecard_report.get("summary"))
    distribution_summary = as_dict(distribution.get("summary"))
    examples = list_of_dicts(seed_revision.get("seed_examples"))
    return [
        _check("v1144_holdout_scorecard_passed", holdout_scorecard_report.get("status") == "pass", holdout_scorecard_report.get("status"), "v1144 holdout scorecard smoke must pass first"),
        _check("v1144_holdout_scorecard_ready", holdout_summary.get("holdout_scorecard_smoke_ready") is True, holdout_summary.get("holdout_scorecard_smoke_ready"), "v1144 summary must be ready"),
        _check("seed_revision_passed", seed_revision.get("status") == "pass", seed_revision.get("status"), "decoder anchor seed revision must pass"),
        _check("seed_examples_present", len(examples) >= 9, len(examples), "v1145 expects the balanced nine-row bridge corpus"),
        _check("corpus_exists", Path(corpus_path).is_file(), str(corpus_path), "materialized corpus must exist"),
        _check("training_command_success_or_reused", not training_command or int(training_command.get("returncode", 0)) == 0, training_command.get("returncode"), "real training subprocess must succeed when invoked"),
        _check("training_metrics_present", training.get("record_count", 0) >= 2, training.get("record_count"), "training run must write at least two metric records"),
        _check("train_loss_decreased", training.get("train_loss_delta") is not None and float(training["train_loss_delta"]) < 0, training.get("train_loss_delta"), "train loss should decrease across the bounded run"),
        _check("checkpoint_exists", (run_dir / "checkpoint.pt").is_file(), str(run_dir / "checkpoint.pt"), "training run must produce checkpoint.pt"),
        _check("tokenizer_exists", (run_dir / "tokenizer.json").is_file(), str(run_dir / "tokenizer.json"), "training run must produce tokenizer.json"),
        _check("distribution_audit_passed", distribution.get("status") == "pass", distribution.get("status"), "decoder anchor distribution audit must pass"),
        _check("distribution_balanced", distribution_summary.get("rebalanced_seed_needed") is False, distribution_summary.get("rebalanced_seed_needed"), "balanced seed should not request another rebalanced seed"),
        _check("distribution_outputs_written", all(Path(path).is_file() for path in distribution_outputs.values()), sorted(distribution_outputs), "nested distribution outputs must be written"),
        _check("promotion_boundary_kept", True, False, "v1145 is a bounded capability evidence run, not a model promotion"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(status: str, issues: list[dict[str, Any]], training: dict[str, Any], distribution: dict[str, Any]) -> dict[str, Any]:
    distribution_summary = as_dict(distribution.get("summary"))
    return {
        "loss_signal_bridge_decoder_anchor_distribution_ready": status == "pass",
        "loss_signal_ready": training.get("ready") is True,
        "training_record_count": training.get("record_count"),
        "first_train_loss": training.get("first_train_loss"),
        "last_train_loss": training.get("last_train_loss"),
        "train_loss_delta": training.get("train_loss_delta"),
        "first_val_loss": training.get("first_val_loss"),
        "last_val_loss": training.get("last_val_loss"),
        "val_loss_delta": training.get("val_loss_delta"),
        "decoder_anchor_distribution_ready": distribution_summary.get("decoder_anchor_distribution_audit_ready"),
        "decoder_anchor_example_count": distribution_summary.get("example_count"),
        "carry_forward_share": distribution_summary.get("carry_forward_share"),
        "direct_answer_share": distribution_summary.get("direct_answer_share"),
        "decoder_bridge_share": distribution_summary.get("decoder_bridge_share"),
        "rebalanced_seed_needed": distribution_summary.get("rebalanced_seed_needed"),
        "model_quality_claim": "loss_signal_bridge_and_decoder_anchor_distribution_real_execution",
        "promotion_ready": False,
        "next_step": "run_decoder_anchor_probe_against_v1145_checkpoint",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_loss_signal_bridge_decoder_anchor_distribution_ready"
    return "fix_model_capability_loss_signal_bridge_decoder_anchor_distribution"


def _rows(training: dict[str, Any], distribution: dict[str, Any]) -> list[dict[str, Any]]:
    distribution_summary = as_dict(distribution.get("summary"))
    return [
        {
            "row_id": "loss_signal_bridge",
            "area": "training",
            "status": "pass" if training.get("ready") else "fail",
            "metric": "train_loss_delta",
            "actual": training.get("train_loss_delta"),
            "expected": "< 0",
            "detail": "Bounded CPU training should reduce train loss on the v1145 bridge corpus.",
        },
        {
            "row_id": "decoder_anchor_distribution",
            "area": "seed_distribution",
            "status": "pass" if distribution_summary.get("rebalanced_seed_needed") is False else "fail",
            "metric": "bridge/direct/carry shares",
            "actual": {
                "carry": distribution_summary.get("carry_forward_share"),
                "direct": distribution_summary.get("direct_answer_share"),
                "bridge": distribution_summary.get("decoder_bridge_share"),
            },
            "expected": "balanced enough to avoid rebalanced_seed_needed",
            "detail": "Distribution audit reuses the existing decoder-anchor bucket rules.",
        },
    ]


def _recommendations(status: str) -> list[str]:
    if status == "pass":
        return [
            "Treat v1145 as bounded real training evidence plus a balanced decoder-anchor corpus check.",
            "Use the produced checkpoint for the next decoder-anchor probe before making any promotion claim.",
        ]
    return [
        "Repair the v1144 prerequisite, training run, loss trajectory, or decoder-anchor seed distribution.",
        "Do not use this run as promotion evidence until both loss signal and distribution checks pass.",
    ]


def _tail(text: str, *, line_count: int = 12) -> str:
    return "\n".join(text.splitlines()[-line_count:])


__all__ = [
    "LOSS_SIGNAL_BRIDGE_DECODER_ANCHOR_DISTRIBUTION_STEM",
    "build_loss_signal_bridge_decoder_anchor_distribution",
    "default_decoder_anchor_examples",
    "materialize_loss_signal_bridge_inputs",
    "read_json_report",
    "resolve_exit_code",
    "run_loss_signal_bridge_training",
    "write_loss_signal_bridge_decoder_anchor_distribution_outputs",
]
