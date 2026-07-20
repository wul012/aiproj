from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_pair_binding_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic.json"
PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic.csv"
PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic.txt"
PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic.md"
PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic.html"


def locate_pair_binding_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / LOSS_SIGNAL_BRIDGE_PAIR_BINDING_REPLAY_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair-binding zero-hit diagnostic input must be a JSON object")
    return dict(payload)


def build_pair_binding_zero_hit_diagnostic(
    replay_comparison: dict[str, Any],
    *,
    replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge pair-binding zero-hit diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(replay_comparison.get("summary"))
    training_summary = as_dict(replay_comparison.get("pair_binding_training_summary"))
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
    continuation = str(row.get("continuation") or "")
    normalized = " ".join(continuation.lower().split())
    label_echo = normalized.startswith("answer") or normalized.startswith("ans") or normalized.startswith("completion")
    return {
        "case_id": row.get("case_id"),
        "continuation": continuation,
        "normalized_continuation": normalized,
        "case_pass": row.get("case_pass") is True,
        "any_hit": row.get("any_hit") is True,
        "hit_terms": [str(term) for term in row.get("hit_terms", [])],
        "missed_terms": [str(term) for term in row.get("missed_terms", [])],
        "label_echo": label_echo,
        "empty_or_label_only": label_echo or normalized == "",
        "continuation_len": len(continuation),
    }


def _root_causes(case_rows: list[dict[str, Any]], replay_summary: dict[str, Any], training_summary: dict[str, Any]) -> list[dict[str, str]]:
    causes: list[dict[str, str]] = []
    if case_rows and all(row["label_echo"] for row in case_rows):
        causes.append(_cause("label_echo_over_target_terms", "all continuations echo answer/completion labels instead of fixed loss."))
    if int(replay_summary.get("any_hit_case_count") or 0) == 0 and int(replay_summary.get("zero_hit_case_count") or 0) == len(case_rows):
        causes.append(_cause("partial_signal_regressed_to_zero_hit", "pair-binding training regressed the prior partial required-term signal to zero-hit replay."))
    if training_summary.get("decoder_anchor_example_count") == 0:
        causes.append(_cause("no_anchor_failure_needs_surface_repair", "failure remains unassisted; repair should target surface format rather than decoder anchors."))
    if any(row["continuation_len"] <= 8 for row in case_rows):
        causes.append(_cause("short_decode_label_fragment", "short continuations are consumed by label fragments before target terms appear."))
    return causes


def _cause(cause_id: str, detail: str) -> dict[str, str]:
    return {"id": cause_id, "detail": detail}


def _checks(replay: dict[str, Any], summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("replay_passed", replay.get("status") == "pass", replay.get("status"), "pair-binding replay must pass structurally"),
        _check(
            "replay_ready",
            summary.get("bounded_objective_loss_signal_bridge_pair_binding_replay_comparison_ready") is True,
            summary.get("bounded_objective_loss_signal_bridge_pair_binding_replay_comparison_ready"),
            "pair-binding replay must be ready",
        ),
        _check("zero_hit_replay", int(summary.get("any_hit_case_count") or 0) == 0, summary.get("any_hit_case_count"), "diagnostic only applies to zero-hit replay"),
        _check("not_recovered", summary.get("objective_contract_recovered") is False, summary.get("objective_contract_recovered"), "diagnostic only applies before recovery"),
        _check("case_rows_present", bool(case_rows), len(case_rows), "diagnostic needs replay rows"),
    ]


def _diagnostic(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, str]]) -> dict[str, Any]:
    label_echo_count = sum(1 for row in case_rows if row["label_echo"])
    return {
        "ready": status == "pass",
        "label_echo_case_count": label_echo_count,
        "zero_hit_case_count": sum(1 for row in case_rows if not row["any_hit"]),
        "all_cases_label_echo": bool(case_rows) and label_echo_count == len(case_rows),
        "root_cause_ids": [cause["id"] for cause in root_causes],
        "next_step": "build_single_line_completion_surface_patch",
    }


def _summary(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, str]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic_ready": status == "pass",
        "case_count": len(case_rows),
        "label_echo_case_count": diagnostic.get("label_echo_case_count"),
        "zero_hit_case_count": diagnostic.get("zero_hit_case_count"),
        "all_cases_label_echo": diagnostic.get("all_cases_label_echo"),
        "root_cause_count": len(root_causes),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic"
    if diagnostic.get("all_cases_label_echo") is True:
        return "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_label_echo"
    return "bounded_objective_loss_signal_bridge_pair_binding_zero_hit_surface_gap"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Zero-hit diagnostic inputs failed.", "next_action": "repair_zero_hit_diagnostic_inputs"}
    if diagnostic.get("all_cases_label_echo") is True:
        return {
            "model_quality_claim": "label_echo_regression",
            "reason": "The checkpoint echoed answer/completion labels on every case, so the next patch should favor single-line target completions.",
            "next_action": diagnostic.get("next_step"),
        }
    return {
        "model_quality_claim": "zero_hit_surface_gap",
        "reason": "The checkpoint produced zero required-term hits and needs a surface-specific repair.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME",
    "build_pair_binding_zero_hit_diagnostic",
    "locate_pair_binding_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
