from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison import (
    TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic.json"
)
TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic.csv"
)
TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic.txt"
)
TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic.md"
)
TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic.html"
)


def locate_target_only_memory_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective loss signal bridge target-only memory partial-hit diagnostic input must be a JSON object")
    return dict(payload)


def build_target_only_memory_partial_hit_diagnostic(
    replay_comparison: dict[str, Any],
    *,
    replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory partial-hit diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(replay_comparison.get("summary"))
    training_summary = as_dict(replay_comparison.get("target_only_memory_training_summary"))
    case_rows = [_case_diagnostic(row) for row in list_of_dicts(replay_comparison.get("replay_rows"))]
    root_causes = _root_causes(case_rows, replay_summary, training_summary)
    checks = _checks(replay_comparison, replay_summary, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    diagnostic = _diagnostic(status, case_rows, root_causes)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, diagnostic),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_comparison": str(replay_comparison_path or ""),
        "replay_summary": replay_summary,
        "training_summary": training_summary,
        "case_diagnostics": case_rows,
        "root_causes": root_causes,
        "check_rows": checks,
        "diagnostic": diagnostic,
        "summary": _summary(status, case_rows, root_causes, diagnostic),
        "interpretation": _interpretation(status, diagnostic),
    }


def resolve_exit_code(report: dict[str, Any], *, require_diagnostic_ready: bool) -> int:
    return 1 if require_diagnostic_ready and report.get("status") != "pass" else 0


def _case_diagnostic(row: dict[str, Any]) -> dict[str, Any]:
    hit_terms = [str(term) for term in row.get("hit_terms", [])]
    missed_terms = [str(term) for term in row.get("missed_terms", [])]
    continuation = str(row.get("continuation") or "")
    normalized = continuation.lower().strip()
    fixed_hit = "fixed" in hit_terms
    loss_hit = "loss" in hit_terms
    has_loss_prefix = "los" in normalized or normalized.endswith(" l")
    if row.get("case_pass") is True:
        label = "pair_pass"
    elif fixed_hit and not loss_hit and has_loss_prefix:
        label = "fixed_with_loss_prefix"
    elif fixed_hit and not loss_hit:
        label = "fixed_only"
    elif loss_hit and not fixed_hit:
        label = "loss_only"
    elif hit_terms:
        label = "other_partial"
    else:
        label = "zero_hit"
    return {
        "case_id": row.get("case_id"),
        "label": label,
        "case_pass": row.get("case_pass") is True,
        "any_hit": bool(hit_terms),
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "continuation": continuation,
        "continuation_len": len(continuation),
        "has_fixed": fixed_hit,
        "has_loss": loss_hit,
        "has_loss_prefix": has_loss_prefix,
        "completion_budget_used": row.get("max_new_tokens"),
    }


def _root_causes(case_rows: list[dict[str, Any]], replay_summary: dict[str, Any], training_summary: dict[str, Any]) -> list[dict[str, Any]]:
    fixed_prefix = sum(1 for row in case_rows if row["label"] == "fixed_with_loss_prefix")
    fixed_only = sum(1 for row in case_rows if row["label"] in {"fixed_only", "fixed_with_loss_prefix"})
    loss_hit = sum(1 for row in case_rows if row["has_loss"])
    causes: list[dict[str, Any]] = []
    if case_rows and fixed_prefix == len(case_rows) and loss_hit == 0:
        causes.append(_cause("loss_suffix_uptake_gap", "all cases reach fixed and a loss prefix, but none complete the loss token."))
    if fixed_only == int(replay_summary.get("any_hit_case_count") or 0) and loss_hit == 0:
        causes.append(_cause("fixed_dominates_required_pair", "target-only memory strengthened fixed more than the full fixed loss pair."))
    if training_summary.get("decoder_anchor_example_count") == 0:
        causes.append(_cause("no_anchor_partial_signal", "partial signal is unassisted; next repair should remain data-level unless replay regresses."))
    if int(replay_summary.get("passed_case_count") or 0) == 0 and int(replay_summary.get("any_hit_case_count") or 0) > 0:
        causes.append(_cause("partial_signal_without_contract_pass", "required-term signal improved, but no case satisfies the full objective."))
    return causes


def _cause(cause_id: str, detail: str) -> dict[str, str]:
    return {"id": cause_id, "detail": detail}


def _checks(replay_comparison: dict[str, Any], replay_summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("replay_passed", replay_comparison.get("status") == "pass", replay_comparison.get("status"), "replay comparison must pass"),
        _check(
            "target_only_memory_replay_ready",
            replay_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison_ready") is True,
            replay_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison_ready"),
            "target-only memory replay comparison must be ready",
        ),
        _check("not_recovered", replay_summary.get("objective_contract_recovered") is False, replay_summary.get("objective_contract_recovered"), "diagnostic only applies before contract recovery"),
        _check("has_partial_hits", int(replay_summary.get("any_hit_case_count") or 0) > 0, replay_summary.get("any_hit_case_count"), "diagnostic requires at least one required-term hit"),
        _check("has_case_rows", bool(case_rows), len(case_rows), "diagnostic needs replay rows"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _diagnostic(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]]) -> dict[str, Any]:
    loss_prefix = sum(1 for row in case_rows if row["label"] == "fixed_with_loss_prefix")
    fixed_without_loss = sum(1 for row in case_rows if row["has_fixed"] and not row["has_loss"])
    loss_hit = sum(1 for row in case_rows if row["has_loss"])
    root_ids = [str(cause.get("id")) for cause in root_causes]
    return {
        "ready": status == "pass",
        "fixed_without_loss_case_count": fixed_without_loss,
        "loss_hit_case_count": loss_hit,
        "loss_prefix_case_count": loss_prefix,
        "all_cases_fixed_without_loss": bool(case_rows) and fixed_without_loss == len(case_rows),
        "all_cases_loss_prefix": bool(case_rows) and loss_prefix == len(case_rows),
        "root_cause_ids": root_ids,
        "next_step": "build_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch",
    }


def _summary(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic_ready": status == "pass",
        "case_count": len(case_rows),
        "partial_case_count": sum(1 for row in case_rows if row["any_hit"] and not row["case_pass"]),
        "fixed_without_loss_case_count": diagnostic.get("fixed_without_loss_case_count"),
        "loss_hit_case_count": diagnostic.get("loss_hit_case_count"),
        "loss_prefix_case_count": diagnostic.get("loss_prefix_case_count"),
        "all_cases_fixed_without_loss": diagnostic.get("all_cases_fixed_without_loss"),
        "all_cases_loss_prefix": diagnostic.get("all_cases_loss_prefix"),
        "root_cause_count": len(root_causes),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic"
    if diagnostic.get("all_cases_loss_prefix") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_loss_suffix_gap"
    return "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_surface_gap"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Target-only memory partial-hit diagnostic inputs failed.", "next_action": "repair_target_only_memory_partial_hit_diagnostic_inputs"}
    if diagnostic.get("all_cases_loss_prefix") is True:
        return {
            "model_quality_claim": "fixed_prefix_recovered_loss_suffix_missing",
            "reason": "The checkpoint consistently reaches fixed and a loss prefix, but still fails to emit the complete loss term.",
            "next_action": diagnostic.get("next_step"),
        }
    return {
        "model_quality_claim": "partial_required_term_signal_needs_surface_repair",
        "reason": "The checkpoint has partial required-term signal, but the remaining surface gap is not uniform.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME",
    "build_target_only_memory_partial_hit_diagnostic",
    "locate_target_only_memory_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
