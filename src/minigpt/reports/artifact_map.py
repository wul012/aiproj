"""Compatibility exports for versioned artifact map reports."""

from __future__ import annotations

from minigpt.artifact_map import (
    DEFAULT_LIMIT,
    build_artifact_map_report,
    resolve_exit_code,
    write_artifact_map_outputs,
)

__all__ = [
    "DEFAULT_LIMIT",
    "build_artifact_map_report",
    "write_artifact_map_outputs",
    "resolve_exit_code",
]
