from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_training_run import (
    PAIR_READINESS_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_route_comparison.json"
)
PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_route_comparison.csv"
)
PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_route_comparison.txt"
)
PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_route_comparison.md"
)
PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_route_comparison.html"
)


def locate_direct_completion_route_comparison_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("direct-completion route comparison input must be a JSON object")
    return dict(payload)


def build_direct_completion_route_comparison(
    *,
    objective_training_report: dict[str, Any],
    bridge_training_report: dict[str, Any],
    direct_completion_training_report: dict[str, Any],
    objective_path: str | Path | None = None,
    bridge_path: str | Path | None = None,
    direct_completion_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [
        _row("objective-structure", objective_training_report, objective_path),
        _row("direct-prompt-bridge", bridge_training_report, bridge_path),
        _row("direct-completion-surface", direct_completion_training_report, direct_completion_path),
    ]
    issues = _issues(rows)
    status = "pass" if not issues else "fail"
    summary = _summary(rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness direct-completion route comparison",
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
    analysis = _replay_analysis(report)
    return {
        "label": label,
        "path": str(path or ""),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": summary.get("checkpoint_exists"),
        "pair_full_observed": summary.get("pair_full_observed"),
        "default_continuation_hit_count": analysis["hit_count"],
        "default_hit_terms": analysis["hit_terms"],
        "default_missed_terms": analysis["missed_terms"],
        "loss_prompt_fixed_pollution_count": analysis["loss_prompt_fixed_pollution_count"],
        "fixed_prompt_loss_pollution_count": analysis["fixed_prompt_loss_pollution_count"],
        "non_term_surface_count": analysis["non_term_surface_count"],
        "suppression_continuation_hit_count": summary.get("suppression_continuation_hit_count"),
        "continuation_previews": analysis["continuation_previews"],
    }


def _replay_analysis(report: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in list_of_dicts(as_dict(report.get("replay_report")).get("case_rows")) if row.get("profile_id") == "default"]
    hit_terms: list[str] = []
    missed_terms: list[str] = []
    loss_prompt_fixed_pollution_count = 0
    fixed_prompt_loss_pollution_count = 0
    non_term_surface_count = 0
    previews: list[str] = []
    for row in rows:
        term = str(row.get("term") or "")
        continuation = str(row.get("continuation") or "").rstrip()
        previews.append(f"{term}:{continuation}")
        if row.get("continuation_hit"):
            hit_terms.append(term)
        else:
            missed_terms.append(term)
        fixed_present = "fixed" in continuation
        loss_present = "loss" in continuation
        if term == "loss" and fixed_present and not row.get("continuation_hit"):
            loss_prompt_fixed_pollution_count += 1
        if term == "fixed" and loss_present and not row.get("continuation_hit"):
            fixed_prompt_loss_pollution_count += 1
        if not fixed_present and not loss_present:
            non_term_surface_count += 1
    return {
        "hit_count": len(hit_terms),
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "loss_prompt_fixed_pollution_count": loss_prompt_fixed_pollution_count,
        "fixed_prompt_loss_pollution_count": fixed_prompt_loss_pollution_count,
        "non_term_surface_count": non_term_surface_count,
        "continuation_previews": previews,
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    objective, bridge, direct = rows
    previous_best = max(int(objective.get("default_continuation_hit_count") or 0), int(bridge.get("default_continuation_hit_count") or 0))
    direct_hits = int(direct.get("default_continuation_hit_count") or 0)
    direct_pollution = int(direct.get("loss_prompt_fixed_pollution_count") or 0) + int(direct.get("fixed_prompt_loss_pollution_count") or 0)
    direct_pair_full = direct.get("pair_full_observed") is True
    return {
        "objective_default_hit_count": objective.get("default_continuation_hit_count"),
        "bridge_default_hit_count": bridge.get("default_continuation_hit_count"),
        "direct_completion_default_hit_count": direct_hits,
        "previous_best_hit_count": previous_best,
        "direct_completion_hit_delta_from_previous_best": direct_hits - previous_best,
        "direct_completion_pair_full_observed": direct_pair_full,
        "direct_completion_pollution_count": direct_pollution,
        "direct_completion_pollution_free": direct_pollution == 0,
        "direct_completion_suppression_hit_count": direct.get("suppression_continuation_hit_count"),
        "direct_completion_candidate": direct_pair_full and direct_hits > previous_best and direct_pollution == 0,
        "selected_route": "direct-completion-surface" if direct_pair_full and direct_hits > previous_best else "",
        "recommended_next_artifact": "pair_readiness_direct_completion_pair_probe_replay",
    }


def _issues(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        label = str(row.get("label"))
        if row.get("status") != "pass":
            issues.append({"id": f"{label}_not_pass", "detail": "training report must pass"})
        if row.get("training_status") != "pass":
            issues.append({"id": f"{label}_training_not_pass", "detail": "underlying training run must pass"})
        if row.get("checkpoint_exists") is not True:
            issues.append({"id": f"{label}_checkpoint_missing", "detail": "checkpoint must exist"})
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_direct_completion_route_comparison_inputs"
    if summary.get("direct_completion_candidate") is True:
        return "pair_readiness_direct_completion_route_candidate_found"
    if summary.get("direct_completion_pair_full_observed") is True:
        return "pair_readiness_direct_completion_pair_full_with_review_flags"
    if int(summary.get("direct_completion_hit_delta_from_previous_best") or 0) > 0:
        return "pair_readiness_direct_completion_partial_improvement"
    return "pair_readiness_direct_completion_no_improvement"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "One or more route training reports are not trustworthy enough to compare.",
            "next_action": "repair training evidence before route comparison",
        }
    if summary.get("direct_completion_candidate") is True:
        return {
            "model_quality_claim": "comparison_candidate",
            "reason": "The direct-completion surface route beats prior objective/bridge routes on default direct hits without direct pollution.",
            "next_action": "run pair-probe replay and stricter promotion checks before accepting this route",
        }
    if summary.get("direct_completion_pair_full_observed") is True:
        return {
            "model_quality_claim": "comparison_with_review_flags",
            "reason": "The direct-completion route reached pair-full but still has comparison flags that need review.",
            "next_action": "inspect pollution and suppression profiles before promotion",
        }
    return {
        "model_quality_claim": "comparison_only",
        "reason": "The direct-completion route does not beat the previous best direct-hit count.",
        "next_action": "close or redesign the direct-completion surface route",
    }


__all__ = [
    "PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_CSV_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_HTML_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_JSON_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_TEXT_FILENAME",
    "build_direct_completion_route_comparison",
    "locate_direct_completion_route_comparison_source",
    "read_json_report",
    "resolve_exit_code",
]
