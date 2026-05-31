from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import (
    PAIR_FIXED_RETENTION_OBJECTIVE_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_FIXED_RETENTION_ROUTE_DECISION_JSON_FILENAME = "model_capability_required_term_pair_fixed_retention_route_decision.json"
PAIR_FIXED_RETENTION_ROUTE_DECISION_CSV_FILENAME = "model_capability_required_term_pair_fixed_retention_route_decision.csv"
PAIR_FIXED_RETENTION_ROUTE_DECISION_TEXT_FILENAME = "model_capability_required_term_pair_fixed_retention_route_decision.txt"
PAIR_FIXED_RETENTION_ROUTE_DECISION_MARKDOWN_FILENAME = "model_capability_required_term_pair_fixed_retention_route_decision.md"
PAIR_FIXED_RETENTION_ROUTE_DECISION_HTML_FILENAME = "model_capability_required_term_pair_fixed_retention_route_decision.html"


def locate_fixed_retention_route_decision_input(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FIXED_RETENTION_OBJECTIVE_COMPARISON_JSON_FILENAME
    return source


def read_fixed_retention_route_decision_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("fixed-retention route decision input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_fixed_retention_route_decision(
    comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    route_rows = [_route_row(row) for row in list_of_dicts(comparison.get("branch_rows"))]
    summary = _summary(comparison, route_rows)
    issues = _issues(comparison, route_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair fixed-retention route decision",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_comparison": str(source_path or ""),
        "route_rows": route_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _route_row(row: dict[str, Any]) -> dict[str, Any]:
    label = str(row.get("source_label") or "")
    corpus_mode = str(row.get("corpus_mode") or "")
    hit_terms = [str(value) for value in row.get("hit_terms", [])]
    return {
        "source_label": label,
        "corpus_mode": corpus_mode,
        "route_type": _route_type(corpus_mode, label),
        "seed": row.get("seed"),
        "hit_terms": hit_terms,
        "missed_terms": [str(value) for value in row.get("missed_terms", [])],
        "fixed_only_tradeoff": bool(row.get("fixed_only_tradeoff")),
        "loss_only_tradeoff": bool(row.get("loss_only_tradeoff")),
        "pair_full_observed": bool(row.get("pair_full_observed")),
    }


def _summary(comparison: dict[str, Any], route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparison_summary = as_dict(comparison.get("summary"))
    pair_full_routes = [row for row in route_rows if row.get("pair_full_observed")]
    fixed_only_routes = [row for row in route_rows if row.get("fixed_only_tradeoff")]
    selected = pair_full_routes[0] if pair_full_routes else (fixed_only_routes[0] if fixed_only_routes else {})
    return {
        "route_count": len(route_rows),
        "pair_full_route_count": len(pair_full_routes),
        "fixed_only_tradeoff_route_count": len(fixed_only_routes),
        "loss_only_tradeoff_route_count": sum(1 for row in route_rows if row.get("loss_only_tradeoff")),
        "comparison_decision": comparison.get("decision"),
        "comparison_union_hit_terms": comparison_summary.get("union_hit_terms", []),
        "promotion_ready": bool(pair_full_routes),
        "mixed_tradeoff_observed": bool(comparison_summary.get("mixed_tradeoff_observed")),
        "selected_route": selected.get("source_label", ""),
        "selected_corpus_mode": selected.get("corpus_mode", ""),
        "selected_route_type": selected.get("route_type", ""),
        "loss_rebalance_objective_required": bool(fixed_only_routes) and not pair_full_routes,
        "seed_stability_replay_required": bool(pair_full_routes),
    }


def _issues(comparison: dict[str, Any], route_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if comparison.get("status") != "pass":
        issues.append("comparison status is not pass")
    if not route_rows:
        issues.append("comparison has no route rows")
    for row in route_rows:
        if "fixed_retention" not in str(row.get("corpus_mode") or ""):
            issues.append(f"{row.get('source_label')} is not fixed-retention corpus mode")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_fixed_retention_route_decision_input"
    if summary.get("promotion_ready"):
        return "promote_fixed_retention_pair_full_route"
    if summary.get("loss_rebalance_objective_required"):
        return "select_fixed_recovery_route_for_loss_rebalance_not_promotion"
    return "stop_fixed_retention_objectives_until_new_design"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The fixed-retention comparison is incomplete or contradictory.",
            "next_action": "repair route decision input before more training",
        }
    if summary.get("promotion_ready"):
        return {
            "model_quality_claim": "pair_full_candidate",
            "reason": "A fixed-retention route reached pair-full.",
            "next_action": "run seed stability before promotion",
        }
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "The first-token route recovers fixed but loses loss, so it is not a promotion route.",
        "next_action": "build a loss-rebalance objective using the fixed-recovery route as evidence",
    }


def _route_type(corpus_mode: str, label: str) -> str:
    text = f"{label} {corpus_mode}".casefold()
    if "first_token" in text or "first-token" in text:
        return "first-token"
    if "prompt_guard" in text or "prompt-guard" in text:
        return "prompt-guard"
    if "balanced" in text:
        return "balanced"
    return "unknown"


__all__ = [
    "PAIR_FIXED_RETENTION_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_FIXED_RETENTION_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_FIXED_RETENTION_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_FIXED_RETENTION_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_FIXED_RETENTION_ROUTE_DECISION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_fixed_retention_route_decision",
    "locate_fixed_retention_route_decision_input",
    "read_fixed_retention_route_decision_input",
    "resolve_exit_code",
]
