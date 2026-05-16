from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from minigpt.pair_artifacts import slug as _artifact_slug


@dataclass(frozen=True)
class CheckpointOption:
    id: str
    name: str
    path: str
    exists: bool
    is_default: bool
    tokenizer_path: str | None
    tokenizer_exists: bool
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_health_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    *,
    safety_profile: Any | None = None,
    request_log_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    request_log = Path(request_log_path) if request_log_path is not None else root / "inference_requests.jsonl"
    checkpoints = discover_checkpoint_options(root, checkpoint, checkpoint_candidates=checkpoint_candidates)
    safety = safety_profile.to_dict() if hasattr(safety_profile, "to_dict") else {}
    return {
        "status": "ok",
        "run_dir": str(root),
        "checkpoint": str(checkpoint),
        "checkpoint_exists": checkpoint.exists(),
        "tokenizer_exists": (root / "tokenizer.json").exists(),
        "playground_exists": (root / "playground.html").exists(),
        "sample_lab_exists": (root / "sample_lab" / "sample_lab.json").exists(),
        "model_info_endpoint": "/api/model-info",
        "generate_endpoint": "/api/generate",
        "generate_stream_endpoint": "/api/generate-stream",
        "generate_pair_endpoint": "/api/generate-pair",
        "generate_pair_artifact_endpoint": "/api/generate-pair-artifact",
        "checkpoints_endpoint": "/api/checkpoints",
        "checkpoint_compare_endpoint": "/api/checkpoint-compare",
        "request_history_endpoint": "/api/request-history",
        "request_history_detail_endpoint": "/api/request-history-detail",
        "checkpoint_count": len(checkpoints),
        "default_checkpoint_id": checkpoints[0].id if checkpoints else None,
        "safety": safety,
        "request_log": str(request_log),
        "request_log_exists": request_log.exists(),
    }


def build_model_info_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    checkpoint_id: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else root / "tokenizer.json"
    manifest = _read_json(root / "run_manifest.json")
    train_config = _read_json(root / "train_config.json")
    model_report = _read_json(root / "model_report" / "model_report.json")
    dataset_version = _read_json(root / "dataset_version.json")
    model = _pick_dict(manifest, "model")
    training = _pick_dict(manifest, "training")
    data = _pick_dict(manifest, "data")
    report_config = _pick_dict(model_report, "config")
    config = _pick_dict(model, "config") or report_config
    version_summary = _pick_dict(data, "dataset_version")
    return {
        "status": "ok",
        "run_dir": str(root),
        "checkpoint_id": checkpoint_id,
        "checkpoint": str(checkpoint),
        "checkpoint_exists": checkpoint.exists(),
        "tokenizer_path": str(tokenizer),
        "tokenizer_exists": tokenizer.exists(),
        "tokenizer": _pick(training, "tokenizer") or _pick(train_config, "tokenizer") or _pick(model_report, "tokenizer"),
        "model_config": config or None,
        "parameter_count": _pick(model, "parameter_count") or _pick(model_report, "total_parameters"),
        "data_source": _pick(data, "source"),
        "dataset_version": _pick(version_summary, "id") or _nested_pick(dataset_version, "dataset", "id"),
        "dataset_fingerprint": _pick(version_summary, "short_fingerprint") or _nested_pick(dataset_version, "stats", "short_fingerprint"),
        "git": _pick(manifest, "git"),
        "artifact_count": _artifact_count(manifest),
    }


def discover_checkpoint_options(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    *,
    tokenizer_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> list[CheckpointOption]:
    root = Path(run_dir)
    default_path = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    paths: list[tuple[Path, str]] = [(default_path, "default")]
    if checkpoint_candidates:
        paths.extend((Path(path), "candidate") for path in checkpoint_candidates)
    else:
        paths.extend((path, "run-root") for path in sorted(root.glob("*.pt")))
        checkpoint_dir = root / "checkpoints"
        if checkpoint_dir.exists():
            paths.extend((path, "checkpoints") for path in sorted(checkpoint_dir.glob("*.pt")))
        paths.extend((path, "nested-run") for path in sorted(root.glob("*/checkpoint.pt")))

    options: list[CheckpointOption] = []
    seen: set[str] = set()
    used_ids: set[str] = set()
    default_key = _path_key(default_path)
    for path, source in paths:
        key = _path_key(path)
        if key in seen:
            continue
        seen.add(key)
        is_default = key == default_key
        option_id = _unique_checkpoint_id(_checkpoint_id(root, path, is_default=is_default), used_ids)
        option_tokenizer = Path(tokenizer_path) if tokenizer_path is not None and is_default else path.parent / "tokenizer.json"
        options.append(
            CheckpointOption(
                id=option_id,
                name=path.parent.name if path.name == "checkpoint.pt" and path.parent != root else path.stem,
                path=str(path),
                exists=path.exists(),
                is_default=is_default,
                tokenizer_path=str(option_tokenizer),
                tokenizer_exists=option_tokenizer.exists(),
                source=source,
            )
        )
    options.sort(key=lambda item: (not item.is_default, item.id))
    return options


def build_checkpoints_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> dict[str, Any]:
    options = discover_checkpoint_options(
        run_dir,
        checkpoint_path,
        tokenizer_path=tokenizer_path,
        checkpoint_candidates=checkpoint_candidates,
    )
    return {
        "status": "ok",
        "run_dir": str(Path(run_dir)),
        "default_checkpoint_id": options[0].id if options else None,
        "checkpoint_count": len(options),
        "checkpoints": [option.to_dict() for option in options],
    }


def build_checkpoint_compare_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    options = discover_checkpoint_options(
        root,
        checkpoint_path,
        tokenizer_path=tokenizer_path,
        checkpoint_candidates=checkpoint_candidates,
    )
    rows = [_checkpoint_compare_row(root, option) for option in options]
    baseline = rows[0] if rows else None
    for row in rows:
        _attach_checkpoint_deltas(row, baseline)
    return {
        "status": "ok",
        "run_dir": str(root),
        "default_checkpoint_id": options[0].id if options else None,
        "checkpoint_count": len(rows),
        "summary": {
            "existing_count": sum(1 for row in rows if row["exists"]),
            "missing_count": sum(1 for row in rows if not row["exists"]),
            "tokenizer_ready_count": sum(1 for row in rows if row["tokenizer_exists"]),
            "ready_count": sum(1 for row in rows if row["status"] == "ready"),
        },
        "checkpoints": rows,
    }


def resolve_checkpoint_option(options: list[CheckpointOption], selector: str | None = None) -> CheckpointOption:
    if not options:
        raise ValueError("no checkpoints are configured")
    if selector is None:
        return options[0]
    wanted = selector.strip()
    if not wanted:
        return options[0]
    if wanted.isdigit():
        index = int(wanted) - 1
        if 0 <= index < len(options):
            option = options[index]
            if not option.exists:
                raise ValueError(f"checkpoint does not exist: {option.id}")
            return option
    for option in options:
        if wanted in {option.id, option.name, option.path, Path(option.path).name}:
            if not option.exists:
                raise ValueError(f"checkpoint does not exist: {option.id}")
            return option
    raise ValueError(f"checkpoint selector did not match an allowed checkpoint: {selector}")


def metadata_run_dir(root: Path, option: CheckpointOption) -> Path:
    checkpoint_parent = Path(option.path).parent
    metadata_files = ("run_manifest.json", "train_config.json", "dataset_version.json")
    if checkpoint_parent != root and any((checkpoint_parent / name).exists() for name in metadata_files):
        return checkpoint_parent
    return root


def _path_key(path: str | Path) -> str:
    return str(Path(path).resolve()).casefold()


def _checkpoint_id(root: Path, path: Path, *, is_default: bool) -> str:
    if is_default:
        return "default"
    try:
        relative = path.resolve().relative_to(root.resolve())
        if relative.name == "checkpoint.pt" and len(relative.parts) > 1:
            return _slug(relative.parts[-2])
        return _slug(relative.with_suffix("").as_posix())
    except ValueError:
        if path.name == "checkpoint.pt" and path.parent.name:
            return _slug(path.parent.name)
        return _slug(path.stem)


def _unique_checkpoint_id(base: str, used: set[str]) -> str:
    candidate = base or "checkpoint"
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _slug(value: Any) -> str:
    return _artifact_slug(value)


def _checkpoint_compare_row(root: Path, option: CheckpointOption) -> dict[str, Any]:
    checkpoint_path = Path(option.path)
    size_bytes: int | None = None
    modified_utc: str | None = None
    if checkpoint_path.exists() and checkpoint_path.is_file():
        stat = checkpoint_path.stat()
        modified_utc = datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        size_bytes = stat.st_size
    metadata_root = metadata_run_dir(root, option)
    info = build_model_info_payload(metadata_root, checkpoint_path, option.tokenizer_path, option.id)
    notes: list[str] = []
    if not option.exists:
        notes.append("checkpoint missing")
    if not option.tokenizer_exists:
        notes.append("tokenizer missing")
    if info.get("model_config") is None:
        notes.append("model config missing")
    if info.get("dataset_version") is None:
        notes.append("dataset version missing")
    status = "ready" if option.exists and option.tokenizer_exists else "incomplete"
    return {
        **option.to_dict(),
        "status": status,
        "size_bytes": size_bytes,
        "modified_utc": modified_utc,
        "metadata_run_dir": str(metadata_root),
        "model_info_endpoint": f"/api/model-info?checkpoint={option.id}",
        "tokenizer": info.get("tokenizer"),
        "parameter_count": info.get("parameter_count"),
        "dataset_version": info.get("dataset_version"),
        "dataset_fingerprint": info.get("dataset_fingerprint"),
        "model_config": info.get("model_config"),
        "artifact_count": info.get("artifact_count"),
        "notes": notes,
    }


def _attach_checkpoint_deltas(row: dict[str, Any], baseline: dict[str, Any] | None) -> None:
    if baseline is None:
        row["size_delta_bytes"] = None
        row["parameter_delta"] = None
        row["same_tokenizer"] = None
        row["same_dataset_version"] = None
        row["same_dataset_fingerprint"] = None
        row["same_model_config"] = None
        return
    row["size_delta_bytes"] = _numeric_delta(row.get("size_bytes"), baseline.get("size_bytes"))
    row["parameter_delta"] = _numeric_delta(row.get("parameter_count"), baseline.get("parameter_count"))
    row["same_tokenizer"] = _same_known(row.get("tokenizer"), baseline.get("tokenizer"))
    row["same_dataset_version"] = _same_known(row.get("dataset_version"), baseline.get("dataset_version"))
    row["same_dataset_fingerprint"] = _same_known(row.get("dataset_fingerprint"), baseline.get("dataset_fingerprint"))
    row["same_model_config"] = _same_known(row.get("model_config"), baseline.get("model_config"))


def _numeric_delta(value: Any, baseline: Any) -> int | float | None:
    if isinstance(value, (int, float)) and isinstance(baseline, (int, float)):
        return value - baseline
    return None


def _same_known(value: Any, baseline: Any) -> bool | None:
    if value is None or baseline is None:
        return None
    return value == baseline


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _pick(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    value = _pick(payload, key)
    return value if isinstance(value, dict) else {}


def _nested_pick(payload: Any, *keys: str) -> Any:
    value = payload
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _artifact_count(manifest: Any) -> int | None:
    artifacts = _pick(manifest, "artifacts")
    if not isinstance(artifacts, list):
        return None
    return sum(1 for item in artifacts if isinstance(item, dict) and item.get("exists"))


__all__ = [
    "CheckpointOption",
    "build_checkpoint_compare_payload",
    "build_checkpoints_payload",
    "build_health_payload",
    "build_model_info_payload",
    "discover_checkpoint_options",
    "metadata_run_dir",
    "resolve_checkpoint_option",
]
