from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_release_readiness_comparison(root: Path) -> dict[str, Any]:
    candidates = [
        root / "release-readiness-comparison" / "release_readiness_comparison.json",
        root / "release_readiness_comparison.json",
    ]
    for path in candidates:
        payload = _read_json(path)
        if isinstance(payload, dict):
            payload["release_readiness_comparison_path"] = str(path)
            return payload
    return {}


def release_readiness_html_exists(root: Path) -> bool:
    return any(
        path.exists()
        for path in [
            root / "release-readiness-comparison" / "release_readiness_comparison.html",
            root / "release_readiness_comparison.html",
        ]
    )


def release_readiness_comparison_status(summary: dict[str, Any]) -> str | None:
    if not summary:
        return None
    if int(summary.get("test_coverage_regression_count") or 0) > 0:
        return "coverage-regressed"
    if int(summary.get("benchmark_history_regression_count") or 0) > 0:
        return "benchmark-regressed"
    if int(summary.get("ci_workflow_regression_count") or 0) > 0:
        return "ci-regressed"
    if int(summary.get("regressed_count") or 0) > 0:
        return "regressed"
    if int(summary.get("improved_count") or 0) > 0:
        return "improved"
    if int(summary.get("changed_panel_delta_count") or 0) > 0:
        return "panel-changed"
    if int(summary.get("blocked_count") or 0) > 0:
        return "blocked"
    return "stable"


def release_readiness_deltas(report: dict[str, Any]) -> list[dict[str, Any]]:
    deltas = report.get("deltas") if isinstance(report, dict) else None
    return [delta for delta in deltas if isinstance(delta, dict)] if isinstance(deltas, list) else []


def release_readiness_benchmark_requirement_status_change_count(
    deltas: list[dict[str, Any]],
) -> int | None:
    if not deltas:
        return None
    return sum(1 for delta in deltas if bool(delta.get("benchmark_history_readiness_requirement_status_changed")))


def summary_int_or_delta(summary: dict[str, Any], key: str, fallback: int | None) -> int | None:
    direct = _as_int(_pick(summary, key))
    return direct if direct is not None else fallback


def release_readiness_numeric_delta_count(deltas: list[dict[str, Any]], key: str) -> int | None:
    if not deltas:
        return None
    return sum(1 for delta in deltas if _as_optional_float(delta.get(key)) not in {None, 0.0})


def release_readiness_positive_delta_count(deltas: list[dict[str, Any]], key: str) -> int | None:
    if not deltas:
        return None
    return sum(1 for delta in deltas if (_as_optional_float(delta.get(key)) or 0.0) > 0)


def release_readiness_benchmark_requirement_exit_code_delta_max(
    deltas: list[dict[str, Any]],
) -> int | float | None:
    values = [
        abs(value)
        for value in (_as_optional_float(delta.get("benchmark_history_readiness_requirement_exit_code_delta")) for delta in deltas)
        if value is not None
    ]
    return _int_if_whole(max(values)) if values else None


def release_readiness_benchmark_requirement_failed_reason_added_count(
    deltas: list[dict[str, Any]],
) -> int | None:
    if not deltas:
        return None
    return sum(_release_readiness_benchmark_requirement_reason_count(delta, "added") for delta in deltas)


def release_readiness_benchmark_requirement_failed_reason_removed_count(
    deltas: list[dict[str, Any]],
) -> int | None:
    if not deltas:
        return None
    return sum(_release_readiness_benchmark_requirement_reason_count(delta, "removed") for delta in deltas)


def release_readiness_benchmark_requirement_failed_reason_mixed_delta_count(
    deltas: list[dict[str, Any]],
) -> int | None:
    if not deltas:
        return None
    return sum(1 for delta in deltas if _release_readiness_benchmark_requirement_reason_drift_status(delta) == "mixed")


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _release_readiness_benchmark_requirement_reason_count(delta: dict[str, Any], kind: str) -> int:
    key = f"benchmark_history_readiness_requirement_failed_reason_{kind}_count"
    direct = _as_int(delta.get(key))
    if direct is not None:
        return direct
    baseline = delta.get("baseline_benchmark_history_readiness_requirement_failed_reasons")
    compared = delta.get("compared_benchmark_history_readiness_requirement_failed_reasons")
    if kind == "added":
        return len(_reason_additions(baseline, compared))
    return len(_reason_removals(baseline, compared))


def _release_readiness_benchmark_requirement_reason_drift_status(delta: dict[str, Any]) -> str:
    direct = _pick(delta, "benchmark_history_readiness_requirement_failed_reason_drift_status")
    if direct:
        return str(direct)
    added = _release_readiness_benchmark_requirement_reason_count(delta, "added")
    removed = _release_readiness_benchmark_requirement_reason_count(delta, "removed")
    if added and removed:
        return "mixed"
    if added:
        return "regressed"
    if removed:
        return "recovered"
    return "stable"


def _reason_additions(baseline: Any, compared: Any) -> list[str]:
    baseline_reasons = set(_as_str_list(baseline))
    return [reason for reason in _as_str_list(compared) if reason not in baseline_reasons]


def _reason_removals(baseline: Any, compared: Any) -> list[str]:
    compared_reasons = set(_as_str_list(compared))
    return [reason for reason in _as_str_list(baseline) if reason not in compared_reasons]


def _pick(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _as_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_if_whole(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


__all__ = [
    "read_release_readiness_comparison",
    "release_readiness_benchmark_requirement_exit_code_delta_max",
    "release_readiness_benchmark_requirement_failed_reason_added_count",
    "release_readiness_benchmark_requirement_failed_reason_mixed_delta_count",
    "release_readiness_benchmark_requirement_failed_reason_removed_count",
    "release_readiness_benchmark_requirement_status_change_count",
    "release_readiness_comparison_status",
    "release_readiness_deltas",
    "release_readiness_html_exists",
    "release_readiness_numeric_delta_count",
    "release_readiness_positive_delta_count",
    "summary_int_or_delta",
]
