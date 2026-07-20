from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison import (
    PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_BRANCH_BINDING_ROUTE_DECISION_JSON_FILENAME = "model_capability_required_term_pair_branch_binding_route_decision.json"
PAIR_BRANCH_BINDING_ROUTE_DECISION_CSV_FILENAME = "model_capability_required_term_pair_branch_binding_route_decision.csv"
PAIR_BRANCH_BINDING_ROUTE_DECISION_TEXT_FILENAME = "model_capability_required_term_pair_branch_binding_route_decision.txt"
PAIR_BRANCH_BINDING_ROUTE_DECISION_MARKDOWN_FILENAME = "model_capability_required_term_pair_branch_binding_route_decision.md"
PAIR_BRANCH_BINDING_ROUTE_DECISION_HTML_FILENAME = "model_capability_required_term_pair_branch_binding_route_decision.html"


def locate_branch_binding_route_decision_input(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME
    return source


def read_branch_binding_route_decision_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("branch-binding route decision input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_branch_binding_route_decision(
    comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_reports = list_of_dicts(comparison.get("source_reports"))
    term_rows = list_of_dicts(comparison.get("term_rows"))
    route_rows = [_route_row(source, term_rows) for source in source_reports]
    summary = _summary(comparison, route_rows)
    issues = _issues(comparison, route_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair branch-binding route decision",
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


def _route_row(source: dict[str, Any], term_rows: list[dict[str, Any]]) -> dict[str, Any]:
    label = str(source.get("source_label") or "")
    scoped = [row for row in term_rows if str(row.get("source_label") or "") == label]
    hit_terms = sorted({str(row.get("term")) for row in scoped if row.get("continuation_hit")})
    route_type = _route_type(label, source.get("corpus_mode"))
    return {
        "source_label": label,
        "corpus_mode": source.get("corpus_mode"),
        "route_type": route_type,
        "pair_full_seed_count": int(source.get("pair_full_seed_count") or 0),
        "seed_count": int(source.get("seed_count") or 0),
        "stable_pair_full": bool(source.get("stable_pair_full")),
        "hit_terms": hit_terms,
        "hit_term_count": len(hit_terms),
        "rejection_reasons": _rejection_reasons(source, hit_terms, route_type),
    }


def _summary(comparison: dict[str, Any], route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparison_summary = as_dict(comparison.get("summary"))
    branch_rows = [row for row in route_rows if row.get("route_type") == "branch_binding"]
    branch_pair_full_count = sum(1 for row in branch_rows if int(row.get("pair_full_seed_count") or 0) > 0)
    branch_visible_hit_count = sum(1 for row in branch_rows if int(row.get("hit_term_count") or 0) > 0)
    baseline_rows = [row for row in route_rows if row.get("route_type") == "baseline"]
    return {
        "route_count": len(route_rows),
        "branch_binding_route_count": len(branch_rows),
        "branch_binding_pair_full_route_count": branch_pair_full_count,
        "branch_binding_visible_hit_route_count": branch_visible_hit_count,
        "baseline_visible_hit_route_count": sum(1 for row in baseline_rows if int(row.get("hit_term_count") or 0) > 0),
        "pair_full_profile_seed_count": comparison_summary.get("pair_full_profile_seed_count"),
        "union_hit_terms": comparison_summary.get("union_hit_terms", []),
        "best_residual_signal": _best_residual_signal(route_rows),
        "stop_branch_binding_v1": len(branch_rows) > 0 and branch_pair_full_count == 0,
        "branch_binding_regressed_below_baseline": branch_visible_hit_count == 0
        and any(int(row.get("hit_term_count") or 0) > 0 for row in baseline_rows),
    }


def _issues(comparison: dict[str, Any], route_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if comparison.get("status") != "pass":
        issues.append("source comparison status is not pass")
    if len(route_rows) < 2:
        issues.append("at least two compared routes are required")
    if not any(row.get("route_type") == "branch_binding" for row in route_rows):
        issues.append("at least one branch-binding route is required")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_branch_binding_route_decision_input"
    if int(summary.get("branch_binding_pair_full_route_count") or 0) > 0:
        return "promote_branch_binding_pair_full_route"
    if summary.get("branch_binding_regressed_below_baseline"):
        return "stop_branch_binding_v1_and_keep_residual_baseline"
    if summary.get("stop_branch_binding_v1"):
        return "stop_branch_binding_v1_until_stronger_objective"
    return "record_branch_binding_route_decision"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The branch-binding route decision input is incomplete or failed.",
            "next_action": "repair comparison inputs before selecting a branch-binding route",
        }
    if int(summary.get("branch_binding_pair_full_route_count") or 0) > 0:
        return {
            "model_quality_claim": "branch_binding_candidate_found",
            "reason": "At least one branch-binding route reached pair-full.",
            "next_action": "run held-out and fresh-seed replay before promotion",
        }
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "Compared branch-binding routes did not reach pair-full and did not preserve the baseline partial hit.",
        "next_action": "stop branch-binding v1/v2; require a stronger objective before another training run",
    }


def _route_type(label: str, corpus_mode: Any) -> str:
    text = f"{label} {corpus_mode}".casefold()
    if "branch-binding" in text or "branch_binding" in text:
        return "branch_binding"
    return "baseline"


def _rejection_reasons(source: dict[str, Any], hit_terms: list[str], route_type: str) -> list[str]:
    reasons = []
    if int(source.get("pair_full_seed_count") or 0) <= 0:
        reasons.append("no_pair_full_seed")
    if not hit_terms:
        reasons.append("no_visible_term_hit")
    if "loss" not in hit_terms:
        reasons.append("loss_term_missing")
    if route_type == "branch_binding":
        reasons.append("branch_binding_not_promotable")
    return reasons


def _best_residual_signal(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    best = max(rows, key=lambda row: (int(row.get("hit_term_count") or 0), -len(row.get("rejection_reasons", []))))
    return str(best.get("source_label") or "")


__all__ = [
    "PAIR_BRANCH_BINDING_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_BRANCH_BINDING_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_BRANCH_BINDING_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_BRANCH_BINDING_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_BRANCH_BINDING_ROUTE_DECISION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_branch_binding_route_decision",
    "locate_branch_binding_route_decision_input",
    "read_branch_binding_route_decision_input",
    "resolve_exit_code",
]
