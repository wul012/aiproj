from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run import (
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run,
)
from minigpt.report_utils import as_dict
from minigpt.report_check_common import resolve_exit_code_training_ready as resolve_exit_code


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run.json"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run.csv"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run.md"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run.html"


def locate_curriculum_patch(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective unassisted repair seed revision curriculum patch training run input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run(
    curriculum_patch_report: dict[str, Any],
    run_dir: str | Path,
    *,
    curriculum_patch_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair seed revision curriculum patch training run",
    generated_at: str | None = None,
) -> dict[str, Any]:
    report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run(
        _adapt_patch(curriculum_patch_report),
        run_dir,
        seed_revision_path=curriculum_patch_path,
        title=title,
        generated_at=generated_at,
    )
    return _adapt_training_report(report, curriculum_patch_report, curriculum_patch_path)


def _adapt_patch(patch_report: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(patch_report)
    summary = dict(as_dict(patch_report.get("summary")))
    summary["bounded_objective_unassisted_repair_seed_revision_ready"] = summary.get(
        "bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready"
    )
    summary["example_count"] = summary.get("patch_example_count")
    summary["direct_example_count"] = summary.get("patch_example_count")
    summary["neutral_prompt_example_count"] = summary.get("loss_focus_example_count")
    summary["decoder_anchor_example_count"] = 0
    summary["corpus_char_count"] = summary.get("patched_corpus_char_count")
    summary["proposed_next_artifact"] = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run"
    adapted["summary"] = summary
    return adapted


def _adapt_training_report(report: dict[str, Any], patch_report: dict[str, Any], source_path: str | Path | None) -> dict[str, Any]:
    adapted = dict(report)
    adapted["decision"] = _decision(str(report.get("decision") or ""))
    adapted["source_curriculum_patch"] = str(source_path or "")
    adapted["curriculum_patch_summary"] = as_dict(patch_report.get("summary"))
    adapted["summary"] = _summary(as_dict(report.get("summary")))
    adapted["unassisted_repair_training"] = _training(as_dict(report.get("unassisted_repair_training")))
    adapted["interpretation"] = _interpretation(as_dict(report.get("interpretation")), adapted["unassisted_repair_training"])
    return adapted


def _training(base: dict[str, Any]) -> dict[str, Any]:
    training = dict(base)
    training["proposed_next_artifact"] = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison"
    training["next_step"] = "run_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison" if training.get("ready") is True else "repair_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run"
    return training


def _summary(base: dict[str, Any]) -> dict[str, Any]:
    summary = dict(base)
    ready = summary.get("bounded_objective_unassisted_repair_seed_revision_training_ready") is True
    summary["bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready"] = ready
    summary["proposed_next_artifact"] = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison" if ready else ""
    summary["next_step"] = "run_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison" if ready else "repair_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run"
    return summary


def _decision(base_decision: str) -> str:
    mapping = {
        "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run_ready": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_ready",
        "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run": "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run",
    }
    return mapping.get(base_decision, base_decision)


def _interpretation(base: dict[str, Any], training: dict[str, Any]) -> dict[str, Any]:
    interpretation = dict(base)
    if training.get("ready") is True:
        interpretation["model_quality_claim"] = "training_artifact_only"
        interpretation["reason"] = "A checkpoint was trained from the curriculum patched corpus, but capability still requires replay comparison."
        interpretation["next_action"] = training.get("next_step")
    return interpretation


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run",
    "locate_curriculum_patch",
    "read_json_report",
    "resolve_exit_code",
]
