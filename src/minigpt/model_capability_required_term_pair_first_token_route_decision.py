from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison import (
    PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_FIRST_TOKEN_ROUTE_DECISION_JSON_FILENAME = "model_capability_required_term_pair_first_token_route_decision.json"
PAIR_FIRST_TOKEN_ROUTE_DECISION_CSV_FILENAME = "model_capability_required_term_pair_first_token_route_decision.csv"
PAIR_FIRST_TOKEN_ROUTE_DECISION_TEXT_FILENAME = "model_capability_required_term_pair_first_token_route_decision.txt"
PAIR_FIRST_TOKEN_ROUTE_DECISION_MARKDOWN_FILENAME = "model_capability_required_term_pair_first_token_route_decision.md"
PAIR_FIRST_TOKEN_ROUTE_DECISION_HTML_FILENAME = "model_capability_required_term_pair_first_token_route_decision.html"


def locate_first_token_route_decision_input(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME
    return source


def read_first_token_route_decision_input(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("first-token route decision input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_first_token_route_decision(
    comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_reports = list_of_dicts(comparison.get("source_reports"))
    issues = _issues(comparison, source_reports)
    selected_route = _selected_route(source_reports) if not issues else {}
    rejected_routes = _rejected_routes(source_reports, selected_route)
    summary = _summary(comparison, source_reports, selected_route, rejected_routes)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair first-token route decision",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_comparison": str(source_path or ""),
        "selected_route": selected_route,
        "rejected_routes": rejected_routes,
        "summary": summary,
        "interpretation": _interpretation(status, summary, selected_route),
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
        issues.append("at least two source reports are required for a route decision")
    if int(as_dict(comparison.get("summary")).get("compared_report_count") or 0) < 2:
        issues.append("source comparison did not compare at least two reports")
    return issues


def _selected_route(source_reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not source_reports:
        return {}
    max_pair_full = max(_pair_full_count(row) for row in source_reports)
    best_rows = [row for row in source_reports if _pair_full_count(row) == max_pair_full]
    simple_rows = [row for row in best_rows if not _is_first_token_density_route(row)]
    selected = simple_rows[0] if simple_rows else best_rows[0]
    return {
        "source_label": selected.get("source_label"),
        "source_path": selected.get("source_path"),
        "corpus_mode": selected.get("corpus_mode"),
        "pair_full_seed_count": _pair_full_count(selected),
        "seed_count": _seed_count(selected),
        "pair_full_seed_rate": selected.get("pair_full_seed_rate"),
        "stable_pair_full": bool(selected.get("stable_pair_full")),
        "rationale": _selected_rationale(selected, max_pair_full, bool(simple_rows)),
    }


def _rejected_routes(source_reports: list[dict[str, Any]], selected_route: dict[str, Any]) -> list[dict[str, Any]]:
    selected_label = str(selected_route.get("source_label") or "")
    return [_rejected_route(row) for row in source_reports if str(row.get("source_label") or "") != selected_label]


def _rejected_route(row: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if _pair_full_count(row) <= 0:
        reasons.append("no_pair_full_seed")
    if not bool(row.get("stable_pair_full")):
        reasons.append("not_stable_across_seeds")
    if _is_first_token_density_route(row):
        reasons.append("first_token_density_no_stable_gain")
    return {
        "source_label": row.get("source_label"),
        "source_path": row.get("source_path"),
        "corpus_mode": row.get("corpus_mode"),
        "pair_full_seed_count": _pair_full_count(row),
        "seed_count": _seed_count(row),
        "pair_full_seed_rate": row.get("pair_full_seed_rate"),
        "reasons": sorted(set(reasons)),
    }


def _summary(
    comparison: dict[str, Any],
    source_reports: list[dict[str, Any]],
    selected_route: dict[str, Any],
    rejected_routes: list[dict[str, Any]],
) -> dict[str, Any]:
    comparison_summary = as_dict(comparison.get("summary"))
    max_pair_full = max((_pair_full_count(row) for row in source_reports), default=0)
    stable_route_count = sum(1 for row in source_reports if bool(row.get("stable_pair_full")))
    first_token_density_count = sum(1 for row in source_reports if _is_first_token_density_route(row))
    return {
        "source_report_count": len(source_reports),
        "first_token_density_route_count": first_token_density_count,
        "stable_route_count": stable_route_count,
        "max_pair_full_seed_count": max_pair_full,
        "selected_source_label": selected_route.get("source_label"),
        "rejected_route_count": len(rejected_routes),
        "source_pair_full_profile_seed_count": comparison_summary.get("pair_full_profile_seed_count"),
        "source_branch_competition_seed_count": comparison_summary.get("branch_competition_seed_count"),
        "stop_first_token_density": stable_route_count == 0 and first_token_density_count > 0,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_first_token_route_decision_input"
    if int(summary.get("stable_route_count") or 0) > 0:
        return "promote_stable_equals_surface_route_to_heldout"
    if bool(summary.get("stop_first_token_density")) and int(summary.get("max_pair_full_seed_count") or 0) > 0:
        return "stop_first_token_density_and_replay_best_baseline"
    if bool(summary.get("stop_first_token_density")):
        return "stop_first_token_density_route"
    return "record_first_token_route_decision"


def _interpretation(status: str, summary: dict[str, Any], selected_route: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route decision input is incomplete or structurally failed.",
            "next_action": "repair the comparison input before selecting another training route",
        }
    if bool(summary.get("stop_first_token_density")):
        return {
            "model_quality_claim": "route_decision_only",
            "reason": "First-token density variants do not improve stable pair-full coverage over the simpler baseline.",
            "next_action": f"replay held-out equals-surface prompts for {selected_route.get('source_label')} before adding more corpus variants",
        }
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "The compared reports do not require a first-token density stop decision.",
        "next_action": "keep the selected route under evidence review",
    }


def _selected_rationale(row: dict[str, Any], max_pair_full: int, preferred_simple: bool) -> str:
    if preferred_simple:
        return "highest pair-full seed count with the simplest non-first-token-density objective"
    if _pair_full_count(row) == max_pair_full:
        return "highest pair-full seed count among available routes"
    return "fallback selected route"


def _is_first_token_density_route(row: dict[str, Any]) -> bool:
    label = str(row.get("source_label") or "").casefold()
    mode = str(row.get("corpus_mode") or "").casefold()
    return "first-token" in label or "first_token" in mode


def _pair_full_count(row: dict[str, Any]) -> int:
    return int(row.get("pair_full_seed_count") or 0)


def _seed_count(row: dict[str, Any]) -> int:
    return int(row.get("seed_count") or 0)


__all__ = [
    "PAIR_FIRST_TOKEN_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_FIRST_TOKEN_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_FIRST_TOKEN_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_FIRST_TOKEN_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_FIRST_TOKEN_ROUTE_DECISION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_first_token_route_decision",
    "locate_first_token_route_decision_input",
    "read_first_token_route_decision_input",
    "resolve_exit_code",
]
