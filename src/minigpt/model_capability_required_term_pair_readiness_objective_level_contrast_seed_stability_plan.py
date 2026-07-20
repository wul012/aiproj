from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.json"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.csv"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.txt"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.md"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.html"
)


def locate_seed_stability_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_GUARD_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-level contrast seed stability plan input must be a JSON object")
    return dict(payload)


def build_objective_level_contrast_seed_stability_plan(
    promotion_guard: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(promotion_guard.get("summary"))
    guard = as_dict(promotion_guard.get("guard"))
    checks = _checks(promotion_guard, summary, guard)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    plan = _plan(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-level contrast seed stability plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_promotion_guard_path": str(source_path or ""),
        "source_promotion_guard": {
            "status": promotion_guard.get("status"),
            "decision": promotion_guard.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(status, checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def _checks(promotion_guard: dict[str, Any], summary: dict[str, Any], guard: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("guard_passed", promotion_guard.get("status") == "pass", promotion_guard.get("status"), "promotion guard must pass"),
        _check(
            "guard_decision",
            promotion_guard.get("decision") == "pair_readiness_objective_level_contrast_promotion_guard_ready_for_seed_stability",
            promotion_guard.get("decision"),
            "seed stability follows only the guarded route candidate decision",
        ),
        _check("guard_ready", summary.get("promotion_guard_ready") is True, summary.get("promotion_guard_ready"), "promotion guard must be ready"),
        _check("promotion_not_allowed_yet", summary.get("promotion_allowed") is False, summary.get("promotion_allowed"), "single-seed promotion must remain blocked"),
        _check(
            "next_artifact_matches",
            guard.get("required_next_artifact") == "pair_readiness_objective_level_contrast_seed_stability_plan",
            guard.get("required_next_artifact"),
            "guard must request this seed stability plan",
        ),
    ]


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "source_seed": 3636,
        "additional_seeds": [3737, 3838],
        "required_seed_count": 3,
        "minimum_ready_replay_count": 2,
        "required_next_artifacts": [
            "pair_readiness_objective_level_contrast_seed_3737_training_run",
            "pair_readiness_objective_level_contrast_seed_3737_pair_probe_replay",
            "pair_readiness_objective_level_contrast_seed_3838_training_run",
            "pair_readiness_objective_level_contrast_seed_3838_pair_probe_replay",
            "pair_readiness_objective_level_contrast_seed_stability_rollup",
        ],
        "acceptance_rule": "accept only if at least two of three seeds replay required pair-full and no seed regresses to zero exact hits",
        "non_goals": [
            "do not reuse the v763 checkpoint as a substitute for additional seeds",
            "do not accept direct training hits without pair replay",
            "do not change corpus or model size during the stability run",
        ],
    }


def _summary(status: str, checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed_stability_plan_ready": status == "pass" and plan.get("ready") is True,
        "source_seed": plan.get("source_seed"),
        "additional_seed_count": len(plan.get("additional_seeds", [])),
        "required_seed_count": plan.get("required_seed_count"),
        "minimum_ready_replay_count": plan.get("minimum_ready_replay_count"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_objective_level_contrast_seed_stability_plan_ready"
    return "fix_pair_readiness_objective_level_contrast_seed_stability_plan"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The promotion guard is not sufficient to plan seed stability.",
            "next_action": "repair promotion guard evidence before seed runs",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "The guarded route candidate needs additional seeds before acceptance.",
        "next_action": "run seed 3737 training and replay first, then seed 3838",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_TEXT_FILENAME",
    "build_objective_level_contrast_seed_stability_plan",
    "locate_seed_stability_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
