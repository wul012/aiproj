from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, number_or_default, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.json"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.csv"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.txt"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.md"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.html"
)


def locate_seed_stability_rollup_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_PLAN_JSON_FILENAME
    return source


def locate_seed_stability_rollup_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-level contrast seed stability rollup input must be a JSON object")
    return dict(payload)


def build_objective_level_contrast_seed_stability_rollup(
    seed_stability_plan: dict[str, Any],
    seed_replays: list[tuple[int, dict[str, Any], str | Path]],
    *,
    source_plan_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan = as_dict(seed_stability_plan.get("plan"))
    expected_seeds = _expected_seeds(plan)
    rows = [_row(seed, report, source_path) for seed, report, source_path in seed_replays]
    checks = _checks(seed_stability_plan, plan, expected_seeds, rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, plan, expected_seeds, rows, checks)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-level contrast seed stability rollup",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_seed_stability_plan_path": str(source_plan_path or ""),
        "source_seed_stability_plan": {
            "status": seed_stability_plan.get("status"),
            "decision": seed_stability_plan.get("decision"),
            "summary": as_dict(seed_stability_plan.get("summary")),
            "plan": plan,
        },
        "seed_rows": rows,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _expected_seeds(plan: dict[str, Any]) -> list[int]:
    seeds = [number_or_default(plan.get("source_seed"), 0, int)]
    seeds.extend(number_or_default(seed, 0, int) for seed in plan.get("additional_seeds", []))
    return [seed for seed in seeds if seed > 0]


def _row(seed: int, report: dict[str, Any], source_path: str | Path) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    pair_full_count = number_or_default(summary.get("pair_full_count"), 0, int)
    return {
        "seed": int(seed),
        "source_path": str(source_path),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "exact_heldout_pair_full": summary.get("exact_heldout_pair_full") is True,
        "required_all_pair_full": summary.get("required_all_pair_full") is True,
        "pair_full_count": pair_full_count,
        "pair_full_rate": summary.get("pair_full_rate"),
        "ready": report.get("status") == "pass"
        and report.get("decision") == "pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready"
        and summary.get("exact_heldout_pair_full") is True
        and summary.get("required_all_pair_full") is True
        and pair_full_count > 0,
    }


def _checks(seed_stability_plan: dict[str, Any], plan: dict[str, Any], expected_seeds: list[int], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observed_seeds = sorted({int(row["seed"]) for row in rows})
    expected_sorted = sorted(expected_seeds)
    ready_count = sum(1 for row in rows if row.get("ready") is True)
    minimum_ready = number_or_default(plan.get("minimum_ready_replay_count"), 0, int)
    missing = [seed for seed in expected_sorted if seed not in observed_seeds]
    unexpected = [seed for seed in observed_seeds if seed not in expected_sorted]
    zero_pair_full = [row["seed"] for row in rows if number_or_default(row.get("pair_full_count"), 0, int) <= 0]
    return [
        _check("plan_passed", seed_stability_plan.get("status") == "pass", seed_stability_plan.get("status"), "seed stability plan must pass"),
        _check(
            "plan_decision",
            seed_stability_plan.get("decision") == "pair_readiness_objective_level_contrast_seed_stability_plan_ready",
            seed_stability_plan.get("decision"),
            "rollup must follow the v767 seed stability plan",
        ),
        _check("all_expected_seeds_observed", not missing, missing, "all planned seeds must have replay evidence"),
        _check("no_unexpected_seeds", not unexpected, unexpected, "rollup must not mix unplanned seeds"),
        _check("minimum_ready_replays", ready_count >= minimum_ready, ready_count, "ready replay count must satisfy the acceptance rule"),
        _check("no_zero_pair_full_seed", not zero_pair_full, zero_pair_full, "no seed may regress to zero pair-full hits"),
        _check("every_observed_replay_ready", all(row.get("ready") is True for row in rows), ready_count, "each observed replay must be replay-ready"),
    ]


def _summary(
    status: str,
    plan: dict[str, Any],
    expected_seeds: list[int],
    rows: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = [number_or_default(row.get("pair_full_count"), 0, int) for row in rows]
    ready_count = sum(1 for row in rows if row.get("ready") is True)
    minimum_ready = number_or_default(plan.get("minimum_ready_replay_count"), 0, int)
    expected_seed_count = len(expected_seeds)
    observed_seed_count = len({int(row["seed"]) for row in rows})
    return {
        "seed_stability_rollup_ready": status == "pass" and ready_count >= minimum_ready and observed_seed_count == expected_seed_count,
        "acceptance_review_ready": status == "pass" and ready_count >= minimum_ready and observed_seed_count == expected_seed_count,
        "promotion_allowed": False,
        "expected_seed_count": expected_seed_count,
        "observed_seed_count": observed_seed_count,
        "ready_replay_count": ready_count,
        "minimum_ready_replay_count": minimum_ready,
        "pair_full_counts": {str(row["seed"]): row.get("pair_full_count") for row in rows},
        "min_pair_full_count": min(counts) if counts else 0,
        "max_pair_full_count": max(counts) if counts else 0,
        "uniform_pair_full_strength": len(set(counts)) <= 1 if counts else False,
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status == "pass" and summary.get("acceptance_review_ready") is True:
        return "pair_readiness_objective_level_contrast_seed_stability_ready_for_acceptance_review"
    if status == "pass":
        return "pair_readiness_objective_level_contrast_seed_stability_observed_not_ready"
    return "fix_pair_readiness_objective_level_contrast_seed_stability_rollup"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The seed stability rollup has missing, unexpected, or non-ready replay evidence.",
            "next_action": "repair the seed replay set before acceptance review",
        }
    if summary.get("acceptance_review_ready") is True:
        return {
            "model_quality_claim": "seed_stable_pair_probe_replay_candidate",
            "reason": "All planned seeds produced replay-ready evidence, with pair-full counts recorded for strength review.",
            "next_action": "run an acceptance review or promotion guard that consumes this seed stability rollup",
        }
    return {
        "model_quality_claim": "seed_stability_observed_not_ready",
        "reason": "The observed seed replay set did not satisfy the planned acceptance rule.",
        "next_action": "continue seed diagnostics before acceptance review",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_TEXT_FILENAME",
    "build_objective_level_contrast_seed_stability_rollup",
    "locate_seed_stability_rollup_plan",
    "locate_seed_stability_rollup_replay",
    "read_json_report",
    "resolve_exit_code",
]
