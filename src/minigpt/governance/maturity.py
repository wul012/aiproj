"""Compatibility exports for maturity governance reports."""

from __future__ import annotations

from minigpt.maturity import (
    CAPABILITY_SPECS,
    CapabilitySpec,
    build_maturity_summary,
    render_maturity_summary_html,
    render_maturity_summary_markdown,
    write_maturity_summary_csv,
    write_maturity_summary_html,
    write_maturity_summary_json,
    write_maturity_summary_markdown,
    write_maturity_summary_outputs,
)
from minigpt.maturity_narrative import (
    build_maturity_narrative,
    render_maturity_narrative_html,
    render_maturity_narrative_markdown,
    write_maturity_narrative_html,
    write_maturity_narrative_json,
    write_maturity_narrative_markdown,
    write_maturity_narrative_outputs,
)

__all__ = [
    "CapabilitySpec",
    "CAPABILITY_SPECS",
    "build_maturity_summary",
    "render_maturity_summary_html",
    "render_maturity_summary_markdown",
    "write_maturity_summary_csv",
    "write_maturity_summary_html",
    "write_maturity_summary_json",
    "write_maturity_summary_markdown",
    "write_maturity_summary_outputs",
    "build_maturity_narrative",
    "render_maturity_narrative_html",
    "render_maturity_narrative_markdown",
    "write_maturity_narrative_html",
    "write_maturity_narrative_json",
    "write_maturity_narrative_markdown",
    "write_maturity_narrative_outputs",
]
