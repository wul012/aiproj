from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_decision_index import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME,
    build_model_capability_route_promotion_decision_index,
    load_route_promotion_review_decision,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_JSON_FILENAME = "model_capability_route_promotion_decision_index_check.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_CSV_FILENAME = "model_capability_route_promotion_decision_index_check.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_TEXT_FILENAME = "model_capability_route_promotion_decision_index_check.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_MARKDOWN_FILENAME = "model_capability_route_promotion_decision_index_check.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_HTML_FILENAME = "model_capability_route_promotion_decision_index_check.html"


def locate_route_promotion_decision_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion decision index check input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_decision_index_check(
    decision_index: dict[str, Any],
    *,
    decision_index_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion decision index contract check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(decision_index.get("summary"))
    source_paths = [str(path) for path in summary.get("source_decision_paths") or _source_paths(decision_index) if str(path)]
    rebuilt = _rebuild_index(source_paths, summary)
    check_rows = _check_rows(decision_index, rebuilt, source_paths)
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
        "source_index": str(decision_index_path or ""),
        "source_decision_paths": source_paths,
        "source_index_summary": summary,
        "rebuilt_index_summary": as_dict(rebuilt.get("summary")),
        "check_rows": check_rows,
        "summary": _summary(status, check_rows, source_paths, decision_index, rebuilt),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _rebuild_index(source_paths: list[str], summary: dict[str, Any]) -> dict[str, Any]:
    if not source_paths:
        return {
            "status": "fail",
            "decision": "fix_model_capability_route_promotion_decision_index",
            "failed_count": 1,
            "summary": {"decision_index_ready": False, "source_decision_paths": [], "failed_check_count": 1},
            "entries": [],
        }
    return build_model_capability_route_promotion_decision_index(
        [load_route_promotion_review_decision(path) for path in source_paths],
        source_decision_paths=source_paths,
        min_ready_routes=int(summary.get("min_ready_routes") or 1),
        required_boundary=str(summary.get("required_boundary") or summary.get("boundary") or "tiny_required_term_pair_probe_only"),
    )


def _check_rows(original: dict[str, Any], rebuilt: dict[str, Any], source_paths: list[str]) -> list[dict[str, Any]]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    return [
        _check("source_paths_present", bool(source_paths), len(source_paths), "decision index must record source decision paths"),
        _compare("status", original.get("status"), rebuilt.get("status")),
        _compare("decision", original.get("decision"), rebuilt.get("decision")),
        _compare("failed_count", original.get("failed_count"), rebuilt.get("failed_count")),
        _compare("decision_index_ready", original_summary.get("decision_index_ready"), rebuilt_summary.get("decision_index_ready")),
        _compare("accepted_route_count", original_summary.get("accepted_route_count"), rebuilt_summary.get("accepted_route_count")),
        _compare("route_ids", original_summary.get("route_ids"), rebuilt_summary.get("route_ids")),
        _compare("boundary", original_summary.get("boundary"), rebuilt_summary.get("boundary")),
        _compare("model_quality_claim", original_summary.get("model_quality_claim"), rebuilt_summary.get("model_quality_claim")),
        _compare("entries", _entry_fingerprint(original), _entry_fingerprint(rebuilt)),
    ]


def _source_paths(decision_index: dict[str, Any]) -> list[str]:
    return [str(source.get("source_decision_path")) for source in list_of_dicts(decision_index.get("sources")) if source.get("source_decision_path")]


def _entry_fingerprint(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": row.get("route_id"),
            "entry_status": row.get("entry_status"),
            "review_scope": row.get("review_scope"),
            "boundary": row.get("boundary"),
            "model_quality_claim": row.get("model_quality_claim"),
        }
        for row in list_of_dicts(report.get("entries"))
    ]


def _compare(check_id: str, original: Any, rebuilt: Any) -> dict[str, Any]:
    return _check(check_id, original == rebuilt, {"source": original, "rebuilt": rebuilt}, f"{check_id} must match when rebuilt from source decisions")


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(
    status: str,
    check_rows: list[dict[str, Any]],
    source_paths: list[str],
    original: dict[str, Any],
    rebuilt: dict[str, Any],
) -> dict[str, Any]:
    original_summary = as_dict(original.get("summary"))
    rebuilt_summary = as_dict(rebuilt.get("summary"))
    return {
        "contract_check_ready": status == "pass",
        "source_decision_count": len(source_paths),
        "original_decision": original.get("decision"),
        "rebuilt_decision": rebuilt.get("decision"),
        "original_route_ids": original_summary.get("route_ids"),
        "rebuilt_route_ids": rebuilt_summary.get("route_ids"),
        "original_accepted_route_count": original_summary.get("accepted_route_count"),
        "rebuilt_accepted_route_count": rebuilt_summary.get("accepted_route_count"),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_decision_index_contract_check_passed"
    return "fix_model_capability_route_promotion_decision_index_contract"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CHECK_TEXT_FILENAME",
    "build_model_capability_route_promotion_decision_index_check",
    "locate_route_promotion_decision_index",
    "read_json_report",
    "resolve_exit_code",
]
