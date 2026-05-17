from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.history import load_records, summarize_records
from minigpt.manifest import collect_run_artifacts
from minigpt.report_utils import (
    utc_now,
)
from minigpt.training_run_evidence_components import (
    build_checks,
    build_summary,
    data_section,
    evaluation_section,
    quality_section,
    recommendations,
    sample_section,
    scorecard_section,
    training_section,
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
    eval_suite = _read_json(root / "eval_suite" / "eval_suite.json", warnings, "eval_suite")
    evaluation = evaluation_section(eval_suite, root / "eval_suite" / "eval_suite.json")
    quality_report = _read_json(root / "generation_quality" / "generation_quality.json", warnings, "generation_quality")
    quality = quality_section(quality_report, root / "generation_quality" / "generation_quality.json")
    scorecard_report = _read_json(root / "benchmark-scorecard" / "benchmark_scorecard.json", warnings, "benchmark_scorecard")
    scorecard = scorecard_section(scorecard_report, root / "benchmark-scorecard" / "benchmark_scorecard.json")
    checks = build_checks(
        root=root,
        artifacts=artifacts,
        train_config=train_config,
        manifest=manifest,
        records=records,
        history_summary=history_summary,
        evaluation=evaluation,
        quality=quality,
        scorecard=scorecard,
        require_sample=require_sample,
        require_eval_suite=require_eval_suite,
    )
    summary = build_summary(checks, artifacts, root, evaluation, quality, scorecard)
    training = training_section(train_config, manifest, history_summary)
    data = data_section(train_config, manifest)
    report = {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "run_dir": str(root),
        "summary": summary,
        "training": training,
        "data": data,
        "evaluation": evaluation,
        "quality": quality,
        "scorecard": scorecard,
        "sample": sample_section(root / "sample.txt"),
        "checks": checks,
        "artifacts": artifacts,
        "warnings": warnings,
        "recommendations": recommendations(summary, checks, data, evaluation, quality, scorecard),
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
