from __future__ import annotations

from typing import Any

from minigpt.report_utils import string_list as _string_list


LOW_RISK_MAINTENANCE_CATEGORIES = {
    "report-utils",
    "utils-migration",
    "docs-only",
    "test-helper",
}

HIGH_RISK_FLAGS = {
    "behavior_change": "behavior changes should keep a focused version boundary",
    "schema_change": "schema or output contract changes should be reviewed independently",
    "service_change": "service/API changes should not hide inside a maintenance batch",
    "ui_change": "visible UI changes need their own evidence path",
    "large_module": "large modules should be split only after a scoped plan",
    "unclear_boundary": "unclear ownership needs review before batching",
}


def category_groups(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for item in items:
        grouped.setdefault(str(item.get("category") or "unknown"), []).append(str(item.get("name")))
    return [{"category": category, "count": len(names), "items": names} for category, names in sorted(grouped.items())]


def category(item: dict[str, Any], fallback_text: str) -> str:
    value = str(item.get("category") or "").strip().lower()
    if value:
        return value.replace("_", "-")
    text = fallback_text.lower().replace("_", "-")
    if "report-utils" in text or ("report" in text and "util" in text):
        return "report-utils"
    if "utils" in text and "migration" in text:
        return "utils-migration"
    if "doc" in text:
        return "docs-only"
    return "feature"


def modules(item: dict[str, Any]) -> list[str]:
    values = item.get("modules")
    if isinstance(values, list):
        return [str(value) for value in values if str(value).strip()]
    if item.get("module"):
        return [str(item.get("module"))]
    return []


def risk_flags(item: dict[str, Any]) -> list[str]:
    flags = [flag.strip().lower().replace("-", "_") for flag in _string_list(item.get("risk_flags")) if flag.strip()]
    return sorted(set(flags))


def unique_strings(values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in result:
            result.append(text)
    return result


def allowed_text(value: Any, allowed: set[str], fallback: str) -> str:
    normalized = str(value or "").strip().lower().replace("_", "-")
    return normalized if normalized in allowed else fallback


def is_low_risk_utils(category_name: str, title: str) -> bool:
    if category_name in LOW_RISK_MAINTENANCE_CATEGORIES:
        return True
    text = title.lower().replace("_", "-")
    return "utils migration" in text or "report-utils" in text or "report utility migration" in text


__all__ = [
    "HIGH_RISK_FLAGS",
    "LOW_RISK_MAINTENANCE_CATEGORIES",
    "allowed_text",
    "category",
    "category_groups",
    "is_low_risk_utils",
    "modules",
    "risk_flags",
    "unique_strings",
]
