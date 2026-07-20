from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_coexistence_refresh import (
    PAIR_COEXISTENCE_REFRESH_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_JSON_FILENAME = "model_capability_required_term_pair_minimal_prompt_batch_closeout.json"
PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_CSV_FILENAME = "model_capability_required_term_pair_minimal_prompt_batch_closeout.csv"
PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_TEXT_FILENAME = "model_capability_required_term_pair_minimal_prompt_batch_closeout.txt"
PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_MARKDOWN_FILENAME = "model_capability_required_term_pair_minimal_prompt_batch_closeout.md"
PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_HTML_FILENAME = "model_capability_required_term_pair_minimal_prompt_batch_closeout.html"


def locate_minimal_prompt_batch_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("minimal prompt batch closeout input must be a JSON object")
    return dict(payload)


def build_minimal_prompt_batch_closeout(
    reports: list[dict[str, Any]],
    *,
    labels: list[str] | None = None,
    paths: list[str | Path] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not reports:
        raise ValueError("at least one minimal prompt training report is required")
    resolved_labels = _labels(reports, labels)
    resolved_paths = [str(path) for path in paths] if paths else [""] * len(reports)
    rows = [_evidence_row(report, resolved_labels[index], resolved_paths[index]) for index, report in enumerate(reports)]
    summary = _summary(rows)
    issues = _issues(rows, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair minimal prompt batch closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_report_count": len(reports),
        "summary": summary,
        "evidence_rows": rows,
        "interpretation": _interpretation(status, summary),
    }


def _labels(reports: list[dict[str, Any]], labels: list[str] | None) -> list[str]:
    if labels is not None and len(labels) != len(reports):
        raise ValueError("labels length must match reports length")
    return labels or [f"minimal-prompt-run-{index + 1}" for index in range(len(reports))]


def _evidence_row(report: dict[str, Any], label: str, path: str) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    settings = as_dict(report.get("settings"))
    replay = as_dict(report.get("replay_report"))
    variant_rows = list_of_dicts(replay.get("variant_rows"))
    hit_terms = sorted({str(term) for row in variant_rows for term in row.get("hit_terms", [])})
    case_rows = list_of_dicts(replay.get("case_rows"))
    return {
        "label": label,
        "path": path,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "corpus_mode": settings.get("corpus_mode", ""),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": bool(summary.get("checkpoint_exists")),
        "pair_full_observed": bool(summary.get("pair_full_observed")),
        "hit_terms": hit_terms,
        "branch_class": _branch_class(hit_terms, bool(summary.get("pair_full_observed"))),
        "fixed_generated": _generated_for_term(case_rows, "fixed"),
        "loss_generated": _generated_for_term(case_rows, "loss"),
        "model_quality_claim": as_dict(report.get("interpretation")).get("model_quality_claim", ""),
    }


def _branch_class(hit_terms: list[str], pair_full: bool) -> str:
    terms = set(hit_terms)
    if pair_full or {"fixed", "loss"}.issubset(terms):
        return "pair-full"
    if terms == {"fixed"}:
        return "fixed-only"
    if terms == {"loss"}:
        return "loss-only"
    if not terms:
        return "all-miss"
    return "partial-other"


def _generated_for_term(case_rows: list[dict[str, Any]], term: str) -> str:
    for row in case_rows:
        if row.get("term") == term and row.get("profile_id") == "default":
            return str(row.get("generated_preview") or row.get("generated") or "").strip()
    for row in case_rows:
        if row.get("term") == term:
            return str(row.get("generated_preview") or row.get("generated") or "").strip()
    return ""


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classes = [str(row.get("branch_class")) for row in rows]
    return {
        "report_count": len(rows),
        "pass_count": sum(1 for row in rows if row.get("status") == "pass"),
        "checkpoint_count": sum(1 for row in rows if row.get("checkpoint_exists") is True),
        "pair_full_report_count": classes.count("pair-full"),
        "fixed_only_report_count": classes.count("fixed-only"),
        "loss_only_report_count": classes.count("loss-only"),
        "all_miss_report_count": classes.count("all-miss"),
        "partial_other_report_count": classes.count("partial-other"),
        "corpus_modes": sorted({str(row.get("corpus_mode")) for row in rows if row.get("corpus_mode")}),
        "branch_classes": classes,
        "closeout_ready": len(rows) >= 3 and classes.count("pair-full") == 0 and all(row.get("status") == "pass" for row in rows),
    }


def _issues(rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if int(summary.get("report_count") or 0) < 3:
        issues.append({"id": "too_few_reports", "detail": "minimal prompt closeout requires at least three real training reports"})
    for row in rows:
        if row.get("status") != "pass":
            issues.append({"id": "source_report_not_pass", "label": row.get("label"), "detail": "source report must pass"})
        if row.get("checkpoint_exists") is not True:
            issues.append({"id": "checkpoint_missing", "label": row.get("label"), "detail": "source report must contain a checkpoint"})
    if int(summary.get("pair_full_report_count") or 0) > 0:
        issues.append({"id": "pair_full_candidate_exists", "detail": "do not close out a batch that already has a pair-full candidate"})
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status == "pass" and summary.get("closeout_ready") is True:
        return "minimal_prompt_batch_closed_without_pair_full"
    if int(summary.get("pair_full_report_count") or 0) > 0:
        return "minimal_prompt_pair_full_candidate_found"
    return "fix_minimal_prompt_batch_closeout_inputs"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The minimal-prompt batch cannot be closed until source reports are complete and pair-full status is resolved.",
            "next_action": "repair closeout inputs before changing training direction",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "Three real minimal-prompt training attempts completed, but none produced full fixed/loss continuation coverage.",
        "next_action": "stop same-family minimal-prompt corpus churn and design a pair-readiness split before more training",
        "summary": summary,
    }


__all__ = [
    "PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_CSV_FILENAME",
    "PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_HTML_FILENAME",
    "PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_JSON_FILENAME",
    "PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_TEXT_FILENAME",
    "build_minimal_prompt_batch_closeout",
    "locate_minimal_prompt_batch_report",
    "read_json_report",
    "resolve_exit_code",
]
