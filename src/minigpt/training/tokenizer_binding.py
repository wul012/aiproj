"""Semantic tokenizer fingerprints for checkpoint pairing."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from minigpt.core.tokenizer import Tokenizer


def tokenizer_digest(tokenizer: Tokenizer) -> str:
    """Hash the ordered token semantics, independent of JSON formatting."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "type": tokenizer.name,
        "itos": list(tokenizer.itos),
        "unk_token": tokenizer.unk_token,
    }
    if tokenizer.name == "bpe":
        payload["merges"] = [list(pair) for pair in tokenizer.merges]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_tokenizer_binding(checkpoint: dict[str, Any], tokenizer: Tokenizer) -> None:
    """Reject a present binding that does not describe the loaded tokenizer."""
    if "tokenizer_sha256" not in checkpoint:
        return
    expected = checkpoint["tokenizer_sha256"]
    actual = tokenizer_digest(tokenizer)
    if not isinstance(expected, str) or expected != actual:
        raise ValueError("Checkpoint tokenizer binding mismatch")
