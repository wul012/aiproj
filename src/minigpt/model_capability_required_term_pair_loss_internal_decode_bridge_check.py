from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_internal_decode_bridge_check.json"
)
PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_CSV_FILENAME = (
    "model_capability_required_term_pair_loss_internal_decode_bridge_check.csv"
)
PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_internal_decode_bridge_check.txt"
)
PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_internal_decode_bridge_check.md"
)
PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_internal_decode_bridge_check.html"
)
TARGET_TERMS = ("fixed", "loss")


def locate_loss_internal_decode_bridge_input(path: str | Path, filename: str) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    direct = source / filename
    if direct.is_file():
        return direct
    matches = sorted(source.rglob(filename)) if source.is_dir() else []
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(f"missing {filename} under {source}")
    raise ValueError(f"ambiguous {filename} under {source}: {len(matches)} matches")


def read_loss_internal_decode_bridge_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("loss-internal decode bridge input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_loss_internal_decode_bridge_check(
    refresh_report: dict[str, Any],
    forced_choice: dict[str, Any],
    route_decision: dict[str, Any],
    *,
    refresh_path: str | Path | None = None,
    forced_choice_path: str | Path | None = None,
    route_decision_path: str | Path | None = None,
    selected_source: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    selected = selected_source or str(as_dict(route_decision.get("summary")).get("selected_decode_bridge_source") or "")
    generation_rows = _generation_rows(refresh_report)
    internal_rows = _internal_rows(forced_choice, selected)
    bridge_rows = [_bridge_row(term, generation_rows, internal_rows) for term in TARGET_TERMS]
    summary = _summary(refresh_report, forced_choice, route_decision, bridge_rows, selected)
    issues = _issues(refresh_report, forced_choice, route_decision, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair loss-internal decode bridge check",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_refresh_report": str(refresh_path or ""),
        "source_forced_choice": str(forced_choice_path or ""),
        "source_route_decision": str(route_decision_path or ""),
        "selected_source": selected,
        "bridge_rows": bridge_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _generation_rows(refresh_report: dict[str, Any]) -> list[dict[str, Any]]:
    replay = as_dict(refresh_report.get("replay_report"))
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(replay.get("case_rows")):
        term = str(row.get("term") or "")
        if term in TARGET_TERMS:
            rows.append(
                {
                    "term": term,
                    "prompt": row.get("prompt"),
                    "generation_hit": bool(row.get("continuation_hit")),
                    "continuation_preview": row.get("continuation_preview"),
                    "profile_id": row.get("profile_id"),
                }
            )
    return rows


def _internal_rows(forced_choice: dict[str, Any], selected_source: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(forced_choice.get("prompt_summaries")):
        if str(row.get("source_label") or "") != selected_source:
            continue
        term = str(row.get("prompt_term") or "")
        if term in TARGET_TERMS:
            rows.append(
                {
                    "term": term,
                    "forced_choice_expected_best": bool(row.get("expected_best")),
                    "best_candidate": row.get("best_candidate"),
                    "expected_avg_nll": row.get("expected_avg_nll"),
                    "best_avg_nll": row.get("best_avg_nll"),
                    "expected_first_token_rank": row.get("expected_first_token_rank"),
                }
            )
    return rows


def _bridge_row(term: str, generation_rows: list[dict[str, Any]], internal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    generation_hit = any(row.get("term") == term and row.get("generation_hit") for row in generation_rows)
    internal = next((row for row in internal_rows if row.get("term") == term), {})
    internal_best = bool(internal.get("forced_choice_expected_best"))
    return {
        "term": term,
        "generation_hit": generation_hit,
        "forced_choice_expected_best": internal_best,
        "bridge_gap": internal_best and not generation_hit,
        "best_candidate": internal.get("best_candidate"),
        "expected_avg_nll": internal.get("expected_avg_nll"),
        "best_avg_nll": internal.get("best_avg_nll"),
        "expected_first_token_rank": internal.get("expected_first_token_rank"),
    }


def _summary(
    refresh_report: dict[str, Any],
    forced_choice: dict[str, Any],
    route_decision: dict[str, Any],
    bridge_rows: list[dict[str, Any]],
    selected_source: str,
) -> dict[str, Any]:
    route_summary = as_dict(route_decision.get("summary"))
    generation_hit_terms = [row["term"] for row in bridge_rows if row.get("generation_hit")]
    internal_hit_terms = [row["term"] for row in bridge_rows if row.get("forced_choice_expected_best")]
    gap_terms = [row["term"] for row in bridge_rows if row.get("bridge_gap")]
    return {
        "selected_source": selected_source,
        "refresh_status": refresh_report.get("status"),
        "forced_choice_status": forced_choice.get("status"),
        "route_status": route_decision.get("status"),
        "route_bridge_required": bool(route_summary.get("internal_to_generation_bridge_required")),
        "generation_hit_terms": generation_hit_terms,
        "forced_choice_expected_best_terms": internal_hit_terms,
        "bridge_gap_terms": gap_terms,
        "bridge_gap_count": len(gap_terms),
        "internal_pair_match": set(TARGET_TERMS).issubset(internal_hit_terms),
        "generation_pair_full": set(TARGET_TERMS).issubset(generation_hit_terms),
        "decode_bridge_ready": set(TARGET_TERMS).issubset(internal_hit_terms) and bool(gap_terms),
    }


def _issues(
    refresh_report: dict[str, Any],
    forced_choice: dict[str, Any],
    route_decision: dict[str, Any],
    summary: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    if refresh_report.get("status") != "pass":
        issues.append("refresh report status is not pass")
    if forced_choice.get("status") != "pass":
        issues.append("forced-choice report status is not pass")
    if route_decision.get("status") != "pass":
        issues.append("route decision status is not pass")
    if not summary.get("route_bridge_required"):
        issues.append("route decision does not require a decode bridge")
    if not summary.get("internal_pair_match"):
        issues.append("selected source does not have internal pair match")
    if summary.get("generation_pair_full"):
        issues.append("selected source already has generation pair-full")
    if not summary.get("bridge_gap_terms"):
        issues.append("no internal-to-generation gap terms were found")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_internal_decode_bridge_inputs"
    return "loss_internal_decode_bridge_gap_confirmed"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The decode bridge inputs are incomplete or contradictory.",
            "next_action": "repair decode bridge inputs before adding a bridge corpus",
        }
    return {
        "model_quality_claim": "decode_bridge_gap_evidence",
        "reason": "The selected checkpoint has internal pair match but generation misses at least one term.",
        "next_action": "train a bridge objective that preserves internal loss while restoring the missed generation term",
    }


__all__ = [
    "PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_CSV_FILENAME",
    "PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_HTML_FILENAME",
    "PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_JSON_FILENAME",
    "PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_MARKDOWN_FILENAME",
    "PAIR_LOSS_INTERNAL_DECODE_BRIDGE_CHECK_TEXT_FILENAME",
    "build_model_capability_required_term_pair_loss_internal_decode_bridge_check",
    "locate_loss_internal_decode_bridge_input",
    "read_loss_internal_decode_bridge_input",
    "resolve_exit_code",
]
