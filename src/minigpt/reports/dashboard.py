"""Compatibility exports for dashboard reports."""

from __future__ import annotations

from minigpt.dashboard import DashboardArtifact, build_dashboard_payload, collect_artifacts, write_dashboard
from minigpt.dashboard_render import render_dashboard_html

__all__ = [
    "DashboardArtifact",
    "collect_artifacts",
    "build_dashboard_payload",
    "write_dashboard",
    "render_dashboard_html",
]
