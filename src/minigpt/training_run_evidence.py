from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.history import load_records, summarize_records
from minigpt.manifest import collect_run_artifacts
from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    utc_now,
)
from minigpt.training_run_evidence_artifacts import (
    render_training_run_evidence_html,
    render_training_run_evidence_markdown,
    write_training_run_evidence_csv,
    write_training_run_evidence_html,
    write_training_run_evidence_json,
    write_training_run_evidence_markdown,
    write_training_run_evidence_outputs,
)


CORE_ARTIFACTS = {"checkpoint", "tokenizer", "train_config", "metrics", "run_manifest"}
REVIEW_ARTIFACTS = {"history_summary", "sample"}


def build_training_run_evidence(
    run_dir: str | Path,
    *,
    title: str = "MiniGPT training run evidence",
    generated_at: str | None = None,
    require_sample: bool = False,
    require_eval_suite: bool = False,
) -> dict[str, Any]:
    root = Path(run_dir)
    warnings: list[str] = []
    train_config = _read_json(root / "train_config.json", warnings, "train_config")
    manifest = _read_json(root / "run_manifest.json", warnings, "run_manifest")
    history_file = root / "metrics.jsonl"
    records = _load_history_records(history_file, warnings)
    computed_history = summarize_records(records)
    stored_history = _read_json(root / "history_summary.json", warnings, "history_summary")
    history_summary = _merge_history_summary(stored_history, computed_history)
    artifacts = _artifact_rows(root)
    checks = _checks(
        root=root,
        artifacts=artifacts,
        train_config=train_config,
        manifest=manifest,
        records=records,
        history_summary=history_summary,
        require_sample=require_sample,
        require_eval_suite=require_eval_suite,
    )
    summary = _summary(checks, artifacts, root)
    training = _training_section(train_config, manifest, history_summary)
    data = _data_section(train_config, manifest)
    report = {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "run_dir": str(root),
        "summary": summary,
        "training": training,
        "data": data,
        "sample": _sample_section(root / "sample.txt"),
        "checks": checks,
        "artifacts": artifacts,
        "warnings": warnings,
        "recommendations": _recommendations(summary, checks, data),
    }
    return report


def _read_json(path: Path, warnings: list[str], label: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{label} is not valid JSON: {exc}")
        return {}
    if not isinstance(payload, dict):
        warnings.append(f"{label} is not a JSON object")
        return {}
    return payload


def _load_history_records(path: Path, warnings: list[str]) -> list[Any]:
    if not path.exists():
        return []
    try:
        return load_records(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        warnings.append(f"metrics.jsonl could not be parsed: {exc}")
        return []


def _merge_history_summary(stored: dict[str, Any], computed: dict[str, Any]) -> dict[str, Any]:
    merged = dict(computed)
    for key, value in stored.items():
        if value is not None:
            merged[key] = value
    return merged


def _artifact_rows(root: Path) -> list[dict[str, Any]]:
    rows = []
    for artifact in collect_run_artifacts(root):
        key = str(artifact.get("key") or "")
        required_level = "core" if key in CORE_ARTIFACTS else "review" if key in REVIEW_ARTIFACTS else "optional"
        rows.append(
            {
                **artifact,
                "required_level": required_level,
                "absolute_path": str(root / str(artifact.get("path") or "")),
            }
        )
    manifest_path = root / "run_manifest.json"
    rows.append(
        {
            "key": "run_manifest",
            "path": "run_manifest.json",
            "description": "reproducibility manifest",
            "exists": manifest_path.exists(),
            "size_bytes": manifest_path.stat().st_size if manifest_path.exists() and manifest_path.is_file() else None,
            "sha256": None,
            "required_level": "core",
            "absolute_path": str(manifest_path),
        }
    )
    return rows


def _checks(
    *,
    root: Path,
    artifacts: list[dict[str, Any]],
    train_config: dict[str, Any],
    manifest: dict[str, Any],
    records: list[Any],
    history_summary: dict[str, Any],
    require_sample: bool,
    require_eval_suite: bool,
) -> list[dict[str, Any]]:
    artifact_map = {item.get("key"): item for item in artifacts}
    checks = [
        _artifact_check(artifact_map, "checkpoint", "checkpoint.pt is available for local generation"),
        _artifact_check(artifact_map, "tokenizer", "tokenizer.json is available for decoding the checkpoint"),
        _artifact_check(artifact_map, "train_config", "train_config.json records the training settings"),
        _artifact_check(artifact_map, "metrics", "metrics.jsonl records training/evaluation losses"),
        _artifact_check(artifact_map, "run_manifest", "run_manifest.json records reproducibility metadata"),
    ]
    checks.append(
        _check(
            "metrics_parseable",
            "training",
            "pass" if records else "fail",
            "metrics.jsonl contains parseable training records" if records else "metrics.jsonl has no parseable training records",
            "Keep metrics.jsonl from scripts/train.py so best/latest losses can be audited.",
            {"record_count": len(records)},
        )
    )
    checks.append(_step_check(train_config, manifest, history_summary))
    checks.append(_loss_check(history_summary))
    checks.append(
        _check(
            "history_summary_present",
            "training",
            "pass" if (root / "history_summary.json").exists() else "warn",
            "history_summary.json is present" if (root / "history_summary.json").exists() else "history_summary.json is missing",
            "Keep history_summary.json next to metrics.jsonl for quick run comparison.",
            {},
        )
    )
    sample_status = "pass" if (root / "sample.txt").exists() else "fail" if require_sample else "warn"
    checks.append(
        _check(
            "sample_present",
            "generation",
            sample_status,
            "sample.txt is present" if (root / "sample.txt").exists() else "sample.txt is missing",
            "Generate a sample when this run will be reviewed by humans.",
            {"required": bool(require_sample)},
        )
    )
    eval_suite_exists = (root / "eval_suite" / "eval_suite.json").exists()
    eval_status = "pass" if eval_suite_exists else "fail" if require_eval_suite else "warn"
    checks.append(
        _check(
            "eval_suite_present",
            "evaluation",
            eval_status,
            "eval suite evidence is present" if eval_suite_exists else "eval suite evidence is missing",
            "Run scripts/eval_suite.py before comparing model quality across checkpoints.",
            {"required": bool(require_eval_suite)},
        )
    )
    if not train_config:
        checks.append(
            _check(
                "train_config_parseable",
                "training",
                "fail",
                "train_config.json is missing or invalid",
                "Re-run training or restore train_config.json before promotion review.",
                {},
            )
        )
    if not manifest:
        checks.append(
            _check(
                "manifest_parseable",
                "reproducibility",
                "fail",
                "run_manifest.json is missing or invalid",
                "Rebuild the run manifest before treating the checkpoint as reproducible evidence.",
                {},
            )
        )
    return checks


def _artifact_check(artifact_map: dict[Any, dict[str, Any]], key: str, pass_message: str) -> dict[str, Any]:
    artifact = artifact_map.get(key, {})
    exists = bool(artifact.get("exists"))
    path = artifact.get("path") or key
    return _check(
        f"{key}_present",
        "artifact",
        "pass" if exists else "fail",
        pass_message if exists else f"{path} is missing",
        f"Keep {path} with this run as promotion evidence." if exists else f"Create or restore {path} before using this run as training evidence.",
        {"path": artifact.get("path"), "size_bytes": artifact.get("size_bytes")},
    )


def _step_check(train_config: dict[str, Any], manifest: dict[str, Any], history_summary: dict[str, Any]) -> dict[str, Any]:
    target = _int(train_config.get("max_iters") or _nested_pick(manifest, "training", "end_step"))
    actual = _int(history_summary.get("last_step") or _nested_pick(manifest, "training", "end_step"))
    if target is None or actual is None:
        return _check(
            "target_step_reached",
            "training",
            "warn",
            "target or actual training step is missing",
            "Keep max_iters and history_summary.last_step so training completion can be checked.",
            {"target_step": target, "actual_last_step": actual},
        )
    return _check(
        "target_step_reached",
        "training",
        "pass" if actual >= target else "fail",
        "training reached the configured target step" if actual >= target else "training stopped before the configured target step",
        "Keep max_iters and metrics.jsonl together so completion can be audited."
        if actual >= target
        else "Resume or rerun training until metrics reach max_iters.",
        {"target_step": target, "actual_last_step": actual},
    )


def _loss_check(history_summary: dict[str, Any]) -> dict[str, Any]:
    best = _float(history_summary.get("best_val_loss"))
    last = _float(history_summary.get("last_val_loss"))
    status = "pass" if best is not None and last is not None else "fail"
    return _check(
        "loss_summary_available",
        "training",
        status,
        "best and last validation losses are available" if status == "pass" else "validation loss summary is missing",
        "Keep metrics.jsonl/history_summary.json so runs can be ranked by validation loss.",
        {"best_val_loss": best, "last_val_loss": last},
    )


def _summary(checks: list[dict[str, Any]], artifacts: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    fail_count = sum(1 for check in checks if check.get("status") == "fail")
    warn_count = sum(1 for check in checks if check.get("status") == "warn")
    status = "blocked" if fail_count else "review" if warn_count else "ready"
    core = [item for item in artifacts if item.get("required_level") == "core"]
    return {
        "status": status,
        "readiness_score": max(0, 100 - fail_count * 20 - warn_count * 5),
        "critical_missing_count": fail_count,
        "warning_count": warn_count,
        "check_count": len(checks),
        "artifact_count": len(artifacts),
        "available_artifact_count": sum(1 for item in artifacts if item.get("exists")),
        "core_artifact_count": len(core),
        "core_available_count": sum(1 for item in core if item.get("exists")),
        "checkpoint_exists": (root / "checkpoint.pt").exists(),
        "run_manifest_exists": (root / "run_manifest.json").exists(),
        "sample_exists": (root / "sample.txt").exists(),
    }


def _training_section(train_config: dict[str, Any], manifest: dict[str, Any], history_summary: dict[str, Any]) -> dict[str, Any]:
    manifest_training = _dict(manifest.get("training"))
    manifest_model = _dict(manifest.get("model"))
    return {
        "tokenizer": train_config.get("tokenizer") or manifest_training.get("tokenizer"),
        "device_used": train_config.get("device_used") or manifest_training.get("device_used"),
        "batch_size": train_config.get("batch_size") or _nested_pick(manifest_training, "args", "batch_size"),
        "block_size": train_config.get("block_size") or _nested_pick(manifest_training, "args", "block_size"),
        "learning_rate": train_config.get("learning_rate") or _nested_pick(manifest_training, "args", "learning_rate"),
        "target_step": _int(train_config.get("max_iters") or manifest_training.get("end_step")),
        "actual_last_step": _int(history_summary.get("last_step") or manifest_training.get("end_step")),
        "best_val_loss": _float(history_summary.get("best_val_loss")),
        "last_val_loss": _float(history_summary.get("last_val_loss")),
        "parameter_count": _int(manifest_model.get("parameter_count")),
    }


def _data_section(train_config: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    data_source = _dict(train_config.get("data_source") or _nested_pick(manifest, "data", "source"))
    manifest_data = _dict(manifest.get("data"))
    quality = _dict(manifest_data.get("dataset_quality"))
    version = _dict(manifest_data.get("dataset_version"))
    return {
        "source_kind": data_source.get("kind"),
        "source_path": data_source.get("path"),
        "token_count": _int(manifest_data.get("token_count")),
        "train_token_count": _int(manifest_data.get("train_token_count")),
        "val_token_count": _int(manifest_data.get("val_token_count")),
        "dataset_quality_status": quality.get("status"),
        "dataset_fingerprint": quality.get("short_fingerprint") or version.get("short_fingerprint"),
        "dataset_id": version.get("id"),
    }


def _sample_section(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path), "prompt": None, "char_count": 0, "preview": None}
    text = path.read_text(encoding="utf-8", errors="replace")
    prompt = None
    for line in text.splitlines():
        if line.startswith("prompt:"):
            prompt = line.partition(":")[2].strip()
            break
    return {
        "exists": True,
        "path": str(path),
        "prompt": prompt,
        "char_count": len(text),
        "preview": text[:240],
    }


def _recommendations(summary: dict[str, Any], checks: list[dict[str, Any]], data: dict[str, Any]) -> list[str]:
    if summary.get("status") == "blocked":
        failing = [str(check.get("code")) for check in checks if check.get("status") == "fail"]
        return ["Fix blocking training evidence checks before promotion: " + ", ".join(failing[:6]) + "."]
    recs = []
    if summary.get("status") == "review":
        recs.append("Review warning checks before treating this checkpoint as promoted training evidence.")
    else:
        recs.append("This run has the core checkpoint, tokenizer, metrics, manifest, and loss evidence needed for promotion review.")
    if data.get("dataset_quality_status") is None:
        recs.append("Attach dataset quality or dataset version evidence so the training data can be audited.")
    if not any(check.get("code") == "eval_suite_present" and check.get("status") == "pass" for check in checks):
        recs.append("Run the fixed eval suite next so model quality can be compared beyond validation loss.")
    return recs


def _check(
    code: str,
    category: str,
    status: str,
    message: str,
    recommendation: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "status": status,
        "message": message,
        "recommendation": recommendation,
        "details": details,
    }


def _nested_pick(payload: Any, *keys: str) -> Any:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "build_training_run_evidence",
    "render_training_run_evidence_html",
    "render_training_run_evidence_markdown",
    "write_training_run_evidence_csv",
    "write_training_run_evidence_html",
    "write_training_run_evidence_json",
    "write_training_run_evidence_markdown",
    "write_training_run_evidence_outputs",
]
