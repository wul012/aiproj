"""Compatibility exports for run registry governance reports."""

from __future__ import annotations

from minigpt.registry import (
    REGISTRY_ARTIFACT_PATHS,
    RegisteredRun,
    build_run_registry,
    discover_run_dirs,
    render_registry_html,
    summarize_registered_run,
    write_registry_csv,
    write_registry_html,
    write_registry_json,
    write_registry_outputs,
    write_registry_svg,
)

__all__ = [
    "REGISTRY_ARTIFACT_PATHS",
    "RegisteredRun",
    "build_run_registry",
    "discover_run_dirs",
    "summarize_registered_run",
    "render_registry_html",
    "write_registry_csv",
    "write_registry_html",
    "write_registry_json",
    "write_registry_outputs",
    "write_registry_svg",
]
