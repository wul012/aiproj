from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs


REQUEST_HISTORY_DEFAULT_LIMIT = 20
REQUEST_HISTORY_MAX_LIMIT = 200
REQUEST_HISTORY_CSV_COLUMNS = [
    "log_index",
    "timestamp",
    "endpoint",
    "status",
    "checkpoint_id",
    "requested_checkpoint",
    "left_checkpoint_id",
    "right_checkpoint_id",
    "requested_left_checkpoint",
    "requested_right_checkpoint",
    "prompt_chars",
    "max_new_tokens",
    "temperature",
    "top_k",
    "seed",
    "generated_chars",
    "continuation_chars",
    "left_generated_chars",
    "right_generated_chars",
    "generated_equal",
    "continuation_equal",
    "stream_chunks",
    "stream_timed_out",
    "stream_cancelled",
    "stream_elapsed_seconds",
    "artifact_json",
    "artifact_html",
    "error",
]


def append_inference_log(path: str | Path, event: dict[str, Any]) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": _utc_now(), **event}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def build_request_history_payload(
    request_log_path: str | Path,
    limit: int = REQUEST_HISTORY_DEFAULT_LIMIT,
    *,
    status_filter: str | None = None,
    endpoint_filter: str | None = None,
    checkpoint_filter: str | None = None,
) -> dict[str, Any]:
    history_limit = request_history_limit(limit)
    log_path = Path(request_log_path)
    normalized_records, invalid_count = read_request_history_log_records(log_path)
    filtered_records = filter_request_history_records(
        normalized_records,
        status_filter=status_filter,
        endpoint_filter=endpoint_filter,
        checkpoint_filter=checkpoint_filter,
    )
    requests = filtered_records[-history_limit:][::-1]
    status_counts = count_values(requests, "status")
    endpoint_counts = count_values(requests, "endpoint")
    return {
        "status": "ok",
        "request_log": str(log_path),
        "request_log_exists": log_path.exists(),
        "limit": history_limit,
        "newest_first": True,
        "total_log_records": len(normalized_records),
        "matching_log_records": len(filtered_records),
        "invalid_record_count": invalid_count,
        "record_count": len(requests),
        "filters": {
            "status": status_filter,
            "endpoint": endpoint_filter,
            "checkpoint": checkpoint_filter,
        },
        "summary": {
            "total_log_records": len(normalized_records),
            "matching_records": len(filtered_records),
            "returned_records": len(requests),
            "invalid_record_count": invalid_count,
            "latest_timestamp": requests[0].get("timestamp") if requests else None,
            "ok_count": status_counts.get("ok", 0),
            "timeout_count": status_counts.get("timeout", 0),
            "cancelled_count": status_counts.get("cancelled", 0),
            "error_count": status_counts.get("error", 0),
            "bad_request_count": status_counts.get("bad_request", 0),
            "returned_status_counts": status_counts,
            "returned_endpoint_counts": endpoint_counts,
        },
        "requests": requests,
    }


def read_request_history_log_records(request_log_path: str | Path) -> tuple[list[dict[str, Any]], int]:
    entries, invalid_count = read_inference_log_entries(Path(request_log_path))
    return [request_history_record(record, log_index=log_index) for log_index, record in entries], invalid_count


def build_request_history_detail_payload(request_log_path: str | Path, log_index: int) -> dict[str, Any]:
    wanted_index = request_history_log_index(log_index)
    log_path = Path(request_log_path)
    entries, invalid_count = read_inference_log_entries(log_path)
    for current_index, record in entries:
        if current_index == wanted_index:
            return {
                "status": "ok",
                "request_log": str(log_path),
                "request_log_exists": log_path.exists(),
                "log_index": current_index,
                "total_log_records": len(entries),
                "invalid_record_count": invalid_count,
                "normalized": request_history_record(record, log_index=current_index),
                "record": record,
            }
    raise LookupError(f"request history record not found: log_index={wanted_index}")


def request_history_to_csv(records: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=REQUEST_HISTORY_CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow({column: csv_value(record.get(column)) for column in REQUEST_HISTORY_CSV_COLUMNS})
    return output.getvalue()


def request_history_limit(value: int) -> int:
    if value < 1 or value > REQUEST_HISTORY_MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {REQUEST_HISTORY_MAX_LIMIT}")
    return value


def request_history_limit_from_query(query: str) -> int:
    raw = query_value(query, "limit")
    if raw is None:
        return REQUEST_HISTORY_DEFAULT_LIMIT
    return request_history_limit(as_int(raw, "limit"))


def request_history_log_index(value: int) -> int:
    if value < 1:
        raise ValueError("log_index must be at least 1")
    return value


def request_history_log_index_from_query(query: str) -> int:
    raw = query_value(query, "log_index")
    if raw is None:
        raise ValueError("log_index is required")
    return request_history_log_index(as_int(raw, "log_index"))


def request_history_filters_from_query(query: str) -> dict[str, str | None]:
    return {
        "status_filter": clean_query_filter(query_value(query, "status")),
        "endpoint_filter": clean_query_filter(query_value(query, "endpoint")),
        "checkpoint_filter": clean_query_filter(query_value(query, "checkpoint")),
    }


def query_value(query: str, key: str) -> str | None:
    values = parse_qs(query).get(key)
    if not values:
        return None
    return values[0]


def clean_query_filter(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text.lower() in {"all", "*"}:
        return None
    return text


def read_inference_log_records(path: str | Path) -> tuple[list[dict[str, Any]], int]:
    entries, invalid_count = read_inference_log_entries(Path(path))
    return [record for _, record in entries], invalid_count


def read_inference_log_entries(path: Path) -> tuple[list[tuple[int, dict[str, Any]]], int]:
    if not path.exists():
        return [], 0
    records: list[tuple[int, dict[str, Any]]] = []
    invalid_count = 0
    for log_index, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            invalid_count += 1
            continue
        if isinstance(payload, dict):
            records.append((log_index, payload))
        else:
            invalid_count += 1
    return records, invalid_count


def filter_request_history_records(
    records: list[dict[str, Any]],
    *,
    status_filter: str | None = None,
    endpoint_filter: str | None = None,
    checkpoint_filter: str | None = None,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    status_wanted = status_filter.casefold() if status_filter is not None else None
    endpoint_wanted = endpoint_filter.casefold() if endpoint_filter is not None else None
    checkpoint_wanted = checkpoint_filter.casefold() if checkpoint_filter is not None else None
    for record in records:
        if status_wanted is not None and str(record.get("status", "")).casefold() != status_wanted:
            continue
        if endpoint_wanted is not None and str(record.get("endpoint", "")).casefold() != endpoint_wanted:
            continue
        if checkpoint_wanted is not None and not request_history_record_matches_checkpoint(record, checkpoint_wanted):
            continue
        filtered.append(record)
    return filtered


def request_history_record_matches_checkpoint(record: dict[str, Any], wanted: str) -> bool:
    fields = [
        "checkpoint_id",
        "requested_checkpoint",
        "left_checkpoint_id",
        "right_checkpoint_id",
        "requested_left_checkpoint",
        "requested_right_checkpoint",
    ]
    return any(str(record.get(field, "")).casefold() == wanted for field in fields)


def request_history_record(record: dict[str, Any], log_index: int | None = None) -> dict[str, Any]:
    fields = [
        "timestamp",
        "endpoint",
        "status",
        "client",
        "checkpoint",
        "checkpoint_id",
        "requested_checkpoint",
        "left_checkpoint",
        "left_checkpoint_id",
        "right_checkpoint",
        "right_checkpoint_id",
        "requested_left_checkpoint",
        "requested_right_checkpoint",
        "prompt_chars",
        "max_new_tokens",
        "temperature",
        "top_k",
        "seed",
        "generated_chars",
        "continuation_chars",
        "left_generated_chars",
        "left_continuation_chars",
        "right_generated_chars",
        "right_continuation_chars",
        "generated_equal",
        "continuation_equal",
        "tokenizer",
        "stream_chunks",
        "stream_timed_out",
        "stream_cancelled",
        "stream_elapsed_seconds",
        "artifact_json",
        "artifact_html",
        "error",
    ]
    normalized = {field: record.get(field) for field in fields if field in record}
    if log_index is not None:
        return {"log_index": log_index, **normalized}
    return normalized


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def count_values(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record.get(key)
        if value is None:
            continue
        label = str(value)
        counts[label] = counts.get(label, 0) + 1
    return counts


def as_int(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
