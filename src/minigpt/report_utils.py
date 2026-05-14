from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any, Iterable


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json_payload(payload: Any, path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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


def count_available_artifacts(rows: Iterable[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("exists"))


def as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


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
