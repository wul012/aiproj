from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from minigpt.model_capability_required_term_pair_colon_immediate_stability import PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME
from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison import PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME
from minigpt.model_capability_required_term_pair_fresh_seed_route_decision import PAIR_FRESH_SEED_ROUTE_DECISION_JSON_FILENAME
from minigpt.model_capability_required_term_pair_route_heldout_replay import PAIR_ROUTE_HELDOUT_REPLAY_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_ROUTE_CLOSEOUT_SUMMARY_JSON_FILENAME = "model_capability_required_term_pair_route_closeout_summary.json"
PAIR_ROUTE_CLOSEOUT_SUMMARY_CSV_FILENAME = "model_capability_required_term_pair_route_closeout_summary.csv"
PAIR_ROUTE_CLOSEOUT_SUMMARY_TEXT_FILENAME = "model_capability_required_term_pair_route_closeout_summary.txt"
PAIR_ROUTE_CLOSEOUT_SUMMARY_MARKDOWN_FILENAME = "model_capability_required_term_pair_route_closeout_summary.md"
PAIR_ROUTE_CLOSEOUT_SUMMARY_HTML_FILENAME = "model_capability_required_term_pair_route_closeout_summary.html"


def locate_heldout_replay_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_ROUTE_HELDOUT_REPLAY_JSON_FILENAME
    return source


def locate_fresh_seed_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME
    return source


def locate_route_comparison_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME
    return source


def locate_fresh_seed_route_decision_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FRESH_SEED_ROUTE_DECISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route closeout input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_route_closeout_summary(
    *,
    heldout_report: dict[str, Any],
    fresh_seed_reports: Sequence[dict[str, Any]],
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
    heldout_path: str | Path | None = None,
    fresh_seed_paths: Sequence[str | Path] | None = None,
    fresh_seed_labels: Sequence[str] | None = None,
    comparison_path: str | Path | None = None,
    route_decision_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    fresh_rows = _fresh_seed_rows(fresh_seed_reports, fresh_seed_paths or [], fresh_seed_labels or [])
    evidence_rows = _evidence_rows(
        heldout_report=heldout_report,
        heldout_path=heldout_path,
        fresh_rows=fresh_rows,
        comparison_report=comparison_report,
        comparison_path=comparison_path,
        route_decision_report=route_decision_report,
        route_decision_path=route_decision_path,
    )
    summary = _summary(heldout_report, fresh_rows, comparison_report, route_decision_report)
    issues = _issues(summary, evidence_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair route closeout summary",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "summary": summary,
        "evidence_rows": evidence_rows,
        "interpretation": _interpretation(status, summary),
    }


def _fresh_seed_rows(
    reports: Sequence[dict[str, Any]],
    paths: Sequence[str | Path],
    labels: Sequence[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, report in enumerate(reports):
        summary = as_dict(report.get("summary"))
        seed_rows = list_of_dicts(report.get("seed_rows"))
        label = _source_value(labels, index, f"fresh-seed-{index + 1}")
        path = _source_value(paths, index, "")
        rows.append(
            {
                "label": label,
                "path": str(path),
                "status": report.get("status"),
                "decision": report.get("decision"),
                "seed_count": int(summary.get("seed_count") or 0),
                "pair_full_seed_count": int(summary.get("pair_full_seed_count") or 0),
                "stable_pair_full": bool(summary.get("stable_pair_full")),
                "continuation_hit_count": sum(int(row.get("continuation_hit_count") or 0) for row in seed_rows),
            }
        )
    return rows


def _evidence_rows(
    *,
    heldout_report: dict[str, Any],
    heldout_path: str | Path | None,
    fresh_rows: list[dict[str, Any]],
    comparison_report: dict[str, Any],
    comparison_path: str | Path | None,
    route_decision_report: dict[str, Any],
    route_decision_path: str | Path | None,
) -> list[dict[str, Any]]:
    heldout_summary = as_dict(heldout_report.get("summary"))
    comparison_summary = as_dict(comparison_report.get("summary"))
    route_summary = as_dict(route_decision_report.get("summary"))
    rows = [
        {
            "label": "v570-heldout-expanded",
            "evidence_type": "heldout_replay",
            "path": str(heldout_path or ""),
            "status": heldout_report.get("status"),
            "decision": heldout_report.get("decision"),
            "key_result": f"{heldout_summary.get('heldout_pair_full_count')}/{heldout_summary.get('heldout_spec_count')} heldout pair-full",
        }
    ]
    rows.extend(
        {
            "label": row.get("label"),
            "evidence_type": "fresh_seed_stability",
            "path": row.get("path"),
            "status": row.get("status"),
            "decision": row.get("decision"),
            "key_result": f"{row.get('pair_full_seed_count')}/{row.get('seed_count')} pair-full, hits={row.get('continuation_hit_count')}",
        }
        for row in fresh_rows
    )
    rows.extend(
        [
            {
                "label": "v576-variable-comparison",
                "evidence_type": "comparison",
                "path": str(comparison_path or ""),
                "status": comparison_report.get("status"),
                "decision": comparison_report.get("decision"),
                "key_result": f"union_hit_terms={','.join(str(term) for term in comparison_summary.get('union_hit_terms', []))}",
            },
            {
                "label": "v577-route-decision",
                "evidence_type": "route_decision",
                "path": str(route_decision_path or ""),
                "status": route_decision_report.get("status"),
                "decision": route_decision_report.get("decision"),
                "key_result": f"best_residual_signal={route_summary.get('best_residual_signal')}",
            },
        ]
    )
    return rows


def _summary(
    heldout_report: dict[str, Any],
    fresh_rows: list[dict[str, Any]],
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
) -> dict[str, Any]:
    heldout = as_dict(heldout_report.get("summary"))
    comparison = as_dict(comparison_report.get("summary"))
    route_decision = as_dict(route_decision_report.get("summary"))
    fresh_pair_full_count = sum(int(row.get("pair_full_seed_count") or 0) for row in fresh_rows)
    fresh_hit_count = sum(int(row.get("continuation_hit_count") or 0) for row in fresh_rows)
    return {
        "heldout_pair_full_count": int(heldout.get("heldout_pair_full_count") or 0),
        "heldout_spec_count": int(heldout.get("heldout_spec_count") or 0),
        "heldout_all_pair_full": bool(heldout.get("heldout_all_pair_full")),
        "fresh_seed_route_count": len(fresh_rows),
        "fresh_seed_pair_full_count": fresh_pair_full_count,
        "fresh_seed_continuation_hit_count": fresh_hit_count,
        "comparison_union_hit_terms": comparison.get("union_hit_terms", []),
        "comparison_pair_full_profile_seed_count": int(comparison.get("pair_full_profile_seed_count") or 0),
        "route_decision": route_decision_report.get("decision"),
        "stop_first_token_route": bool(route_decision.get("stop_first_token_route")),
        "stop_width_scaling": bool(route_decision.get("stop_width_scaling")),
        "best_residual_signal": route_decision.get("best_residual_signal"),
        "closeout_ready": bool(heldout.get("heldout_all_pair_full"))
        and fresh_pair_full_count == 0
        and route_decision_report.get("decision") == "stop_first_token_and_width_for_fresh_seed",
    }


def _issues(summary: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> list[str]:
    issues = []
    for row in evidence_rows:
        if row.get("status") != "pass":
            issues.append(f"{row.get('label')} status is not pass")
    if not summary.get("heldout_all_pair_full"):
        issues.append("heldout replay did not remain pair-full on all prompts")
    if int(summary.get("fresh_seed_pair_full_count") or 0) > 0:
        issues.append("fresh-seed route reached pair-full; closeout should promote instead")
    if not summary.get("stop_first_token_route"):
        issues.append("route decision did not stop first-token route")
    if not summary.get("stop_width_scaling"):
        issues.append("route decision did not stop width scaling")
    if not summary.get("closeout_ready"):
        issues.append("route closeout summary is not ready")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_route_closeout_inputs"
    if summary.get("closeout_ready"):
        return "close_required_term_pair_route_before_new_objective"
    return "record_required_term_pair_route_closeout"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route closeout inputs are incomplete or contradictory.",
            "next_action": "repair evidence inputs before closing the route",
        }
    return {
        "model_quality_claim": "bounded_transfer_not_generalized",
        "reason": "The selected route transfers across held-out surfaces but does not generalize to fresh seed 3535.",
        "next_action": "start a branch-binding objective; do not continue first-token rows or width scaling variants",
    }


def _source_value(values: Sequence[Any], index: int, default: Any) -> Any:
    if index < len(values):
        return values[index]
    return default


__all__ = [
    "PAIR_ROUTE_CLOSEOUT_SUMMARY_CSV_FILENAME",
    "PAIR_ROUTE_CLOSEOUT_SUMMARY_HTML_FILENAME",
    "PAIR_ROUTE_CLOSEOUT_SUMMARY_JSON_FILENAME",
    "PAIR_ROUTE_CLOSEOUT_SUMMARY_MARKDOWN_FILENAME",
    "PAIR_ROUTE_CLOSEOUT_SUMMARY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_route_closeout_summary",
    "locate_fresh_seed_report",
    "locate_fresh_seed_route_decision_report",
    "locate_heldout_replay_report",
    "locate_route_comparison_report",
    "read_json_report",
    "resolve_exit_code",
]
