from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison import (
    PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_FRESH_SEED_ROUTE_DECISION_JSON_FILENAME = "model_capability_required_term_pair_fresh_seed_route_decision.json"
PAIR_FRESH_SEED_ROUTE_DECISION_CSV_FILENAME = "model_capability_required_term_pair_fresh_seed_route_decision.csv"
PAIR_FRESH_SEED_ROUTE_DECISION_TEXT_FILENAME = "model_capability_required_term_pair_fresh_seed_route_decision.txt"
PAIR_FRESH_SEED_ROUTE_DECISION_MARKDOWN_FILENAME = "model_capability_required_term_pair_fresh_seed_route_decision.md"
PAIR_FRESH_SEED_ROUTE_DECISION_HTML_FILENAME = "model_capability_required_term_pair_fresh_seed_route_decision.html"


def locate_fresh_seed_route_decision_input(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME
    return source


def read_fresh_seed_route_decision_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("fresh-seed route decision input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_fresh_seed_route_decision(
    comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_reports = list_of_dicts(comparison.get("source_reports"))
    term_rows = list_of_dicts(comparison.get("term_rows"))
    issues = _issues(comparison, source_reports)
    route_rows = [_route_row(row, term_rows) for row in source_reports]
    summary = _summary(comparison, route_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair fresh-seed route decision",
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


def _issues(comparison: dict[str, Any], source_reports: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if comparison.get("status") != "pass":
        issues.append("source comparison status is not pass")
    if len(source_reports) < 2:
        issues.append("at least two source reports are required")
    return issues


def _route_row(source: dict[str, Any], term_rows: list[dict[str, Any]]) -> dict[str, Any]:
    label = str(source.get("source_label") or "")
    scoped = [row for row in term_rows if str(row.get("source_label") or "") == label]
    hit_terms = sorted({str(row.get("term")) for row in scoped if row.get("continuation_hit")})
    return {
        "source_label": label,
        "corpus_mode": source.get("corpus_mode"),
        "pair_full_seed_count": int(source.get("pair_full_seed_count") or 0),
        "seed_count": int(source.get("seed_count") or 0),
        "stable_pair_full": bool(source.get("stable_pair_full")),
        "hit_terms": hit_terms,
        "hit_term_count": len(hit_terms),
        "route_type": _route_type(label, source.get("corpus_mode")),
        "rejection_reasons": _rejection_reasons(source, hit_terms),
    }


def _summary(comparison: dict[str, Any], route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparison_summary = as_dict(comparison.get("summary"))
    pair_full_route_count = sum(1 for row in route_rows if int(row.get("pair_full_seed_count") or 0) > 0)
    first_token_route_count = sum(1 for row in route_rows if row.get("route_type") == "first_token")
    width_route_count = sum(1 for row in route_rows if row.get("route_type") == "width_scaling")
    return {
        "route_count": len(route_rows),
        "pair_full_route_count": pair_full_route_count,
        "first_token_route_count": first_token_route_count,
        "width_route_count": width_route_count,
        "union_hit_terms": comparison_summary.get("union_hit_terms", []),
        "pair_full_profile_seed_count": comparison_summary.get("pair_full_profile_seed_count"),
        "stop_first_token_route": first_token_route_count > 0 and pair_full_route_count == 0,
        "stop_width_scaling": width_route_count > 0 and pair_full_route_count == 0,
        "best_residual_signal": _best_residual_signal(route_rows),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_fresh_seed_route_decision_input"
    if summary.get("pair_full_route_count"):
        return "promote_fresh_seed_pair_full_route"
    if summary.get("stop_first_token_route") and summary.get("stop_width_scaling"):
        return "stop_first_token_and_width_for_fresh_seed"
    if summary.get("stop_first_token_route"):
        return "stop_first_token_route_for_fresh_seed"
    if summary.get("stop_width_scaling"):
        return "stop_width_scaling_for_fresh_seed"
    return "record_fresh_seed_route_decision"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The fresh-seed comparison input is incomplete or failed.",
            "next_action": "repair comparison inputs before choosing a route",
        }
    if summary.get("pair_full_route_count"):
        return {
            "model_quality_claim": "fresh_seed_candidate_found",
            "reason": "At least one compared fresh-seed route reached pair-full.",
            "next_action": "replay held-out prompts before raising the claim",
        }
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "Compared fresh-seed routes did not reach pair-full and only preserved limited fixed-term evidence.",
        "next_action": "stop first-token rows and width scaling; design a branch-binding objective before another seed sweep",
    }


def _route_type(label: str, corpus_mode: Any) -> str:
    text = f"{label} {corpus_mode}".casefold()
    if "first-token" in text or "first_token" in text:
        return "first_token"
    if "wider" in text or "embd" in text or "width" in text:
        return "width_scaling"
    return "baseline"


def _rejection_reasons(source: dict[str, Any], hit_terms: list[str]) -> list[str]:
    reasons = []
    if int(source.get("pair_full_seed_count") or 0) <= 0:
        reasons.append("no_pair_full_seed")
    if "loss" not in hit_terms:
        reasons.append("loss_term_missing")
    if not bool(source.get("stable_pair_full")):
        reasons.append("not_stable")
    return reasons


def _best_residual_signal(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    best = max(rows, key=lambda row: (int(row.get("hit_term_count") or 0), -len(row.get("rejection_reasons", []))))
    return str(best.get("source_label") or "")


__all__ = [
    "PAIR_FRESH_SEED_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_FRESH_SEED_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_FRESH_SEED_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_FRESH_SEED_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_FRESH_SEED_ROUTE_DECISION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_fresh_seed_route_decision",
    "locate_fresh_seed_route_decision_input",
    "read_fresh_seed_route_decision_input",
    "resolve_exit_code",
]
