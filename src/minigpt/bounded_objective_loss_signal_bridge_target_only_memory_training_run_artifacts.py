from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_training_run import (
    TARGET_ONLY_MEMORY_TRAINING_RUN_CSV_FILENAME,
    TARGET_ONLY_MEMORY_TRAINING_RUN_HTML_FILENAME,
    TARGET_ONLY_MEMORY_TRAINING_RUN_JSON_FILENAME,
    TARGET_ONLY_MEMORY_TRAINING_RUN_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_TRAINING_RUN_TEXT_FILENAME,
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


def render_target_only_memory_training_run_text(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_training_run_text(report).replace(
        "bounded_objective_loss_signal_bridge_training_ready=",
        "bounded_objective_loss_signal_bridge_target_only_memory_training_ready=",
    )


def render_target_only_memory_training_run_markdown(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_training_run_markdown(report).replace(
        "MiniGPT bounded objective loss signal bridge training run",
        "MiniGPT bounded objective loss signal bridge target-only memory training run",
    )


def render_target_only_memory_training_run_html(report: dict[str, Any]) -> str:
    return render_loss_signal_bridge_training_run_html(report).replace(
        "MiniGPT bounded objective loss signal bridge training run",
        "MiniGPT bounded objective loss signal bridge target-only memory training run",
    )


def write_target_only_memory_training_run_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_TRAINING_RUN_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_TRAINING_RUN_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_TRAINING_RUN_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_TRAINING_RUN_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_TRAINING_RUN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_unassisted_repair_training_run_csv(report, paths["csv"])
    paths["text"].write_text(render_target_only_memory_training_run_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_target_only_memory_training_run_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_target_only_memory_training_run_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "render_target_only_memory_training_run_html",
    "render_target_only_memory_training_run_markdown",
    "render_target_only_memory_training_run_text",
    "write_target_only_memory_training_run_outputs",
]
