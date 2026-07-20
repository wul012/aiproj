from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_route_decision.json"
)
PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_CSV_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_route_decision.csv"
)
PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_route_decision.txt"
)
PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_route_decision.md"
)
PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_route_decision.html"
)


def locate_loss_internal_preference_route_input(path: str | Path, filename: str) -> Path:
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


def read_loss_internal_preference_route_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("loss-internal-preference route input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_loss_internal_preference_route_decision(
    comparison: dict[str, Any],
    forced_choice: dict[str, Any],
    *,
    comparison_path: str | Path | None = None,
    forced_choice_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    route_rows = _route_rows(comparison, forced_choice)
    summary = _summary(comparison, forced_choice, route_rows)
    issues = _issues(comparison, forced_choice, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair loss-internal-preference route decision",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_comparison": str(comparison_path or ""),
        "source_forced_choice": str(forced_choice_path or ""),
        "route_rows": route_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _route_rows(comparison: dict[str, Any], forced_choice: dict[str, Any]) -> list[dict[str, Any]]:
    internal_sources = {str(value) for value in as_dict(forced_choice.get("summary")).get("best_internal_sources", [])}
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(comparison.get("branch_rows")):
        label = str(row.get("source_label") or "")
        has_internal_pair = label in internal_sources
        generation_pair_full = bool(row.get("pair_full_observed"))
        rows.append(
            {
                "source_label": label,
                "corpus_mode": row.get("corpus_mode"),
                "hit_terms": [str(term) for term in row.get("hit_terms", [])],
                "missed_terms": [str(term) for term in row.get("missed_terms", [])],
                "generation_pair_full": generation_pair_full,
                "forced_choice_pair_full": has_internal_pair,
                "decode_bridge_candidate": has_internal_pair and not generation_pair_full,
                "promotion_candidate": has_internal_pair and generation_pair_full,
                "rejection_reasons": _rejection_reasons(generation_pair_full, has_internal_pair, row),
            }
        )
    return rows


def _summary(comparison: dict[str, Any], forced_choice: dict[str, Any], route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparison_summary = as_dict(comparison.get("summary"))
    forced_summary = as_dict(forced_choice.get("summary"))
    bridge = _selected_decode_bridge(route_rows)
    return {
        "comparison_decision": comparison.get("decision"),
        "forced_choice_decision": forced_choice.get("decision"),
        "route_count": len(route_rows),
        "generation_pair_full_route_count": int(comparison_summary.get("pair_full_report_count") or 0),
        "forced_choice_full_match_source_count": int(forced_summary.get("forced_choice_full_match_source_count") or 0),
        "mixed_generation_tradeoff": bool(comparison_summary.get("mixed_tradeoff_observed")),
        "decode_bridge_candidate_count": sum(1 for row in route_rows if row.get("decode_bridge_candidate")),
        "promotion_candidate_count": sum(1 for row in route_rows if row.get("promotion_candidate")),
        "selected_decode_bridge_source": bridge.get("source_label"),
        "selected_decode_bridge_corpus_mode": bridge.get("corpus_mode"),
        "internal_to_generation_bridge_required": bool(bridge),
        "new_training_required": not bool(bridge),
    }


def _issues(comparison: dict[str, Any], forced_choice: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if comparison.get("status") != "pass":
        issues.append("comparison status is not pass")
    if forced_choice.get("status") != "pass":
        issues.append("forced-choice status is not pass")
    if int(summary.get("route_count") or 0) == 0:
        issues.append("no route rows available")
    if not summary.get("mixed_generation_tradeoff"):
        issues.append("comparison did not confirm mixed generation tradeoff")
    if int(summary.get("forced_choice_full_match_source_count") or 0) == 0:
        issues.append("forced-choice found no internal pair match")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_internal_preference_route_inputs"
    if int(summary.get("promotion_candidate_count") or 0) > 0:
        return "promote_loss_internal_preference_pair_full_candidate"
    if summary.get("internal_to_generation_bridge_required"):
        return "select_loss_internal_first_token_for_decode_bridge_not_promotion"
    return "run_another_loss_internal_preference_objective"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The comparison and forced-choice evidence do not form a complete route decision.",
            "next_action": "repair route inputs before new training",
        }
    if summary.get("internal_to_generation_bridge_required"):
        return {
            "model_quality_claim": "internal_pair_match_not_generation_pair_full",
            "reason": "The selected route has internal pair match but no generation pair-full.",
            "next_action": "build a decode bridge check around the selected first-token checkpoint",
        }
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "No decode bridge route was selected.",
        "next_action": "run another loss-internal-preference objective",
    }


def _selected_decode_bridge(route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in route_rows if row.get("decode_bridge_candidate")]
    if not candidates:
        return {}
    return min(candidates, key=lambda row: str(row.get("source_label") or ""))


def _rejection_reasons(generation_pair_full: bool, internal_pair_full: bool, row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not generation_pair_full:
        reasons.append("generation_not_pair_full")
    if not internal_pair_full:
        reasons.append("forced_choice_not_pair_full")
    if row.get("fixed_only_tradeoff"):
        reasons.append("fixed_only_generation")
    if row.get("loss_only_tradeoff"):
        reasons.append("loss_only_generation")
    return reasons


__all__ = [
    "PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_loss_internal_preference_route_decision",
    "locate_loss_internal_preference_route_input",
    "read_loss_internal_preference_route_input",
    "resolve_exit_code",
]
