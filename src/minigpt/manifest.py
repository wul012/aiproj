from __future__ import annotations

from datetime import datetime
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
from typing import Any

from minigpt.report_utils import html_escape as _e, utc_now, write_json_payload


RUN_ARTIFACT_SPECS = [
    ("checkpoint", "checkpoint.pt", "model and optimizer state"),
    ("tokenizer", "tokenizer.json", "tokenizer vocabulary and metadata"),
    ("train_config", "train_config.json", "training command configuration"),
    ("metrics", "metrics.jsonl", "step-by-step training metrics"),
    ("history_summary", "history_summary.json", "best/latest loss summary"),
    ("loss_curve", "loss_curve.svg", "loss curve chart"),
    ("prepared_corpus", "prepared_corpus.txt", "merged training corpus"),
    ("dataset_report", "dataset_report.json", "dataset source statistics"),
    ("dataset_chart", "dataset_report.svg", "dataset source chart"),
    ("dataset_quality", "dataset_quality.json", "dataset quality report"),
    ("dataset_quality_chart", "dataset_quality.svg", "dataset quality chart"),
    ("dataset_version", "dataset_version.json", "dataset version manifest"),
    ("dataset_version_html", "dataset_version.html", "browser dataset version report"),
    ("sample", "sample.txt", "post-training sample"),
    ("eval_report", "eval_report.json", "checkpoint evaluation report"),
    ("eval_suite", "eval_suite/eval_suite.json", "fixed prompt evaluation suite"),
    ("eval_suite_csv", "eval_suite/eval_suite.csv", "fixed prompt evaluation table"),
    ("eval_suite_chart", "eval_suite/eval_suite.svg", "fixed prompt evaluation chart"),
    ("eval_suite_html", "eval_suite/eval_suite.html", "browser benchmark evaluation report"),
    ("model_report", "model_report/model_report.json", "model architecture report"),
    ("model_chart", "model_report/model_architecture.svg", "model architecture chart"),
    ("prediction_report", "predictions/predictions.json", "next-token prediction report"),
    ("prediction_chart", "predictions/predictions.svg", "next-token prediction chart"),
    ("attention_report", "attention/attention.json", "attention inspection report"),
    ("attention_chart", "attention/attention.svg", "attention heatmap"),
    ("transcript", "transcript.json", "chat transcript"),
    ("generated", "generated.txt", "standalone generation output"),
    ("experiment_card_json", "experiment_card.json", "machine-readable experiment card"),
    ("experiment_card_md", "experiment_card.md", "markdown experiment card"),
    ("experiment_card_html", "experiment_card.html", "browser experiment card"),
    ("dashboard", "dashboard.html", "static dashboard"),
    ("playground", "playground.html", "static playground"),
]


def build_run_manifest(
    run_dir: str | Path,
    *,
    args: dict[str, Any],
    data_source: dict[str, Any],
    model_config: dict[str, Any],
    tokenizer_name: str,
    token_count: int,
    train_token_count: int,
    val_token_count: int,
    parameter_count: int,
    device_used: str,
    started_at: str,
    finished_at: str,
    start_step: int,
    end_step: int,
    last_loss: float | None,
    history_summary: dict[str, Any] | None = None,
    command: list[str] | None = None,
    repo_root: str | Path | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    dataset_report = _read_json(root / "dataset_report.json")
    dataset_quality = _read_json(root / "dataset_quality.json")
    dataset_version = _read_json(root / "dataset_version.json")
    return {
        "schema_version": 1,
        "run_dir": str(root),
        "created_at": finished_at,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": _duration_seconds(started_at, finished_at),
        "command": list(command or []),
        "git": collect_git_metadata(repo_root or Path.cwd()),
        "environment": environment or build_environment_metadata(),
        "data": {
            "source": _jsonable(data_source),
            "token_count": token_count,
            "train_token_count": train_token_count,
            "val_token_count": val_token_count,
            "dataset_report": _dataset_report_summary(dataset_report),
            "dataset_quality": _dataset_quality_summary(dataset_quality),
            "dataset_version": _dataset_version_summary(dataset_version),
        },
        "model": {
            "config": _jsonable(model_config),
            "parameter_count": parameter_count,
        },
        "training": {
            "args": _jsonable(args),
            "tokenizer": tokenizer_name,
            "device_used": device_used,
            "start_step": start_step,
            "end_step": end_step,
        },
        "results": {
            "last_loss": last_loss,
            "history_summary": _jsonable(history_summary or {}),
        },
        "artifacts": collect_run_artifacts(root),
    }


def build_environment_metadata(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": sys.executable,
    }
    if extra:
        payload.update(_jsonable(extra))
    return payload


def collect_git_metadata(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root)
    commit = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    tag = _git(root, "describe", "--tags", "--exact-match")
    status = _git(root, "status", "--short")
    return {
        "commit": commit,
        "short_commit": None if commit is None else commit[:7],
        "branch": branch,
        "tag": tag,
        "dirty": None if status is None else bool(status.strip()),
    }


def collect_run_artifacts(run_dir: str | Path, max_digest_bytes: int = 20 * 1024 * 1024) -> list[dict[str, Any]]:
    root = Path(run_dir)
    artifacts = []
    for key, relative, description in RUN_ARTIFACT_SPECS:
        path = root / relative
        exists = path.exists()
        size = path.stat().st_size if exists and path.is_file() else None
        artifacts.append(
            {
                "key": key,
                "path": relative,
                "description": description,
                "exists": exists,
                "size_bytes": size,
                "sha256": sha256_file(path, max_digest_bytes=max_digest_bytes) if exists and path.is_file() else None,
            }
        )
    return artifacts


def sha256_file(path: str | Path, max_digest_bytes: int = 20 * 1024 * 1024) -> str | None:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None
    if file_path.stat().st_size > max_digest_bytes:
        return None
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_run_manifest_json(manifest: dict[str, Any], path: str | Path) -> None:
    write_json_payload(manifest, path)


def write_run_manifest_svg(manifest: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    artifacts = [item for item in manifest.get("artifacts", []) if isinstance(item, dict) and item.get("exists")]
    rows = []
    for index, artifact in enumerate(artifacts[:10]):
        y = 210 + index * 30
        rows.append(
            f'<text x="40" y="{y}" font-family="Arial" font-size="13" fill="#111827">'
            f'{_e(artifact.get("key"))} - {_fmt_bytes(artifact.get("size_bytes"))}</text>'
        )
    git = manifest.get("git", {})
    data = manifest.get("data", {})
    model = manifest.get("model", {})
    results = manifest.get("results", {})
    summary = [
        ("Run", manifest.get("run_dir")),
        ("Git", _pick(git, "short_commit") or "unknown"),
        ("Dirty", _pick(git, "dirty")),
        ("Tokens", _pick(data, "token_count")),
        ("Parameters", _pick(model, "parameter_count")),
        ("Best val", _pick(_pick(results, "history_summary"), "best_val_loss")),
        ("Artifacts", len(artifacts)),
        ("Duration", f"{manifest.get('duration_seconds')}s"),
    ]
    cards = []
    for index, (label, value) in enumerate(summary):
        col = index % 4
        row = index // 4
        x = 40 + col * 225
        y = 82 + row * 66
        cards.append(f'<rect x="{x}" y="{y}" width="200" height="48" rx="8" fill="#ffffff" stroke="#d1d5db"/>')
        cards.append(f'<text x="{x + 12}" y="{y + 18}" font-family="Arial" font-size="11" fill="#6b7280">{_e(label)}</text>')
        cards.append(f'<text x="{x + 12}" y="{y + 38}" font-family="Arial" font-size="15" fill="#111827">{_e(_clip(value, 22))}</text>')
    height = 250 + max(1, min(len(artifacts), 10)) * 30
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="980" height="{height}" viewBox="0 0 980 {height}">
  <rect width="100%" height="100%" fill="#f7f7f2"/>
  <text x="40" y="42" font-family="Arial" font-size="22" fill="#111827">MiniGPT run manifest</text>
  <text x="40" y="64" font-family="Arial" font-size="13" fill="#4b5563">Reproducibility snapshot for training data, code, config, metrics, and artifacts.</text>
  {''.join(cards)}
  <text x="40" y="184" font-family="Arial" font-size="16" fill="#111827">Available artifacts</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _dataset_report_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        "source_count": report.get("source_count"),
        "char_count": report.get("char_count"),
        "line_count": report.get("line_count"),
        "unique_char_count": report.get("unique_char_count"),
        "output_text": report.get("output_text"),
    }


def _dataset_quality_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        "status": report.get("status"),
        "fingerprint": report.get("fingerprint"),
        "short_fingerprint": report.get("short_fingerprint"),
        "issue_count": report.get("issue_count"),
        "warning_count": report.get("warning_count"),
        "duplicate_line_count": report.get("duplicate_line_count"),
    }


def _dataset_version_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(report, dict):
        return None
    dataset = _pick(report, "dataset")
    stats = _pick(report, "stats")
    quality = _pick(report, "quality")
    return {
        "id": _pick(dataset, "id"),
        "name": _pick(dataset, "name"),
        "version": _pick(dataset, "version"),
        "short_fingerprint": _pick(stats, "short_fingerprint"),
        "source_count": _pick(stats, "source_count"),
        "char_count": _pick(stats, "char_count"),
        "quality_status": _pick(quality, "status"),
    }


def _duration_seconds(started_at: str, finished_at: str) -> float | None:
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        finish = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((finish - start).total_seconds(), 3)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


def _pick(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _fmt_bytes(value: Any) -> str:
    if not isinstance(value, int):
        return "missing"
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."
