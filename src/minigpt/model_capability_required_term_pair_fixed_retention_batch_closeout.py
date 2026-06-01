from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import (
    PAIR_FIXED_RETENTION_OBJECTIVE_COMPARISON_JSON_FILENAME,
    TARGET_TERMS,
)
from minigpt.model_capability_required_term_pair_fixed_retention_route_decision import (
    PAIR_FIXED_RETENTION_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_JSON_FILENAME = "model_capability_required_term_pair_fixed_retention_batch_closeout.json"
PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_CSV_FILENAME = "model_capability_required_term_pair_fixed_retention_batch_closeout.csv"
PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_TEXT_FILENAME = "model_capability_required_term_pair_fixed_retention_batch_closeout.txt"
PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_MARKDOWN_FILENAME = "model_capability_required_term_pair_fixed_retention_batch_closeout.md"
PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_HTML_FILENAME = "model_capability_required_term_pair_fixed_retention_batch_closeout.html"


def locate_fixed_retention_refresh_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def locate_fixed_retention_comparison_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FIXED_RETENTION_OBJECTIVE_COMPARISON_JSON_FILENAME
    return source


def locate_fixed_retention_route_decision_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FIXED_RETENTION_ROUTE_DECISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("fixed-retention batch closeout input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_fixed_retention_batch_closeout(
    *,
    initial_reports: Sequence[dict[str, Any]],
    loss_rebalance_reports: Sequence[dict[str, Any]],
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
    initial_paths: Sequence[str | Path] | None = None,
    loss_rebalance_paths: Sequence[str | Path] | None = None,
    comparison_path: str | Path | None = None,
    route_decision_path: str | Path | None = None,
    initial_labels: Sequence[str] | None = None,
    loss_rebalance_labels: Sequence[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    initial_rows = [
        _refresh_row("initial-objective", index, report, _source_label(initial_labels, index, "initial"), _source_path(initial_paths, index))
        for index, report in enumerate(initial_reports)
    ]
    loss_rows = [
        _refresh_row(
            "loss-rebalance",
            index,
            report,
            _source_label(loss_rebalance_labels, index, "loss-rebalance"),
            _source_path(loss_rebalance_paths, index),
        )
        for index, report in enumerate(loss_rebalance_reports)
    ]
    evidence_rows = [
        *_control_rows(comparison_report, route_decision_report, comparison_path, route_decision_path),
        *initial_rows,
        *loss_rows,
    ]
    summary = _summary(initial_rows, loss_rows, comparison_report, route_decision_report)
    issues = _issues(evidence_rows, summary, comparison_report, route_decision_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair fixed-retention batch closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "summary": summary,
        "evidence_rows": evidence_rows,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _source_path(paths: Sequence[str | Path] | None, index: int) -> str:
    if paths is None or index >= len(paths):
        return ""
    return str(paths[index])


def _source_label(labels: Sequence[str] | None, index: int, prefix: str) -> str:
    if labels is not None and index < len(labels) and labels[index]:
        return str(labels[index])
    return f"{prefix}-{index + 1}"


def _refresh_row(phase: str, index: int, report: dict[str, Any], label: str, path: str) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    settings = as_dict(report.get("settings"))
    hit_terms = _hit_terms(report)
    missed_terms = [term for term in TARGET_TERMS if term not in hit_terms]
    pair_full = bool(summary.get("pair_full_observed"))
    return {
        "label": label,
        "phase": phase,
        "index": index,
        "path": path,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "corpus_mode": settings.get("corpus_mode"),
        "seed": settings.get("seed"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": bool(summary.get("checkpoint_exists")),
        "pair_full_observed": pair_full,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "branch_class": _branch_class(hit_terms, pair_full),
        "key_result": f"hits={','.join(hit_terms) or 'none'}; pair_full={pair_full}",
    }


def _hit_terms(report: dict[str, Any]) -> list[str]:
    replay = as_dict(report.get("replay_report"))
    hits = {
        str(row.get("term"))
        for row in list_of_dicts(replay.get("case_rows"))
        if row.get("continuation_hit") and str(row.get("term")) in TARGET_TERMS
    }
    return sorted(hits)


def _branch_class(hit_terms: list[str], pair_full: bool) -> str:
    if pair_full or set(TARGET_TERMS).issubset(hit_terms):
        return "pair-full"
    if hit_terms == ["fixed"]:
        return "fixed-only"
    if hit_terms == ["loss"]:
        return "loss-only"
    if hit_terms:
        return "partial"
    return "all-miss"


def _control_rows(
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
    comparison_path: str | Path | None,
    route_decision_path: str | Path | None,
) -> list[dict[str, Any]]:
    comparison_summary = as_dict(comparison_report.get("summary"))
    route_summary = as_dict(route_decision_report.get("summary"))
    return [
        {
            "label": "v603-comparison",
            "phase": "control",
            "path": str(comparison_path or ""),
            "status": comparison_report.get("status"),
            "decision": comparison_report.get("decision"),
            "key_result": f"pair_full={comparison_summary.get('pair_full_report_count')}; mixed={comparison_summary.get('mixed_tradeoff_observed')}",
        },
        {
            "label": "v604-route-decision",
            "phase": "control",
            "path": str(route_decision_path or ""),
            "status": route_decision_report.get("status"),
            "decision": route_decision_report.get("decision"),
            "key_result": f"selected={route_summary.get('selected_route')}; loss_rebalance_required={route_summary.get('loss_rebalance_objective_required')}",
        },
    ]


def _summary(
    initial_rows: list[dict[str, Any]],
    loss_rows: list[dict[str, Any]],
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
) -> dict[str, Any]:
    all_rows = [*initial_rows, *loss_rows]
    route_summary = as_dict(route_decision_report.get("summary"))
    loss_pair_full_count = _count_branch(loss_rows, "pair-full")
    loss_fixed_only_count = _count_branch(loss_rows, "fixed-only")
    loss_loss_only_count = _count_branch(loss_rows, "loss-only")
    return {
        "initial_report_count": len(initial_rows),
        "loss_rebalance_report_count": len(loss_rows),
        "total_refresh_report_count": len(all_rows),
        "all_refresh_passed": all(row.get("status") == "pass" for row in all_rows),
        "all_training_passed": all(row.get("training_status") == "pass" for row in all_rows),
        "all_checkpoints_exist": all(bool(row.get("checkpoint_exists")) for row in all_rows),
        "pair_full_report_count": _count_branch(all_rows, "pair-full"),
        "fixed_only_tradeoff_report_count": _count_branch(all_rows, "fixed-only"),
        "loss_only_tradeoff_report_count": _count_branch(all_rows, "loss-only"),
        "loss_rebalance_pair_full_count": loss_pair_full_count,
        "loss_rebalance_fixed_only_count": loss_fixed_only_count,
        "loss_rebalance_loss_only_count": loss_loss_only_count,
        "loss_rebalance_tradeoff_confirmed": loss_pair_full_count == 0 and loss_fixed_only_count > 0 and loss_loss_only_count > 0,
        "route_selected": route_summary.get("selected_route"),
        "route_selected_corpus_mode": route_summary.get("selected_corpus_mode"),
        "route_requires_loss_rebalance": bool(route_summary.get("loss_rebalance_objective_required")),
        "comparison_decision": comparison_report.get("decision"),
        "route_decision": route_decision_report.get("decision"),
        "stop_current_loss_rebalance_routes": loss_pair_full_count == 0 and loss_fixed_only_count > 0 and loss_loss_only_count > 0,
    }


def _count_branch(rows: Sequence[dict[str, Any]], branch_class: str) -> int:
    return sum(1 for row in rows if row.get("branch_class") == branch_class)


def _issues(
    evidence_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    comparison_report: dict[str, Any],
    route_decision_report: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    if comparison_report.get("status") != "pass":
        issues.append("comparison report status is not pass")
    if route_decision_report.get("status") != "pass":
        issues.append("route decision report status is not pass")
    for row in evidence_rows:
        if row.get("phase") == "control":
            continue
        label = row.get("label")
        if row.get("status") != "pass":
            issues.append(f"{label} refresh status is not pass")
        if row.get("training_status") != "pass":
            issues.append(f"{label} training status is not pass")
        if not row.get("checkpoint_exists"):
            issues.append(f"{label} checkpoint is missing")
        if "fixed_retention" not in str(row.get("corpus_mode") or ""):
            issues.append(f"{label} is not a fixed-retention corpus mode")
    if int(summary.get("initial_report_count") or 0) < 3:
        issues.append("at least three initial fixed-retention reports are required")
    if int(summary.get("loss_rebalance_report_count") or 0) < 2:
        issues.append("at least two loss-rebalance reports are required")
    if not summary.get("route_requires_loss_rebalance"):
        issues.append("route decision does not require loss rebalance")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_fixed_retention_batch_closeout_inputs"
    if int(summary.get("loss_rebalance_pair_full_count") or 0) > 0:
        return "promote_loss_rebalance_pair_full_candidate_to_seed_stability"
    if summary.get("loss_rebalance_tradeoff_confirmed"):
        return "close_fixed_retention_loss_rebalance_batch_before_new_design"
    return "record_fixed_retention_batch_without_pair_full"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The fixed-retention batch closeout inputs are incomplete or contradictory.",
            "next_action": "repair closeout inputs before another training route",
        }
    if int(summary.get("loss_rebalance_pair_full_count") or 0) > 0:
        return {
            "model_quality_claim": "pair_full_candidate",
            "reason": "A loss-rebalance route reached pair-full and needs seed stability before promotion.",
            "next_action": "run multi-seed stability on the pair-full loss-rebalance route",
        }
    return {
        "model_quality_claim": "negative_tradeoff_evidence",
        "reason": "Loss-rebalance routes split into loss-only and fixed-only outcomes; no route keeps both terms.",
        "next_action": "stop this fixed-retention/loss-rebalance branch and inspect first-token preference or a new objective shape",
    }


__all__ = [
    "PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_CSV_FILENAME",
    "PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_HTML_FILENAME",
    "PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_JSON_FILENAME",
    "PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_FIXED_RETENTION_BATCH_CLOSEOUT_TEXT_FILENAME",
    "build_model_capability_required_term_pair_fixed_retention_batch_closeout",
    "locate_fixed_retention_comparison_report",
    "locate_fixed_retention_refresh_report",
    "locate_fixed_retention_route_decision_report",
    "read_json_report",
    "resolve_exit_code",
]
