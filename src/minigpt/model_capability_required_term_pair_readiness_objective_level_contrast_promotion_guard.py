from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_training_run import (
    PAIR_READINESS_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.json"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.csv"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.txt"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.md"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.html"
)


def locate_promotion_guard_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ROUTE_COMPARISON_JSON_FILENAME
    return source


def locate_promotion_guard_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME
    return source


def locate_promotion_guard_training(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-level contrast promotion guard input must be a JSON object")
    return dict(payload)


def build_objective_level_contrast_promotion_guard(
    route_comparison: dict[str, Any],
    objective_replay: dict[str, Any],
    training_run: dict[str, Any],
    *,
    comparison_path: str | Path | None = None,
    replay_path: str | Path | None = None,
    training_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    checks = _checks(route_comparison, objective_replay, training_run)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    guard = _guard(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-level contrast promotion guard",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_paths": {
            "route_comparison": str(comparison_path or ""),
            "objective_replay": str(replay_path or ""),
            "training_run": str(training_path or ""),
        },
        "source_summaries": {
            "route_comparison": as_dict(route_comparison.get("summary")),
            "objective_replay": as_dict(objective_replay.get("summary")),
            "training_run": as_dict(training_run.get("summary")),
        },
        "check_rows": checks,
        "guard": guard,
        "summary": _summary(status, checks, guard),
        "interpretation": _interpretation(status, guard),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _checks(route_comparison: dict[str, Any], objective_replay: dict[str, Any], training_run: dict[str, Any]) -> list[dict[str, Any]]:
    comparison_summary = as_dict(route_comparison.get("summary"))
    replay_summary = as_dict(objective_replay.get("summary"))
    training_summary = as_dict(training_run.get("summary"))
    training = as_dict(training_run.get("training"))
    source_materialization = as_dict(training_run.get("source_materialization"))
    materialization_summary = as_dict(source_materialization.get("summary"))
    return [
        _check("comparison_passed", route_comparison.get("status") == "pass", route_comparison.get("status"), "route comparison must pass"),
        _check(
            "comparison_decision",
            route_comparison.get("decision") == "pair_readiness_objective_level_contrast_replay_wins_needs_promotion_guard",
            route_comparison.get("decision"),
            "promotion guard follows only the objective-level contrast winner decision",
        ),
        _check("objective_route_best", comparison_summary.get("objective_route_best") is True, comparison_summary.get("objective_route_best"), "objective route must be best in comparison"),
        _check("promotion_guard_required", comparison_summary.get("promotion_guard_required") is True, comparison_summary.get("promotion_guard_required"), "comparison must require this guard"),
        _check("replay_passed", objective_replay.get("status") == "pass", objective_replay.get("status"), "objective replay must pass"),
        _check("replay_decision_ready", objective_replay.get("decision") == "pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready", objective_replay.get("decision"), "objective replay must be ready"),
        _check("replay_required_all_pair_full", replay_summary.get("required_all_pair_full") is True, replay_summary.get("required_all_pair_full"), "all required pair probes must be full"),
        _check("replay_pair_full_count", int(replay_summary.get("pair_full_count") or 0) >= 3, replay_summary.get("pair_full_count"), "all three pair surfaces should be pair-full"),
        _check("training_passed", training_run.get("status") == "pass", training_run.get("status"), "training report must pass"),
        _check("checkpoint_exists", training.get("checkpoint_exists") is True, training.get("checkpoint_exists"), "checkpoint must exist"),
        _check("tokenizer_exists", training.get("tokenizer_exists") is True, training.get("tokenizer_exists"), "tokenizer must exist"),
        _check("direct_pair_full", training_summary.get("pair_full_observed") is True, training_summary.get("pair_full_observed"), "training run should observe direct pair-full before replay"),
        _check("materialized_corpus_large_enough", int(materialization_summary.get("training_line_count") or 0) >= 8000, materialization_summary.get("training_line_count"), "source corpus should be the objective-level contrast materialization"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _guard(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "guard_result": "ready_for_seed_stability" if status == "pass" else "blocked",
        "promotion_allowed": False,
        "required_next_artifact": "pair_readiness_objective_level_contrast_seed_stability_plan",
        "acceptance_boundary": "single-seed replay winner is insufficient for accepting a model-capability route",
        "non_goals": [
            "do not tag the checkpoint as accepted before seed stability",
            "do not remove replay artifacts from the evidence chain",
            "do not replace seed stability with direct training-run hits",
        ],
    }


def _summary(status: str, checks: list[dict[str, Any]], guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "promotion_guard_ready": status == "pass" and guard.get("ready") is True,
        "promotion_allowed": guard.get("promotion_allowed") is True,
        "guard_result": guard.get("guard_result"),
        "required_next_artifact": guard.get("required_next_artifact"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_objective_level_contrast_promotion_guard_ready_for_seed_stability"
    return "fix_pair_readiness_objective_level_contrast_promotion_guard"


def _interpretation(status: str, guard: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The comparison, replay, or training evidence is not sufficient for a promotion guard.",
            "next_action": "repair objective-level contrast evidence before seed stability",
        }
    return {
        "model_quality_claim": "guarded_route_candidate",
        "reason": "The objective-level contrast checkpoint wins replay comparison, but a single seed is not enough for acceptance.",
        "next_action": f"build {guard.get('required_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_TEXT_FILENAME",
    "build_objective_level_contrast_promotion_guard",
    "locate_promotion_guard_comparison",
    "locate_promotion_guard_replay",
    "locate_promotion_guard_training",
    "read_json_report",
    "resolve_exit_code",
]
