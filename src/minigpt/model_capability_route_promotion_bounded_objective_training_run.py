from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_seed import (
    BOUNDED_OBJECTIVE_SEED_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check


BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_training_run.json"
BOUNDED_OBJECTIVE_TRAINING_RUN_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_training_run.csv"
BOUNDED_OBJECTIVE_TRAINING_RUN_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_training_run.txt"
BOUNDED_OBJECTIVE_TRAINING_RUN_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_training_run.md"
BOUNDED_OBJECTIVE_TRAINING_RUN_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_training_run.html"


def locate_objective_seed(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_SEED_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective training run input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_training_run(
    objective_seed_report: dict[str, Any],
    run_dir: str | Path,
    *,
    objective_seed_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective training run",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    seed_summary = as_dict(objective_seed_report.get("summary"))
    artifacts = _artifacts(root)
    metrics = _metrics(root / "metrics.jsonl")
    train_config = _read_json(root / "train_config.json")
    manifest = _read_json(root / "run_manifest.json")
    checks = _checks(objective_seed_report, seed_summary, artifacts, metrics, train_config)
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
        "source_objective_seed": str(objective_seed_path or ""),
        "run_dir": str(root),
        "objective_seed_summary": seed_summary,
        "artifacts": artifacts,
        "metrics": metrics,
        "train_config": train_config,
        "manifest": manifest,
        "check_rows": checks,
        "objective_training": training,
        "summary": _summary(status, checks, training),
        "interpretation": _interpretation(status, training),
    }


def resolve_exit_code(report: dict[str, Any], *, require_training_ready: bool) -> int:
    if require_training_ready and report.get("status") != "pass":
        return 1
    return 0


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
    records = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            records.append(json.loads(line))
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


def _checks(
    seed: dict[str, Any],
    seed_summary: dict[str, Any],
    artifacts: list[dict[str, Any]],
    metrics: dict[str, Any],
    train_config: dict[str, Any],
) -> list[dict[str, Any]]:
    artifact_map = {row["key"]: row for row in artifacts}
    return [
        _check("objective_seed_passed", seed.get("status") == "pass", seed.get("status"), "objective seed must pass"),
        _check("objective_seed_ready", seed_summary.get("bounded_objective_seed_ready") is True, seed_summary.get("bounded_objective_seed_ready"), "objective seed must be ready"),
        _check("direct_examples_present", int(seed_summary.get("direct_example_count") or 0) == int(seed_summary.get("example_count") or -1), seed_summary.get("direct_example_count"), "all objective seed rows must be direct examples"),
        _check("no_carry_forward_examples", int(seed_summary.get("carry_forward_example_count") or 0) == 0, seed_summary.get("carry_forward_example_count"), "objective training must not use carry-forward rows"),
        _check("checkpoint_exists", artifact_map["checkpoint"]["exists"], artifact_map["checkpoint"]["path"], "training must produce checkpoint.pt"),
        _check("tokenizer_exists", artifact_map["tokenizer"]["exists"], artifact_map["tokenizer"]["path"], "training must produce tokenizer.json"),
        _check("metrics_exists", artifact_map["metrics"]["exists"], artifact_map["metrics"]["path"], "training must produce metrics.jsonl"),
        _check("manifest_exists", artifact_map["run_manifest"]["exists"], artifact_map["run_manifest"]["path"], "training must produce run_manifest.json"),
        _check("prepared_corpus_exists", artifact_map["prepared_corpus"]["exists"], artifact_map["prepared_corpus"]["path"], "training must copy prepared corpus"),
        _check("metrics_records_present", int(metrics.get("record_count") or 0) >= 2, metrics.get("record_count"), "training should record at least first and last metrics"),
        _check("max_iters_positive", int(train_config.get("max_iters") or 0) > 0, train_config.get("max_iters"), "train_config must record positive max_iters"),
    ]


def _training(
    status: str,
    artifacts: list[dict[str, Any]],
    metrics: dict[str, Any],
    train_config: dict[str, Any],
    manifest: dict[str, Any],
    seed_summary: dict[str, Any],
) -> dict[str, Any]:
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
        "objective_example_count": seed_summary.get("example_count"),
        "direct_example_count": seed_summary.get("direct_example_count"),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_replay_comparison",
        "next_step": "run_bounded_objective_checkpoint_replay" if status == "pass" else "repair_bounded_objective_training_run",
    }


def _summary(status: str, checks: list[dict[str, Any]], training: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_training_ready": status == "pass" and training.get("ready") is True,
        "artifact_count": training.get("artifact_count"),
        "metric_record_count": training.get("metric_record_count"),
        "final_step": training.get("final_step"),
        "final_train_loss": training.get("final_train_loss"),
        "final_val_loss": training.get("final_val_loss"),
        "train_loss_delta": training.get("train_loss_delta"),
        "val_loss_delta": training.get("val_loss_delta"),
        "objective_example_count": training.get("objective_example_count"),
        "direct_example_count": training.get("direct_example_count"),
        "proposed_next_artifact": training.get("proposed_next_artifact"),
        "next_step": training.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_training_run_ready"
    return "fix_model_capability_route_promotion_bounded_objective_training_run"


def _interpretation(status: str, training: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Objective training artifacts are incomplete.", "next_action": "repair objective training run"}
    return {
        "model_quality_claim": "training_artifact_only",
        "reason": "A bounded objective checkpoint exists, but model improvement still requires bounded replay comparison.",
        "next_action": training.get("next_step"),
    }


def _delta(first: Any, last: Any) -> float | None:
    if first is None or last is None:
        return None
    return round(float(last) - float(first), 6)


__all__ = [
    "BOUNDED_OBJECTIVE_TRAINING_RUN_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_TRAINING_RUN_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_TRAINING_RUN_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_TRAINING_RUN_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_training_run",
    "locate_objective_seed",
    "read_json_report",
    "resolve_exit_code",
]
