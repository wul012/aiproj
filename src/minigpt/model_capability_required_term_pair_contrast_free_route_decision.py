from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_fixed_retention_batch_closeout import (
    PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import (
    PAIR_FIXED_RETENTION_OBJECTIVE_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_first_token_preference_diagnostic import (
    PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_CONTRAST_FREE_ROUTE_DECISION_JSON_FILENAME = "model_capability_required_term_pair_contrast_free_route_decision.json"
PAIR_CONTRAST_FREE_ROUTE_DECISION_CSV_FILENAME = "model_capability_required_term_pair_contrast_free_route_decision.csv"
PAIR_CONTRAST_FREE_ROUTE_DECISION_TEXT_FILENAME = "model_capability_required_term_pair_contrast_free_route_decision.txt"
PAIR_CONTRAST_FREE_ROUTE_DECISION_MARKDOWN_FILENAME = "model_capability_required_term_pair_contrast_free_route_decision.md"
PAIR_CONTRAST_FREE_ROUTE_DECISION_HTML_FILENAME = "model_capability_required_term_pair_contrast_free_route_decision.html"


def locate_contrast_free_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FIXED_RETENTION_OBJECTIVE_COMPARISON_JSON_FILENAME
    return source


def locate_prior_closeout(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_JSON_FILENAME
    return source


def locate_first_token_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("contrast-free route decision input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_contrast_free_route_decision(
    *,
    comparison: dict[str, Any],
    prior_closeout: dict[str, Any],
    first_token_diagnostic: dict[str, Any],
    comparison_path: str | Path | None = None,
    prior_closeout_path: str | Path | None = None,
    first_token_diagnostic_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    route_rows = [_route_row(row) for row in list_of_dicts(comparison.get("branch_rows"))]
    evidence_rows = _evidence_rows(comparison, prior_closeout, first_token_diagnostic, comparison_path, prior_closeout_path, first_token_diagnostic_path)
    summary = _summary(comparison, prior_closeout, first_token_diagnostic, route_rows)
    issues = _issues(evidence_rows, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair contrast-free route decision",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "route_rows": route_rows,
        "evidence_rows": evidence_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _route_row(row: dict[str, Any]) -> dict[str, Any]:
    hit_terms = [str(value) for value in row.get("hit_terms", [])]
    return {
        "source_label": row.get("source_label"),
        "corpus_mode": row.get("corpus_mode"),
        "hit_terms": hit_terms,
        "missed_terms": [str(value) for value in row.get("missed_terms", [])],
        "fixed_only_tradeoff": bool(row.get("fixed_only_tradeoff")),
        "loss_only_tradeoff": bool(row.get("loss_only_tradeoff")),
        "pair_full_observed": bool(row.get("pair_full_observed")),
        "route_role": _route_role(str(row.get("source_label") or ""), str(row.get("corpus_mode") or "")),
    }


def _route_role(label: str, mode: str) -> str:
    text = f"{label} {mode}".casefold()
    if "delimiter" in text:
        return "delimiter-span"
    if "context" in text:
        return "context-switch"
    if "contrast" in text:
        return "contrast-free"
    return "unknown"


def _evidence_rows(
    comparison: dict[str, Any],
    prior_closeout: dict[str, Any],
    diagnostic: dict[str, Any],
    comparison_path: str | Path | None,
    prior_closeout_path: str | Path | None,
    diagnostic_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        {
            "label": "v608-fixed-retention-closeout",
            "path": str(prior_closeout_path or ""),
            "status": prior_closeout.get("status"),
            "decision": prior_closeout.get("decision"),
            "key_result": f"stop_loss_rebalance={as_dict(prior_closeout.get('summary')).get('stop_current_loss_rebalance_routes')}",
        },
        {
            "label": "v609-first-token-diagnostic",
            "path": str(diagnostic_path or ""),
            "status": diagnostic.get("status"),
            "decision": diagnostic.get("decision"),
            "key_result": f"conflict={as_dict(diagnostic.get('summary')).get('first_token_conflict_confirmed')}",
        },
        {
            "label": "v614-contrast-free-comparison",
            "path": str(comparison_path or ""),
            "status": comparison.get("status"),
            "decision": comparison.get("decision"),
            "key_result": f"pair_full={as_dict(comparison.get('summary')).get('pair_full_report_count')}; union={as_dict(comparison.get('summary')).get('union_hit_terms')}",
        },
    ]


def _summary(
    comparison: dict[str, Any],
    prior_closeout: dict[str, Any],
    diagnostic: dict[str, Any],
    route_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    comparison_summary = as_dict(comparison.get("summary"))
    closeout_summary = as_dict(prior_closeout.get("summary"))
    diagnostic_summary = as_dict(diagnostic.get("summary"))
    pair_full_routes = [row for row in route_rows if row.get("pair_full_observed")]
    fixed_only_routes = [row for row in route_rows if row.get("fixed_only_tradeoff")]
    return {
        "route_count": len(route_rows),
        "pair_full_route_count": len(pair_full_routes),
        "fixed_only_route_count": len(fixed_only_routes),
        "loss_only_route_count": sum(1 for row in route_rows if row.get("loss_only_tradeoff")),
        "union_hit_terms": [str(value) for value in comparison_summary.get("union_hit_terms", [])],
        "selected_fixed_signal_route": fixed_only_routes[0].get("source_label") if fixed_only_routes else "",
        "selected_fixed_signal_role": fixed_only_routes[0].get("route_role") if fixed_only_routes else "",
        "prior_loss_rebalance_stopped": bool(closeout_summary.get("stop_current_loss_rebalance_routes")),
        "first_token_conflict_confirmed": bool(diagnostic_summary.get("first_token_conflict_confirmed")),
        "mixed_branch_tradeoff_confirmed": bool(diagnostic_summary.get("mixed_branch_tradeoff_confirmed")),
        "repeat_loss_rebalance_allowed": bool(pair_full_routes),
        "requires_forced_choice_diagnostic": not pair_full_routes,
        "requires_new_objective_shape": not pair_full_routes and bool(closeout_summary.get("stop_current_loss_rebalance_routes")),
    }


def _issues(evidence_rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for row in evidence_rows:
        if row.get("status") != "pass":
            issues.append(f"{row.get('label')} status is not pass")
    if int(summary.get("route_count") or 0) < 3:
        issues.append("three contrast-free route rows are required")
    if not summary.get("prior_loss_rebalance_stopped"):
        issues.append("prior closeout did not stop loss-rebalance routes")
    if not summary.get("first_token_conflict_confirmed"):
        issues.append("first-token conflict diagnostic is not confirmed")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_contrast_free_route_decision_inputs"
    if int(summary.get("pair_full_route_count") or 0) > 0:
        return "promote_contrast_free_pair_full_candidate_to_seed_stability"
    if summary.get("requires_forced_choice_diagnostic"):
        return "stop_contrast_free_routes_and_run_forced_choice_diagnostic"
    return "record_contrast_free_route_decision"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route decision inputs are incomplete or contradictory.",
            "next_action": "repair comparison, closeout, or diagnostic inputs before more training",
        }
    if int(summary.get("pair_full_route_count") or 0) > 0:
        return {
            "model_quality_claim": "pair_full_candidate",
            "reason": "A contrast-free route reached pair-full and should be replayed across seeds.",
            "next_action": "run seed stability before promotion",
        }
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "Contrast-free routes only recovered fixed while prior loss-rebalance was already stopped.",
        "next_action": "run teacher-forced/forced-choice diagnostics on the fixed-signal routes before designing another corpus",
    }


__all__ = [
    "PAIR_CONTRAST_FREE_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_CONTRAST_FREE_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_CONTRAST_FREE_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_CONTRAST_FREE_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_CONTRAST_FREE_ROUTE_DECISION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_contrast_free_route_decision",
    "locate_contrast_free_comparison",
    "locate_first_token_diagnostic",
    "locate_prior_closeout",
    "read_json_report",
    "resolve_exit_code",
]
