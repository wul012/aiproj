from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_replay_comparison_artifacts import (
    render_loss_signal_bridge_replay_comparison_html,
    render_loss_signal_bridge_replay_comparison_markdown,
    render_loss_signal_bridge_replay_comparison_text,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_CSV_FILENAME,
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_HTML_FILENAME,
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME,
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_MARKDOWN_FILENAME,
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_TEXT_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison_artifacts import (
    write_bounded_objective_replay_comparison_csv,
)
from minigpt.report_utils import write_json_payload


def render_single_line_surface_replay_comparison_text(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_replay_comparison_text(report).replace(
        "bounded_objective_loss_signal_bridge_replay_comparison_ready=",
        "bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_ready=",
    )


def render_single_line_surface_replay_comparison_markdown(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_replay_comparison_markdown(report)


def render_single_line_surface_replay_comparison_html(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_replay_comparison_html(report).replace(
        "MiniGPT bounded objective loss signal bridge replay comparison",
        "MiniGPT bounded objective loss signal bridge single-line surface replay comparison",
    )


def write_single_line_surface_replay_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME,
        "csv": root / LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_CSV_FILENAME,
        "text": root / LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_TEXT_FILENAME,
        "markdown": root / LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_MARKDOWN_FILENAME,
        "html": root / LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_replay_comparison_csv(report, paths["csv"])
    paths["text"].write_text(render_single_line_surface_replay_comparison_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_single_line_surface_replay_comparison_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_single_line_surface_replay_comparison_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "render_single_line_surface_replay_comparison_html",
    "render_single_line_surface_replay_comparison_markdown",
    "render_single_line_surface_replay_comparison_text",
    "write_single_line_surface_replay_comparison_outputs",
]
