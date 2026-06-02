from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.json"
)
PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.csv"
)
PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.txt"
)
PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.md"
)
PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.html"
)


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair prompt transfer regression diagnostic input must be a JSON object")
    return dict(payload)


def build_pair_prompt_transfer_regression_diagnostic(
    *,
    direct_completion_training_report: dict[str, Any],
    pair_probe_replay_report: dict[str, Any],
    transfer_training_report: dict[str, Any],
    direct_completion_path: str | Path | None = None,
    pair_probe_path: str | Path | None = None,
    transfer_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [
        _training_row("direct-completion-surface", direct_completion_training_report, direct_completion_path),
        _pair_probe_row("direct-completion-pair-probe", pair_probe_replay_report, pair_probe_path),
        _training_row("pair-prompt-transfer", transfer_training_report, transfer_path),
    ]
    issues = _issues(rows)
    status = "pass" if not issues else "fail"
    summary = _summary(rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair prompt transfer regression diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "diagnostic_rows": rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _training_row(label: str, report: dict[str, Any], path: str | Path | None) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    default = _default_variant(report)
    hit_terms = [str(term) for term in default.get("hit_terms", [])]
    missed_terms = [str(term) for term in default.get("missed_terms", [])]
    hit_count = int(default.get("hit_count") or summary.get("default_continuation_hit_count") or 0)
    pair_full = bool(default.get("pair_full_hit") or summary.get("pair_full_observed"))
    return {
        "label": label,
        "kind": "training",
        "path": str(path or ""),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "checkpoint_exists": bool(summary.get("checkpoint_exists")),
        "training_status": summary.get("training_status"),
        "default_hit_terms": hit_terms,
        "default_missed_terms": missed_terms,
        "default_hit_count": hit_count,
        "pair_full_observed": pair_full,
    }


def _pair_probe_row(label: str, report: dict[str, Any], path: str | Path | None) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    return {
        "label": label,
        "kind": "pair_probe_replay",
        "path": str(path or ""),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "checkpoint_exists": True,
        "training_status": "n/a",
        "default_hit_terms": [],
        "default_missed_terms": [],
        "default_hit_count": int(summary.get("required_pair_full_count") or 0),
        "pair_full_observed": bool(summary.get("exact_heldout_pair_full")),
        "required_pair_full_count": int(summary.get("required_pair_full_count") or 0),
        "required_all_pair_full": bool(summary.get("required_all_pair_full")),
        "exact_heldout_pair_full": bool(summary.get("exact_heldout_pair_full")),
    }


def _default_variant(report: dict[str, Any]) -> dict[str, Any]:
    replay = as_dict(report.get("replay_report"))
    for row in list_of_dicts(replay.get("variant_rows")):
        if row.get("profile_id") == "default":
            return row
    return {}


def _issues(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        label = str(row.get("label"))
        if row.get("status") != "pass":
            issues.append({"id": f"{label}_status_not_pass", "detail": row.get("status")})
        if row.get("kind") == "training" and not row.get("checkpoint_exists"):
            issues.append({"id": f"{label}_checkpoint_missing", "detail": row.get("path")})
    return issues


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    direct = _row_by_label(rows, "direct-completion-surface")
    pair_probe = _row_by_label(rows, "direct-completion-pair-probe")
    transfer = _row_by_label(rows, "pair-prompt-transfer")
    direct_hits = int(direct.get("default_hit_count") or 0)
    transfer_hits = int(transfer.get("default_hit_count") or 0)
    direct_hit_terms = set(str(term) for term in direct.get("default_hit_terms", []))
    transfer_hit_terms = set(str(term) for term in transfer.get("default_hit_terms", []))
    fixed_regressed = "fixed" in direct_hit_terms and "fixed" not in transfer_hit_terms
    loss_regressed = "loss" in direct_hit_terms and "loss" not in transfer_hit_terms
    return {
        "direct_completion_default_hit_count": direct_hits,
        "transfer_default_hit_count": transfer_hits,
        "transfer_hit_delta_from_direct": transfer_hits - direct_hits,
        "direct_completion_pair_full_observed": bool(direct.get("pair_full_observed")),
        "transfer_pair_full_observed": bool(transfer.get("pair_full_observed")),
        "pair_probe_exact_heldout_pair_full": bool(pair_probe.get("exact_heldout_pair_full")),
        "fixed_regressed": fixed_regressed,
        "loss_regressed": loss_regressed,
        "direct_completion_regressed": transfer_hits < direct_hits or fixed_regressed or loss_regressed,
        "transfer_route_closed": transfer_hits < direct_hits and not transfer.get("pair_full_observed"),
        "closed_route": "pair_prompt_transfer_full_surrogate_patch",
    }


def _row_by_label(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    for row in rows:
        if row.get("label") == label:
            return row
    return {}


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_prompt_transfer_regression_diagnostic_inputs"
    if summary.get("transfer_pair_full_observed"):
        return "pair_readiness_pair_prompt_transfer_candidate_found"
    if summary.get("direct_completion_regressed"):
        return "pair_readiness_pair_prompt_transfer_regressed_stop_route"
    return "pair_readiness_pair_prompt_transfer_needs_review"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "One or more diagnostic inputs are missing or invalid.",
            "next_action": "repair training or replay inputs before judging the transfer route",
        }
    if summary.get("transfer_pair_full_observed"):
        return {
            "model_quality_claim": "comparison_pair_full_candidate",
            "reason": "The pair prompt transfer route preserved or improved direct heldout pair-full behavior.",
            "next_action": "run stricter pair-probe replay and multi-seed stability before promotion",
        }
    if summary.get("direct_completion_regressed"):
        return {
            "model_quality_claim": "negative_route_diagnostic",
            "reason": "The transfer route regressed from direct pair-full to a weaker heldout direct result while pair-probe replay was still not ready.",
            "next_action": "stop the full surrogate transfer patch route and diagnose a lighter fixed-preserving transfer objective",
        }
    return {
        "model_quality_claim": "comparison_only",
        "reason": "The transfer route did not regress but also did not provide pair-full evidence.",
        "next_action": "review failure surfaces before changing corpus rows",
    }


__all__ = [
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_TEXT_FILENAME",
    "build_pair_prompt_transfer_regression_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
