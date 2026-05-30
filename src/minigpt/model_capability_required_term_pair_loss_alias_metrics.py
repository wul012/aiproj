from __future__ import annotations

from typing import Any


def normalize_for_required_term(value: Any) -> str:
    return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())


def required_term_hit_metrics(continuation: Any, expected: Any, *, strict_hit: bool) -> dict[str, Any]:
    normalized_continuation = normalize_for_required_term(continuation)
    normalized_expected = normalize_for_required_term(expected)
    normalized_hit = bool(normalized_expected and normalized_expected in normalized_continuation)
    return {
        "strict_hit": bool(strict_hit),
        "normalized_hit": normalized_hit,
        "normalization_gain": normalized_hit and not strict_hit,
        "normalized_continuation": normalized_continuation,
    }
