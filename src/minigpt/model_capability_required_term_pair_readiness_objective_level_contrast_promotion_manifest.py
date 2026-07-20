from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, number_or_default, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.json"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.csv"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.txt"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.md"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.html"
)


def locate_objective_level_contrast_promotion_manifest_acceptance_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_ACCEPTANCE_REVIEW_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-level contrast promotion manifest input must be a JSON object")
    return dict(payload)


def build_objective_level_contrast_promotion_manifest(
    acceptance_review: dict[str, Any],
    *,
    source_acceptance_review_path: str | Path | None = None,
    route_id: str = "objective_level_contrast",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(acceptance_review.get("summary"))
    interpretation = as_dict(acceptance_review.get("interpretation"))
    source_rollup = as_dict(acceptance_review.get("source_seed_stability_rollup"))
    source_rollup_summary = as_dict(source_rollup.get("summary"))
    seed_rows = _seed_rows(acceptance_review)
    checks = _checks(acceptance_review, summary, interpretation, source_rollup_summary, seed_rows, route_id=route_id)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    manifest = _manifest(status, summary, interpretation, source_rollup_summary, seed_rows, route_id=route_id)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-level contrast promotion manifest",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_acceptance_review_path": str(source_acceptance_review_path or ""),
        "source_acceptance_review": {
            "status": acceptance_review.get("status"),
            "decision": acceptance_review.get("decision"),
            "summary": summary,
            "interpretation": interpretation,
        },
        "source_seed_stability_rollup_path": str(acceptance_review.get("source_seed_stability_rollup_path") or ""),
        "check_rows": checks,
        "seed_rows": seed_rows,
        "manifest": manifest,
        "summary": _summary(status, checks, manifest),
        "interpretation": _interpretation(status, manifest),
    }


def _seed_rows(acceptance_review: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in list_of_dicts(acceptance_review.get("seed_rows")):
        rows.append(
            {
                "seed": number_or_default(row.get("seed"), 0, int),
                "ready": row.get("ready") is True,
                "pair_full_count": number_or_default(row.get("pair_full_count"), 0, int),
                "pair_full_rate": row.get("pair_full_rate"),
                "source_path": str(row.get("source_path") or ""),
            }
        )
    return rows


def _checks(
    acceptance_review: dict[str, Any],
    summary: dict[str, Any],
    interpretation: dict[str, Any],
    source_rollup_summary: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    *,
    route_id: str,
) -> list[dict[str, Any]]:
    return [
        _check("acceptance_review_passed", acceptance_review.get("status") == "pass", acceptance_review.get("status"), "acceptance review must pass"),
        _check(
            "acceptance_decision",
            acceptance_review.get("decision") == "pair_readiness_objective_level_contrast_acceptance_review_accepted",
            acceptance_review.get("decision"),
            "promotion manifest follows only an accepted objective-level contrast review",
        ),
        _check(
            "promotion_allowed",
            summary.get("promotion_allowed") is True,
            summary.get("promotion_allowed"),
            "acceptance review must allow promotion inside its declared boundary",
        ),
        _check(
            "route_id_matches",
            summary.get("accepted_route") == route_id,
            summary.get("accepted_route"),
            "accepted route must match manifest route id",
        ),
        _check(
            "boundary_scoped",
            summary.get("model_quality_boundary") == "tiny_required_term_pair_probe_only",
            summary.get("model_quality_boundary"),
            "promotion manifest must preserve the tiny pair-probe boundary",
        ),
        _check(
            "claim_scoped",
            interpretation.get("model_quality_claim") == "seed_stable_pair_probe_route_accepted",
            interpretation.get("model_quality_claim"),
            "accepted claim must remain route/probe scoped",
        ),
        _check(
            "seed_rows_present",
            bool(seed_rows) and all(row.get("ready") is True for row in seed_rows),
            {"seed_count": len(seed_rows), "ready": sum(1 for row in seed_rows if row.get("ready") is True)},
            "manifest should carry ready seed evidence",
        ),
        _check(
            "source_rollup_was_review_ready",
            source_rollup_summary.get("acceptance_review_ready") is True,
            source_rollup_summary.get("acceptance_review_ready"),
            "manifest must trace back to a review-ready seed-stability rollup",
        ),
    ]


def _manifest(
    status: str,
    summary: dict[str, Any],
    interpretation: dict[str, Any],
    source_rollup_summary: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    *,
    route_id: str,
) -> dict[str, Any]:
    promotion_ready = status == "pass"
    return {
        "route_id": route_id,
        "route_status": "promoted" if promotion_ready else "blocked",
        "promotion_ready": promotion_ready,
        "promotion_scope": summary.get("model_quality_boundary") or "tiny_required_term_pair_probe_only",
        "model_quality_claim": interpretation.get("model_quality_claim") or "not_claimed",
        "accepted_seed_count": len(seed_rows),
        "ready_replay_count": summary.get("ready_replay_count"),
        "minimum_ready_replay_count": summary.get("minimum_ready_replay_count"),
        "pair_full_counts": summary.get("pair_full_counts") or {},
        "min_pair_full_count": summary.get("min_pair_full_count"),
        "max_pair_full_count": summary.get("max_pair_full_count"),
        "pair_full_strength_spread": summary.get("pair_full_strength_spread"),
        "source_rollup_expected_seed_count": source_rollup_summary.get("expected_seed_count"),
        "source_rollup_observed_seed_count": source_rollup_summary.get("observed_seed_count"),
        "benchmark_history_entry": {
            "entry_type": "model_capability_route_promotion",
            "route_id": route_id,
            "status": "ready" if promotion_ready else "blocked",
            "boundary": summary.get("model_quality_boundary") or "tiny_required_term_pair_probe_only",
            "model_quality_claim": interpretation.get("model_quality_claim") or "not_claimed",
            "seed_count": len(seed_rows),
            "min_pair_full_count": summary.get("min_pair_full_count"),
            "pair_full_strength_spread": summary.get("pair_full_strength_spread"),
        },
    }


def _summary(status: str, checks: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "promotion_manifest_ready": status == "pass" and manifest.get("promotion_ready") is True,
        "promoted_route_id": manifest.get("route_id") if status == "pass" else None,
        "route_status": manifest.get("route_status"),
        "can_feed_benchmark_history": status == "pass",
        "benchmark_history_entry_status": as_dict(manifest.get("benchmark_history_entry")).get("status"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_objective_level_contrast_promotion_manifest_ready"
    return "fix_pair_readiness_objective_level_contrast_promotion_manifest"


def _interpretation(status: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The accepted route could not be converted into a promotion manifest.",
            "next_action": "repair the acceptance review before exporting a benchmark-history entry",
        }
    return {
        "model_quality_claim": manifest.get("model_quality_claim"),
        "reason": "The accepted objective-level contrast route is now represented as a benchmark-history-ready promotion manifest.",
        "next_action": "append the manifest benchmark_history_entry to the model capability benchmark history",
    }


__all__ = [
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_TEXT_FILENAME",
    "build_objective_level_contrast_promotion_manifest",
    "locate_objective_level_contrast_promotion_manifest_acceptance_review",
    "read_json_report",
    "resolve_exit_code",
]
