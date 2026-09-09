"""Publish one checkpoint without truncating the previous successful save."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import torch


def save_checkpoint(checkpoint: dict[str, Any], path: Path) -> None:
    """Serialize beside the target, then replace it after closing the file.

    The parent must exist. This is a single-file operation, not a transaction
    over a training directory or a directory-entry power-loss durability promise.
    """
    pending = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
        ) as stream:
            pending = Path(stream.name)
            torch.save(checkpoint, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, path)
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)
