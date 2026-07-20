from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_training_run import (
    PAIR_READINESS_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_BRIDGE_COMPARISON_JSON_FILENAME = "model_capability_required_term_pair_readiness_bridge_comparison.json"
PAIR_READINESS_BRIDGE_COMPARISON_CSV_FILENAME = "model_capability_required_term_pair_readiness_bridge_comparison.csv"
PAIR_READINESS_BRIDGE_COMPARISON_TEXT_FILENAME = "model_capability_required_term_pair_readiness_bridge_comparison.txt"
PAIR_READINESS_BRIDGE_COMPARISON_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_bridge_comparison.md"
PAIR_READINESS_BRIDGE_COMPARISON_HTML_FILENAME = "model_capability_required_term_pair_readiness_bridge_comparison.html"


def locate_bridge_comparison_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bridge comparison input must be a JSON object")
    return dict(payload)


def build_bridge_comparison(
    *,
    objective_training_report: dict[str, Any],
    bridge_training_report: dict[str, Any],
    objective_path: str | Path | None = None,
    bridge_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [
        _row("objective-structure", objective_training_report, objective_path),
        _row("direct-prompt-bridge", bridge_training_report, bridge_path),
    ]
    summary = _summary(rows)
    issues = _issues(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness bridge comparison",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "comparison_rows": rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


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
        if term == "loss" and fixed_present:
            loss_prompt_fixed_pollution_count += 1
        if term == "fixed" and loss_present:
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
    objective = rows[0]
    bridge = rows[1]
    hit_delta = int(bridge.get("default_continuation_hit_count") or 0) - int(objective.get("default_continuation_hit_count") or 0)
    bridge_pollution_introduced = (
        int(objective.get("loss_prompt_fixed_pollution_count") or 0) == 0
        and int(bridge.get("loss_prompt_fixed_pollution_count") or 0) > 0
    )
    return {
        "objective_default_hit_count": objective.get("default_continuation_hit_count"),
        "bridge_default_hit_count": bridge.get("default_continuation_hit_count"),
        "default_hit_delta": hit_delta,
        "bridge_improved": hit_delta > 0,
        "bridge_pair_full_observed": bridge.get("pair_full_observed"),
        "objective_non_term_surface_count": objective.get("non_term_surface_count"),
        "bridge_non_term_surface_count": bridge.get("non_term_surface_count"),
        "bridge_loss_prompt_fixed_pollution_count": bridge.get("loss_prompt_fixed_pollution_count"),
        "bridge_pollution_introduced": bridge_pollution_introduced,
        "failure_shape_changed": objective.get("continuation_previews") != bridge.get("continuation_previews"),
        "recommended_next_artifact": "pair_readiness_bridge_closeout",
    }


def _issues(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        if row.get("status") != "pass":
            issues.append({"id": f"{row.get('label')}_not_pass", "detail": "training report must pass"})
        if row.get("decision") != "pair_readiness_training_no_pair_full":
            issues.append({"id": f"{row.get('label')}_unexpected_decision", "detail": "comparison expects no-pair-full runs"})
        if row.get("checkpoint_exists") is not True:
            issues.append({"id": f"{row.get('label')}_checkpoint_missing", "detail": "checkpoint must exist"})
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_bridge_comparison_inputs"
    if summary.get("bridge_pair_full_observed") is True:
        return "pair_readiness_bridge_pair_full_candidate_found"
    if summary.get("bridge_improved") is True:
        return "pair_readiness_bridge_improved_direct_hits"
    if summary.get("bridge_pollution_introduced") is True:
        return "pair_readiness_bridge_no_improvement_introduced_fixed_pollution"
    return "pair_readiness_bridge_no_improvement"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The bridge comparison could not trust both training reports.",
            "next_action": "repair training evidence before comparing bridge effects",
        }
    if summary.get("bridge_improved") is True:
        return {
            "model_quality_claim": "comparison_only",
            "reason": "The bridge route improved direct hit count and should be replayed more strictly.",
            "next_action": "run stricter direct and pair replay before any promotion",
        }
    if summary.get("bridge_pollution_introduced") is True:
        return {
            "model_quality_claim": "comparison_only",
            "reason": "The bridge route did not improve hit count and introduced loss-prompt fixed pollution.",
            "next_action": "close this bridge patch and plan a different objective surface instead of adding more bridge rows",
        }
    return {
        "model_quality_claim": "comparison_only",
        "reason": "The bridge route did not improve direct hit count.",
        "next_action": "close or redesign the bridge route before further training",
    }


__all__ = [
    "PAIR_READINESS_BRIDGE_COMPARISON_CSV_FILENAME",
    "PAIR_READINESS_BRIDGE_COMPARISON_HTML_FILENAME",
    "PAIR_READINESS_BRIDGE_COMPARISON_JSON_FILENAME",
    "PAIR_READINESS_BRIDGE_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_READINESS_BRIDGE_COMPARISON_TEXT_FILENAME",
    "build_bridge_comparison",
    "locate_bridge_comparison_source",
    "read_json_report",
    "resolve_exit_code",
]
