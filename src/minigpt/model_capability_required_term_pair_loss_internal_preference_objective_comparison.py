from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import TARGET_TERMS
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_objective_comparison.json"
)
PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_CSV_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_objective_comparison.csv"
)
PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_objective_comparison.txt"
)
PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_objective_comparison.md"
)
PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_internal_preference_objective_comparison.html"
)


def locate_loss_internal_preference_objective_refresh_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def read_loss_internal_preference_objective_refresh_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("loss-internal-preference objective comparison input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_loss_internal_preference_objective_comparison(
    reports: Sequence[dict[str, Any]],
    *,
    source_paths: Sequence[str | Path] | None = None,
    source_labels: Sequence[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    paths = [str(path) for path in source_paths] if source_paths else []
    labels = [str(label) for label in source_labels] if source_labels else []
    report_rows = [
        _report_row(index, report, _source_path(paths, index), _source_label(labels, index, report, paths))
        for index, report in enumerate(reports)
    ]
    term_rows = [term for index, report in enumerate(reports) for term in _term_rows(report_rows[index], report)]
    branch_rows = [_branch_row(row, term_rows) for row in report_rows]
    issues = _issues(report_rows, term_rows)
    summary = _summary(report_rows, branch_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair loss-internal-preference objective comparison",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_reports": report_rows,
        "term_rows": term_rows,
        "branch_rows": branch_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _source_path(paths: Sequence[str], index: int) -> str:
    return paths[index] if index < len(paths) else ""


def _source_label(labels: Sequence[str], index: int, report: dict[str, Any], paths: Sequence[str]) -> str:
    if index < len(labels) and labels[index]:
        return labels[index]
    mode = str(as_dict(report.get("settings")).get("corpus_mode") or "")
    if "first_token" in mode:
        return "loss-internal-first-token"
    if "ranked_choice" in mode:
        return "loss-internal-ranked-choice"
    if "preference" in mode:
        return "loss-internal-preference"
    if index < len(paths) and paths[index]:
        return Path(paths[index]).parent.name
    return f"loss-internal-report-{index + 1}"


def _report_row(index: int, report: dict[str, Any], source_path: str, label: str) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    settings = as_dict(report.get("settings"))
    return {
        "index": index,
        "source_label": label,
        "source_path": source_path,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "corpus_mode": settings.get("corpus_mode"),
        "seed": settings.get("seed"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": bool(summary.get("checkpoint_exists")),
        "pair_full_observed": bool(summary.get("pair_full_observed")),
        "default_pair_full_variant_count": int(summary.get("default_pair_full_variant_count") or 0),
        "suppression_pair_full_variant_count": int(summary.get("suppression_pair_full_variant_count") or 0),
    }


def _term_rows(report_row: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
    replay = as_dict(report.get("replay_report"))
    rows: list[dict[str, Any]] = []
    for case in list_of_dicts(replay.get("case_rows")):
        term = str(case.get("term") or "")
        if term not in TARGET_TERMS:
            continue
        rows.append(
            {
                "source_label": report_row.get("source_label"),
                "source_path": report_row.get("source_path"),
                "corpus_mode": report_row.get("corpus_mode"),
                "seed": report_row.get("seed"),
                "profile_id": case.get("profile_id"),
                "term": term,
                "prompt": case.get("prompt"),
                "continuation_hit": bool(case.get("continuation_hit")),
                "continuation_preview": case.get("continuation_preview"),
            }
        )
    return rows


def _branch_row(report_row: dict[str, Any], term_rows: list[dict[str, Any]]) -> dict[str, Any]:
    label = str(report_row.get("source_label") or "")
    scoped = [row for row in term_rows if str(row.get("source_label") or "") == label and row.get("continuation_hit")]
    hit_terms = sorted({str(row.get("term")) for row in scoped})
    pair_full_profiles = _pair_full_profiles(scoped)
    return {
        "source_label": label,
        "corpus_mode": report_row.get("corpus_mode"),
        "seed": report_row.get("seed"),
        "hit_terms": hit_terms,
        "missed_terms": [term for term in TARGET_TERMS if term not in hit_terms],
        "hit_term_count": len(hit_terms),
        "pair_full_profiles": pair_full_profiles,
        "fixed_only_tradeoff": hit_terms == ["fixed"],
        "loss_only_tradeoff": hit_terms == ["loss"],
        "pair_full_observed": bool(pair_full_profiles),
    }


def _pair_full_profiles(rows: list[dict[str, Any]]) -> list[str]:
    grouped: dict[str, set[str]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("profile_id") or ""), set()).add(str(row.get("term") or ""))
    return sorted(profile for profile, terms in grouped.items() if set(TARGET_TERMS).issubset(terms))


def _issues(report_rows: list[dict[str, Any]], term_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(report_rows) < 2:
        issues.append("at least two loss-internal-preference objective reports are required")
    for row in report_rows:
        label = row.get("source_label")
        if row.get("status") != "pass":
            issues.append(f"{label} report status is not pass")
        if row.get("training_status") != "pass":
            issues.append(f"{label} training status is not pass")
        if "loss_internal" not in str(row.get("corpus_mode") or ""):
            issues.append(f"{label} is not a loss-internal-preference objective corpus mode")
    if not term_rows:
        issues.append("no fixed/loss term rows found")
    return issues


def _summary(report_rows: list[dict[str, Any]], branch_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pair_full_count = sum(1 for row in branch_rows if row.get("pair_full_observed"))
    fixed_only_count = sum(1 for row in branch_rows if row.get("fixed_only_tradeoff"))
    loss_only_count = sum(1 for row in branch_rows if row.get("loss_only_tradeoff"))
    union_terms = sorted({term for row in branch_rows for term in row.get("hit_terms", [])})
    return {
        "compared_report_count": len(report_rows),
        "pair_full_report_count": pair_full_count,
        "fixed_only_tradeoff_report_count": fixed_only_count,
        "loss_only_tradeoff_report_count": loss_only_count,
        "fixed_hit_report_count": sum(1 for row in branch_rows if "fixed" in row.get("hit_terms", [])),
        "loss_hit_report_count": sum(1 for row in branch_rows if "loss" in row.get("hit_terms", [])),
        "union_hit_terms": union_terms,
        "mixed_tradeoff_observed": fixed_only_count > 0 and loss_only_count > 0 and pair_full_count == 0,
        "best_hit_term_count": max([int(row.get("hit_term_count") or 0) for row in branch_rows] or [0]),
        "best_routes": _best_routes(branch_rows),
        "loss_recovery_route": _first_route(branch_rows, "loss_only_tradeoff"),
        "fixed_recovery_routes": [str(row.get("source_label") or "") for row in branch_rows if row.get("fixed_only_tradeoff")],
    }


def _best_routes(branch_rows: list[dict[str, Any]]) -> list[str]:
    best = max([int(row.get("hit_term_count") or 0) for row in branch_rows] or [0])
    return [str(row.get("source_label") or "") for row in branch_rows if int(row.get("hit_term_count") or 0) == best]


def _first_route(branch_rows: list[dict[str, Any]], key: str) -> str:
    for row in branch_rows:
        if row.get(key):
            return str(row.get("source_label") or "")
    return ""


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_internal_preference_comparison_inputs"
    if int(summary.get("pair_full_report_count") or 0) > 0:
        return "promote_loss_internal_preference_pair_full_candidate"
    if summary.get("mixed_tradeoff_observed"):
        return "loss_internal_preference_objectives_confirm_branch_tradeoff"
    if int(summary.get("loss_only_tradeoff_report_count") or 0) > 0:
        return "select_loss_internal_preference_loss_recovery_route"
    return "loss_internal_preference_objectives_still_fixed_biased"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The loss-internal-preference objective reports are not structurally comparable.",
            "next_action": "repair comparison inputs before route decision",
        }
    if int(summary.get("pair_full_report_count") or 0) > 0:
        return {
            "model_quality_claim": "pair_full_candidate",
            "reason": "At least one loss-internal-preference objective reached pair-full.",
            "next_action": "run seed stability and forced-choice diagnostics before promotion",
        }
    if summary.get("mixed_tradeoff_observed"):
        return {
            "model_quality_claim": "tradeoff_only",
            "reason": "The routes recover different branches but no route keeps both at once.",
            "next_action": "run forced-choice diagnostics to separate generation failure from internal preference",
        }
    return {
        "model_quality_claim": "comparison_only",
        "reason": "The compared routes do not yet recover the full fixed/loss pair.",
        "next_action": "inspect internal preference before another objective",
    }


__all__ = [
    "PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_CSV_FILENAME",
    "PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_HTML_FILENAME",
    "PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_JSON_FILENAME",
    "PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_COMPARISON_TEXT_FILENAME",
    "build_model_capability_required_term_pair_loss_internal_preference_objective_comparison",
    "locate_loss_internal_preference_objective_refresh_report",
    "read_loss_internal_preference_objective_refresh_report",
    "resolve_exit_code",
]
