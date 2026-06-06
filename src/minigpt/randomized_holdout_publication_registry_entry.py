from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_decision_index import RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_JSON_FILENAME
from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE,
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_ENTRY_ID,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_SOURCE_KINDS,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME = "randomized_holdout_publication_registry_entry.json"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CSV_FILENAME = "randomized_holdout_publication_registry_entry.csv"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_TEXT_FILENAME = "randomized_holdout_publication_registry_entry.txt"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_MARKDOWN_FILENAME = "randomized_holdout_publication_registry_entry.md"
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_HTML_FILENAME = "randomized_holdout_publication_registry_entry.html"

def locate_randomized_holdout_publication_decision_index(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_INDEX_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("randomized holdout publication registry entry input must be a JSON object")
    return dict(payload)


def build_randomized_holdout_publication_registry_entry(
    publication_decision_index: dict[str, Any],
    *,
    publication_decision_index_path: str | Path | None = None,
    entry_id: str = RANDOMIZED_HOLDOUT_PUBLICATION_ENTRY_ID,
    title: str = "MiniGPT randomized holdout publication registry entry",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(publication_decision_index.get("summary"))
    index = as_dict(publication_decision_index.get("index"))
    source_rows = list_of_dicts(publication_decision_index.get("source_rows"))
    checks = _checks(publication_decision_index, summary, index, source_rows, publication_decision_index_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    entry = _entry(status, entry_id, summary, index, source_rows, publication_decision_index_path)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "publication_decision_index_path": str(publication_decision_index_path or ""),
        "source_index_summary": summary,
        "source_index": index,
        "source_rows": source_rows,
        "check_rows": checks,
        "registry_entry": entry,
        "summary": _summary(status, checks, entry),
        "interpretation": _interpretation(status, entry),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_entry_ready: bool,
    require_bounded_publication: bool = False,
    require_promotion_ready: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_entry_ready and summary.get("randomized_holdout_publication_registry_entry_ready") is not True:
        return 1
    if require_bounded_publication and summary.get("bounded_publication_accepted") is not True:
        return 1
    if require_promotion_ready and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _checks(
    index_report: dict[str, Any],
    summary: dict[str, Any],
    index: dict[str, Any],
    source_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("source_index_file_exists", _path_exists(index_path), str(index_path or ""), "source publication decision index file must exist"),
        _check("source_index_passed", index_report.get("status") == "pass", index_report.get("status"), "source publication decision index must pass"),
        _check("source_index_decision_ready", index_report.get("decision") == "randomized_holdout_publication_decision_index_ready", index_report.get("decision"), "source publication decision index decision must be ready"),
        _check("source_index_summary_ready", summary.get("randomized_holdout_publication_decision_index_ready") is True and index.get("index_ready") is True, {"summary": summary.get("randomized_holdout_publication_decision_index_ready"), "index": index.get("index_ready")}, "source index summary and body must be ready"),
        _check("indexed_decision_expected", summary.get("indexed_decision") == "accept_bounded_randomized_holdout_publication", summary.get("indexed_decision"), "registry entry expects the bounded publication acceptance decision"),
        _check("bounded_publication_accepted", summary.get("bounded_publication_accepted") is True and index.get("bounded_publication_accepted") is True, {"summary": summary.get("bounded_publication_accepted"), "index": index.get("bounded_publication_accepted")}, "registry entry only accepts bounded publication-ready indexes"),
        _check("accepted_claim_count", int(summary.get("accepted_claim_count") or 0) == 1, summary.get("accepted_claim_count"), "registry entry expects exactly one accepted bounded claim"),
        _check("blocked_claim_count", int(summary.get("blocked_claim_count") or 0) >= 3, summary.get("blocked_claim_count"), "registry entry expects blocked claim boundaries"),
        _check("candidate_case_count", int(summary.get("candidate_case_count") or 0) >= 20, summary.get("candidate_case_count"), "registry entry expects the randomized 20-case floor"),
        _check("pass_rate_complete", float(summary.get("pass_rate") or 0.0) == 1.0, summary.get("pass_rate"), "registry entry expects complete randomized replay pass rate"),
        _check("allowed_use_bounded", summary.get("allowed_use") == RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE and index.get("allowed_use") == RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE, {"summary": summary.get("allowed_use"), "index": index.get("allowed_use")}, "allowed use must stay bounded governance only"),
        _check("model_quality_claim_bounded", summary.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM and index.get("model_quality_claim") == RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM, {"summary": summary.get("model_quality_claim"), "index": index.get("model_quality_claim")}, "model quality claim must stay bounded to randomized holdout"),
        _check("promotion_still_false", summary.get("promotion_ready") is False and index.get("promotion_ready") is False, {"summary": summary.get("promotion_ready"), "index": index.get("promotion_ready")}, "registry entry must not enable direct promotion"),
        _check("approved_for_promotion_false", summary.get("approved_for_promotion") is False and index.get("approved_for_promotion") is False, {"summary": summary.get("approved_for_promotion"), "index": index.get("approved_for_promotion")}, "direct promotion approval must remain false"),
        _check("source_count_expected", int(summary.get("source_count") or 0) == len(source_rows) == 3, {"summary": summary.get("source_count"), "rows": len(source_rows)}, "registry entry expects the three-source publication chain"),
        _check("source_kinds_expected", list(summary.get("source_kinds") or []) == RANDOMIZED_HOLDOUT_PUBLICATION_SOURCE_KINDS, summary.get("source_kinds"), "source kinds must keep publication decision, review, and packet order"),
        _check("source_checks_clean", int(summary.get("failed_check_count") or 0) == 0, summary.get("failed_check_count"), "source index checks must be clean"),
        _check("source_next_step_matches", summary.get("next_step") == "build_randomized_holdout_publication_registry_entry", summary.get("next_step"), "source index must route to registry entry build"),
    ]


def _path_exists(path: str | Path | None) -> bool:
    return bool(path) and Path(path).exists()


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _entry(
    status: str,
    entry_id: str,
    summary: dict[str, Any],
    index: dict[str, Any],
    source_rows: list[dict[str, Any]],
    index_path: str | Path | None,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "entry_ready": ready,
        "entry_id": entry_id if ready else "not_registered",
        "registry_status": "registered" if ready else "blocked",
        "entry_type": "bounded_model_capability_publication",
        "source_index_path": str(index_path or ""),
        "source_index_decision": summary.get("indexed_decision") or index.get("indexed_decision"),
        "bounded_publication_accepted": bool(ready and summary.get("bounded_publication_accepted") is True),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "accepted_claim_count": summary.get("accepted_claim_count"),
        "blocked_claim_count": summary.get("blocked_claim_count"),
        "candidate_case_count": summary.get("candidate_case_count"),
        "random_seed": summary.get("random_seed"),
        "pass_rate": summary.get("pass_rate"),
        "allowed_use": RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE if ready else "none",
        "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM if ready else "not_claimed",
        "decision_scope": summary.get("decision_scope") if ready else "not_claimed",
        "source_count": len(source_rows),
        "source_kinds": [str(row.get("kind")) for row in source_rows],
        "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
        "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_NEXT_STEP if ready else "repair_randomized_holdout_publication_decision_index",
    }


def _summary(status: str, checks: list[dict[str, Any]], entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "randomized_holdout_publication_registry_entry_ready": status == "pass" and entry.get("entry_ready") is True,
        "entry_id": entry.get("entry_id"),
        "registry_status": entry.get("registry_status"),
        "entry_type": entry.get("entry_type"),
        "bounded_publication_accepted": entry.get("bounded_publication_accepted"),
        "promotion_ready": False,
        "approved_for_promotion": False,
        "accepted_claim_count": entry.get("accepted_claim_count"),
        "blocked_claim_count": entry.get("blocked_claim_count"),
        "candidate_case_count": entry.get("candidate_case_count"),
        "random_seed": entry.get("random_seed"),
        "pass_rate": entry.get("pass_rate"),
        "allowed_use": entry.get("allowed_use"),
        "model_quality_claim": entry.get("model_quality_claim"),
        "decision_scope": entry.get("decision_scope"),
        "source_count": entry.get("source_count"),
        "source_kinds": entry.get("source_kinds"),
        "consumer_boundary": entry.get("consumer_boundary"),
        "next_step": entry.get("next_step"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "randomized_holdout_publication_registry_entry_ready"
    return "fix_randomized_holdout_publication_registry_entry"


def _interpretation(status: str, entry: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The randomized holdout publication index cannot be registered until bounded fields and source checks align.",
            "next_action": "repair randomized holdout publication decision index",
        }
    return {
        "model_quality_claim": entry.get("model_quality_claim"),
        "reason": "The bounded randomized holdout publication decision is registered for governance lookup while direct promotion remains blocked.",
        "next_action": entry.get("next_step"),
    }


__all__ = [
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CSV_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_HTML_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_JSON_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_MARKDOWN_FILENAME",
    "RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_TEXT_FILENAME",
    "build_randomized_holdout_publication_registry_entry",
    "locate_randomized_holdout_publication_decision_index",
    "read_json_report",
    "resolve_exit_code",
]
