from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, read_json_object, utc_now, write_json_payload
from minigpt.unassisted_holdout_repair_plan_v1148 import EXPLAIN_DIR_NAME
from minigpt.unassisted_loss_suffix_repair_seed_v1153 import UNASSISTED_LOSS_SUFFIX_REPAIR_SEED_V1153_STEM
from minigpt.report_check_common import check_entry as _check


UNASSISTED_LOSS_SUFFIX_REPAIR_TRAINING_RUN_V1154_STEM = "unassisted_loss_suffix_repair_training_run_v1154"
SEED_CORPUS_TEXT_NAME = "unassisted_loss_suffix_repair_seed_corpus_v1153.txt"
HOLDOUT_PROMPTS_NAME = "unassisted_loss_suffix_repair_holdout_prompts_v1153.json"
TRAINING_HANDOFF_NAME = "unassisted_loss_suffix_repair_training_handoff_v1154.json"


def locate_v1153_seed_corpus(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / f"{UNASSISTED_LOSS_SUFFIX_REPAIR_SEED_V1153_STEM}.json"
    return source


def default_v1153_seed_corpus_path(repo_root: str | Path) -> Path:
    return (
        Path(repo_root)
        / "f"
        / "1153"
        / EXPLAIN_DIR_NAME
        / "unassisted-loss-suffix-repair-seed-v1153"
        / f"{UNASSISTED_LOSS_SUFFIX_REPAIR_SEED_V1153_STEM}.json"
    )


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def seed_corpus_text_path(seed_corpus_report_path: str | Path) -> Path:
    return Path(seed_corpus_report_path).parent / SEED_CORPUS_TEXT_NAME


def build_unassisted_loss_suffix_repair_training_run_v1154(
    seed_corpus_report: dict[str, Any],
    run_dir: str | Path,
    *,
    seed_corpus_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    seed_summary = as_dict(seed_corpus_report.get("summary"))
    artifacts = _artifacts(root)
    metrics = _metrics(root / "metrics.jsonl")
    train_config = _read_json(root / "train_config.json")
    manifest = _read_json(root / "run_manifest.json")
    prepared_text = _read_text(root / "prepared_corpus.txt")
    sample_text = _read_text(root / "sample.txt")
    checks = _checks(seed_corpus_report, seed_summary, artifacts, metrics, train_config, prepared_text)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    training = _training(status, artifacts, metrics, train_config, manifest, sample_text, seed_corpus_path)
    return {
        "schema_version": 1,
        "title": "MiniGPT unassisted loss suffix repair training run v1154",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_unassisted_loss_suffix_repair_seed_corpus": str(seed_corpus_path or ""),
        "run_dir": str(root),
        "seed_summary": seed_summary,
        "artifact_rows": artifacts,
        "metrics": metrics,
        "train_config": train_config,
        "manifest": manifest,
        "sample_preview": sample_text[:240],
        "check_rows": checks,
        "training_run": training,
        "summary": _summary(status, checks, training),
        "interpretation": _interpretation(status, training),
        "csv_fieldnames": ["key", "path", "exists", "size"],
    }


def write_unassisted_loss_suffix_repair_training_run_v1154_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    outputs = write_readability_outputs(
        report,
        out_dir,
        stem=UNASSISTED_LOSS_SUFFIX_REPAIR_TRAINING_RUN_V1154_STEM,
        row_title="Training Artifacts",
        row_key="artifact_rows",
    )
    handoff_path = Path(out_dir) / TRAINING_HANDOFF_NAME
    write_json_payload(_handoff(report), handoff_path)
    outputs["training_handoff"] = str(handoff_path)
    return outputs


def resolve_exit_code(report: dict[str, Any], *, require_training_ready: bool = False) -> int:
    return 1 if require_training_ready and report.get("status") != "pass" else 0


def _artifacts(root: Path) -> list[dict[str, Any]]:
    rows = []
    for key, name in [
        ("checkpoint", "checkpoint.pt"),
        ("tokenizer", "tokenizer.json"),
        ("metrics", "metrics.jsonl"),
        ("train_config", "train_config.json"),
        ("run_manifest", "run_manifest.json"),
        ("history_summary", "history_summary.json"),
        ("loss_curve", "loss_curve.svg"),
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


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.is_file() else ""


def _checks(
    seed_corpus_report: dict[str, Any],
    seed_summary: dict[str, Any],
    artifacts: list[dict[str, Any]],
    metrics: dict[str, Any],
    train_config: dict[str, Any],
    prepared_text: str,
) -> list[dict[str, Any]]:
    artifact_map = {row["key"]: row for row in artifacts}
    expected_corpus = str(seed_corpus_report.get("corpus_text") or "")
    max_iters = int(train_config.get("max_iters") or 0)
    last_step = int(as_dict(metrics.get("last")).get("step") or 0)
    return [
        _check("seed_corpus_passed", seed_corpus_report.get("status") == "pass", seed_corpus_report.get("status"), "v1153 seed corpus must pass"),
        _check("seed_corpus_ready", seed_summary.get("unassisted_loss_suffix_repair_seed_ready") is True, seed_summary.get("unassisted_loss_suffix_repair_seed_ready"), "v1153 seed corpus ready flag must be true"),
        _check("seed_corpus_next_step_matches_training", seed_summary.get("next_step") == "run_unassisted_loss_suffix_repair_training", seed_summary.get("next_step"), "v1153 must point to bounded training"),
        _check("checkpoint_exists", artifact_map["checkpoint"]["exists"], artifact_map["checkpoint"]["path"], "training must produce checkpoint.pt"),
        _check("tokenizer_exists", artifact_map["tokenizer"]["exists"], artifact_map["tokenizer"]["path"], "training must produce tokenizer.json"),
        _check("metrics_exists", artifact_map["metrics"]["exists"], artifact_map["metrics"]["path"], "training must produce metrics.jsonl"),
        _check("manifest_exists", artifact_map["run_manifest"]["exists"], artifact_map["run_manifest"]["path"], "training must produce run_manifest.json"),
        _check("prepared_corpus_matches_seed", bool(expected_corpus) and prepared_text == expected_corpus, artifact_map["prepared_corpus"]["path"], "training must consume the exact v1153 seed corpus text"),
        _check("metrics_records_present", int(metrics.get("record_count") or 0) >= 2, metrics.get("record_count"), "training should record first and last metrics"),
        _check("max_iters_reached", max_iters > 0 and last_step == max_iters, {"last_step": last_step, "max_iters": max_iters}, "metrics must reach train_config.max_iters"),
        _check("train_loss_decreased", _negative(metrics.get("train_loss_delta")), metrics.get("train_loss_delta"), "bounded training should reduce train loss"),
        _check("val_loss_decreased", _negative(metrics.get("val_loss_delta")), metrics.get("val_loss_delta"), "bounded training should reduce validation loss on the small holdout split"),
        _check("promotion_boundary_kept", seed_summary.get("promotion_ready") is False, seed_summary.get("promotion_ready"), "training artifact is not promotion evidence before replay comparison"),
    ]


def _training(
    status: str,
    artifacts: list[dict[str, Any]],
    metrics: dict[str, Any],
    train_config: dict[str, Any],
    manifest: dict[str, Any],
    sample_text: str,
    seed_corpus_path: str | Path | None,
) -> dict[str, Any]:
    artifact_map = {row["key"]: row for row in artifacts}
    last = as_dict(metrics.get("last"))
    sample_lower = sample_text.lower()
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
        "checkpoint": artifact_map["checkpoint"]["path"],
        "tokenizer": artifact_map["tokenizer"]["path"],
        "prepared_data": train_config.get("prepared_data"),
        "source_seed_corpus": str(seed_corpus_path or ""),
        "sample_fixed_hit": "fixed" in sample_lower,
        "sample_loss_hit": "loss" in sample_lower,
        "promotion_ready": False,
        "model_quality_claim": "training_artifact_only",
        "proposed_next_artifact": "unassisted_loss_suffix_repair_replay_comparison_v1155",
        "next_step": "run_unassisted_loss_suffix_repair_replay_comparison" if status == "pass" else "repair_unassisted_loss_suffix_repair_training_run",
    }


def _summary(status: str, checks: list[dict[str, Any]], training: dict[str, Any]) -> dict[str, Any]:
    return {
        "unassisted_loss_suffix_repair_training_ready": status == "pass" and training.get("ready") is True,
        "artifact_count": training.get("artifact_count"),
        "metric_record_count": training.get("metric_record_count"),
        "final_step": training.get("final_step"),
        "final_train_loss": training.get("final_train_loss"),
        "final_val_loss": training.get("final_val_loss"),
        "train_loss_delta": training.get("train_loss_delta"),
        "val_loss_delta": training.get("val_loss_delta"),
        "sample_fixed_hit": training.get("sample_fixed_hit"),
        "sample_loss_hit": training.get("sample_loss_hit"),
        "model_quality_claim": training.get("model_quality_claim"),
        "promotion_ready": False,
        "proposed_next_artifact": training.get("proposed_next_artifact"),
        "next_step": training.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "unassisted_loss_suffix_repair_training_run_ready"
    return "fix_unassisted_loss_suffix_repair_training_run"


def _interpretation(status: str, training: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Bounded repair training artifacts are incomplete.", "next_action": "repair training run"}
    return {
        "model_quality_claim": "training_artifact_only",
        "reason": "A bounded checkpoint was trained from the v1153 repaired corpus, but capability improvement must be proven by replaying the unchanged target-free holdout prompts.",
        "next_action": training.get("next_step"),
    }


def _handoff(report: dict[str, Any]) -> dict[str, Any]:
    training = as_dict(report.get("training_run"))
    return {
        "schema_version": 1,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "source_unassisted_loss_suffix_repair_seed_corpus": report.get("source_unassisted_loss_suffix_repair_seed_corpus"),
        "run_dir": report.get("run_dir"),
        "checkpoint": training.get("checkpoint"),
        "tokenizer": training.get("tokenizer"),
        "holdout_prompts": str(Path(str(report.get("source_unassisted_loss_suffix_repair_seed_corpus") or "")).parent / HOLDOUT_PROMPTS_NAME),
        "model_quality_claim": training.get("model_quality_claim"),
        "promotion_ready": False,
        "next_step": training.get("next_step"),
    }


def _delta(first: Any, last: Any) -> float | None:
    if first is None or last is None:
        return None
    return round(float(last) - float(first), 6)


def _negative(value: Any) -> bool:
    return value is not None and float(value) < 0.0


__all__ = [
    "HOLDOUT_PROMPTS_NAME",
    "SEED_CORPUS_TEXT_NAME",
    "TRAINING_HANDOFF_NAME",
    "UNASSISTED_LOSS_SUFFIX_REPAIR_TRAINING_RUN_V1154_STEM",
    "build_unassisted_loss_suffix_repair_training_run_v1154",
    "default_v1153_seed_corpus_path",
    "locate_v1153_seed_corpus",
    "read_json_report",
    "resolve_exit_code",
    "seed_corpus_text_path",
    "write_unassisted_loss_suffix_repair_training_run_v1154_outputs",
]
