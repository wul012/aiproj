from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison import GeneratorRunner
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison import (
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict
from minigpt.report_check_common import resolve_exit_code_comparison_objective as resolve_exit_code


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison.json"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison.csv"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison.md"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison.html"


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def locate_curriculum_patch_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective unassisted repair seed revision curriculum patch replay comparison input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison(
    objective_contract_report: dict[str, Any],
    curriculum_patch_training_run_report: dict[str, Any],
    *,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    objective_contract_path: str | Path | None = None,
    curriculum_patch_training_run_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair seed revision curriculum patch replay comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison(
        objective_contract_report,
        _adapt_training(curriculum_patch_training_run_report),
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        device=device,
        objective_contract_path=objective_contract_path,
        seed_revision_training_run_path=curriculum_patch_training_run_path,
        generator_runner=generator_runner,
        title=title,
        generated_at=generated_at,
    )
    return _adapt_replay_report(report, curriculum_patch_training_run_report, curriculum_patch_training_run_path)


def _adapt_training(training_report: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(training_report)
    summary = dict(as_dict(training_report.get("summary")))
    summary["bounded_objective_unassisted_repair_seed_revision_training_ready"] = summary.get(
        "bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready"
    )
    adapted["summary"] = summary
    return adapted


def _adapt_replay_report(report: dict[str, Any], original_training_report: dict[str, Any], source_path: str | Path | None) -> dict[str, Any]:
    adapted = dict(report)
    adapted["source_curriculum_patch_training_run"] = str(source_path or "")
    adapted["curriculum_patch_training_summary"] = as_dict(original_training_report.get("summary"))
    adapted["decision"] = _decision(str(report.get("decision") or ""))
    adapted["comparison"] = _comparison(as_dict(report.get("comparison")))
    adapted["summary"] = _summary(as_dict(report.get("summary")), adapted["comparison"])
    adapted["interpretation"] = _interpretation(as_dict(report.get("interpretation")), adapted["comparison"])
    return adapted


def _decision(base_decision: str) -> str:
    mapping = {
        "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison": "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison",
        "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_contract_recovered_holdout_required": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_contract_recovered_holdout_required",
        "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_partial_required_term_hit": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_partial_required_term_hit",
        "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_zero_hit": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_zero_hit",
    }
    return mapping.get(base_decision, base_decision)


def _comparison(base: dict[str, Any]) -> dict[str, Any]:
    comparison = dict(base)
    comparison["route"] = "bounded_objective_unassisted_repair_seed_revision_curriculum_patch"
    comparison["training_source"] = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run"
    comparison["decoder_anchor_used"] = False
    comparison["next_step"] = _next_step(comparison.get("objective_contract_recovered") is True, int(comparison.get("any_hit_case_count") or 0))
    return comparison


def _summary(base: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    summary = dict(base)
    summary["bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_ready"] = summary.get(
        "bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready", False
    )
    summary["route"] = comparison.get("route")
    summary["decoder_anchor_used"] = False
    summary["next_step"] = comparison.get("next_step")
    return summary


def _interpretation(base: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    interpretation = dict(base)
    if comparison.get("objective_contract_recovered") is True:
        interpretation["next_action"] = "run_unchanged_bounded_suite_holdout_replay"
    elif int(comparison.get("any_hit_case_count") or 0) > 0:
        interpretation["next_action"] = "diagnose_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_partial_hit_before_more_training"
    else:
        interpretation["next_action"] = "diagnose_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_zero_hit_before_more_training"
    interpretation["reason"] = str(interpretation.get("reason") or "") + " This replay used the v856 curriculum patch checkpoint and no decoder anchors."
    return interpretation


def _next_step(recovered: bool, any_hit_count: int) -> str:
    if recovered:
        return "run_unchanged_bounded_suite_holdout_replay"
    if any_hit_count > 0:
        return "diagnose_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_partial_hit_before_more_training"
    return "diagnose_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_zero_hit_before_more_training"


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison",
    "locate_curriculum_patch_training_run",
    "locate_objective_contract",
    "read_json_report",
    "resolve_exit_code",
]
