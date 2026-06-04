from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_CSV_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_HTML_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_JSON_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_TEXT_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_training_run_artifacts import (
    render_bounded_objective_unassisted_repair_training_run_html,
    render_bounded_objective_unassisted_repair_training_run_markdown,
    render_bounded_objective_unassisted_repair_training_run_text,
    write_bounded_objective_unassisted_repair_training_run_csv,
)
from minigpt.report_utils import write_json_payload


def render_bounded_objective_unassisted_repair_seed_revision_training_run_text(report: dict[str, Any]) -> str:
    return render_bounded_objective_unassisted_repair_training_run_text(report).replace(
        "bounded_objective_unassisted_repair_training_ready=",
        "bounded_objective_unassisted_repair_seed_revision_training_ready=",
    )


def render_bounded_objective_unassisted_repair_seed_revision_training_run_markdown(report: dict[str, Any]) -> str:
    return render_bounded_objective_unassisted_repair_training_run_markdown(report)


def render_bounded_objective_unassisted_repair_seed_revision_training_run_html(report: dict[str, Any]) -> str:
    return render_bounded_objective_unassisted_repair_training_run_html(report)


def write_bounded_objective_unassisted_repair_seed_revision_training_run_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_unassisted_repair_training_run_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_unassisted_repair_seed_revision_training_run_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_unassisted_repair_seed_revision_training_run_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_unassisted_repair_seed_revision_training_run_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "render_bounded_objective_unassisted_repair_seed_revision_training_run_html",
    "render_bounded_objective_unassisted_repair_seed_revision_training_run_markdown",
    "render_bounded_objective_unassisted_repair_seed_revision_training_run_text",
    "write_bounded_objective_unassisted_repair_seed_revision_training_run_outputs",
]
