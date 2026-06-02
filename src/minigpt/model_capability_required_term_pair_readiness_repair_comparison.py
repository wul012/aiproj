from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_training_run import (
    PAIR_READINESS_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_READINESS_REPAIR_COMPARISON_JSON_FILENAME = "model_capability_required_term_pair_readiness_repair_comparison.json"
PAIR_READINESS_REPAIR_COMPARISON_CSV_FILENAME = "model_capability_required_term_pair_readiness_repair_comparison.csv"
PAIR_READINESS_REPAIR_COMPARISON_TEXT_FILENAME = "model_capability_required_term_pair_readiness_repair_comparison.txt"
PAIR_READINESS_REPAIR_COMPARISON_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_repair_comparison.md"
PAIR_READINESS_REPAIR_COMPARISON_HTML_FILENAME = "model_capability_required_term_pair_readiness_repair_comparison.html"


def locate_pair_readiness_repair_comparison_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair-readiness repair comparison input must be a JSON object")
    return dict(payload)


def build_pair_readiness_repair_comparison(
    *,
    baseline_report: dict[str, Any],
    candidate_report: dict[str, Any],
    baseline_path: str | Path | None = None,
    candidate_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [_row("baseline", baseline_report, baseline_path), _row("loss-retention-candidate", candidate_report, candidate_path)]
    summary = _summary(rows)
    issues = _issues(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness repair comparison",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "comparison_rows": rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _row(label: str, report: dict[str, Any], path: str | Path | None) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    return {
        "label": label,
        "path": str(path or ""),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": summary.get("checkpoint_exists"),
        "pair_full_observed": bool(summary.get("pair_full_observed")),
        "default_continuation_hit_count": int(summary.get("default_continuation_hit_count") or 0),
        "suppression_continuation_hit_count": int(summary.get("suppression_continuation_hit_count") or 0),
        "model_quality_claim": as_dict(report.get("interpretation")).get("model_quality_claim", ""),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = rows[0]
    candidate = rows[1]
    default_delta = int(candidate.get("default_continuation_hit_count") or 0) - int(baseline.get("default_continuation_hit_count") or 0)
    suppression_delta = int(candidate.get("suppression_continuation_hit_count") or 0) - int(
        baseline.get("suppression_continuation_hit_count") or 0
    )
    return {
        "baseline_default_hit_count": baseline.get("default_continuation_hit_count"),
        "candidate_default_hit_count": candidate.get("default_continuation_hit_count"),
        "default_hit_delta": default_delta,
        "suppression_hit_delta": suppression_delta,
        "baseline_pair_full_observed": baseline.get("pair_full_observed"),
        "candidate_pair_full_observed": candidate.get("pair_full_observed"),
        "candidate_improved": bool(candidate.get("pair_full_observed")) or default_delta > 0,
        "candidate_regressed": default_delta < 0,
    }


def _issues(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        if row.get("status") != "pass":
            issues.append({"id": "source_report_not_pass", "label": row.get("label"), "detail": "source training report must pass"})
        if row.get("checkpoint_exists") is not True:
            issues.append({"id": "checkpoint_missing", "label": row.get("label"), "detail": "source checkpoint must exist"})
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_repair_comparison_inputs"
    if summary.get("candidate_improved") is True:
        return "pair_readiness_repair_candidate_improved"
    if summary.get("candidate_regressed") is True:
        return "pair_readiness_loss_retention_patch_regressed"
    return "pair_readiness_repair_candidate_flat"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Comparison inputs are incomplete.",
            "next_action": "repair source training reports before drawing a route conclusion",
        }
    if summary.get("candidate_regressed") is True:
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The loss-retention patch reduced heldout direct hits versus the baseline split run.",
            "next_action": "close this repair route and avoid more single-sided prefix weighting",
        }
    return {
        "model_quality_claim": "comparison_only",
        "reason": "The candidate did not regress but also did not prove pair capability.",
        "next_action": "run a stricter heldout pair probe only after direct probes improve",
    }


__all__ = [
    "PAIR_READINESS_REPAIR_COMPARISON_CSV_FILENAME",
    "PAIR_READINESS_REPAIR_COMPARISON_HTML_FILENAME",
    "PAIR_READINESS_REPAIR_COMPARISON_JSON_FILENAME",
    "PAIR_READINESS_REPAIR_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_READINESS_REPAIR_COMPARISON_TEXT_FILENAME",
    "build_pair_readiness_repair_comparison",
    "locate_pair_readiness_repair_comparison_source",
    "read_json_report",
    "resolve_exit_code",
]
