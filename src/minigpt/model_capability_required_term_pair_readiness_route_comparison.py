from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_training_run import (
    PAIR_READINESS_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_ROUTE_COMPARISON_JSON_FILENAME = "model_capability_required_term_pair_readiness_route_comparison.json"
PAIR_READINESS_ROUTE_COMPARISON_CSV_FILENAME = "model_capability_required_term_pair_readiness_route_comparison.csv"
PAIR_READINESS_ROUTE_COMPARISON_TEXT_FILENAME = "model_capability_required_term_pair_readiness_route_comparison.txt"
PAIR_READINESS_ROUTE_COMPARISON_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_route_comparison.md"
PAIR_READINESS_ROUTE_COMPARISON_HTML_FILENAME = "model_capability_required_term_pair_readiness_route_comparison.html"


def locate_pair_readiness_route_comparison_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair-readiness route comparison input must be a JSON object")
    return dict(payload)


def build_pair_readiness_route_comparison(
    *,
    baseline_report: dict[str, Any],
    loss_retention_report: dict[str, Any],
    structured_template_report: dict[str, Any],
    fixed_recovery_report: dict[str, Any] | None = None,
    capacity_probe_report: dict[str, Any] | None = None,
    baseline_path: str | Path | None = None,
    loss_retention_path: str | Path | None = None,
    structured_template_path: str | Path | None = None,
    fixed_recovery_path: str | Path | None = None,
    capacity_probe_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [
        _row("baseline-split", baseline_report, baseline_path),
        _row("loss-retention-prefix", loss_retention_report, loss_retention_path),
        _row("structured-template", structured_template_report, structured_template_path),
    ]
    if fixed_recovery_report is not None:
        rows.append(_row("fixed-recovery", fixed_recovery_report, fixed_recovery_path))
    if capacity_probe_report is not None:
        rows.append(_row("capacity-probe", capacity_probe_report, capacity_probe_path))
    summary = _summary(rows)
    issues = _issues(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness route comparison",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "route_rows": rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _row(label: str, report: dict[str, Any], path: str | Path | None) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    replay = as_dict(report.get("replay_report"))
    default_variant = _profile_variant(replay, "default")
    suppression_variant = _profile_variant(replay, "suppress_newline_tokens")
    return {
        "label": label,
        "path": str(path or ""),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": bool(summary.get("checkpoint_exists")),
        "pair_full_observed": bool(summary.get("pair_full_observed")),
        "default_continuation_hit_count": int(summary.get("default_continuation_hit_count") or 0),
        "suppression_continuation_hit_count": int(summary.get("suppression_continuation_hit_count") or 0),
        "default_hit_terms": [str(item) for item in default_variant.get("hit_terms", [])],
        "default_missed_terms": [str(item) for item in default_variant.get("missed_terms", [])],
        "suppression_hit_terms": [str(item) for item in suppression_variant.get("hit_terms", [])],
        "model_quality_claim": as_dict(report.get("interpretation")).get("model_quality_claim", ""),
    }


def _profile_variant(replay_report: dict[str, Any], profile_id: str) -> dict[str, Any]:
    for row in list_of_dicts(replay_report.get("variant_rows")):
        if row.get("profile_id") == profile_id:
            return row
    return {}


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_label = {str(row.get("label")): row for row in rows}
    baseline = by_label["baseline-split"]
    loss_retention = by_label["loss-retention-prefix"]
    structured = by_label["structured-template"]
    fixed_recovery = by_label.get("fixed-recovery")
    capacity_probe = by_label.get("capacity-probe")
    best_hit_count = max(int(row.get("default_continuation_hit_count") or 0) for row in rows)
    best_routes = [str(row.get("label")) for row in rows if int(row.get("default_continuation_hit_count") or 0) == best_hit_count]
    pair_full_routes = [str(row.get("label")) for row in rows if row.get("pair_full_observed") is True]
    structured_vs_baseline_delta = int(structured.get("default_continuation_hit_count") or 0) - int(
        baseline.get("default_continuation_hit_count") or 0
    )
    structured_vs_loss_retention_delta = int(structured.get("default_continuation_hit_count") or 0) - int(
        loss_retention.get("default_continuation_hit_count") or 0
    )
    failure_shape_changed = structured.get("default_hit_terms") != baseline.get("default_hit_terms")
    fixed_recovery_vs_baseline_delta = _hit_delta(fixed_recovery, baseline)
    fixed_recovery_vs_structured_delta = _hit_delta(fixed_recovery, structured)
    capacity_vs_fixed_recovery_delta = _hit_delta(capacity_probe, fixed_recovery)
    capacity_vs_baseline_delta = _hit_delta(capacity_probe, baseline)
    fixed_recovery_returns_to_baseline = bool(
        fixed_recovery
        and fixed_recovery.get("default_hit_terms") == baseline.get("default_hit_terms")
        and int(fixed_recovery.get("default_continuation_hit_count") or 0) == int(baseline.get("default_continuation_hit_count") or 0)
    )
    capacity_probe_no_improvement = bool(
        capacity_probe
        and fixed_recovery
        and capacity_probe.get("default_hit_terms") == fixed_recovery.get("default_hit_terms")
        and int(capacity_probe.get("default_continuation_hit_count") or 0) == int(fixed_recovery.get("default_continuation_hit_count") or 0)
    )
    summary = {
        "route_count": len(rows),
        "best_default_hit_count": best_hit_count,
        "best_routes": best_routes,
        "pair_full_routes": pair_full_routes,
        "any_pair_full_observed": bool(pair_full_routes),
        "structured_vs_baseline_default_hit_delta": structured_vs_baseline_delta,
        "structured_vs_loss_retention_default_hit_delta": structured_vs_loss_retention_delta,
        "baseline_default_hit_terms": baseline.get("default_hit_terms"),
        "loss_retention_default_hit_terms": loss_retention.get("default_hit_terms"),
        "structured_default_hit_terms": structured.get("default_hit_terms"),
        "structured_default_missed_terms": structured.get("default_missed_terms"),
        "failure_shape_changed": failure_shape_changed,
    }
    if fixed_recovery is not None:
        summary.update(
            {
                "fixed_recovery_vs_baseline_default_hit_delta": fixed_recovery_vs_baseline_delta,
                "fixed_recovery_vs_structured_default_hit_delta": fixed_recovery_vs_structured_delta,
                "fixed_recovery_default_hit_terms": fixed_recovery.get("default_hit_terms"),
                "fixed_recovery_default_missed_terms": fixed_recovery.get("default_missed_terms"),
                "fixed_recovery_returns_to_baseline": fixed_recovery_returns_to_baseline,
            }
        )
    if capacity_probe is not None:
        summary.update(
            {
                "capacity_probe_vs_fixed_recovery_default_hit_delta": capacity_vs_fixed_recovery_delta,
                "capacity_probe_vs_baseline_default_hit_delta": capacity_vs_baseline_delta,
                "capacity_probe_default_hit_terms": capacity_probe.get("default_hit_terms"),
                "capacity_probe_default_missed_terms": capacity_probe.get("default_missed_terms"),
                "capacity_probe_no_improvement": capacity_probe_no_improvement,
            }
        )
    return summary


def _hit_delta(left: dict[str, Any] | None, right: dict[str, Any] | None) -> int | None:
    if left is None or right is None:
        return None
    return int(left.get("default_continuation_hit_count") or 0) - int(right.get("default_continuation_hit_count") or 0)


def _issues(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        if row.get("status") != "pass":
            issues.append({"id": "source_report_not_pass", "label": row.get("label"), "detail": "source training report must pass"})
        if row.get("training_status") != "pass":
            issues.append({"id": "training_not_pass", "label": row.get("label"), "detail": "training status must pass"})
        if row.get("checkpoint_exists") is not True:
            issues.append({"id": "checkpoint_missing", "label": row.get("label"), "detail": "checkpoint must exist"})
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_route_comparison_inputs"
    if summary.get("any_pair_full_observed") is True:
        return "pair_readiness_route_pair_full_candidate_found"
    if summary.get("capacity_probe_no_improvement") is True:
        return "pair_readiness_capacity_probe_no_improvement_fixed_only"
    if summary.get("fixed_recovery_returns_to_baseline") is True:
        return "pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full"
    if summary.get("structured_vs_baseline_default_hit_delta") > 0:
        return "pair_readiness_structured_template_route_improved_without_pair_full"
    if summary.get("structured_vs_baseline_default_hit_delta") < 0:
        return "pair_readiness_structured_template_route_regressed"
    if summary.get("failure_shape_changed") is True:
        return "pair_readiness_structured_template_changes_failure_shape_without_pair_full"
    return "pair_readiness_routes_flat_without_pair_full"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "One or more training reports are incomplete.",
            "next_action": "repair source training evidence before comparing routes",
        }
    if summary.get("any_pair_full_observed") is True:
        return {
            "model_quality_claim": "comparison_pair_full_candidate",
            "reason": "At least one compared route observed pair-full behavior.",
            "next_action": "run stricter heldout pair-probe replay before promotion",
        }
    if summary.get("capacity_probe_no_improvement") is True:
        return {
            "model_quality_claim": "comparison_only",
            "reason": "The capacity probe matches the fixed-recovery route's fixed-only behavior and does not recover loss.",
            "next_action": "treat this light capacity bump as closed and plan an objective-structure change before larger runs",
        }
    if summary.get("fixed_recovery_returns_to_baseline") is True:
        return {
            "model_quality_claim": "comparison_only",
            "reason": "The fixed-recovery route returns to the baseline fixed-only shape and does not preserve the structured route's loss hit.",
            "next_action": "close single-sided fixed/loss row patching and test capacity or objective structure instead",
        }
    if summary.get("failure_shape_changed") is True:
        return {
            "model_quality_claim": "comparison_only",
            "reason": "The structured-template route ties the baseline hit count but flips the hit term, so it changes the failure mode without solving pair-full.",
            "next_action": "diagnose fixed recovery or capacity before expanding the structured corpus",
        }
    return {
        "model_quality_claim": "comparison_only",
        "reason": "No compared route produced pair-full behavior.",
        "next_action": "choose the next route from the strongest non-promotion evidence",
    }


__all__ = [
    "PAIR_READINESS_ROUTE_COMPARISON_CSV_FILENAME",
    "PAIR_READINESS_ROUTE_COMPARISON_HTML_FILENAME",
    "PAIR_READINESS_ROUTE_COMPARISON_JSON_FILENAME",
    "PAIR_READINESS_ROUTE_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_READINESS_ROUTE_COMPARISON_TEXT_FILENAME",
    "build_pair_readiness_route_comparison",
    "locate_pair_readiness_route_comparison_source",
    "read_json_report",
    "resolve_exit_code",
]
