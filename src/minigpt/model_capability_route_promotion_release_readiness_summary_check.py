from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_release_readiness_summary import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, string_list, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_JSON_FILENAME = "model_capability_route_promotion_release_readiness_summary_check.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_CSV_FILENAME = "model_capability_route_promotion_release_readiness_summary_check.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_TEXT_FILENAME = "model_capability_route_promotion_release_readiness_summary_check.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_MARKDOWN_FILENAME = "model_capability_route_promotion_release_readiness_summary_check.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_HTML_FILENAME = "model_capability_route_promotion_release_readiness_summary_check.html"

EXPECTED_SOURCE_KINDS = ("release_packet", "release_packet_review", "governance_snapshot")
READY_DECISION = "model_capability_route_promotion_release_readiness_summary_ready"
READY_SCOPE = "bounded_route_promotion_release_governance_only"
SOURCE_READY_SCOPE = "bounded_model_capability_governance_only"


def locate_route_promotion_release_readiness_summary(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion release readiness summary check input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_release_readiness_summary_check(
    release_readiness_summary: dict[str, Any],
    *,
    release_readiness_summary_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion release readiness summary contract check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(release_readiness_summary.get("summary"))
    route_alignment = as_dict(release_readiness_summary.get("route_alignment"))
    boundary_claim = as_dict(release_readiness_summary.get("boundary_claim"))
    downstream_policy = as_dict(release_readiness_summary.get("downstream_policy"))
    source_rows = list_of_dicts(release_readiness_summary.get("source_rows"))
    source_digest_rows = _source_digest_rows(source_rows)
    check_rows = _check_rows(
        release_readiness_summary,
        summary,
        route_alignment,
        boundary_claim,
        downstream_policy,
        source_rows,
        source_digest_rows,
        required_boundary,
    )
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
        "source_summary": str(release_readiness_summary_path or ""),
        "source_summary_exists": Path(str(release_readiness_summary_path)).exists() if release_readiness_summary_path else False,
        "source_summary_digest": _sha256_or_empty(release_readiness_summary_path),
        "source_summary_summary": summary,
        "route_alignment": route_alignment,
        "boundary_claim": boundary_claim,
        "downstream_policy": downstream_policy,
        "source_rows": source_rows,
        "source_digest_rows": source_digest_rows,
        "check_rows": check_rows,
        "summary": _summary(status, check_rows, summary, route_alignment, boundary_claim, source_digest_rows),
        "interpretation": _interpretation(status),
    }


def _check_rows(
    report: dict[str, Any],
    summary: dict[str, Any],
    route_alignment: dict[str, Any],
    boundary_claim: dict[str, Any],
    downstream_policy: dict[str, Any],
    source_rows: list[dict[str, Any]],
    source_digest_rows: list[dict[str, Any]],
    required_boundary: str,
) -> list[dict[str, Any]]:
    check_rows = list_of_dicts(report.get("check_rows"))
    issues = list_of_dicts(report.get("issues"))
    summary_active_routes = _unique_sorted(summary.get("active_routes"))
    alignment_active_routes = _unique_sorted(route_alignment.get("active_routes"))
    source_kinds = sorted(str(row.get("kind")) for row in source_rows if row.get("kind"))
    digest_kinds = sorted(str(row.get("kind")) for row in source_digest_rows if row.get("kind"))
    return [
        _check("summary_passed", report.get("status") == "pass", report.get("status"), "release readiness summary must pass"),
        _check("summary_decision_ready", report.get("decision") == READY_DECISION, report.get("decision"), "summary decision must be ready"),
        _check("summary_ready_flag", summary.get("release_readiness_summary_ready") is True, summary.get("release_readiness_summary_ready"), "summary ready flag must be true"),
        _check("summary_failed_count_zero", int(report.get("failed_count") or 0) == 0, report.get("failed_count"), "summary failed_count must be zero"),
        _check("summary_issues_empty", not issues, len(issues), "summary issues must be empty"),
        _check("summary_check_rows_clean", all(row.get("status") == "pass" for row in check_rows), _status_counts(check_rows), "all summary check rows must pass"),
        _check(
            "summary_check_counts_match",
            summary.get("failed_check_count") == 0 and summary.get("passed_check_count") == len(check_rows),
            {"summary": {"passed": summary.get("passed_check_count"), "failed": summary.get("failed_check_count")}, "actual": len(check_rows)},
            "summary check counts must match check_rows",
        ),
        _check("source_rows_present", len(source_rows) == len(EXPECTED_SOURCE_KINDS), len(source_rows), "summary must record the three upstream source rows"),
        _check("source_kinds_match", source_kinds == sorted(EXPECTED_SOURCE_KINDS), source_kinds, "summary source kinds must match the expected packet/review/snapshot set"),
        _check("source_rows_mark_existing", all(row.get("exists") is True for row in source_rows), source_rows, "summary source rows must mark files as existing"),
        _check("source_files_digestible", all(row.get("exists") is True and row.get("sha256") for row in source_digest_rows), source_digest_rows, "source files must exist and have digests"),
        _check("source_digest_kinds_match", digest_kinds == sorted(EXPECTED_SOURCE_KINDS), digest_kinds, "source digest rows must cover the expected source kinds"),
        _check("source_evidence_count_matches", summary.get("evidence_count") == len(source_rows), {"summary": summary.get("evidence_count"), "actual": len(source_rows)}, "evidence_count must match source rows"),
        _check("active_routes_align", route_alignment.get("aligned") is True, route_alignment, "route alignment must be true"),
        _check("active_routes_match_summary", summary_active_routes == alignment_active_routes and bool(summary_active_routes), {"summary": summary_active_routes, "alignment": alignment_active_routes}, "summary routes must match route alignment"),
        _check("active_route_count_matches", int(summary.get("active_route_count") or 0) == int(route_alignment.get("route_count") or 0), {"summary": summary.get("active_route_count"), "alignment": route_alignment.get("route_count")}, "active route count must match route alignment"),
        _check("boundary_consistent", boundary_claim.get("boundary_consistent") is True, boundary_claim.get("boundaries"), "boundary claim must be internally consistent"),
        _check("boundary_required", boundary_claim.get("boundary") == required_boundary and summary.get("boundary") == required_boundary, {"summary": summary.get("boundary"), "boundary_claim": boundary_claim.get("boundary")}, f"boundary must remain {required_boundary}"),
        _check("claim_consistent", boundary_claim.get("claim_consistent") is True, boundary_claim.get("claims"), "model quality claim must be internally consistent"),
        _check("claim_bounded", boundary_claim.get("claim_bounded") is True, boundary_claim.get("model_quality_claim"), "model quality claim must remain pair-probe scoped"),
        _check("claim_matches_summary", summary.get("model_quality_claim") == boundary_claim.get("model_quality_claim"), {"summary": summary.get("model_quality_claim"), "boundary_claim": boundary_claim.get("model_quality_claim")}, "summary claim must match boundary_claim"),
        _check("handoff_ready", summary.get("handoff_status") == "ready_for_bounded_governance_release", summary.get("handoff_status"), "handoff status must be ready for bounded governance release"),
        _check("downstream_policy_allowed", downstream_policy.get("allowed") is True, downstream_policy, "downstream policy must allow bounded release governance"),
        _check("downstream_scope_bounded", downstream_policy.get("allowed_scope") == READY_SCOPE, downstream_policy.get("allowed_scope"), "downstream scope must be the release-readiness governance scope"),
        _check("source_downstream_scope_bounded", downstream_policy.get("source_allowed_scope") == SOURCE_READY_SCOPE, downstream_policy.get("source_allowed_scope"), "source downstream scope must remain model-capability governance only"),
    ]


def _source_digest_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        path = str(row.get("path") or "")
        exists = Path(path).is_file() if path else False
        rows.append(
            {
                "kind": row.get("kind"),
                "path": path,
                "exists": exists,
                "sha256": _sha256_or_empty(path) if exists else "",
            }
        )
    return rows


def _sha256_or_empty(path: str | Path | None) -> str:
    if not path:
        return ""
    source = Path(path)
    if not source.is_file():
        return ""
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _summary(
    status: str,
    check_rows: list[dict[str, Any]],
    source_summary: dict[str, Any],
    route_alignment: dict[str, Any],
    boundary_claim: dict[str, Any],
    source_digest_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "contract_check_ready": status == "pass",
        "source_summary_ready": source_summary.get("release_readiness_summary_ready") is True,
        "active_route_count": source_summary.get("active_route_count"),
        "active_routes": route_alignment.get("active_routes"),
        "boundary": boundary_claim.get("boundary"),
        "model_quality_claim": boundary_claim.get("model_quality_claim") if status == "pass" else "not_claimed",
        "source_evidence_count": len(source_digest_rows),
        "source_digest_count": sum(1 for row in source_digest_rows if row.get("sha256")),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
        "next_step": "publish_contract_checked_route_promotion_release_readiness_summary" if status == "pass" else "repair_route_promotion_release_readiness_summary_contract",
    }


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The release readiness summary failed contract checks or source digest verification.",
            "next_action": "repair the summary, source paths, or bounded-scope fields before downstream consumption",
        }
    return {
        "model_quality_claim": "bounded_route_promotion_release_governance_only",
        "reason": "The release readiness summary is contract-checked and source-digestable for bounded downstream governance.",
        "next_action": "use the checked summary as bounded route-promotion release governance evidence",
    }


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "pass": sum(1 for row in rows if row.get("status") == "pass"),
        "fail": sum(1 for row in rows if row.get("status") != "pass"),
    }


def _unique_sorted(value: Any) -> list[str]:
    return sorted({str(item) for item in string_list(value) if str(item)})


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_release_readiness_summary_contract_check_passed"
    return "fix_model_capability_route_promotion_release_readiness_summary_contract"


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CHECK_TEXT_FILENAME",
    "build_model_capability_route_promotion_release_readiness_summary_check",
    "locate_route_promotion_release_readiness_summary",
    "read_json_report",
    "resolve_exit_code",
]
