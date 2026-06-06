from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_acceptance_summary import (
    RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME,
    build_randomized_holdout_acceptance_summary,
    read_json_report as read_acceptance_input_json,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_JSON_FILENAME = "randomized_holdout_acceptance_summary_check.json"
RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_CSV_FILENAME = "randomized_holdout_acceptance_summary_check.csv"
RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_TEXT_FILENAME = "randomized_holdout_acceptance_summary_check.txt"
RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_MARKDOWN_FILENAME = "randomized_holdout_acceptance_summary_check.md"
RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_HTML_FILENAME = "randomized_holdout_acceptance_summary_check.html"

CHECKED_SUMMARY_FIELDS = (
    "randomized_holdout_acceptance_summary_ready",
    "bounded_promotion_accepted",
    "accepted_claim_count",
    "blocked_claim_count",
    "candidate_case_count",
    "random_seed",
    "pass_rate",
    "promotion_ready",
    "approved_for_promotion",
    "model_quality_claim",
    "allowed_use",
    "source_count",
    "next_step",
)


def locate_randomized_holdout_acceptance_summary(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout acceptance summary check input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_acceptance_summary_check(
    acceptance_summary: dict[str, Any],
    *,
    acceptance_summary_path: str | Path | None = None,
    title: str = "MiniGPT randomized holdout acceptance summary contract check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(acceptance_summary.get("summary"))
    source_index = _resolve_source_index(acceptance_summary.get("source_decision_index"), acceptance_summary_path)
    rebuilt = _rebuild_summary(source_index, acceptance_summary)
    check_rows = _check_rows(acceptance_summary, rebuilt, source_index)
    issues = [row for row in check_rows if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_acceptance_summary": str(acceptance_summary_path or ""),
        "source_decision_index": "" if source_index is None else str(source_index),
        "source_summary": summary,
        "rebuilt_summary": as_dict(rebuilt.get("summary")),
        "check_rows": check_rows,
        "summary": _summary(status, check_rows, acceptance_summary, rebuilt, source_index),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _resolve_source_index(value: Any, summary_path: str | Path | None) -> Path | None:
    text = str(value or "")
    if not text:
        return None
    direct = Path(text)
    if direct.is_file():
        return direct
    if summary_path:
        sibling = Path(summary_path).parent / text
        if sibling.is_file():
            return sibling
    return direct


def _rebuild_summary(source_index: Path | None, original: dict[str, Any]) -> dict[str, Any]:
    if source_index is None or not source_index.is_file():
        return {
            "status": "fail",
            "decision": "fix_randomized_holdout_acceptance_summary",
            "failed_count": 1,
            "summary": {
                "randomized_holdout_acceptance_summary_ready": False,
                "bounded_promotion_accepted": False,
                "promotion_ready": False,
                "failed_check_count": 1,
            },
            "accepted_claims": [],
            "blocked_claims": [],
            "source_rows": [],
        }
    return build_randomized_holdout_acceptance_summary(
        read_acceptance_input_json(source_index),
        decision_index_path=source_index,
        minimum_candidate_cases=int(as_dict(original.get("summary")).get("candidate_case_count") or 20),
    )


def _check_rows(original: dict[str, Any], rebuilt: dict[str, Any], source_index: Path | None) -> list[dict[str, Any]]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    rows = [
        _check("source_decision_index_present", source_index is not None, str(source_index or ""), "summary must record a source decision index"),
        _check("source_decision_index_exists", bool(source_index and source_index.is_file()), str(source_index or ""), "source decision index must exist"),
        _compare("status", original.get("status"), rebuilt.get("status")),
        _compare("decision", original.get("decision"), rebuilt.get("decision")),
        _compare("failed_count", original.get("failed_count"), rebuilt.get("failed_count")),
    ]
    rows.extend(_compare(field, original_summary.get(field), rebuilt_summary.get(field)) for field in CHECKED_SUMMARY_FIELDS)
    rows.extend(
        [
            _compare("accepted_claims", _claim_fingerprint(original.get("accepted_claims")), _claim_fingerprint(rebuilt.get("accepted_claims"))),
            _compare("blocked_claims", _blocked_fingerprint(original.get("blocked_claims")), _blocked_fingerprint(rebuilt.get("blocked_claims"))),
            _compare("source_rows", _source_fingerprint(original.get("source_rows")), _source_fingerprint(rebuilt.get("source_rows"))),
        ]
    )
    return rows


def _claim_fingerprint(rows: Any) -> list[dict[str, Any]]:
    return [
        {
            "claim_id": row.get("claim_id"),
            "status": row.get("status"),
            "scope": row.get("scope"),
            "model_quality_claim": row.get("model_quality_claim"),
            "allowed_use": row.get("allowed_use"),
        }
        for row in list_of_dicts(rows)
    ]


def _blocked_fingerprint(rows: Any) -> list[dict[str, Any]]:
    return [{"claim_id": row.get("claim_id"), "status": row.get("status"), "reason": row.get("reason")} for row in list_of_dicts(rows)]


def _source_fingerprint(rows: Any) -> list[dict[str, Any]]:
    return [
        {
            "kind": row.get("kind"),
            "status": row.get("status"),
            "decision": row.get("decision"),
            "ready_key": row.get("ready_key"),
            "ready_value": row.get("ready_value"),
            "promotion_ready": row.get("promotion_ready"),
            "model_quality_claim": row.get("model_quality_claim"),
        }
        for row in list_of_dicts(rows)
    ]


def _compare(check_id: str, original: Any, rebuilt: Any) -> dict[str, Any]:
    return _check(check_id, original == rebuilt, {"source": original, "rebuilt": rebuilt}, f"{check_id} must match the rebuilt acceptance summary")


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(
    status: str,
    check_rows: list[dict[str, Any]],
    original: dict[str, Any],
    rebuilt: dict[str, Any],
    source_index: Path | None,
) -> dict[str, Any]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    return {
        "contract_check_ready": status == "pass",
        "source_decision_index": "" if source_index is None else str(source_index),
        "original_decision": original.get("decision"),
        "rebuilt_decision": rebuilt.get("decision"),
        "original_bounded_promotion_accepted": original_summary.get("bounded_promotion_accepted"),
        "rebuilt_bounded_promotion_accepted": rebuilt_summary.get("bounded_promotion_accepted"),
        "original_accepted_claim_count": original_summary.get("accepted_claim_count"),
        "rebuilt_accepted_claim_count": rebuilt_summary.get("accepted_claim_count"),
        "original_blocked_claim_count": original_summary.get("blocked_claim_count"),
        "rebuilt_blocked_claim_count": rebuilt_summary.get("blocked_claim_count"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_acceptance_summary_contract_check_passed"
    return "fix_randomized_holdout_acceptance_summary_contract"


__all__ = [
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_TEXT_FILENAME",
    "build_randomized_holdout_acceptance_summary_check",
    "locate_randomized_holdout_acceptance_summary",
    "read_json_report",
    "resolve_exit_code",
]
