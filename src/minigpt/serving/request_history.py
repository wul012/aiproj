"""Compatibility exports for serving request-history endpoints."""

from __future__ import annotations

from minigpt.server_request_history import (
    handle_request_history_detail_endpoint,
    handle_request_history_endpoint,
)

__all__ = [
    "handle_request_history_detail_endpoint",
    "handle_request_history_endpoint",
]

