from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_colon_immediate_stability import (
    PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_first_token_preference import (
    ScoreFunc,
    build_model_capability_required_term_pair_first_token_preference,
    resolve_exit_code as _first_token_exit_code,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_JSON_FILENAME = (
    "model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.json"
)
PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_CSV_FILENAME = (
    "model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.csv"
)
PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_TEXT_FILENAME = (
    "model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.txt"
)
PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.md"
)
PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_HTML_FILENAME = (
    "model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.html"
)


def locate_pair_colon_immediate_stability(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("colon-immediate stability report must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    top_k: int = 8,
    device: str = "cpu",
    generated_at: str | None = None,
    score_func: ScoreFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    seed_rows = list_of_dicts(stability_report.get("seed_rows"))
    seed_reports = _seed_reports_by_seed(stability_report)
    issues = _input_issues(stability_report, seed_rows, seed_reports)
    diagnostic_rows: list[dict[str, Any]] = []
    first_token_reports: list[dict[str, Any]] = []

    if not issues:
        for seed_row in seed_rows:
            seed = int(seed_row.get("seed") or 0)
            refresh_report = seed_reports.get(seed)
            if refresh_report is None:
                issues.append(f"missing seed report for seed {seed}")
                diagnostic_rows.append(_missing_seed_row(seed_row))
                continue
            first_token_report = build_model_capability_required_term_pair_first_token_preference(
                refresh_report,
                out_dir=root / "first-token-runs" / f"seed-{seed}",
                source_path=refresh_report.get("out_dir") or seed_row.get("out_dir"),
                top_k=top_k,
                device=device,
                generated_at=generated_at,
                score_func=score_func,
            )
            first_token_reports.append({"seed": seed, "report": first_token_report})
            diagnostic_rows.append(_diagnostic_row(seed_row, first_token_report))
            if first_token_report.get("status") != "pass":
                issues.append(f"first-token diagnostic failed for seed {seed}")

    summary = _summary(diagnostic_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair colon-immediate missed-seed diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_pair_colon_immediate_stability": "" if source_path is None else str(source_path),
        "out_dir": str(root),
        "settings": {
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "diagnose v536 missed seeds with first-token logits without retraining",
        },
        "seed_rows": diagnostic_rows,
        "first_token_reports": first_token_reports,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    for entry in list_of_dicts(report.get("first_token_reports")):
        child = as_dict(entry.get("report"))
        if child and _first_token_exit_code(child, require_pass=require_pass):
            return 1
    return 0


def _seed_reports_by_seed(stability_report: dict[str, Any]) -> dict[int, dict[str, Any]]:
    reports: dict[int, dict[str, Any]] = {}
    for report in list_of_dicts(stability_report.get("seed_reports")):
        seed = as_dict(report.get("settings")).get("seed")
        if seed is not None:
            reports[int(seed)] = report
    return reports


def _input_issues(
    stability_report: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    seed_reports: dict[int, dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if stability_report.get("status") != "pass":
        issues.append("stability report status is not pass")
    if not seed_rows:
        issues.append("stability report has no seed_rows")
    if not seed_reports:
        issues.append("stability report has no embedded seed_reports")
    return issues


def _missing_seed_row(seed_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": seed_row.get("seed"),
        "status": "fail",
        "pair_full_observed": bool(seed_row.get("pair_full_observed")),
        "refresh_decision": seed_row.get("decision"),
        "first_token_decision": "missing_seed_report",
        "expected_top_count": 0,
        "term_count": 0,
        "expected_all_top": False,
        "max_expected_rank": 0,
        "fixed_expected_rank": None,
        "loss_expected_rank": None,
        "fixed_top_token": "",
        "loss_top_token": "",
        "observed_continuation_hit_count": seed_row.get("continuation_hit_count"),
    }


def _diagnostic_row(seed_row: dict[str, Any], first_token_report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(first_token_report.get("summary"))
    rows = list_of_dicts(first_token_report.get("rows"))
    return {
        "seed": seed_row.get("seed"),
        "status": first_token_report.get("status"),
        "pair_full_observed": bool(seed_row.get("pair_full_observed")),
        "refresh_decision": seed_row.get("decision"),
        "first_token_decision": first_token_report.get("decision"),
        "expected_top_count": summary.get("expected_top_count"),
        "term_count": summary.get("term_count"),
        "expected_all_top": bool(summary.get("expected_all_top")),
        "max_expected_rank": summary.get("max_expected_rank"),
        "fixed_expected_rank": _term_field(rows, "fixed", "expected_rank"),
        "loss_expected_rank": _term_field(rows, "loss", "expected_rank"),
        "fixed_top_token": _term_field(rows, "fixed", "top_token_text"),
        "loss_top_token": _term_field(rows, "loss", "top_token_text"),
        "observed_continuation_hit_count": seed_row.get("continuation_hit_count"),
    }


def _term_field(rows: list[dict[str, Any]], term: str, field: str) -> Any:
    for row in rows:
        if row.get("term") == term:
            return row.get(field)
    return None


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(rows)
    pair_full_rows = [row for row in rows if row.get("pair_full_observed")]
    missed_rows = [row for row in rows if not row.get("pair_full_observed")]
    missed_expected_top_rows = [row for row in missed_rows if row.get("expected_all_top")]
    missed_first_token_gap_rows = [row for row in missed_rows if row.get("status") == "pass" and not row.get("expected_all_top")]
    return {
        "seed_count": seed_count,
        "pair_full_seed_count": len(pair_full_rows),
        "missed_seed_count": len(missed_rows),
        "missed_expected_top_count": len(missed_expected_top_rows),
        "missed_first_token_gap_count": len(missed_first_token_gap_rows),
        "pair_full_expected_top_count": sum(1 for row in pair_full_rows if row.get("expected_all_top")),
        "all_missed_expected_top": bool(missed_rows) and len(missed_expected_top_rows) == len(missed_rows),
        "any_missed_first_token_gap": bool(missed_first_token_gap_rows),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_colon_immediate_missed_seed_diagnostic"
    if not summary.get("missed_seed_count"):
        return "required_term_pair_colon_immediate_no_missed_seed"
    if summary.get("all_missed_expected_top"):
        return "required_term_pair_colon_immediate_missed_after_top_token"
    if summary.get("any_missed_first_token_gap"):
        return "required_term_pair_colon_immediate_first_token_gap"
    return "required_term_pair_colon_immediate_missed_seed_mixed_signal"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The missed-seed diagnostic could not score every seed."
        next_action = "repair diagnostic inputs before changing corpus or model size"
    elif not summary.get("missed_seed_count"):
        reason = "No missed seeds remain in the stability report."
        next_action = "promote the colon-immediate objective to the next held-out check"
    elif summary.get("all_missed_expected_top"):
        reason = "Missed seeds still rank the expected first tokens on top, so the gap is later continuation dynamics."
        next_action = "inspect second-token and continuation span before adding more corpus variants"
    elif summary.get("any_missed_first_token_gap"):
        reason = "At least one missed seed does not rank all expected first tokens on top."
        next_action = "strengthen first-token preference before extending continuation training"
    else:
        reason = "Missed seeds have mixed first-token evidence."
        next_action = "separate first-token and continuation diagnostics by seed"
    return {
        "model_quality_claim": "targeted_pair_refresh_missed_seed_diagnostic_only" if status == "pass" else "not_claimed",
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic",
    "locate_pair_colon_immediate_stability",
    "read_json_report",
    "resolve_exit_code",
]
