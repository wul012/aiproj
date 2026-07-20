from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, number_or_default, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.json"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.csv"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.txt"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.md"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.html"
)


def locate_objective_level_contrast_acceptance_review_rollup(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_SEED_STABILITY_ROLLUP_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-level contrast acceptance review input must be a JSON object")
    return dict(payload)


def build_objective_level_contrast_acceptance_review(
    seed_stability_rollup: dict[str, Any],
    *,
    source_rollup_path: str | Path | None = None,
    minimum_pair_full_count: int = 2,
    require_uniform_strength: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(seed_stability_rollup.get("summary"))
    rows = _seed_rows(seed_stability_rollup)
    checks = _checks(
        seed_stability_rollup,
        summary,
        rows,
        minimum_pair_full_count=minimum_pair_full_count,
        require_uniform_strength=require_uniform_strength,
    )
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    review_summary = _summary(
        status,
        summary,
        rows,
        checks,
        minimum_pair_full_count=minimum_pair_full_count,
        require_uniform_strength=require_uniform_strength,
    )
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-level contrast acceptance review",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, review_summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_seed_stability_rollup_path": str(source_rollup_path or ""),
        "source_seed_stability_rollup": {
            "status": seed_stability_rollup.get("status"),
            "decision": seed_stability_rollup.get("decision"),
            "summary": summary,
        },
        "settings": {
            "minimum_pair_full_count": int(minimum_pair_full_count),
            "require_uniform_strength": bool(require_uniform_strength),
            "review_boundary": "accept the objective-level contrast route only inside the tiny pair-probe benchmark boundary",
        },
        "seed_rows": rows,
        "check_rows": checks,
        "summary": review_summary,
        "interpretation": _interpretation(status, review_summary),
    }


def _seed_rows(rollup: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in rollup.get("seed_rows", []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "seed": number_or_default(row.get("seed"), 0, int),
                "ready": row.get("ready") is True,
                "pair_full_count": number_or_default(row.get("pair_full_count"), 0, int),
                "pair_full_rate": row.get("pair_full_rate"),
                "exact_heldout_pair_full": row.get("exact_heldout_pair_full") is True,
                "required_all_pair_full": row.get("required_all_pair_full") is True,
                "source_path": str(row.get("source_path") or ""),
            }
        )
    return rows


def _checks(
    rollup: dict[str, Any],
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    minimum_pair_full_count: int,
    require_uniform_strength: bool,
) -> list[dict[str, Any]]:
    expected_seed_count = number_or_default(summary.get("expected_seed_count"), 0, int)
    observed_seed_count = number_or_default(summary.get("observed_seed_count"), 0, int)
    ready_count = sum(1 for row in rows if row.get("ready") is True)
    counts = [number_or_default(row.get("pair_full_count"), 0, int) for row in rows]
    min_count = min(counts) if counts else 0
    max_count = max(counts) if counts else 0
    return [
        _check("rollup_passed", rollup.get("status") == "pass", rollup.get("status"), "seed stability rollup must pass"),
        _check(
            "rollup_decision_ready",
            rollup.get("decision") == "pair_readiness_objective_level_contrast_seed_stability_ready_for_acceptance_review",
            rollup.get("decision"),
            "acceptance review follows only a ready seed-stability rollup",
        ),
        _check(
            "rollup_acceptance_review_ready",
            summary.get("acceptance_review_ready") is True,
            summary.get("acceptance_review_ready"),
            "rollup must explicitly be ready for acceptance review",
        ),
        _check(
            "rollup_not_preapproved",
            summary.get("promotion_allowed") is False,
            summary.get("promotion_allowed"),
            "rollup should not have already allowed promotion before this review",
        ),
        _check(
            "observed_expected_seed_count",
            expected_seed_count > 0 and observed_seed_count == expected_seed_count and len(rows) == expected_seed_count,
            {"expected": expected_seed_count, "observed": observed_seed_count, "rows": len(rows)},
            "all expected seeds must be represented by replay rows",
        ),
        _check(
            "all_seed_replays_ready",
            bool(rows) and ready_count == len(rows),
            {"ready": ready_count, "rows": len(rows)},
            "each seed replay must be ready",
        ),
        _check(
            "minimum_pair_full_strength",
            bool(rows) and min_count >= int(minimum_pair_full_count),
            {"minimum": minimum_pair_full_count, "observed_min": min_count},
            "each accepted seed should keep enough pair-full surfaces",
        ),
        _check(
            "uniform_strength_when_required",
            (not require_uniform_strength) or min_count == max_count,
            {"min": min_count, "max": max_count, "required": require_uniform_strength},
            "uniform pair-full strength is optional unless explicitly required",
        ),
        _check(
            "rollup_checks_clean",
            number_or_default(summary.get("failed_check_count"), 0, int) == 0,
            summary.get("failed_check_count"),
            "source rollup should have no failed checks",
        ),
    ]


def _summary(
    status: str,
    rollup_summary: dict[str, Any],
    rows: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    *,
    minimum_pair_full_count: int,
    require_uniform_strength: bool,
) -> dict[str, Any]:
    counts = [number_or_default(row.get("pair_full_count"), 0, int) for row in rows]
    min_count = min(counts) if counts else 0
    max_count = max(counts) if counts else 0
    spread = max_count - min_count if counts else 0
    passed = status == "pass"
    return {
        "acceptance_review_passed": passed,
        "promotion_allowed": passed,
        "accepted_route": "objective_level_contrast" if passed else None,
        "model_quality_boundary": "tiny_required_term_pair_probe_only",
        "expected_seed_count": rollup_summary.get("expected_seed_count"),
        "observed_seed_count": rollup_summary.get("observed_seed_count"),
        "ready_replay_count": rollup_summary.get("ready_replay_count"),
        "minimum_ready_replay_count": rollup_summary.get("minimum_ready_replay_count"),
        "pair_full_counts": rollup_summary.get("pair_full_counts") or {},
        "minimum_pair_full_count": int(minimum_pair_full_count),
        "min_pair_full_count": min_count,
        "max_pair_full_count": max_count,
        "pair_full_strength_spread": spread,
        "uniform_strength_required": bool(require_uniform_strength),
        "uniform_pair_full_strength": min_count == max_count if counts else False,
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status == "pass" and summary.get("promotion_allowed") is True:
        return "pair_readiness_objective_level_contrast_acceptance_review_accepted"
    return "fix_pair_readiness_objective_level_contrast_acceptance_review"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The objective-level contrast route did not satisfy acceptance review checks.",
            "next_action": "repair seed-stability evidence or lower the route claim before promotion",
        }
    return {
        "model_quality_claim": "seed_stable_pair_probe_route_accepted",
        "reason": "All planned seed replays are ready and each seed retains the required pair-full strength.",
        "next_action": "promote the route inside the tiny pair-probe benchmark boundary and keep production claims out of scope",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_TEXT_FILENAME",
    "build_objective_level_contrast_acceptance_review",
    "locate_objective_level_contrast_acceptance_review_rollup",
    "read_json_report",
    "resolve_exit_code",
]
