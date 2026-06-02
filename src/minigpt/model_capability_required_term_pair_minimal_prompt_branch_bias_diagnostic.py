from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import TARGET_TERMS
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_JSON_FILENAME = "model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic.json"
PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_CSV_FILENAME = "model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic.csv"
PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_TEXT_FILENAME = "model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic.txt"
PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic.md"
PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_HTML_FILENAME = "model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic.html"


def locate_minimal_prompt_branch_bias_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("minimal prompt branch-bias diagnostic input must be a JSON object")
    return dict(payload)


def build_minimal_prompt_branch_bias_diagnostic(
    refresh_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = _diagnostic_rows(refresh_report)
    summary = _summary(refresh_report, rows)
    issues = _issues(refresh_report, rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair minimal prompt branch-bias diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_refresh_path": str(source_path or ""),
        "source_refresh": {
            "status": refresh_report.get("status"),
            "decision": refresh_report.get("decision"),
            "settings": as_dict(refresh_report.get("settings")),
            "summary": as_dict(refresh_report.get("summary")),
        },
        "diagnostic_rows": rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _diagnostic_rows(refresh_report: dict[str, Any]) -> list[dict[str, Any]]:
    replay = as_dict(refresh_report.get("replay_report"))
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(replay.get("case_rows")):
        term = str(row.get("term") or "")
        if term not in TARGET_TERMS:
            continue
        continuation = str(row.get("continuation") or "")
        other = _other_term(term)
        rows.append(
            {
                "profile_id": row.get("profile_id"),
                "term": term,
                "prompt": row.get("prompt"),
                "expected_first_char": term[:1],
                "observed_first_char": _first_visible_char(continuation),
                "expected_term_at_start": continuation.startswith(term),
                "other_term_at_start": continuation.startswith(other),
                "continuation_hit": bool(row.get("continuation_hit")),
                "newline_cleanup_hit": bool(row.get("newline_cleanup_hit")),
                "branch_vote": _branch_vote(continuation),
                "continuation_preview": continuation.replace("\n", "\\n").replace("\r", "\\r")[:120],
                "generated_preview": str(row.get("generated") or row.get("generated_preview") or "")[:120],
            }
        )
    return rows


def _summary(refresh_report: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_summary = as_dict(refresh_report.get("summary"))
    fixed_rows = [row for row in rows if row.get("term") == "fixed"]
    loss_rows = [row for row in rows if row.get("term") == "loss"]
    return {
        "corpus_mode": as_dict(refresh_report.get("settings")).get("corpus_mode", ""),
        "seed": as_dict(refresh_report.get("settings")).get("seed"),
        "prompt_row_count": len(rows),
        "fixed_prompt_count": len(fixed_rows),
        "loss_prompt_count": len(loss_rows),
        "fixed_hit_count": sum(1 for row in fixed_rows if row.get("continuation_hit")),
        "loss_hit_count": sum(1 for row in loss_rows if row.get("continuation_hit")),
        "loss_prompt_fixed_start_count": sum(1 for row in loss_rows if row.get("branch_vote") == "fixed-start"),
        "fixed_prompt_loss_start_count": sum(1 for row in fixed_rows if row.get("branch_vote") == "loss-start"),
        "expected_first_char_match_count": sum(1 for row in rows if row.get("observed_first_char") == row.get("expected_first_char")),
        "pair_full_observed": bool(source_summary.get("pair_full_observed")),
        "checkpoint_exists": bool(source_summary.get("checkpoint_exists")),
        "training_status": source_summary.get("training_status"),
        "dominant_bias": _dominant_bias(rows),
    }


def _issues(refresh_report: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    summary = as_dict(refresh_report.get("summary"))
    if refresh_report.get("status") != "pass":
        issues.append("source refresh report is not pass")
    if summary.get("training_status") != "pass":
        issues.append("source refresh training is not pass")
    if not summary.get("checkpoint_exists"):
        issues.append("source refresh checkpoint is missing")
    if not rows:
        issues.append("source refresh replay has no fixed/loss case rows")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_minimal_prompt_branch_bias_diagnostic_input"
    if summary.get("pair_full_observed"):
        return "minimal_prompt_branch_bias_pair_full_observed"
    if int(summary.get("loss_prompt_fixed_start_count") or 0) > 0:
        return "minimal_prompt_branch_bias_fixed_absorbs_loss"
    if int(summary.get("fixed_prompt_loss_start_count") or 0) > 0:
        return "minimal_prompt_branch_bias_loss_absorbs_fixed"
    return "minimal_prompt_branch_bias_recorded"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The source refresh report is incomplete.",
            "next_action": "repair or rerun the minimal prompt training before diagnosis",
        }
    if summary.get("pair_full_observed"):
        return {
            "model_quality_claim": "pair_full_candidate_observed",
            "reason": "The refresh report already contains pair-full evidence.",
            "next_action": "repeat across seeds before promotion",
        }
    if int(summary.get("loss_prompt_fixed_start_count") or 0) > 0:
        return {
            "model_quality_claim": "diagnostic_only",
            "reason": "The loss prompt begins with the competing fixed term, so the miss is a branch-bias failure rather than a missing checkpoint.",
            "next_action": "strengthen loss first-token and branch separation before rerunning the minimal-prompt training",
        }
    return {
        "model_quality_claim": "diagnostic_only",
        "reason": "The replay rows did not show pair-full and did not isolate a cross-branch first-token start.",
        "next_action": "inspect token ranks or add a forced-choice diagnostic",
    }


def _first_visible_char(text: str) -> str:
    for char in text:
        if not char.isspace():
            return char
    return ""


def _branch_vote(text: str) -> str:
    for term in TARGET_TERMS:
        if text.startswith(term):
            return f"{term}-start"
    return "other"


def _other_term(term: str) -> str:
    return "loss" if term == "fixed" else "fixed"


def _dominant_bias(rows: list[dict[str, Any]]) -> str:
    fixed_votes = sum(1 for row in rows if row.get("branch_vote") == "fixed-start")
    loss_votes = sum(1 for row in rows if row.get("branch_vote") == "loss-start")
    if fixed_votes > loss_votes:
        return "fixed"
    if loss_votes > fixed_votes:
        return "loss"
    return "balanced_or_unknown"


__all__ = [
    "PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_TEXT_FILENAME",
    "build_minimal_prompt_branch_bias_diagnostic",
    "locate_minimal_prompt_branch_bias_source",
    "read_json_report",
    "resolve_exit_code",
]
