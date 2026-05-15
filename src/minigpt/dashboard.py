from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any

from minigpt.dashboard_render import render_dashboard_html


@dataclass(frozen=True)
class DashboardArtifact:
    key: str
    title: str
    path: Path
    kind: str
    description: str
    exists: bool
    size_bytes: int | None
    href: str | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        return payload


def _read_json(path: Path, warnings: list[str]) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path.name} is not valid JSON: {exc}")
        return None


def _read_text(path: Path, limit: int = 1200) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit].rstrip() + "\n..."
    return text


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _href(path: Path, base_dir: Path) -> str | None:
    if not path.exists():
        return None
    return Path(os.path.relpath(path, base_dir)).as_posix()


def _artifact(
    key: str,
    title: str,
    path: Path,
    kind: str,
    description: str,
    base_dir: Path,
) -> DashboardArtifact:
    exists = path.exists()
    return DashboardArtifact(
        key=key,
        title=title,
        path=path,
        kind=kind,
        description=description,
        exists=exists,
        size_bytes=path.stat().st_size if exists and path.is_file() else None,
        href=_href(path, base_dir),
    )


def collect_artifacts(run_dir: str | Path, base_dir: str | Path) -> list[DashboardArtifact]:
    root = Path(run_dir)
    base = Path(base_dir)
    specs = [
        ("checkpoint", "Checkpoint", "checkpoint.pt", "PT", "saved model and optimizer state"),
        ("tokenizer", "Tokenizer", "tokenizer.json", "JSON", "token vocabulary and tokenizer metadata"),
        ("train_config", "Train config", "train_config.json", "JSON", "training command configuration"),
        ("metrics", "Metrics history", "metrics.jsonl", "JSONL", "step-by-step train/validation losses"),
        ("history_summary", "History summary", "history_summary.json", "JSON", "best and latest loss summary"),
        ("loss_curve", "Loss curve", "loss_curve.svg", "SVG", "training and validation loss chart"),
        ("run_manifest", "Run manifest", "run_manifest.json", "JSON", "reproducibility metadata for the run"),
        ("manifest_svg", "Manifest chart", "run_manifest.svg", "SVG", "run manifest summary chart"),
        ("prepared_corpus", "Prepared corpus", "prepared_corpus.txt", "TXT", "merged training corpus from data-dir sources"),
        ("dataset_report", "Dataset report", "dataset_report.json", "JSON", "source and character statistics for the corpus"),
        ("dataset_svg", "Dataset chart", "dataset_report.svg", "SVG", "dataset source size chart"),
        ("dataset_quality", "Dataset quality", "dataset_quality.json", "JSON", "fingerprint and lightweight corpus quality checks"),
        ("dataset_quality_svg", "Dataset quality chart", "dataset_quality.svg", "SVG", "dataset quality summary chart"),
        ("dataset_version", "Dataset version", "dataset_version.json", "JSON", "dataset name/version/fingerprint manifest"),
        ("dataset_version_html", "Dataset version report", "dataset_version.html", "HTML", "browser dataset version report"),
        ("sample", "Sample text", "sample.txt", "TXT", "generated sample saved after training"),
        ("eval_report", "Evaluation report", "eval_report.json", "JSON", "loss and perplexity report"),
        ("eval_suite", "Eval suite", "eval_suite/eval_suite.json", "JSON", "fixed prompt generation evaluation report"),
        ("eval_suite_csv", "Eval suite table", "eval_suite/eval_suite.csv", "CSV", "fixed prompt evaluation table"),
        ("eval_suite_svg", "Eval suite chart", "eval_suite/eval_suite.svg", "SVG", "fixed prompt evaluation chart"),
        ("eval_suite_html", "Eval suite report", "eval_suite/eval_suite.html", "HTML", "browser benchmark evaluation report"),
        ("pair_batch_json", "Pair batch", "pair_batch/pair_generation_batch.json", "JSON", "fixed prompt pair-generation batch report"),
        ("pair_batch_csv", "Pair batch table", "pair_batch/pair_generation_batch.csv", "CSV", "pair-generation batch table"),
        ("pair_batch_md", "Pair batch markdown", "pair_batch/pair_generation_batch.md", "MD", "pair-generation batch summary"),
        ("pair_batch_html", "Pair batch HTML", "pair_batch/pair_generation_batch.html", "HTML", "browser pair-generation batch report"),
        ("pair_trend_json", "Pair batch trend", "pair_batch_trend/pair_batch_trend.json", "JSON", "trend comparison for saved pair batch reports"),
        ("pair_trend_csv", "Pair batch trend table", "pair_batch_trend/pair_batch_trend.csv", "CSV", "pair batch trend table"),
        ("pair_trend_md", "Pair batch trend markdown", "pair_batch_trend/pair_batch_trend.md", "MD", "pair batch trend summary"),
        ("pair_trend_html", "Pair batch trend HTML", "pair_batch_trend/pair_batch_trend.html", "HTML", "browser pair batch trend report"),
        ("model_report", "Model report", "model_report/model_report.json", "JSON", "architecture and parameter report"),
        ("model_svg", "Model architecture", "model_report/model_architecture.svg", "SVG", "model structure diagram"),
        ("predictions", "Prediction report", "predictions/predictions.json", "JSON", "next-token top-k probabilities"),
        ("predictions_svg", "Prediction chart", "predictions/predictions.svg", "SVG", "next-token probability chart"),
        ("attention", "Attention report", "attention/attention.json", "JSON", "attention matrix and top links"),
        ("attention_svg", "Attention chart", "attention/attention.svg", "SVG", "attention heatmap"),
        ("transcript", "Chat transcript", "transcript.json", "JSON", "one-shot or interactive chat transcript"),
        ("generated", "Generated text", "generated.txt", "TXT", "standalone generation output"),
        ("experiment_card_json", "Experiment card", "experiment_card.json", "JSON", "machine-readable experiment card"),
        ("experiment_card_md", "Experiment card markdown", "experiment_card.md", "MD", "shareable experiment summary"),
        ("experiment_card_html", "Experiment card HTML", "experiment_card.html", "HTML", "browser-readable experiment card"),
    ]
    return [
        _artifact(key, title, root / relative, kind, description, base)
        for key, title, relative, kind, description in specs
    ]


def build_dashboard_payload(
    run_dir: str | Path,
    output_path: str | Path | None = None,
    title: str = "MiniGPT experiment dashboard",
) -> dict[str, Any]:
    root = Path(run_dir)
    out_path = Path(output_path) if output_path is not None else root / "dashboard.html"
    base_dir = out_path.parent
    warnings: list[str] = []

    train_config = _read_json(root / "train_config.json", warnings)
    history_summary = _read_json(root / "history_summary.json", warnings)
    eval_report = _read_json(root / "eval_report.json", warnings)
    eval_suite = _read_json(root / "eval_suite" / "eval_suite.json", warnings)
    pair_batch = _read_json(root / "pair_batch" / "pair_generation_batch.json", warnings)
    pair_trend = _read_json(root / "pair_batch_trend" / "pair_batch_trend.json", warnings)
    run_manifest = _read_json(root / "run_manifest.json", warnings)
    dataset_report = _read_json(root / "dataset_report.json", warnings)
    dataset_quality = _read_json(root / "dataset_quality.json", warnings)
    dataset_version = _read_json(root / "dataset_version.json", warnings)
    model_report = _read_json(root / "model_report" / "model_report.json", warnings)
    predictions = _read_json(root / "predictions" / "predictions.json", warnings)
    attention = _read_json(root / "attention" / "attention.json", warnings)
    transcript = _read_json(root / "transcript.json", warnings)
    sample_text = _read_text(root / "sample.txt")
    generated_text = _read_text(root / "generated.txt")

    artifacts = collect_artifacts(root, base_dir)
    available = [artifact for artifact in artifacts if artifact.exists]
    model_config = model_report.get("config") if isinstance(model_report, dict) else None
    top_prediction = None
    if isinstance(predictions, dict) and predictions.get("predictions"):
        top_prediction = predictions["predictions"][0]
    last_assistant = None
    if isinstance(transcript, dict):
        turns = transcript.get("turns", [])
        for turn in reversed(turns):
            if isinstance(turn, dict) and turn.get("role") == "assistant":
                last_assistant = turn.get("content")
                break

    summary = {
        "run_dir": str(root),
        "available_artifacts": len(available),
        "metrics_records": _line_count(root / "metrics.jsonl"),
        "tokenizer": _pick(train_config, "tokenizer") or _pick(eval_report, "tokenizer") or _pick(model_report, "tokenizer"),
        "max_iters": _pick(train_config, "max_iters"),
        "best_val_loss": _pick(history_summary, "best_val_loss"),
        "last_val_loss": _pick(history_summary, "last_val_loss"),
        "eval_loss": _pick(eval_report, "loss"),
        "perplexity": _pick(eval_report, "perplexity"),
        "eval_suite_cases": _pick(eval_suite, "case_count"),
        "pair_batch_cases": _pick(pair_batch, "case_count"),
        "pair_batch_generated_differences": _pick(pair_batch, "generated_difference_count"),
        "pair_trend_reports": _pick(pair_trend, "report_count"),
        "pair_trend_changed_cases": _pick(pair_trend, "changed_generated_equal_cases"),
        "dataset_sources": _pick(dataset_report, "source_count"),
        "dataset_chars": _pick(dataset_report, "char_count"),
        "dataset_quality": _pick(dataset_quality, "status"),
        "dataset_fingerprint": _pick(dataset_quality, "short_fingerprint"),
        "dataset_version": _nested_pick(dataset_version, "dataset", "id"),
        "git_commit": _nested_pick(run_manifest, "git", "short_commit"),
        "manifest_created_at": _pick(run_manifest, "created_at"),
        "total_parameters": _pick(model_report, "total_parameters") or _nested_pick(run_manifest, "model", "parameter_count"),
        "top_prediction": top_prediction,
        "last_assistant": last_assistant,
    }

    return {
        "title": title,
        "run_dir": str(root),
        "output_path": str(out_path),
        "summary": summary,
        "artifacts": [artifact.to_dict() for artifact in artifacts],
        "train_config": train_config if isinstance(train_config, dict) else None,
        "history_summary": history_summary if isinstance(history_summary, dict) else None,
        "eval_report": eval_report if isinstance(eval_report, dict) else None,
        "eval_suite": eval_suite if isinstance(eval_suite, dict) else None,
        "pair_batch": pair_batch if isinstance(pair_batch, dict) else None,
        "pair_trend": pair_trend if isinstance(pair_trend, dict) else None,
        "run_manifest": run_manifest if isinstance(run_manifest, dict) else None,
        "dataset_report": dataset_report if isinstance(dataset_report, dict) else None,
        "dataset_quality": dataset_quality if isinstance(dataset_quality, dict) else None,
        "dataset_version": dataset_version if isinstance(dataset_version, dict) else None,
        "model_report": model_report if isinstance(model_report, dict) else None,
        "model_config": model_config if isinstance(model_config, dict) else None,
        "predictions": predictions if isinstance(predictions, dict) else None,
        "attention": attention if isinstance(attention, dict) else None,
        "transcript": transcript if isinstance(transcript, dict) else None,
        "sample_text": sample_text,
        "generated_text": generated_text,
        "warnings": warnings,
    }


def _pick(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def _nested_pick(payload: Any, section: str, key: str) -> Any:
    if not isinstance(payload, dict):
        return None
    nested = payload.get(section)
    if isinstance(nested, dict):
        return nested.get(key)
    return None


def write_dashboard(
    run_dir: str | Path,
    output_path: str | Path | None = None,
    title: str = "MiniGPT experiment dashboard",
) -> dict[str, Any]:
    out_path = Path(output_path) if output_path is not None else Path(run_dir) / "dashboard.html"
    payload = build_dashboard_payload(run_dir, output_path=out_path, title=title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_dashboard_html(payload), encoding="utf-8")
    return payload
