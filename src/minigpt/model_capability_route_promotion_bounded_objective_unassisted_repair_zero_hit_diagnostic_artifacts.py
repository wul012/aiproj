from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic_artifacts import (
    render_bounded_objective_replay_zero_hit_diagnostic_html,
    render_bounded_objective_replay_zero_hit_diagnostic_markdown,
    render_bounded_objective_replay_zero_hit_diagnostic_text,
    write_bounded_objective_replay_zero_hit_diagnostic_csv,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import write_json_payload


def render_bounded_objective_unassisted_repair_zero_hit_diagnostic_text(report: dict[str, Any]) -> str:
    return render_bounded_objective_replay_zero_hit_diagnostic_text(report).replace(
        "bounded_objective_zero_hit_diagnostic_ready=",
        "bounded_objective_unassisted_repair_zero_hit_diagnostic_ready=",
    )


def render_bounded_objective_unassisted_repair_zero_hit_diagnostic_markdown(report: dict[str, Any]) -> str:
    return render_bounded_objective_replay_zero_hit_diagnostic_markdown(report)


def render_bounded_objective_unassisted_repair_zero_hit_diagnostic_html(report: dict[str, Any]) -> str:
    return render_bounded_objective_replay_zero_hit_diagnostic_html(report)


def write_bounded_objective_unassisted_repair_zero_hit_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_replay_zero_hit_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_unassisted_repair_zero_hit_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_unassisted_repair_zero_hit_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_unassisted_repair_zero_hit_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "render_bounded_objective_unassisted_repair_zero_hit_diagnostic_html",
    "render_bounded_objective_unassisted_repair_zero_hit_diagnostic_markdown",
    "render_bounded_objective_unassisted_repair_zero_hit_diagnostic_text",
    "write_bounded_objective_unassisted_repair_zero_hit_diagnostic_outputs",
]
