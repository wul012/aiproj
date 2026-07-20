from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_constrained_decode_feasibility import (
    BLOCK_COMPETING_INITIAL_PROFILE_ID,
    PAIR_CONSTRAINED_DECODE_FEASIBILITY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_JSON_FILENAME = (
    "model_capability_required_term_pair_constrained_decode_miss_diagnostic.json"
)
PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_CSV_FILENAME = (
    "model_capability_required_term_pair_constrained_decode_miss_diagnostic.csv"
)
PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_TEXT_FILENAME = (
    "model_capability_required_term_pair_constrained_decode_miss_diagnostic.txt"
)
PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_constrained_decode_miss_diagnostic.md"
)
PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_HTML_FILENAME = (
    "model_capability_required_term_pair_constrained_decode_miss_diagnostic.html"
)


def locate_pair_constrained_decode_miss_diagnostic_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_CONSTRAINED_DECODE_FEASIBILITY_JSON_FILENAME
    return source


def read_pair_constrained_decode_miss_diagnostic_source(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("constrained decode miss diagnostic source must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_constrained_decode_miss_diagnostic(
    feasibility_report: dict[str, Any],
    *,
    source_path: str | Path = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    case_rows = list_of_dicts(feasibility_report.get("case_rows"))
    summary = as_dict(feasibility_report.get("summary"))
    diagnostic_rows = [_diagnostic_row(row) for row in case_rows]
    issues = _issues(feasibility_report, case_rows)
    diagnostic_summary = _summary(diagnostic_rows, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair constrained decode miss diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, diagnostic_summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_constrained_decode_feasibility": str(source_path),
        "source_status": feasibility_report.get("status"),
        "source_decision": feasibility_report.get("decision"),
        "diagnostic_rows": diagnostic_rows,
        "summary": diagnostic_summary,
        "interpretation": _interpretation(status, diagnostic_summary),
    }


def _diagnostic_row(row: dict[str, Any]) -> dict[str, Any]:
    term = str(row.get("term") or "")
    profile_id = str(row.get("profile_id") or "")
    continuation = str(row.get("continuation") or "")
    hit = bool(row.get("continuation_hit"))
    return {
        "term": term,
        "profile_id": profile_id,
        "continuation_hit": hit,
        "blocked_token_texts": list(row.get("blocked_token_texts") or []),
        "blocked_reason": row.get("blocked_reason") or "",
        "continuation_preview": str(row.get("continuation_preview") or continuation.replace("\n", "\\n")[:120]),
        "miss_class": _miss_class(term, continuation, hit),
        "term_prefix_present": _term_prefix_present(term, continuation),
        "full_term_present": term.casefold() in continuation.casefold() if term else False,
    }


def _miss_class(term: str, continuation: str, hit: bool) -> str:
    if hit:
        return "not_missed"
    lowered = continuation.casefold()
    if term and term[:3].casefold() in lowered:
        return "prefix_fragment_without_full_term"
    if "=" in continuation:
        return "equals_surface_drift_without_term"
    if continuation.strip():
        return "nonempty_continuation_without_term"
    return "empty_continuation"


def _term_prefix_present(term: str, continuation: str) -> bool:
    if len(term) < 3:
        return bool(term and term.casefold() in continuation.casefold())
    return term[:3].casefold() in continuation.casefold()


def _issues(feasibility_report: dict[str, Any], case_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if feasibility_report.get("status") != "pass":
        issues.append("source constrained decode feasibility status is not pass")
    if not case_rows:
        issues.append("source constrained decode feasibility has no case rows")
    if not _find_case(case_rows, "fixed", BLOCK_COMPETING_INITIAL_PROFILE_ID):
        issues.append("source has no constrained fixed case")
    if not _find_case(case_rows, "loss", BLOCK_COMPETING_INITIAL_PROFILE_ID):
        issues.append("source has no constrained loss case")
    return issues


def _summary(diagnostic_rows: list[dict[str, Any]], feasibility_summary: dict[str, Any]) -> dict[str, Any]:
    fixed_constrained = _find_diag(diagnostic_rows, "fixed", BLOCK_COMPETING_INITIAL_PROFILE_ID)
    loss_constrained = _find_diag(diagnostic_rows, "loss", BLOCK_COMPETING_INITIAL_PROFILE_ID)
    remaining_missed = [
        term
        for term, row in (("fixed", fixed_constrained), ("loss", loss_constrained))
        if row and not row.get("continuation_hit")
    ]
    return {
        "source_constrained_pair_full": bool(feasibility_summary.get("constrained_pair_full")),
        "source_hit_delta": feasibility_summary.get("hit_delta"),
        "fixed_constrained_hit": bool(fixed_constrained.get("continuation_hit")),
        "loss_constrained_hit": bool(loss_constrained.get("continuation_hit")),
        "fixed_miss_class": fixed_constrained.get("miss_class", ""),
        "loss_miss_class": loss_constrained.get("miss_class", ""),
        "remaining_missed_terms": remaining_missed,
        "fixed_term_prefix_present": bool(fixed_constrained.get("term_prefix_present")),
        "recommended_next_route": _recommended_next_route(fixed_constrained, loss_constrained),
    }


def _recommended_next_route(fixed_row: dict[str, Any], loss_row: dict[str, Any]) -> str:
    if fixed_row.get("continuation_hit") and loss_row.get("continuation_hit"):
        return "promote_constrained_decode_profile"
    if not fixed_row.get("continuation_hit") and loss_row.get("continuation_hit"):
        return "explicit_dual_objective_boundary_for_fixed_retention"
    if fixed_row.get("continuation_hit") and not loss_row.get("continuation_hit"):
        return "explicit_dual_objective_boundary_for_loss_retention"
    return "return_to_objective_design"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_constrained_decode_miss_diagnostic"
    if summary.get("source_constrained_pair_full"):
        return "constrained_decode_pair_full_no_miss"
    if summary.get("fixed_constrained_hit") is False and summary.get("loss_constrained_hit"):
        return "fixed_branch_still_missed_after_constrained_decode"
    if summary.get("remaining_missed_terms"):
        return "constrained_decode_still_has_missed_terms"
    return "constrained_decode_miss_diagnostic_complete"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The constrained decode diagnostic source is incomplete.",
            "next_action": "repair constrained decode feasibility evidence",
        }
    if summary.get("fixed_constrained_hit") is False and summary.get("loss_constrained_hit"):
        return {
            "model_quality_claim": "decode_diagnostic_only",
            "reason": "Blocking the competing initial recovers loss, but fixed remains a miss.",
            "next_action": "design an explicit dual-objective boundary that preserves fixed while retaining loss",
        }
    if summary.get("source_constrained_pair_full"):
        return {
            "model_quality_claim": "decode_pair_full_candidate",
            "reason": "The constrained profile already reaches pair-full.",
            "next_action": "replay held-out prompts before promotion",
        }
    return {
        "model_quality_claim": "decode_diagnostic_only",
        "reason": "The constrained profile still has missed terms.",
        "next_action": "return to objective design",
    }


def _find_case(rows: list[dict[str, Any]], term: str, profile_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("term") == term and row.get("profile_id") == profile_id:
            return row
    return {}


def _find_diag(rows: list[dict[str, Any]], term: str, profile_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("term") == term and row.get("profile_id") == profile_id:
            return row
    return {}


__all__ = [
    "PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_CONSTRAINED_DECODE_MISS_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_required_term_pair_constrained_decode_miss_diagnostic",
    "locate_pair_constrained_decode_miss_diagnostic_source",
    "read_pair_constrained_decode_miss_diagnostic_source",
    "resolve_exit_code",
]
