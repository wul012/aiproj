"""Compatibility exports for serving log event builders."""

from __future__ import annotations

from minigpt.server_logging import build_generation_log_event, build_pair_generation_log_event

__all__ = ["build_generation_log_event", "build_pair_generation_log_event"]

