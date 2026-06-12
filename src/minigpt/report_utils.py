from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any, Iterable


CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON = "archived_path_portability_check_not_ready"
CI_BOUNDARY_PLAN_CHECK_READY_REGRESSION_REASON = "boundary_gate_plan_check_not_ready"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def write_json_payload(payload: Any, path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def locate_upstream_report(path: str | Path, default_name: str) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / default_name
    return source


def read_json_object(path: str | Path, *, description: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must be a JSON object")
    return dict(payload)


def write_csv_row(row: dict[str, Any], path: str | Path, fieldnames: list[str]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def csv_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def make_artifact_row(key: str, path: str | Path, *, exists: bool | None = None, count: int | None = None) -> dict[str, Any]:
    item_path = Path(path)
    present = item_path.exists() if exists is None else bool(exists)
    resolved_count = (1 if present else 0) if count is None else int(count)
    return {"key": str(key), "path": str(item_path), "exists": present, "count": resolved_count}


def make_artifact_rows(items: Iterable[tuple[str, str | Path]]) -> list[dict[str, Any]]:
    return [make_artifact_row(key, path) for key, path in items]


def archived_reference_path(value: Any) -> Path:
    """Resolve archived artifact refs written on Windows or POSIX runners."""
    return Path(str(value).replace("\\", "/"))


def resolve_archived_reference_path(value: Any, base_dir: str | Path | None = None) -> Path | None:
    if not value:
        return None
    candidate = archived_reference_path(value)
    if candidate.is_file() or candidate.is_absolute() or base_dir is None:
        return candidate
    base = Path(base_dir)
    for anchor in (base, *base.parents):
        based = anchor / candidate
        if based.is_file():
            return based
    return candidate


def count_available_artifacts(rows: Iterable[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("exists"))


def as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def positive_int_mapping(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw_count in value.items():
        name = str(key).strip()
        count = int(number_or_default(raw_count, 0, int))
        if name and count > 0:
            result[name] = count
    return dict(sorted(result.items()))


def ci_regression_reason_count(reason: str, *values: Any) -> int:
    reason_name = str(reason).strip()
    if not reason_name:
        return 0
    for value in values:
        count = positive_int_mapping(value).get(reason_name)
        if count is not None:
            return count
    return 0


def ci_boundary_plan_check_ready_regression_count(*values: Any) -> int:
    for value in values:
        count = _int_count_or_none(value)
        if count is not None:
            return max(0, count)
    return ci_regression_reason_count(CI_BOUNDARY_PLAN_CHECK_READY_REGRESSION_REASON, *values)


def format_mapping(value: Any) -> str:
    counts = as_dict(value)
    if not counts:
        return "none"
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def list_of_strs(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def number_or_none(value: Any, number_type: type[int] | type[float] = float) -> int | float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return number_type(value)
    except (TypeError, ValueError):
        return None


def number_or_default(value: Any, default: int | float = 0, number_type: type[int] | type[float] = float) -> int | float:
    number = number_or_none(value, number_type)
    return default if number is None else number


def display_command(value: Any) -> str:
    if not isinstance(value, list):
        return "" if value is None else str(value)
    return " ".join(_quote_command_part(str(part)) for part in value)


def markdown_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def html_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _quote_command_part(part: str) -> str:
    if not part:
        return '""'
    if any(char.isspace() for char in part) or '"' in part:
        return '"' + part.replace('"', '\\"') + '"'
    return part


def _int_count_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or isinstance(value, (dict, list, tuple)) or value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
