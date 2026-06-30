"""Compatibility exports for serving POST route handling."""

from __future__ import annotations

from minigpt.server_post_routes import (
    handle_generate_pair_request,
    handle_generate_request,
    handle_generate_stream_request,
    handle_post_request,
)

__all__ = [
    "handle_generate_pair_request",
    "handle_generate_request",
    "handle_generate_stream_request",
    "handle_post_request",
]

