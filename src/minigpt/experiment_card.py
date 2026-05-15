from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.experiment_card_artifacts import (
    render_experiment_card_html,
    render_experiment_card_markdown,
    write_experiment_card_html,
    write_experiment_card_json,
    write_experiment_card_markdown,
    write_experiment_card_outputs,
)
from minigpt.report_utils import utc_now


CARD_ARTIFACT_PATHS = [
    ("checkpoint", "checkpoint.pt", "model checkpoint"),
    ("tokenizer", "tokenizer.json", "tokenizer metadata"),
    ("train_config", "train_config.json", "training configuration"),
    ("history_summary", "history_summary.json", "training loss summary"),
    ("dataset_report", "dataset_report.json", "dataset source report"),
    ("dataset_quality", "dataset_quality.json", "dataset quality report"),
    ("eval_suite", "eval_suite/eval_suite.json", "fixed prompt evaluation suite"),
    ("run_manifest", "run_manifest.json", "reproducibility manifest"),
    ("dashboard", "dashboard.html", "static dashboard"),
    ("playground", "playground.html", "static playground"),
    ("experiment_card_json", "experiment_card.json", "machine-readable experiment card"),
    ("experiment_card_md", "experiment_card.md", "markdown experiment card"),
    ("experiment_card_html", "experiment_card.html", "browser experiment card"),
]

def build_experiment_card(
    run_dir: str | Path,
    *,
    registry_path: str | Path | None = None,
    title: str = "MiniGPT experiment card",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    warnings: list[str] = []
    train_config = _read_json(root / "train_config.json", warnings)
    history = _read_json(root / "history_summary.json", warnings)
    dataset_report = _read_json(root / "dataset_report.json", warnings)
    dataset_quality = _read_json(root / "dataset_quality.json", warnings)
    eval_report = _read_json(root / "eval_report.json", warnings)
    eval_suite = _read_json(root / "eval_suite" / "eval_suite.json", warnings)
    manifest = _read_json(root / "run_manifest.json", warnings)
    model_report = _read_json(root / "model_report" / "model_report.json", warnings)
    run_notes = _read_json(root / "run_notes.json", warnings)
    registry = _read_json(Path(registry_path), warnings) if registry_path is not None else None
    registry_run = _find_registry_run(root, registry if isinstance(registry, dict) else None)

    notes = _build_notes(run_notes, registry_run)
    summary = _build_summary(root, train_config, history, dataset_quality, eval_report, eval_suite, manifest, model_report, registry_run, notes)
    data = _build_data_section(dataset_report, dataset_quality, manifest)
    training = _build_training_section(train_config, history, manifest)
    evaluation = _build_evaluation_section(eval_report, eval_suite, registry_run)
    registry_context = _build_registry_context(registry, registry_run, registry_path)
    artifacts = _collect_card_artifacts(root)
    recommendations = _build_recommendations(summary, data, evaluation, artifacts, warnings)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "run_dir": str(root),
        "summary": summary,
        "notes": notes,
        "data": data,
        "training": training,
        "evaluation": evaluation,
        "registry": registry_context,
        "artifacts": artifacts,
        "recommendations": recommendations,
        "warnings": warnings,
    }

def _read_json(path: Path, warnings: list[str]) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path.name} is not valid JSON: {exc}")
        return None


def _find_registry_run(root: Path, registry: dict[str, Any] | None) -> dict[str, Any] | None:
    if registry is None:
        return None
    try:
        resolved = root.resolve()
    except OSError:
        resolved = root.absolute()
    for run in registry.get("runs", []):
        if not isinstance(run, dict):
            continue
        path = run.get("path")
        if path is None:
            continue
        try:
            candidate = Path(str(path)).resolve()
        except OSError:
            candidate = Path(str(path)).absolute()
        if candidate == resolved or str(path) == str(root):
            return run
    return None


def _build_notes(run_notes: Any, registry_run: dict[str, Any] | None) -> dict[str, Any]:
    notes = run_notes if isinstance(run_notes, dict) else {}
    note = _pick(notes, "note") or _pick(notes, "summary") or _pick(registry_run, "note")
    tags = _as_str_list(_pick(notes, "tags") or _pick(registry_run, "tags"))
    return {"note": _as_str(note), "tags": tags}


def _build_summary(
    root: Path,
    train_config: Any,
    history: Any,
    dataset_quality: Any,
    eval_report: Any,
    eval_suite: Any,
    manifest: Any,
    model_report: Any,
    registry_run: dict[str, Any] | None,
    notes: dict[str, Any],
) -> dict[str, Any]:
    manifest_data = _pick_dict(manifest, "data")
    manifest_training = _pick_dict(manifest, "training")
    manifest_model = _pick_dict(manifest, "model")
    manifest_results = _pick_dict(manifest, "results")
    manifest_history = _pick_dict(manifest_results, "history_summary")
    git = _pick_dict(manifest, "git")
    best_val_loss = (
        _pick(registry_run, "best_val_loss")
        or _pick(history, "best_val_loss")
        or _pick(manifest_history, "best_val_loss")
    )
    dataset_status = (
        _pick(registry_run, "dataset_quality")
        or _pick(dataset_quality, "status")
        or _pick(_pick_dict(manifest_data, "dataset_quality"), "status")
    )
    checkpoint_exists = (root / "checkpoint.pt").exists()
    eval_cases = _pick(registry_run, "eval_suite_cases") or _pick(eval_suite, "case_count")
    status = _overall_status(dataset_status, checkpoint_exists, best_val_loss, eval_cases)
    return {
        "run_name": _pick(registry_run, "name") or root.name,
        "status": status,
        "checkpoint_exists": checkpoint_exists,
        "tokenizer": _pick(train_config, "tokenizer") or _pick(manifest_training, "tokenizer"),
        "max_iters": _pick(train_config, "max_iters") or _nested_pick(manifest_training, "args", "max_iters"),
        "best_val_loss": _as_optional_float(best_val_loss),
        "best_val_loss_rank": _pick(registry_run, "best_val_loss_rank"),
        "best_val_loss_delta": _pick(registry_run, "best_val_loss_delta"),
        "is_best_val_loss": bool(_pick(registry_run, "is_best_val_loss")),
        "last_val_loss": _as_optional_float(_pick(history, "last_val_loss") or _pick(manifest_history, "last_val_loss")),
        "eval_loss": _as_optional_float(_pick(eval_report, "loss")),
        "perplexity": _as_optional_float(_pick(eval_report, "perplexity")),
        "dataset_quality": _as_str(dataset_status),
        "dataset_fingerprint": _as_str(_pick(registry_run, "dataset_fingerprint") or _pick(dataset_quality, "short_fingerprint")),
        "eval_suite_cases": _as_int(eval_cases),
        "git_commit": _as_str(_pick(registry_run, "git_commit") or _pick(git, "short_commit")),
        "git_dirty": _pick(registry_run, "git_dirty") if _pick(registry_run, "git_dirty") is not None else _pick(git, "dirty"),
        "total_parameters": _as_int(_pick(registry_run, "total_parameters") or _pick(model_report, "total_parameters") or _pick(manifest_model, "parameter_count")),
        "note": notes.get("note"),
        "tags": notes.get("tags", []),
    }


def _build_data_section(dataset_report: Any, dataset_quality: Any, manifest: Any) -> dict[str, Any]:
    manifest_data = _pick_dict(manifest, "data")
    source = _pick_dict(manifest_data, "source")
    manifest_quality = _pick_dict(manifest_data, "dataset_quality")
    return {
        "source_kind": _pick(source, "kind"),
        "source_count": _pick(dataset_report, "source_count"),
        "char_count": _pick(dataset_report, "char_count"),
        "line_count": _pick(dataset_report, "line_count"),
        "unique_char_count": _pick(dataset_report, "unique_char_count"),
        "token_count": _pick(manifest_data, "token_count"),
        "train_token_count": _pick(manifest_data, "train_token_count"),
        "val_token_count": _pick(manifest_data, "val_token_count"),
        "status": _pick(dataset_quality, "status") or _pick(manifest_quality, "status"),
        "short_fingerprint": _pick(dataset_quality, "short_fingerprint") or _pick(manifest_quality, "short_fingerprint"),
        "warning_count": _pick(dataset_quality, "warning_count"),
        "issue_count": _pick(dataset_quality, "issue_count"),
    }


def _build_training_section(train_config: Any, history: Any, manifest: Any) -> dict[str, Any]:
    manifest_training = _pick_dict(manifest, "training")
    args = _pick_dict(manifest_training, "args")
    return {
        "tokenizer": _pick(train_config, "tokenizer") or _pick(manifest_training, "tokenizer"),
        "max_iters": _pick(train_config, "max_iters") or _pick(args, "max_iters"),
        "batch_size": _pick(train_config, "batch_size") or _pick(args, "batch_size"),
        "block_size": _pick(train_config, "block_size") or _pick(args, "block_size"),
        "learning_rate": _pick(train_config, "learning_rate") or _pick(args, "learning_rate"),
        "device_used": _pick(manifest_training, "device_used"),
        "start_step": _pick(manifest_training, "start_step"),
        "end_step": _pick(manifest_training, "end_step"),
        "best_val_loss": _pick(history, "best_val_loss"),
        "last_val_loss": _pick(history, "last_val_loss"),
    }


def _build_evaluation_section(eval_report: Any, eval_suite: Any, registry_run: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "eval_loss": _pick(eval_report, "loss"),
        "perplexity": _pick(eval_report, "perplexity"),
        "eval_suite_cases": _pick(eval_suite, "case_count") or _pick(registry_run, "eval_suite_cases"),
        "avg_unique_chars": _pick(eval_suite, "avg_unique_chars") or _pick(registry_run, "eval_suite_avg_unique"),
        "best_val_loss_rank": _pick(registry_run, "best_val_loss_rank"),
        "best_val_loss_delta": _pick(registry_run, "best_val_loss_delta"),
        "is_best_val_loss": bool(_pick(registry_run, "is_best_val_loss")),
    }


def _build_registry_context(registry: Any, registry_run: dict[str, Any] | None, registry_path: str | Path | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {
            "registry_path": None if registry_path is None else str(registry_path),
            "run_count": None,
            "quality_counts": None,
            "tag_counts": None,
            "matched_run": registry_run is not None,
        }
    return {
        "registry_path": None if registry_path is None else str(registry_path),
        "run_count": registry.get("run_count"),
        "quality_counts": registry.get("quality_counts"),
        "tag_counts": registry.get("tag_counts"),
        "matched_run": registry_run is not None,
    }


def _collect_card_artifacts(root: Path) -> list[dict[str, Any]]:
    artifacts = []
    for key, relative, description in CARD_ARTIFACT_PATHS:
        path = root / relative
        exists = path.exists()
        artifacts.append(
            {
                "key": key,
                "path": relative,
                "description": description,
                "exists": exists,
                "size_bytes": path.stat().st_size if exists and path.is_file() else None,
            }
        )
    return artifacts


def _build_recommendations(
    summary: dict[str, Any],
    data: dict[str, Any],
    evaluation: dict[str, Any],
    artifacts: list[dict[str, Any]],
    warnings: list[str],
) -> list[str]:
    items: list[str] = []
    if summary.get("is_best_val_loss"):
        items.append("Keep this run as the current best-val reference until a lower-loss run is registered.")
    if summary.get("dataset_quality") in {None, "missing"}:
        items.append("Generate dataset_quality.json before comparing this run seriously.")
    elif summary.get("dataset_quality") != "pass":
        items.append("Review dataset quality warnings before promoting this run.")
    if evaluation.get("eval_suite_cases") in {None, 0}:
        items.append("Run the fixed prompt eval suite so generations can be compared across checkpoints.")
    if not summary.get("checkpoint_exists"):
        items.append("Create or restore checkpoint.pt before using this run for generation.")
    if data.get("short_fingerprint") is None:
        items.append("Record a dataset fingerprint to make data provenance reproducible.")
    if warnings:
        items.append("Fix invalid JSON inputs listed in the warnings section.")
    if not any(item.get("key") == "dashboard" and item.get("exists") for item in artifacts):
        items.append("Build dashboard.html to make all run artifacts easier to inspect.")
    return items or ["This run has the core metadata needed for a first-pass experiment review."]


def _overall_status(dataset_status: Any, checkpoint_exists: bool, best_val_loss: Any, eval_cases: Any) -> str:
    if not checkpoint_exists or best_val_loss is None:
        return "incomplete"
    if dataset_status in {None, "missing"}:
        return "needs-data-quality"
    if dataset_status not in {"pass", None}:
        return "review"
    if eval_cases in {None, 0}:
        return "needs-eval"
    return "ready"


def _pick(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    nested = _pick(payload, key)
    return nested if isinstance(nested, dict) else {}


def _nested_pick(payload: Any, section: str, key: str) -> Any:
    return _pick(_pick_dict(payload, section), key)


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _as_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)
