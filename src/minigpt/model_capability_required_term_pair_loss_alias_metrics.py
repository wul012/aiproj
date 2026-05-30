from __future__ import annotations

from typing import Any


def normalize_for_required_term(value: Any) -> str:
    return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())


def remove_newline_separators(value: Any) -> str:
    return str(value or "").replace("\r", "").replace("\n", "")


def required_term_hit_metrics(continuation: Any, expected: Any, *, strict_hit: bool) -> dict[str, Any]:
    newline_cleanup_continuation = remove_newline_separators(continuation).casefold()
    newline_cleanup_expected = remove_newline_separators(expected).casefold()
    newline_cleanup_hit = bool(newline_cleanup_expected and newline_cleanup_expected in newline_cleanup_continuation)
    normalized_continuation = normalize_for_required_term(continuation)
    normalized_expected = normalize_for_required_term(expected)
    normalized_hit = bool(normalized_expected and normalized_expected in normalized_continuation)
    return {
        "strict_hit": bool(strict_hit),
        "newline_cleanup_hit": newline_cleanup_hit,
        "newline_cleanup_gain": newline_cleanup_hit and not strict_hit,
        "newline_cleanup_continuation": newline_cleanup_continuation,
        "normalized_hit": normalized_hit,
        "normalization_gain": normalized_hit and not strict_hit,
        "normalized_continuation": normalized_continuation,
    }
