from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge import LOSS_SIGNAL_BRIDGE_JSON_FILENAME
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run import (
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run,
)
from minigpt.report_utils import as_dict


LOSS_SIGNAL_BRIDGE_TRAINING_RUN_JSON_FILENAME = "bounded_objective_loss_signal_bridge_training_run.json"
LOSS_SIGNAL_BRIDGE_TRAINING_RUN_CSV_FILENAME = "bounded_objective_loss_signal_bridge_training_run.csv"
LOSS_SIGNAL_BRIDGE_TRAINING_RUN_TEXT_FILENAME = "bounded_objective_loss_signal_bridge_training_run.txt"
LOSS_SIGNAL_BRIDGE_TRAINING_RUN_MARKDOWN_FILENAME = "bounded_objective_loss_signal_bridge_training_run.md"
LOSS_SIGNAL_BRIDGE_TRAINING_RUN_HTML_FILENAME = "bounded_objective_loss_signal_bridge_training_run.html"


def locate_loss_signal_bridge(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / LOSS_SIGNAL_BRIDGE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective loss signal bridge training run input must be a JSON object")
    return dict(payload)


def build_bounded_objective_loss_signal_bridge_training_run(
    bridge_report: dict[str, Any],
    run_dir: str | Path,
    *,
    bridge_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge training run",
    generated_at: str | None = None,
) -> dict[str, Any]:
    report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run(
        _adapt_bridge(bridge_report),
        run_dir,
        seed_revision_path=bridge_path,
        title=title,
        generated_at=generated_at,
    )
    return _adapt_training_report(report, bridge_report, bridge_path)


def resolve_exit_code(report: dict[str, Any], *, require_training_ready: bool) -> int:
    return 1 if require_training_ready and report.get("status") != "pass" else 0


def _adapt_bridge(bridge_report: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(bridge_report)
    summary = dict(as_dict(bridge_report.get("summary")))
    summary["bounded_objective_unassisted_repair_seed_revision_ready"] = summary.get("bounded_objective_loss_signal_bridge_ready")
    summary["example_count"] = summary.get("bridge_example_count")
    summary["direct_example_count"] = summary.get("bridge_example_count")
    summary["neutral_prompt_example_count"] = summary.get("loss_signal_bridge_example_count")
    summary["decoder_anchor_example_count"] = 0
    summary["corpus_char_count"] = summary.get("bridged_corpus_char_count")
    summary["proposed_next_artifact"] = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run"
    adapted["summary"] = summary
    return adapted


def _adapt_training_report(report: dict[str, Any], bridge_report: dict[str, Any], source_path: str | Path | None) -> dict[str, Any]:
    adapted = dict(report)
    adapted["decision"] = _decision(str(report.get("decision") or ""))
    adapted["source_loss_signal_bridge"] = str(source_path or "")
    adapted["loss_signal_bridge_summary"] = as_dict(bridge_report.get("summary"))
    adapted["summary"] = _summary(as_dict(report.get("summary")))
    adapted["unassisted_repair_training"] = _training(as_dict(report.get("unassisted_repair_training")))
    adapted["loss_signal_bridge_training"] = adapted["unassisted_repair_training"]
    adapted["interpretation"] = _interpretation(as_dict(report.get("interpretation")), adapted["loss_signal_bridge_training"])
    return adapted


def _training(base: dict[str, Any]) -> dict[str, Any]:
    training = dict(base)
    training["proposed_next_artifact"] = "bounded_objective_loss_signal_bridge_replay_comparison"
    training["next_step"] = "run_bounded_objective_loss_signal_bridge_replay_comparison" if training.get("ready") is True else "repair_bounded_objective_loss_signal_bridge_training_run"
    return training


def _summary(base: dict[str, Any]) -> dict[str, Any]:
    summary = dict(base)
    ready = summary.get("bounded_objective_unassisted_repair_seed_revision_training_ready") is True
    summary["bounded_objective_loss_signal_bridge_training_ready"] = ready
    summary["proposed_next_artifact"] = "bounded_objective_loss_signal_bridge_replay_comparison" if ready else ""
    summary["next_step"] = "run_bounded_objective_loss_signal_bridge_replay_comparison" if ready else "repair_bounded_objective_loss_signal_bridge_training_run"
    return summary


def _decision(base_decision: str) -> str:
    mapping = {
        "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run_ready": "bounded_objective_loss_signal_bridge_training_run_ready",
        "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run": "fix_bounded_objective_loss_signal_bridge_training_run",
    }
    return mapping.get(base_decision, base_decision)


def _interpretation(base: dict[str, Any], training: dict[str, Any]) -> dict[str, Any]:
    interpretation = dict(base)
    if training.get("ready") is True:
        interpretation["model_quality_claim"] = "training_artifact_only"
        interpretation["reason"] = "A checkpoint was trained from the loss-signal bridge corpus, but capability still requires replay comparison."
        interpretation["next_action"] = training.get("next_step")
    return interpretation


__all__ = [
    "LOSS_SIGNAL_BRIDGE_TRAINING_RUN_CSV_FILENAME",
    "LOSS_SIGNAL_BRIDGE_TRAINING_RUN_HTML_FILENAME",
    "LOSS_SIGNAL_BRIDGE_TRAINING_RUN_JSON_FILENAME",
    "LOSS_SIGNAL_BRIDGE_TRAINING_RUN_MARKDOWN_FILENAME",
    "LOSS_SIGNAL_BRIDGE_TRAINING_RUN_TEXT_FILENAME",
    "build_bounded_objective_loss_signal_bridge_training_run",
    "locate_loss_signal_bridge",
    "read_json_report",
    "resolve_exit_code",
]
