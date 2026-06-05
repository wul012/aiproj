from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_replay_comparison import (
    GeneratorRunner,
    build_bounded_objective_loss_signal_bridge_replay_comparison,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict


TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison.json"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison.csv"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison.txt"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison.md"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison.html"
)


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def locate_stagnation_aware_suffix_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("stagnation-aware suffix replay comparison input must be a JSON object")
    return dict(payload)


def build_stagnation_aware_suffix_replay_comparison(
    objective_contract_report: dict[str, Any],
    stagnation_aware_suffix_training_run_report: dict[str, Any],
    *,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    objective_contract_path: str | Path | None = None,
    stagnation_aware_suffix_training_run_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix replay comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    report = build_bounded_objective_loss_signal_bridge_replay_comparison(
        objective_contract_report,
        _adapt_training_run(stagnation_aware_suffix_training_run_report),
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        device=device,
        objective_contract_path=objective_contract_path,
        loss_signal_bridge_training_run_path=stagnation_aware_suffix_training_run_path,
        generator_runner=generator_runner,
        title=title,
        generated_at=generated_at,
    )
    return _adapt_replay_report(report, stagnation_aware_suffix_training_run_report, stagnation_aware_suffix_training_run_path)


def resolve_exit_code(report: dict[str, Any], *, require_comparison_ready: bool, require_objective_pass: bool = False) -> int:
    if require_comparison_ready and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_objective_pass and summary.get("objective_contract_recovered") is not True:
        return 1
    return 0


def _adapt_training_run(training_report: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(training_report)
    summary = dict(as_dict(training_report.get("summary")))
    summary["bounded_objective_loss_signal_bridge_training_ready"] = summary.get(
        "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_ready"
    )
    adapted["summary"] = summary
    return adapted


def _adapt_replay_report(report: dict[str, Any], training_report: dict[str, Any], source_path: str | Path | None) -> dict[str, Any]:
    adapted = dict(report)
    adapted["source_stagnation_aware_suffix_training_run"] = str(source_path or "")
    adapted["stagnation_aware_suffix_training_summary"] = as_dict(training_report.get("summary"))
    adapted["decision"] = _decision(str(report.get("decision") or ""))
    adapted["comparison"] = _comparison(as_dict(report.get("comparison")))
    adapted["summary"] = _summary(as_dict(report.get("summary")), adapted["comparison"])
    adapted["interpretation"] = _interpretation(as_dict(report.get("interpretation")), adapted["comparison"])
    return adapted


def _comparison(base: dict[str, Any]) -> dict[str, Any]:
    comparison = dict(base)
    comparison["route"] = "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix"
    comparison["training_source"] = "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run"
    comparison["next_step"] = _next_step(
        comparison.get("objective_contract_recovered") is True,
        int(comparison.get("any_hit_case_count") or 0),
    )
    return comparison


def _summary(base: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    summary = dict(base)
    summary["bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison_ready"] = summary.get(
        "bounded_objective_loss_signal_bridge_replay_comparison_ready", False
    )
    summary["route"] = comparison.get("route")
    summary["next_step"] = comparison.get("next_step")
    return summary


def _decision(base_decision: str) -> str:
    mapping = {
        "fix_bounded_objective_loss_signal_bridge_replay_comparison": "fix_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison",
        "bounded_objective_loss_signal_bridge_replay_contract_recovered_holdout_required": "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_contract_recovered_holdout_required",
        "bounded_objective_loss_signal_bridge_replay_partial_required_term_hit": "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_partial_required_term_hit",
        "bounded_objective_loss_signal_bridge_replay_zero_hit": "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_zero_hit",
    }
    return mapping.get(base_decision, base_decision)


def _interpretation(base: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    interpretation = dict(base)
    if comparison.get("objective_contract_recovered") is True:
        interpretation["next_action"] = "run_unchanged_bounded_suite_holdout_replay"
        interpretation["reason"] = "The stagnation-aware suffix checkpoint passed the objective contract, but unchanged holdout replay remains required."
    elif int(comparison.get("any_hit_case_count") or 0) > 0:
        interpretation["next_action"] = "diagnose_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_partial_hit_before_more_training"
        interpretation["reason"] = "The stagnation-aware suffix checkpoint produced partial required-term signal without recovering the full contract."
    else:
        interpretation["next_action"] = "diagnose_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_zero_hit_before_more_training"
        interpretation["reason"] = "The stagnation-aware suffix checkpoint produced zero required-term hits on the objective contract."
    return interpretation


def _next_step(recovered: bool, any_hit_count: int) -> str:
    if recovered:
        return "run_unchanged_bounded_suite_holdout_replay"
    if any_hit_count > 0:
        return "diagnose_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_partial_hit_before_more_training"
    return "diagnose_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_zero_hit_before_more_training"


__all__ = [
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_TEXT_FILENAME",
    "build_stagnation_aware_suffix_replay_comparison",
    "locate_objective_contract",
    "locate_stagnation_aware_suffix_training_run",
    "read_json_report",
    "resolve_exit_code",
]
