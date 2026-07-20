from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME = "bounded_objective_loss_signal_bridge_partial_hit_diagnostic.json"
LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME = "bounded_objective_loss_signal_bridge_partial_hit_diagnostic.csv"
LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME = "bounded_objective_loss_signal_bridge_partial_hit_diagnostic.txt"
LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME = "bounded_objective_loss_signal_bridge_partial_hit_diagnostic.md"
LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME = "bounded_objective_loss_signal_bridge_partial_hit_diagnostic.html"


def locate_loss_signal_bridge_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective loss signal bridge partial-hit diagnostic input must be a JSON object")
    return dict(payload)


def build_bounded_objective_loss_signal_bridge_partial_hit_diagnostic(
    replay_comparison: dict[str, Any],
    *,
    replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge partial-hit diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(replay_comparison.get("summary"))
    training_summary = as_dict(replay_comparison.get("loss_signal_bridge_training_summary"))
    replay_rows = list_of_dicts(replay_comparison.get("replay_rows"))
    case_rows = [_case_diagnostic(row) for row in replay_rows]
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


def _case_diagnostic(row: dict[str, Any]) -> dict[str, Any]:
    hit_terms = [str(term) for term in row.get("hit_terms", [])]
    missed_terms = [str(term) for term in row.get("missed_terms", [])]
    continuation = str(row.get("continuation") or "")
    fixed_hit = "fixed" in hit_terms
    loss_hit = "loss" in hit_terms
    if row.get("case_pass") is True:
        label = "pair_pass"
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
        "max_new_tokens": row.get("max_new_tokens"),
        "has_fixed_fragment": "fix" in continuation.lower(),
        "has_loss_fragment": "los" in continuation.lower(),
    }


def _root_causes(case_rows: list[dict[str, Any]], replay_summary: dict[str, Any], training_summary: dict[str, Any]) -> list[dict[str, Any]]:
    fixed_only = sum(1 for row in case_rows if row["label"] == "fixed_only")
    loss_only = sum(1 for row in case_rows if row["label"] == "loss_only")
    zero_hit = sum(1 for row in case_rows if row["label"] == "zero_hit")
    causes: list[dict[str, Any]] = []
    if fixed_only and loss_only and int(replay_summary.get("passed_case_count") or 0) == 0:
        causes.append(_cause("paired_term_binding_gap", "fixed and loss appear separately, but no case binds the pair."))
    if any(row["case_id"] == "completion_label_surface" and row["label"] == "zero_hit" for row in case_rows):
        causes.append(_cause("completion_surface_zero_hit", "the completion-label surface still loses both required terms."))
    if any(row["has_fixed_fragment"] or row["has_loss_fragment"] for row in case_rows):
        causes.append(_cause("fragmented_required_term_surface", "continuations show short fragments around fixed/loss instead of stable pair output."))
    if training_summary.get("decoder_anchor_example_count") == 0 and int(replay_summary.get("any_hit_case_count") or 0) > 0:
        causes.append(_cause("no_anchor_partial_signal", "partial signal is unassisted and should be repaired through pair-binding data, not decoder anchors."))
    if not causes and zero_hit:
        causes.append(_cause("weak_required_term_uptake", "partial-hit route was requested, but replay still contains zero-hit cases."))
    return causes


def _cause(cause_id: str, detail: str) -> dict[str, str]:
    return {"id": cause_id, "detail": detail}


def _checks(replay_comparison: dict[str, Any], replay_summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("replay_passed", replay_comparison.get("status") == "pass", replay_comparison.get("status"), "replay comparison must pass"),
        _check(
            "replay_ready",
            replay_summary.get("bounded_objective_loss_signal_bridge_replay_comparison_ready") is True,
            replay_summary.get("bounded_objective_loss_signal_bridge_replay_comparison_ready"),
            "loss-signal bridge replay must be ready",
        ),
        _check("not_recovered", replay_summary.get("objective_contract_recovered") is False, replay_summary.get("objective_contract_recovered"), "diagnostic only applies before contract recovery"),
        _check("has_partial_hits", int(replay_summary.get("any_hit_case_count") or 0) > 0, replay_summary.get("any_hit_case_count"), "diagnostic requires at least one required-term hit"),
        _check("has_case_rows", bool(case_rows), len(case_rows), "diagnostic needs replay rows"),
    ]


def _diagnostic(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]]) -> dict[str, Any]:
    fixed_only = sum(1 for row in case_rows if row["label"] == "fixed_only")
    loss_only = sum(1 for row in case_rows if row["label"] == "loss_only")
    return {
        "ready": status == "pass",
        "fixed_only_case_count": fixed_only,
        "loss_only_case_count": loss_only,
        "zero_hit_case_count": sum(1 for row in case_rows if row["label"] == "zero_hit"),
        "pair_pass_case_count": sum(1 for row in case_rows if row["label"] == "pair_pass"),
        "paired_signal_split": fixed_only > 0 and loss_only > 0,
        "root_cause_ids": [str(cause.get("id")) for cause in root_causes],
        "next_step": "build_bounded_objective_loss_signal_bridge_pair_binding_patch",
    }


def _summary(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_partial_hit_diagnostic_ready": status == "pass",
        "case_count": len(case_rows),
        "partial_case_count": sum(1 for row in case_rows if row["any_hit"] and not row["case_pass"]),
        "fixed_only_case_count": diagnostic.get("fixed_only_case_count"),
        "loss_only_case_count": diagnostic.get("loss_only_case_count"),
        "zero_hit_case_count": diagnostic.get("zero_hit_case_count"),
        "paired_signal_split": diagnostic.get("paired_signal_split"),
        "root_cause_count": len(root_causes),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_partial_hit_diagnostic"
    if diagnostic.get("paired_signal_split") is True:
        return "bounded_objective_loss_signal_bridge_partial_hit_pair_binding_gap"
    return "bounded_objective_loss_signal_bridge_partial_hit_surface_gap"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Partial-hit diagnostic inputs failed.", "next_action": "repair_partial_hit_diagnostic_inputs"}
    if diagnostic.get("paired_signal_split") is True:
        return {
            "model_quality_claim": "partial_signal_split_without_pair_binding",
            "reason": "The checkpoint emits fixed and loss on separate cases, so the next data patch should reinforce the ordered pair.",
            "next_action": diagnostic.get("next_step"),
        }
    return {
        "model_quality_claim": "partial_signal_surface_gap",
        "reason": "The checkpoint has partial required-term signal, but the missing surface pattern still needs targeted repair.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME",
    "build_bounded_objective_loss_signal_bridge_partial_hit_diagnostic",
    "locate_loss_signal_bridge_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
