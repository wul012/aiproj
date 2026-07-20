from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_training_ready as resolve_exit_code


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.html"


def locate_rebalanced_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder anchor rebalanced training run input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run(
    rebalanced_seed_report: dict[str, Any],
    run_dir: str | Path,
    *,
    rebalanced_seed_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced training run",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    seed_summary = as_dict(rebalanced_seed_report.get("summary"))
    artifacts = _artifacts(root)
    metrics = _metrics(root / "metrics.jsonl")
    train_config = _read_json(root / "train_config.json")
    manifest = _read_json(root / "run_manifest.json")
    checks = _checks(rebalanced_seed_report, seed_summary, artifacts, metrics, train_config)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    training = _training(status, artifacts, metrics, train_config, manifest, seed_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_decoder_anchor_rebalanced_seed_revision": str(rebalanced_seed_path or ""),
        "run_dir": str(root),
        "rebalanced_seed_summary": seed_summary,
        "artifacts": artifacts,
        "metrics": metrics,
        "train_config": train_config,
        "manifest": manifest,
        "check_rows": checks,
        "decoder_anchor_rebalanced_training": training,
        "summary": _summary(status, checks, training),
        "interpretation": _interpretation(status, training),
    }


def _artifacts(root: Path) -> list[dict[str, Any]]:
    rows = []
    for key, name in [
        ("checkpoint", "checkpoint.pt"),
        ("tokenizer", "tokenizer.json"),
        ("metrics", "metrics.jsonl"),
        ("train_config", "train_config.json"),
        ("run_manifest", "run_manifest.json"),
        ("sample", "sample.txt"),
        ("prepared_corpus", "prepared_corpus.txt"),
    ]:
        path = root / name
        rows.append({"key": key, "path": str(path), "exists": path.is_file(), "size": path.stat().st_size if path.is_file() else 0})
    return rows


def _metrics(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"record_count": 0, "first": {}, "last": {}, "train_loss_delta": None, "val_loss_delta": None}
    records = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    first = dict(records[0]) if records else {}
    last = dict(records[-1]) if records else {}
    return {
        "record_count": len(records),
        "first": first,
        "last": last,
        "train_loss_delta": _delta(first.get("train_loss"), last.get("train_loss")),
        "val_loss_delta": _delta(first.get("val_loss"), last.get("val_loss")),
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def _checks(seed: dict[str, Any], seed_summary: dict[str, Any], artifacts: list[dict[str, Any]], metrics: dict[str, Any], train_config: dict[str, Any]) -> list[dict[str, Any]]:
    artifact_map = {row["key"]: row for row in artifacts}
    return [
        _check("rebalanced_seed_passed", seed.get("status") == "pass", seed.get("status"), "rebalanced seed revision must pass"),
        _check("rebalanced_seed_ready", seed_summary.get("decoder_anchor_rebalanced_seed_revision_ready") is True, seed_summary.get("decoder_anchor_rebalanced_seed_revision_ready"), "rebalanced seed revision must be ready"),
        _check("direct_answer_share_repaired", float(seed_summary.get("direct_answer_share") or 0.0) >= 0.2, seed_summary.get("direct_answer_share"), "direct answer share must remain repaired"),
        _check("carry_forward_share_repaired", float(seed_summary.get("carry_forward_share") or 0.0) <= 0.5, seed_summary.get("carry_forward_share"), "carry-forward share must remain capped"),
        _check("decoder_bridge_examples_present", int(seed_summary.get("decoder_bridge_count") or 0) > 0, seed_summary.get("decoder_bridge_count"), "rebalanced seed must retain decoder bridge examples"),
        _check("checkpoint_exists", artifact_map["checkpoint"]["exists"], artifact_map["checkpoint"]["path"], "training must produce checkpoint.pt"),
        _check("tokenizer_exists", artifact_map["tokenizer"]["exists"], artifact_map["tokenizer"]["path"], "training must produce tokenizer.json"),
        _check("metrics_exists", artifact_map["metrics"]["exists"], artifact_map["metrics"]["path"], "training must produce metrics.jsonl"),
        _check("manifest_exists", artifact_map["run_manifest"]["exists"], artifact_map["run_manifest"]["path"], "training must produce run_manifest.json"),
        _check("prepared_corpus_exists", artifact_map["prepared_corpus"]["exists"], artifact_map["prepared_corpus"]["path"], "training must copy prepared corpus"),
        _check("metrics_records_present", int(metrics.get("record_count") or 0) >= 2, metrics.get("record_count"), "training should record at least first and last metrics"),
        _check("max_iters_positive", int(train_config.get("max_iters") or 0) > 0, train_config.get("max_iters"), "train_config must record positive max_iters"),
    ]


def _training(status: str, artifacts: list[dict[str, Any]], metrics: dict[str, Any], train_config: dict[str, Any], manifest: dict[str, Any], seed_summary: dict[str, Any]) -> dict[str, Any]:
    last = as_dict(metrics.get("last"))
    return {
        "ready": status == "pass",
        "artifact_count": sum(1 for row in artifacts if row.get("exists")),
        "metric_record_count": metrics.get("record_count"),
        "final_step": last.get("step"),
        "final_train_loss": last.get("train_loss"),
        "final_val_loss": last.get("val_loss"),
        "train_loss_delta": metrics.get("train_loss_delta"),
        "val_loss_delta": metrics.get("val_loss_delta"),
        "max_iters": train_config.get("max_iters"),
        "seed": train_config.get("seed") or as_dict(as_dict(manifest.get("training")).get("args")).get("seed"),
        "rebalanced_example_count": seed_summary.get("example_count"),
        "direct_answer_count": seed_summary.get("direct_answer_count"),
        "decoder_bridge_count": seed_summary.get("decoder_bridge_count"),
        "carry_forward_count": seed_summary.get("carry_forward_count"),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_replay",
        "next_step": "run_decoder_anchor_rebalanced_checkpoint_bounded_replay" if status == "pass" else "repair_decoder_anchor_rebalanced_training_run",
    }


def _summary(status: str, checks: list[dict[str, Any]], training: dict[str, Any]) -> dict[str, Any]:
    return {
        "decoder_anchor_rebalanced_training_ready": status == "pass" and training.get("ready") is True,
        "artifact_count": training.get("artifact_count"),
        "metric_record_count": training.get("metric_record_count"),
        "final_step": training.get("final_step"),
        "final_train_loss": training.get("final_train_loss"),
        "final_val_loss": training.get("final_val_loss"),
        "train_loss_delta": training.get("train_loss_delta"),
        "val_loss_delta": training.get("val_loss_delta"),
        "rebalanced_example_count": training.get("rebalanced_example_count"),
        "direct_answer_count": training.get("direct_answer_count"),
        "decoder_bridge_count": training.get("decoder_bridge_count"),
        "carry_forward_count": training.get("carry_forward_count"),
        "proposed_next_artifact": training.get("proposed_next_artifact"),
        "next_step": training.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run"


def _interpretation(status: str, training: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Rebalanced training artifacts are incomplete.", "next_action": "repair rebalanced training run"}
    return {
        "model_quality_claim": "training_artifact_only",
        "reason": "A checkpoint exists for the rebalanced seed, but improvement still requires bounded replay comparison.",
        "next_action": training.get("next_step"),
    }


def _delta(first: Any, last: Any) -> float | None:
    if first is None or last is None:
        return None
    return round(float(last) - float(first), 6)


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run",
    "locate_rebalanced_seed_revision",
    "read_json_report",
    "resolve_exit_code",
]
