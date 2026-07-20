from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic import (
    build_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic.json"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic.csv"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic.md"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic.html"


def locate_unassisted_repair_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_REPLAY_COMPARISON_JSON_FILENAME
    return source


def locate_unassisted_repair_seed(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME
    return source


def locate_unassisted_repair_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective unassisted repair zero-hit diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic(
    unassisted_repair_replay_comparison: dict[str, Any],
    unassisted_repair_seed: dict[str, Any],
    unassisted_repair_training_run: dict[str, Any],
    *,
    corpus_path: str | Path,
    replay_comparison_path: str | Path | None = None,
    unassisted_repair_seed_path: str | Path | None = None,
    unassisted_repair_training_run_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair zero-hit diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    report = build_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic(
        _adapt_replay(unassisted_repair_replay_comparison),
        _adapt_seed(unassisted_repair_seed),
        _adapt_training(unassisted_repair_training_run),
        corpus_path=corpus_path,
        replay_comparison_path=replay_comparison_path,
        objective_seed_path=unassisted_repair_seed_path,
        objective_training_run_path=unassisted_repair_training_run_path,
        title=title,
        generated_at=generated_at,
    )
    return _adapt_diagnostic_report(report, unassisted_repair_seed, unassisted_repair_training_run)


def _adapt_replay(replay: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(replay)
    summary = dict(as_dict(replay.get("summary")))
    summary["bounded_objective_replay_comparison_ready"] = summary.get("bounded_objective_replay_comparison_ready") or summary.get("bounded_objective_unassisted_repair_replay_comparison_ready")
    adapted["summary"] = summary
    return adapted


def _adapt_seed(seed: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(seed)
    summary = dict(as_dict(seed.get("summary")))
    summary["bounded_objective_seed_ready"] = summary.get("bounded_objective_unassisted_repair_seed_ready")
    adapted["summary"] = summary
    return adapted


def _adapt_training(training: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(training)
    summary = dict(as_dict(training.get("summary")))
    summary["bounded_objective_training_ready"] = summary.get("bounded_objective_unassisted_repair_training_ready")
    adapted["summary"] = summary
    return adapted


def _adapt_diagnostic_report(report: dict[str, Any], seed: dict[str, Any], training: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(report)
    adapted["decision"] = _decision(str(report.get("decision") or ""))
    adapted["source_unassisted_repair_seed_summary"] = as_dict(seed.get("summary"))
    adapted["source_unassisted_repair_training_summary"] = as_dict(training.get("summary"))
    adapted["diagnostic"] = _diagnostic(as_dict(report.get("diagnostic")))
    adapted["summary"] = _summary(as_dict(report.get("summary")), adapted["diagnostic"])
    adapted["interpretation"] = _interpretation(as_dict(report.get("interpretation")), adapted["diagnostic"])
    return adapted


def _diagnostic(base: dict[str, Any]) -> dict[str, Any]:
    diagnostic = dict(base)
    diagnostic["route"] = "bounded_objective_unassisted_repair"
    diagnostic["decoder_anchor_used"] = False
    diagnostic["proposed_next_artifact"] = "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision"
    diagnostic["next_step"] = "build_bounded_objective_unassisted_repair_curriculum_revision" if diagnostic.get("ready") is True else "repair_bounded_objective_unassisted_repair_zero_hit_diagnostic_inputs"
    return diagnostic


def _summary(base: dict[str, Any], diagnostic: dict[str, Any]) -> dict[str, Any]:
    summary = dict(base)
    summary["bounded_objective_unassisted_repair_zero_hit_diagnostic_ready"] = summary.get("bounded_objective_zero_hit_diagnostic_ready", False)
    summary["decoder_anchor_used"] = False
    summary["route"] = diagnostic.get("route")
    summary["proposed_next_artifact"] = diagnostic.get("proposed_next_artifact")
    summary["next_step"] = diagnostic.get("next_step")
    return summary


def _decision(base_decision: str) -> str:
    mapping = {
        "model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic_ready": "model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic_ready",
        "fix_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic": "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic",
    }
    return mapping.get(base_decision, base_decision)


def _interpretation(base: dict[str, Any], diagnostic: dict[str, Any]) -> dict[str, Any]:
    interpretation = dict(base)
    if diagnostic.get("ready") is True:
        interpretation["model_quality_claim"] = "not_improved_diagnosed"
        interpretation["reason"] = "The unassisted repair checkpoint still has zero exact required-term hits; one row shows only a partial loss fragment, so the next step is corpus/curriculum revision rather than promotion."
        interpretation["next_action"] = diagnostic.get("next_step")
    return interpretation


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic",
    "locate_unassisted_repair_replay_comparison",
    "locate_unassisted_repair_seed",
    "locate_unassisted_repair_training_run",
    "read_json_report",
    "resolve_exit_code",
]
