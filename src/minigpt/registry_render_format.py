from __future__ import annotations

import html
from typing import Any

from minigpt.registry_data import _as_optional_float


def fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def fmt_delta(value: Any) -> str:
    number = _as_optional_float(value)
    if number is None:
        return "delta missing"
    return f"{number:+.5g}"


def fmt_int(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{int(value):,}"


def rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def sort_number(value: Any) -> str:
    if value is None:
        return ""
    return str(float(value))


def csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return value


def escape_html(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


__all__ = [
    "csv_value",
    "escape_html",
    "fmt",
    "fmt_delta",
    "fmt_int",
    "rank_label",
    "sort_number",
]
