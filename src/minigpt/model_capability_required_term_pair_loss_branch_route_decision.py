from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_branch_objective_comparison import (
    PAIR_LOSS_BRANCH_OBJECTIVE_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_LOSS_BRANCH_ROUTE_DECISION_JSON_FILENAME = "model_capability_required_term_pair_loss_branch_route_decision.json"
PAIR_LOSS_BRANCH_ROUTE_DECISION_CSV_FILENAME = "model_capability_required_term_pair_loss_branch_route_decision.csv"
PAIR_LOSS_BRANCH_ROUTE_DECISION_TEXT_FILENAME = "model_capability_required_term_pair_loss_branch_route_decision.txt"
PAIR_LOSS_BRANCH_ROUTE_DECISION_MARKDOWN_FILENAME = "model_capability_required_term_pair_loss_branch_route_decision.md"
PAIR_LOSS_BRANCH_ROUTE_DECISION_HTML_FILENAME = "model_capability_required_term_pair_loss_branch_route_decision.html"


def locate_loss_branch_route_decision_input(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_LOSS_BRANCH_OBJECTIVE_COMPARISON_JSON_FILENAME
    return source


def read_loss_branch_route_decision_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("loss-branch route decision input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_loss_branch_route_decision(
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
        "title": "MiniGPT required-term pair loss-branch route decision",
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
    corpus_mode = str(row.get("corpus_mode") or "")
    route_type = _route_type(corpus_mode, str(row.get("source_label") or ""))
    hit_terms = [str(term) for term in row.get("hit_terms") or []]
    missed_terms = [str(term) for term in row.get("missed_terms") or []]
    pair_full = bool(row.get("pair_full_observed"))
    loss_only = hit_terms == ["loss"]
    complexity = _complexity_score(route_type)
    return {
        "source_label": row.get("source_label"),
        "corpus_mode": corpus_mode,
        "route_type": route_type,
        "seed": row.get("seed"),
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "pair_full_observed": pair_full,
        "loss_only_tradeoff": loss_only,
        "complexity_score": complexity,
        "stability_replay_candidate": loss_only and complexity == 1,
        "rejection_reasons": _rejection_reasons(pair_full, hit_terms, missed_terms),
    }


def _summary(comparison: dict[str, Any], route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparison_summary = as_dict(comparison.get("summary"))
    pair_full_count = sum(1 for row in route_rows if row.get("pair_full_observed"))
    loss_only_count = sum(1 for row in route_rows if row.get("loss_only_tradeoff"))
    candidate = _selected_stability_candidate(route_rows)
    return {
        "route_count": len(route_rows),
        "pair_full_route_count": pair_full_count,
        "loss_only_tradeoff_route_count": loss_only_count,
        "comparison_decision": comparison.get("decision"),
        "comparison_union_hit_terms": comparison_summary.get("union_hit_terms", []),
        "promotion_ready": pair_full_count > 0,
        "all_routes_loss_only_tradeoff": bool(route_rows) and loss_only_count == len(route_rows),
        "selected_stability_route": candidate.get("source_label"),
        "selected_stability_corpus_mode": candidate.get("corpus_mode"),
        "selected_stability_route_type": candidate.get("route_type"),
        "seed_stability_replay_required": bool(candidate),
        "fixed_retention_objective_required": pair_full_count == 0 and loss_only_count > 0,
    }


def _issues(comparison: dict[str, Any], route_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if comparison.get("status") != "pass":
        issues.append("source comparison status is not pass")
    if not route_rows:
        issues.append("at least one loss-branch route row is required")
    if not any(row.get("loss_only_tradeoff") for row in route_rows):
        issues.append("no loss-only tradeoff route is available for decision")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_branch_route_decision_input"
    if summary.get("promotion_ready"):
        return "promote_loss_branch_pair_full_route"
    if summary.get("seed_stability_replay_required"):
        return "select_targeted_loss_branch_for_seed_stability_not_promotion"
    return "stop_loss_branch_objectives_until_fixed_retention_design"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The loss-branch comparison is incomplete or failed.",
            "next_action": "repair the comparison before selecting a route",
        }
    if summary.get("promotion_ready"):
        return {
            "model_quality_claim": "pair_full_candidate",
            "reason": "At least one route reached pair-full.",
            "next_action": "run held-out and fresh-seed replay before promotion",
        }
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "All available loss-branch routes recover loss but miss fixed; the simplest route is selected only as a stability baseline.",
        "next_action": "run targeted loss-branch seed stability, then design a fixed-retention objective",
    }


def _selected_stability_candidate(route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in route_rows if row.get("loss_only_tradeoff")]
    if not candidates:
        return {}
    return min(candidates, key=lambda row: (int(row.get("complexity_score") or 99), str(row.get("source_label") or "")))


def _route_type(corpus_mode: str, label: str) -> str:
    text = f"{label} {corpus_mode}".casefold()
    if "targeted" in text:
        return "targeted"
    if "dual_anchor" in text or "dual-anchor" in text:
        return "dual_anchor"
    if "micro_span" in text or "micro-span" in text:
        return "micro_span"
    return "unknown"


def _complexity_score(route_type: str) -> int:
    return {"targeted": 1, "dual_anchor": 2, "micro_span": 3}.get(route_type, 99)


def _rejection_reasons(pair_full: bool, hit_terms: list[str], missed_terms: list[str]) -> list[str]:
    reasons: list[str] = []
    if not pair_full:
        reasons.append("no_pair_full")
    if "fixed" in missed_terms:
        reasons.append("fixed_missing")
    if "loss" not in hit_terms:
        reasons.append("loss_missing")
    if hit_terms == ["loss"]:
        reasons.append("loss_only_tradeoff")
    return reasons


__all__ = [
    "PAIR_LOSS_BRANCH_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_LOSS_BRANCH_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_LOSS_BRANCH_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_LOSS_BRANCH_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_LOSS_BRANCH_ROUTE_DECISION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_loss_branch_route_decision",
    "locate_loss_branch_route_decision_input",
    "read_loss_branch_route_decision_input",
    "resolve_exit_code",
]
