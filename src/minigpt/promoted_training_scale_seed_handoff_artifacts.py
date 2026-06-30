from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_sections import (
    render_promoted_training_scale_seed_handoff_html,
    render_promoted_training_scale_seed_handoff_markdown,
)
from minigpt.promoted_training_scale_seed_handoff_csv import (
    write_promoted_training_scale_seed_handoff_csv,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_artifacts import (
    build_promoted_training_scale_seed_handoff_automation_receipt,
    render_promoted_training_scale_seed_handoff_automation_receipt_text,
    write_promoted_training_scale_seed_handoff_automation_receipt_json,
    write_promoted_training_scale_seed_handoff_automation_receipt_text,
)
from minigpt.report_utils import write_json_payload


def write_promoted_training_scale_seed_handoff_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_seed_handoff_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_html(report), encoding="utf-8")


def write_promoted_training_scale_seed_handoff_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_seed_handoff_markdown(report), encoding="utf-8")


def write_promoted_training_scale_seed_handoff_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_seed_handoff.json",
        "csv": root / "promoted_training_scale_seed_handoff.csv",
        "markdown": root / "promoted_training_scale_seed_handoff.md",
        "html": root / "promoted_training_scale_seed_handoff.html",
        "automation_receipt_json": root / "promoted_training_scale_seed_handoff_automation_receipt.json",
        "automation_receipt_text": root / "promoted_training_scale_seed_handoff_automation_receipt.txt",
    }
    write_promoted_training_scale_seed_handoff_json(report, paths["json"])
    write_promoted_training_scale_seed_handoff_csv(report, paths["csv"])
    write_promoted_training_scale_seed_handoff_markdown(report, paths["markdown"])
    write_promoted_training_scale_seed_handoff_html(report, paths["html"])
    write_promoted_training_scale_seed_handoff_automation_receipt_json(report, paths["automation_receipt_json"])
    write_promoted_training_scale_seed_handoff_automation_receipt_text(report, paths["automation_receipt_text"])
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "build_promoted_training_scale_seed_handoff_automation_receipt",
    "render_promoted_training_scale_seed_handoff_automation_receipt_text",
    "write_promoted_training_scale_seed_handoff_automation_receipt_json",
    "write_promoted_training_scale_seed_handoff_automation_receipt_text",
    "write_promoted_training_scale_seed_handoff_csv",
    "write_promoted_training_scale_seed_handoff_html",
    "write_promoted_training_scale_seed_handoff_json",
    "write_promoted_training_scale_seed_handoff_markdown",
    "write_promoted_training_scale_seed_handoff_outputs",
]
