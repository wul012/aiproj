from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison_artifacts import (
    write_bounded_objective_replay_comparison_csv,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_CSV_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_HTML_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_TEXT_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison_artifacts import (
    render_bounded_objective_unassisted_repair_seed_revision_replay_comparison_html,
    render_bounded_objective_unassisted_repair_seed_revision_replay_comparison_markdown,
    render_bounded_objective_unassisted_repair_seed_revision_replay_comparison_text,
)
from minigpt.report_utils import write_json_payload


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_text(report: dict[str, Any]) -> str:
    return render_bounded_objective_unassisted_repair_seed_revision_replay_comparison_text(report).replace(
        "bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready=",
        "bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_ready=",
    )


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_markdown(report: dict[str, Any]) -> str:
    return render_bounded_objective_unassisted_repair_seed_revision_replay_comparison_markdown(report)


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_html(report: dict[str, Any]) -> str:
    return render_bounded_objective_unassisted_repair_seed_revision_replay_comparison_html(report)


def write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_replay_comparison_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_html",
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_markdown",
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_text",
    "write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_outputs",
]
