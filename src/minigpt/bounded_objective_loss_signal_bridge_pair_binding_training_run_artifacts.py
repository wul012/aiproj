from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_pair_binding_training_run import (
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_CSV_FILENAME,
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_HTML_FILENAME,
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_JSON_FILENAME,
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_MARKDOWN_FILENAME,
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_TEXT_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_training_run_artifacts import (
    render_loss_signal_bridge_training_run_html,
    render_loss_signal_bridge_training_run_markdown,
    render_loss_signal_bridge_training_run_text,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_training_run_artifacts import (
    write_bounded_objective_unassisted_repair_training_run_csv,
)
from minigpt.report_utils import write_json_payload


def render_pair_binding_training_run_text(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_training_run_text(report).replace(
        "bounded_objective_loss_signal_bridge_training_ready=",
        "bounded_objective_loss_signal_bridge_pair_binding_training_ready=",
    )


def render_pair_binding_training_run_markdown(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_training_run_markdown(report)


def render_pair_binding_training_run_html(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_training_run_html(report).replace(
        "MiniGPT bounded objective loss signal bridge training run",
        "MiniGPT bounded objective loss signal bridge pair-binding training run",
    )


def write_pair_binding_training_run_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_JSON_FILENAME,
        "csv": root / LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_CSV_FILENAME,
        "text": root / LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_TEXT_FILENAME,
        "markdown": root / LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_MARKDOWN_FILENAME,
        "html": root / LOSS_SIGNAL_BRIDGE_PAIR_BINDING_TRAINING_RUN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_unassisted_repair_training_run_csv(report, paths["csv"])
    paths["text"].write_text(render_pair_binding_training_run_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_pair_binding_training_run_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_pair_binding_training_run_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "render_pair_binding_training_run_html",
    "render_pair_binding_training_run_markdown",
    "render_pair_binding_training_run_text",
    "write_pair_binding_training_run_outputs",
]
