"""Reconcile same-run metrics with a checkpoint's committed byte prefix."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from minigpt.training.checkpoint_io import write_atomically


def _read_history(path: Path) -> bytes:
    return path.read_bytes() if path.exists() else b""


def snapshot_history(path: Path) -> dict[str, Any]:
    """Describe exact bytes, retaining existing JSONL formatting and line endings."""
    data = _read_history(path)
    return {"version": 1, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def recover_history(path: Path, checkpoint: dict[str, Any]) -> Path | None:
    """Archive an uncommitted suffix's original file before atomically restoring its prefix.

    Legacy checkpoints are no-ops. The caller must restrict this to the original
    run directory and single-writer operation; backups are retained evidence.
    """
    if "history_state" not in checkpoint:
        return None
    state = checkpoint["history_state"]
    if not isinstance(state, dict) or type(state.get("version")) is not int or state["version"] != 1:
        raise ValueError("Invalid checkpoint history state version")
    data = _read_history(path)
    size = state.get("size")
    if type(size) is not int or not 0 <= size <= len(data):
        raise ValueError("Checkpoint history prefix size mismatch")
    prefix = data[:size]
    if hashlib.sha256(prefix).hexdigest() != state.get("sha256"):
        raise ValueError("Checkpoint history prefix digest mismatch")
    if len(data) == size:
        return None

    digest = hashlib.sha256(data).hexdigest()[:12]
    backup = path.with_name(f"metrics-{digest}.jsonl")
    if backup.exists():
        if backup.read_bytes() != data:
            raise ValueError("History recovery backup conflict")
    else:
        write_atomically(backup, lambda stream: stream.write(data))
    write_atomically(path, lambda stream: stream.write(prefix))
    return backup
