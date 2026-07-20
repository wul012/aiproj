from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic.json"
)
SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic.csv"
)
SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic.txt"
)
SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic.md"
)
SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic.html"
)


def locate_single_line_surface_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("single-line surface zero-hit diagnostic input must be a JSON object")
    return dict(payload)


def build_single_line_surface_zero_hit_diagnostic(
    replay_comparison: dict[str, Any],
    *,
    replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge single-line surface zero-hit diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(replay_comparison.get("summary"))
    training_summary = as_dict(replay_comparison.get("single_line_surface_training_summary"))
    replay_rows = list_of_dicts(replay_comparison.get("replay_rows"))
    case_rows = [_case_diagnostic(row) for row in replay_rows]
    root_causes = _root_causes(case_rows, replay_summary, training_summary)
    checks = _checks(replay_comparison, replay_summary, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    diagnostic = _diagnostic(status, case_rows, root_causes, replay_summary, training_summary)
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
    exact_label_echo = normalized in {"answer", "answer:", "ans", "ans:", "completion", "completion:"}
    label_prefix_fragment = not exact_label_echo and (
        normalized.startswith("answer") or normalized.startswith("ans") or normalized.startswith("completion")
    )
    continuation_class = _continuation_class(normalized, exact_label_echo, label_prefix_fragment)
    return {
        "case_id": row.get("case_id"),
        "continuation": continuation,
        "normalized_continuation": normalized,
        "continuation_class": continuation_class,
        "case_pass": row.get("case_pass") is True,
        "any_hit": row.get("any_hit") is True,
        "hit_terms": [str(term) for term in row.get("hit_terms", [])],
        "missed_terms": [str(term) for term in row.get("missed_terms", [])],
        "exact_label_echo": exact_label_echo,
        "label_prefix_fragment": label_prefix_fragment,
        "label_or_fragment": exact_label_echo or label_prefix_fragment,
        "continuation_len": len(continuation),
    }


def _continuation_class(normalized: str, exact_label_echo: bool, label_prefix_fragment: bool) -> str:
    if normalized == "":
        return "empty"
    if exact_label_echo:
        return "exact_label_echo"
    if label_prefix_fragment:
        return "label_prefix_fragment"
    return "non_target_fragment"


def _root_causes(
    case_rows: list[dict[str, Any]],
    replay_summary: dict[str, Any],
    training_summary: dict[str, Any],
) -> list[dict[str, str]]:
    causes: list[dict[str, str]] = []
    if case_rows and all(row["label_or_fragment"] for row in case_rows):
        causes.append(_cause("label_echo_persisted_after_single_line_patch", "all continuations remain answer/completion label echoes or label-prefix fragments."))
    if sum(1 for row in case_rows if row["exact_label_echo"]) >= 2:
        causes.append(_cause("answer_label_echo_still_dominant", "multiple direct-answer cases still emit answer labels instead of target terms."))
    if any(row["label_prefix_fragment"] for row in case_rows):
        causes.append(_cause("completion_label_fragment", "at least one continuation is a label-prefix fragment such as ans... rather than fixed loss."))
    if float(training_summary.get("train_loss_delta") or 0.0) < 0 and int(replay_summary.get("any_hit_case_count") or 0) == 0:
        causes.append(_cause("loss_improved_without_required_term_uptake", "training loss improved, but replay still has zero required-term hits."))
    if training_summary.get("decoder_anchor_example_count") == 0:
        causes.append(_cause("no_anchor_surface_failure", "failure remains on the unassisted no-anchor route."))
    if case_rows and all(int(row["continuation_len"] or 0) <= 8 for row in case_rows):
        causes.append(_cause("short_decode_budget_consumed_by_label", "short continuations are consumed by labels or fragments before target terms appear."))
    return causes


def _cause(cause_id: str, detail: str) -> dict[str, str]:
    return {"id": cause_id, "detail": detail}


def _checks(replay: dict[str, Any], summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("replay_passed", replay.get("status") == "pass", replay.get("status"), "single-line surface replay must pass structurally"),
        _check(
            "replay_ready",
            summary.get("bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_ready") is True,
            summary.get("bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_ready"),
            "single-line surface replay must be ready",
        ),
        _check("zero_hit_replay", int(summary.get("any_hit_case_count") or 0) == 0, summary.get("any_hit_case_count"), "diagnostic only applies to zero-hit replay"),
        _check("not_recovered", summary.get("objective_contract_recovered") is False, summary.get("objective_contract_recovered"), "diagnostic only applies before recovery"),
        _check("case_rows_present", bool(case_rows), len(case_rows), "diagnostic needs replay rows"),
    ]


def _diagnostic(
    status: str,
    case_rows: list[dict[str, Any]],
    root_causes: list[dict[str, str]],
    replay_summary: dict[str, Any],
    training_summary: dict[str, Any],
) -> dict[str, Any]:
    exact_echo_count = sum(1 for row in case_rows if row["exact_label_echo"])
    fragment_count = sum(1 for row in case_rows if row["label_prefix_fragment"])
    label_or_fragment_count = sum(1 for row in case_rows if row["label_or_fragment"])
    return {
        "ready": status == "pass",
        "exact_label_echo_case_count": exact_echo_count,
        "label_prefix_fragment_case_count": fragment_count,
        "label_or_fragment_case_count": label_or_fragment_count,
        "zero_hit_case_count": int(replay_summary.get("zero_hit_case_count") or 0),
        "all_cases_label_or_fragment": bool(case_rows) and label_or_fragment_count == len(case_rows),
        "loss_improved_without_required_term_uptake": float(training_summary.get("train_loss_delta") or 0.0) < 0
        and int(replay_summary.get("any_hit_case_count") or 0) == 0,
        "root_cause_ids": [cause["id"] for cause in root_causes],
        "next_step": "build_target_only_completion_memory_patch",
    }


def _summary(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, str]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic_ready": status == "pass",
        "case_count": len(case_rows),
        "exact_label_echo_case_count": diagnostic.get("exact_label_echo_case_count"),
        "label_prefix_fragment_case_count": diagnostic.get("label_prefix_fragment_case_count"),
        "label_or_fragment_case_count": diagnostic.get("label_or_fragment_case_count"),
        "zero_hit_case_count": diagnostic.get("zero_hit_case_count"),
        "all_cases_label_or_fragment": diagnostic.get("all_cases_label_or_fragment"),
        "loss_improved_without_required_term_uptake": diagnostic.get("loss_improved_without_required_term_uptake"),
        "root_cause_count": len(root_causes),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic"
    if diagnostic.get("all_cases_label_or_fragment") is True:
        return "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_label_echo_persisted"
    return "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_surface_gap"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Single-line zero-hit diagnostic inputs failed.", "next_action": "repair_single_line_zero_hit_diagnostic_inputs"}
    if diagnostic.get("all_cases_label_or_fragment") is True:
        return {
            "model_quality_claim": "label_echo_persisted_after_single_line_training",
            "reason": "The checkpoint still emits answer/completion labels or label-prefix fragments after single-line surface training.",
            "next_action": diagnostic.get("next_step"),
        }
    return {
        "model_quality_claim": "zero_hit_surface_gap",
        "reason": "The checkpoint produced zero required-term hits and needs a stricter target-only repair.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME",
    "SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME",
    "SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME",
    "SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME",
    "build_single_line_surface_zero_hit_diagnostic",
    "locate_single_line_surface_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
