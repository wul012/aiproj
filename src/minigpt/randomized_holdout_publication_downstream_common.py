from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_BLOCKED_USES,
    RANDOMIZED_HOLDOUT_PUBLICATION_DOWNSTREAM_LOOKUP_USE,
)


def downstream_lookup_use() -> str:
    return RANDOMIZED_HOLDOUT_PUBLICATION_DOWNSTREAM_LOOKUP_USE


def blocked_uses() -> list[str]:
    return list(RANDOMIZED_HOLDOUT_PUBLICATION_BLOCKED_USES)


def blocked_uses_complete(value: Any) -> bool:
    values = list(value or []) if isinstance(value, list) else []
    return all(use in values for use in RANDOMIZED_HOLDOUT_PUBLICATION_BLOCKED_USES)


def is_downstream_lookup_only(value: Any) -> bool:
    return value == RANDOMIZED_HOLDOUT_PUBLICATION_DOWNSTREAM_LOOKUP_USE


def is_sha256(value: Any) -> bool:
    digest = str(value or "")
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def sha256_file(path: Any) -> str:
    if not path or not Path(str(path)).is_file():
        return ""
    return sha256(Path(str(path)).read_bytes()).hexdigest()


__all__ = [
    "blocked_uses",
    "blocked_uses_complete",
    "downstream_lookup_use",
    "is_downstream_lookup_only",
    "is_sha256",
    "sha256_file",
]
