from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any

from minigpt.request_history import (
    build_request_history_detail_payload,
    build_request_history_payload,
    query_value,
    request_history_filters_from_query,
    request_history_limit_from_query,
    request_history_log_index_from_query,
    request_history_to_csv,
)


def handle_request_history_endpoint(handler: Any, request_log: str | Path, query: str) -> None:
    try:
        history_limit = request_history_limit_from_query(query)
        history_filters = request_history_filters_from_query(query)
    except ValueError as exc:
        handler._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        return
    payload = build_request_history_payload(request_log, limit=history_limit, **history_filters)
    if query_value(query, "format") == "csv":
        handler._send_text(
            request_history_to_csv(payload["requests"]),
            content_type="text/csv; charset=utf-8",
            filename="request_history.csv",
        )
        return
    handler._send_json(payload)


def handle_request_history_detail_endpoint(handler: Any, request_log: str | Path, query: str) -> None:
    try:
        log_index = request_history_log_index_from_query(query)
        payload = build_request_history_detail_payload(request_log, log_index)
    except ValueError as exc:
        handler._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        return
    except LookupError as exc:
        handler._send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
        return
    handler._send_json(payload)


__all__ = [
    "handle_request_history_detail_endpoint",
    "handle_request_history_endpoint",
]
