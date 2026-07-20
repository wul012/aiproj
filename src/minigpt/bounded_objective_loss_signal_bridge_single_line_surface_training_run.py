from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_patch import (
    SINGLE_LINE_SURFACE_PATCH_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_training_run import (
    build_bounded_objective_loss_signal_bridge_training_run,
)
from minigpt.report_utils import as_dict
from minigpt.report_check_common import resolve_exit_code_training_ready as resolve_exit_code


LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_training_run.json"
)
LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_training_run.csv"
)
LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_training_run.txt"
)
LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_training_run.md"
)
LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_training_run.html"
)


def locate_single_line_surface_patch(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / SINGLE_LINE_SURFACE_PATCH_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective loss signal bridge single-line surface training run input must be a JSON object")
    return dict(payload)


def build_bounded_objective_loss_signal_bridge_single_line_surface_training_run(
    single_line_surface_patch: dict[str, Any],
    run_dir: str | Path,
    *,
    single_line_surface_patch_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge single-line surface training run",
    generated_at: str | None = None,
) -> dict[str, Any]:
    report = build_bounded_objective_loss_signal_bridge_training_run(
        _adapt_patch(single_line_surface_patch),
        run_dir,
        bridge_path=single_line_surface_patch_path,
        title=title,
        generated_at=generated_at,
    )
    return _adapt_training_report(report, single_line_surface_patch, single_line_surface_patch_path)


def _adapt_patch(single_line_surface_patch: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(single_line_surface_patch)
    summary = dict(as_dict(single_line_surface_patch.get("summary")))
    summary["bounded_objective_loss_signal_bridge_ready"] = summary.get(
        "bounded_objective_loss_signal_bridge_single_line_surface_patch_ready"
    )
    summary["bridge_example_count"] = summary.get("patch_example_count")
    summary["loss_signal_bridge_example_count"] = summary.get("single_line_case_example_count")
    summary["decoder_anchor_example_count"] = 0
    summary["bridged_corpus_char_count"] = summary.get("patched_corpus_char_count")
    adapted["summary"] = summary
    return adapted


def _adapt_training_report(
    report: dict[str, Any],
    single_line_surface_patch: dict[str, Any],
    source_path: str | Path | None,
) -> dict[str, Any]:
    adapted = dict(report)
    adapted["decision"] = _decision(str(report.get("decision") or ""))
    adapted["source_single_line_surface_patch"] = str(source_path or "")
    adapted["single_line_surface_patch_summary"] = as_dict(single_line_surface_patch.get("summary"))
    adapted["summary"] = _summary(as_dict(report.get("summary")))
    adapted["single_line_surface_training"] = _training(as_dict(report.get("loss_signal_bridge_training")))
    adapted["interpretation"] = _interpretation(
        as_dict(report.get("interpretation")),
        adapted["single_line_surface_training"],
    )
    return adapted


def _training(base: dict[str, Any]) -> dict[str, Any]:
    training = dict(base)
    training["proposed_next_artifact"] = "bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison"
    training["next_step"] = (
        "run_bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison"
        if training.get("ready") is True
        else "repair_bounded_objective_loss_signal_bridge_single_line_surface_training_run"
    )
    return training


def _summary(base: dict[str, Any]) -> dict[str, Any]:
    summary = dict(base)
    ready = summary.get("bounded_objective_loss_signal_bridge_training_ready") is True
    summary["bounded_objective_loss_signal_bridge_single_line_surface_training_ready"] = ready
    summary["proposed_next_artifact"] = (
        "bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison" if ready else ""
    )
    summary["next_step"] = (
        "run_bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison"
        if ready
        else "repair_bounded_objective_loss_signal_bridge_single_line_surface_training_run"
    )
    return summary


def _decision(base_decision: str) -> str:
    mapping = {
        "bounded_objective_loss_signal_bridge_training_run_ready": "bounded_objective_loss_signal_bridge_single_line_surface_training_run_ready",
        "fix_bounded_objective_loss_signal_bridge_training_run": "fix_bounded_objective_loss_signal_bridge_single_line_surface_training_run",
    }
    return mapping.get(base_decision, base_decision)


def _interpretation(base: dict[str, Any], training: dict[str, Any]) -> dict[str, Any]:
    interpretation = dict(base)
    if training.get("ready") is True:
        interpretation["model_quality_claim"] = "training_artifact_only"
        interpretation["reason"] = (
            "A checkpoint was trained from the single-line surface patch corpus, but capability still requires replay comparison."
        )
        interpretation["next_action"] = training.get("next_step")
    return interpretation


__all__ = [
    "LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_CSV_FILENAME",
    "LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_HTML_FILENAME",
    "LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_JSON_FILENAME",
    "LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_MARKDOWN_FILENAME",
    "LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_TRAINING_RUN_TEXT_FILENAME",
    "build_bounded_objective_loss_signal_bridge_single_line_surface_training_run",
    "locate_single_line_surface_patch",
    "read_json_report",
    "resolve_exit_code",
]
