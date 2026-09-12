"""Optional checkpoint identity for loaded training text and its split."""

from __future__ import annotations

import hashlib
from typing import Any


def build_data_binding(text: str, train_ratio: float) -> dict[str, Any]:
    """Build a stable identity from content, not the source path."""
    return {
        "version": 1,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text_length": len(text),
        "train_ratio": train_ratio,
    }


def validate_data_binding(checkpoint: dict[str, Any], text: str, train_ratio: float) -> None:
    """Reject a present binding that describes different training inputs."""
    if "data_binding" not in checkpoint:
        return
    expected = checkpoint["data_binding"]
    if not isinstance(expected, dict) or type(expected.get("version")) is not int or expected["version"] != 1:
        raise ValueError("Unsupported checkpoint data binding version")
    length = expected.get("text_length")
    ratio = expected.get("train_ratio")
    if type(length) is not int or length < 0:
        raise ValueError("Invalid checkpoint data binding text length")
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not 0 < ratio < 1:
        raise ValueError("Invalid checkpoint data binding train ratio")
    if expected != build_data_binding(text, train_ratio):
        raise ValueError("Checkpoint data binding mismatch")
