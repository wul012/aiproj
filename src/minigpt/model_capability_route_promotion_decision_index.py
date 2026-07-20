from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_review_decision import MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, number_or_default, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME = "model_capability_route_promotion_decision_index.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CSV_FILENAME = "model_capability_route_promotion_decision_index.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_TEXT_FILENAME = "model_capability_route_promotion_decision_index.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_MARKDOWN_FILENAME = "model_capability_route_promotion_decision_index.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_HTML_FILENAME = "model_capability_route_promotion_decision_index.html"


def locate_route_promotion_review_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_REVIEW_DECISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion decision index input must be a JSON object")
    return dict(payload)


def load_route_promotion_review_decision(path: str | Path) -> dict[str, Any]:
    resolved = locate_route_promotion_review_decision(path)
    report = read_json_report(resolved)
    report["_source_path"] = str(resolved)
    return report


def build_model_capability_route_promotion_decision_index(
    decision_reports: list[dict[str, Any]],
    *,
    source_decision_paths: list[str | Path] | None = None,
    min_ready_routes: int = 1,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion decision index",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not decision_reports:
        raise ValueError("at least one route promotion review decision is required")
    if source_decision_paths is not None and len(source_decision_paths) != len(decision_reports):
        raise ValueError("source_decision_paths length must match decision_reports length")
    sources = [
        _source(decision, _source_path(decision, source_decision_paths, index), index, required_boundary)
        for index, decision in enumerate(decision_reports)
    ]
    entries = [entry for source in sources for entry in source["route_entries"]]
    checks = _checks(sources, entries, min_ready_routes, required_boundary)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "check_rows": checks,
        "sources": sources,
        "entries": entries,
        "summary": _summary(status, sources, entries, checks, required_boundary, min_ready_routes),
        "recommendations": _recommendations(status, entries),
    }


def resolve_exit_code(report: dict[str, Any], *, require_ready_index: bool) -> int:
    return 1 if require_ready_index and report.get("status") != "pass" else 0


def _source(decision_report: dict[str, Any], source_path: str, index: int, required_boundary: str) -> dict[str, Any]:
    summary = as_dict(decision_report.get("summary"))
    final_decision = as_dict(decision_report.get("final_decision"))
    route_ids = [str(item) for item in final_decision.get("active_routes") or summary.get("active_routes") or [] if str(item)]
    check_rows = list_of_dicts(decision_report.get("check_rows"))
    source_checks_failed = [row for row in check_rows if row.get("status") != "pass"]
    accepted = (
        decision_report.get("status") == "pass"
        and decision_report.get("decision") == "model_capability_route_promotion_final_review_accepted"
        and final_decision.get("accepted") is True
        and final_decision.get("decision") == "accept_bounded_route_promotion"
        and final_decision.get("review_scope") == "bounded_route_promotion_review_only"
        and final_decision.get("boundary") == required_boundary
        and not source_checks_failed
    )
    return {
        "index": index,
        "source_decision_path": source_path,
        "source_status": decision_report.get("status"),
        "source_decision": decision_report.get("decision"),
        "source_failed_count": number_or_default(decision_report.get("failed_count"), 0, int),
        "final_decision": final_decision.get("decision"),
        "accepted": accepted,
        "review_scope": final_decision.get("review_scope"),
        "boundary": final_decision.get("boundary"),
        "model_quality_claim": final_decision.get("model_quality_claim") if accepted else "not_claimed",
        "active_route_count": len(route_ids),
        "source_check_failed_count": len(source_checks_failed),
        "route_entries": [_entry(route_id, source_path, index, final_decision, accepted) for route_id in route_ids],
    }


def _entry(route_id: str, source_path: str, source_index: int, final_decision: dict[str, Any], accepted: bool) -> dict[str, Any]:
    return {
        "route_id": route_id,
        "entry_status": "accepted" if accepted else "blocked",
        "source_index": source_index,
        "source_decision_path": source_path,
        "review_scope": final_decision.get("review_scope"),
        "boundary": final_decision.get("boundary"),
        "model_quality_claim": final_decision.get("model_quality_claim") if accepted else "not_claimed",
        "next_step": final_decision.get("next_step"),
    }


def _checks(sources: list[dict[str, Any]], entries: list[dict[str, Any]], min_ready_routes: int, required_boundary: str) -> list[dict[str, Any]]:
    accepted_sources = [source for source in sources if source.get("accepted") is True]
    accepted_entries = [entry for entry in entries if entry.get("entry_status") == "accepted"]
    boundary_mismatches = [entry for entry in entries if entry.get("boundary") != required_boundary]
    widened_scopes = [entry for entry in entries if entry.get("review_scope") != "bounded_route_promotion_review_only"]
    return [
        _check("decision_sources_present", bool(sources), len(sources), "at least one source decision is required"),
        _check("accepted_source_present", bool(accepted_sources), len(accepted_sources), "at least one source decision must be accepted"),
        _check("ready_route_count", len(accepted_entries) >= max(0, min_ready_routes), len(accepted_entries), "accepted route count must satisfy the index threshold"),
        _check("blocked_sources_absent", len(accepted_sources) == len(sources), len(sources) - len(accepted_sources), "all source decisions must be accepted"),
        _check("boundary_scoped", not boundary_mismatches, len(boundary_mismatches), "all indexed routes must keep the required boundary"),
        _check("review_scope_bounded", not widened_scopes, len(widened_scopes), "all indexed routes must keep bounded review scope"),
    ]


def _summary(
    status: str,
    sources: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    required_boundary: str,
    min_ready_routes: int,
) -> dict[str, Any]:
    accepted_entries = [entry for entry in entries if entry.get("entry_status") == "accepted"]
    route_ids = sorted({str(entry.get("route_id")) for entry in accepted_entries if entry.get("route_id")})
    claims = sorted({str(entry.get("model_quality_claim")) for entry in accepted_entries if entry.get("model_quality_claim")})
    return {
        "decision_index_ready": status == "pass",
        "source_decision_count": len(sources),
        "accepted_source_count": sum(1 for source in sources if source.get("accepted") is True),
        "route_entry_count": len(entries),
        "accepted_route_count": len(accepted_entries),
        "min_ready_routes": max(0, min_ready_routes),
        "route_ids": route_ids,
        "route_id_count": len(route_ids),
        "required_boundary": required_boundary,
        "boundary": required_boundary if status == "pass" else "mixed_or_blocked",
        "model_quality_claims": claims,
        "model_quality_claim": claims[0] if len(claims) == 1 else "mixed_or_not_claimed",
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
        "source_decision_paths": [source.get("source_decision_path") for source in sources],
    }


def _source_path(decision_report: dict[str, Any], paths: list[str | Path] | None, index: int) -> str:
    if paths is not None:
        return str(paths[index])
    return str(decision_report.get("_source_path") or "")


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_decision_index_ready"
    return "fix_model_capability_route_promotion_decision_index"


def _recommendations(status: str, entries: list[dict[str, Any]]) -> list[str]:
    if status != "pass":
        return ["Repair rejected, widened, or boundary-mismatched route promotion decisions before indexing them."]
    routes = ", ".join(str(entry.get("route_id")) for entry in entries if entry.get("entry_status") == "accepted") or "none"
    return [
        f"Use the accepted bounded route promotion decision index for downstream route consumers: {routes}.",
        "Keep this index scoped to tiny required-term pair probes until a stronger model-quality evaluation exists.",
    ]


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_DECISION_INDEX_TEXT_FILENAME",
    "build_model_capability_route_promotion_decision_index",
    "load_route_promotion_review_decision",
    "locate_route_promotion_review_decision",
    "read_json_report",
    "resolve_exit_code",
]
