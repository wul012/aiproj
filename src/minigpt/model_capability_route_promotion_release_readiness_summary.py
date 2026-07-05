from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_governance_snapshot import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_release_packet import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_release_packet_review import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, string_list, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_JSON_FILENAME = "model_capability_route_promotion_release_readiness_summary.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CSV_FILENAME = "model_capability_route_promotion_release_readiness_summary.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_TEXT_FILENAME = "model_capability_route_promotion_release_readiness_summary.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_MARKDOWN_FILENAME = "model_capability_route_promotion_release_readiness_summary.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_HTML_FILENAME = "model_capability_route_promotion_release_readiness_summary.html"


def locate_route_promotion_release_packet(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_JSON_FILENAME
    return source


def locate_route_promotion_release_packet_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_REVIEW_JSON_FILENAME
    return source


def locate_route_promotion_governance_snapshot(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_GOVERNANCE_SNAPSHOT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion release readiness summary input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_release_readiness_summary(
    release_packet: dict[str, Any],
    release_packet_review: dict[str, Any],
    governance_snapshot: dict[str, Any],
    *,
    release_packet_path: str | Path | None = None,
    release_packet_review_path: str | Path | None = None,
    governance_snapshot_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion release readiness summary",
    generated_at: str | None = None,
) -> dict[str, Any]:
    packet_summary = as_dict(release_packet.get("summary"))
    review_summary = as_dict(release_packet_review.get("summary"))
    snapshot_summary = as_dict(governance_snapshot.get("summary"))
    downstream_policy = as_dict(governance_snapshot.get("downstream_policy"))
    source_rows = _source_rows(release_packet_path, release_packet_review_path, governance_snapshot_path)
    route_alignment = _route_alignment(packet_summary, review_summary, snapshot_summary)
    boundary_claim = _boundary_claim(packet_summary, review_summary, snapshot_summary, required_boundary)
    check_rows = _checks(
        release_packet,
        release_packet_review,
        governance_snapshot,
        packet_summary,
        review_summary,
        snapshot_summary,
        downstream_policy,
        source_rows,
        route_alignment,
        boundary_claim,
        required_boundary,
    )
    issues = [row for row in check_rows if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, check_rows, route_alignment, boundary_claim, source_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_release_packet": str(release_packet_path or ""),
        "source_release_packet_review": str(release_packet_review_path or ""),
        "source_governance_snapshot": str(governance_snapshot_path or ""),
        "source_rows": source_rows,
        "source_summaries": {
            "release_packet": packet_summary,
            "release_packet_review": review_summary,
            "governance_snapshot": snapshot_summary,
        },
        "route_alignment": route_alignment,
        "boundary_claim": boundary_claim,
        "downstream_policy": _downstream_policy(status, downstream_policy, route_alignment, boundary_claim),
        "check_rows": check_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _source_rows(
    release_packet_path: str | Path | None,
    release_packet_review_path: str | Path | None,
    governance_snapshot_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _source("release_packet", release_packet_path),
        _source("release_packet_review", release_packet_review_path),
        _source("governance_snapshot", governance_snapshot_path),
    ]


def _source(kind: str, path: str | Path | None) -> dict[str, Any]:
    text = str(path or "")
    return {"kind": kind, "path": text, "exists": Path(text).exists() if text else False}


def _route_alignment(
    packet_summary: dict[str, Any],
    review_summary: dict[str, Any],
    snapshot_summary: dict[str, Any],
) -> dict[str, Any]:
    packet_routes = _unique_sorted(packet_summary.get("active_routes"))
    review_routes = _unique_sorted(review_summary.get("active_routes"))
    snapshot_routes = _unique_sorted(snapshot_summary.get("route_ids"))
    route_sets = [set(packet_routes), set(review_routes), set(snapshot_routes)]
    aligned = bool(packet_routes) and route_sets[0] == route_sets[1] == route_sets[2]
    return {
        "aligned": aligned,
        "active_routes": packet_routes if aligned else [],
        "route_count": len(packet_routes) if aligned else 0,
        "packet_routes": packet_routes,
        "review_routes": review_routes,
        "snapshot_routes": snapshot_routes,
    }


def _boundary_claim(
    packet_summary: dict[str, Any],
    review_summary: dict[str, Any],
    snapshot_summary: dict[str, Any],
    required_boundary: str,
) -> dict[str, Any]:
    boundaries = [
        _as_text(packet_summary.get("boundary")),
        _as_text(review_summary.get("boundary")),
        _as_text(snapshot_summary.get("boundary")),
    ]
    claims = [
        _as_text(packet_summary.get("model_quality_claim")),
        _as_text(review_summary.get("model_quality_claim")),
        _as_text(snapshot_summary.get("model_quality_claim")),
    ]
    unique_boundaries = sorted({item for item in boundaries if item})
    unique_claims = sorted({item for item in claims if item})
    claim = unique_claims[0] if len(unique_claims) == 1 else "mixed_or_not_claimed"
    return {
        "required_boundary": required_boundary,
        "boundaries": boundaries,
        "boundary": unique_boundaries[0] if len(unique_boundaries) == 1 else "mixed_or_missing",
        "boundary_consistent": len(unique_boundaries) == 1 and unique_boundaries[0] == required_boundary,
        "claims": claims,
        "model_quality_claim": claim,
        "claim_consistent": len(unique_claims) == 1,
        "claim_bounded": claim.startswith("seed_stable_pair_probe_route"),
    }


def _checks(
    release_packet: dict[str, Any],
    release_packet_review: dict[str, Any],
    governance_snapshot: dict[str, Any],
    packet_summary: dict[str, Any],
    review_summary: dict[str, Any],
    snapshot_summary: dict[str, Any],
    downstream_policy: dict[str, Any],
    source_rows: list[dict[str, Any]],
    route_alignment: dict[str, Any],
    boundary_claim: dict[str, Any],
    required_boundary: str,
) -> list[dict[str, Any]]:
    return [
        _check("release_packet_passed", release_packet.get("status") == "pass", release_packet.get("status"), "release packet must pass"),
        _check(
            "release_packet_ready",
            release_packet.get("decision") == "model_capability_route_promotion_release_packet_ready"
            and packet_summary.get("release_packet_ready") is True,
            {"decision": release_packet.get("decision"), "ready": packet_summary.get("release_packet_ready")},
            "release packet must be ready",
        ),
        _check("release_packet_review_passed", release_packet_review.get("status") == "pass", release_packet_review.get("status"), "release packet review must pass"),
        _check(
            "release_packet_review_ready",
            release_packet_review.get("decision") == "model_capability_route_promotion_release_packet_review_ready"
            and review_summary.get("release_packet_review_ready") is True,
            {"decision": release_packet_review.get("decision"), "ready": review_summary.get("release_packet_review_ready")},
            "release packet review must be ready",
        ),
        _check("governance_snapshot_passed", governance_snapshot.get("status") == "pass", governance_snapshot.get("status"), "governance snapshot must pass"),
        _check(
            "governance_snapshot_ready",
            governance_snapshot.get("decision") == "model_capability_route_promotion_governance_snapshot_ready"
            and snapshot_summary.get("governance_snapshot_ready") is True,
            {"decision": governance_snapshot.get("decision"), "ready": snapshot_summary.get("governance_snapshot_ready")},
            "governance snapshot must be ready",
        ),
        _check("source_files_exist", all(row.get("exists") is True for row in source_rows), source_rows, "release readiness source files must exist"),
        _check("active_routes_align", route_alignment.get("aligned") is True, route_alignment, "packet, review, and snapshot routes must align"),
        _check("active_route_present", int(route_alignment.get("route_count") or 0) > 0, route_alignment.get("route_count"), "summary requires at least one active route"),
        _check("boundary_scoped", boundary_claim.get("boundary_consistent") is True, boundary_claim.get("boundaries"), f"all boundaries must be {required_boundary}"),
        _check("claim_consistent", boundary_claim.get("claim_consistent") is True, boundary_claim.get("claims"), "all source claims must match"),
        _check("claim_bounded", boundary_claim.get("claim_bounded") is True, boundary_claim.get("model_quality_claim"), "claim must remain pair-probe scoped"),
        _check("source_checks_clean", _failed_count(packet_summary) + _failed_count(review_summary) + _failed_count(snapshot_summary) == 0, {"packet": packet_summary.get("failed_check_count"), "review": review_summary.get("failed_check_count"), "snapshot": snapshot_summary.get("failed_check_count")}, "source summaries must have no failed checks"),
        _check("downstream_policy_allowed", downstream_policy.get("allowed") is True, downstream_policy, "governance snapshot must allow bounded downstream use"),
        _check(
            "downstream_scope_bounded",
            downstream_policy.get("allowed_scope") == "bounded_model_capability_governance_only",
            downstream_policy.get("allowed_scope"),
            "downstream scope must stay bounded to model capability governance",
        ),
    ]


def _summary(
    status: str,
    check_rows: list[dict[str, Any]],
    route_alignment: dict[str, Any],
    boundary_claim: dict[str, Any],
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "release_readiness_summary_ready": status == "pass",
        "handoff_status": "ready_for_bounded_governance_release" if status == "pass" else "blocked",
        "active_route_count": route_alignment.get("route_count"),
        "active_routes": route_alignment.get("active_routes"),
        "boundary": boundary_claim.get("boundary"),
        "model_quality_claim": boundary_claim.get("model_quality_claim") if status == "pass" else "not_claimed",
        "evidence_count": len(source_rows),
        "passed_check_count": sum(1 for row in check_rows if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in check_rows if row["status"] != "pass"),
        "next_step": "publish_bounded_route_promotion_release_readiness_summary" if status == "pass" else "repair_route_promotion_release_readiness_inputs",
    }


def _downstream_policy(
    status: str,
    source_policy: dict[str, Any],
    route_alignment: dict[str, Any],
    boundary_claim: dict[str, Any],
) -> dict[str, Any]:
    if status != "pass":
        return {"allowed": False, "allowed_scope": "none", "reason": "release readiness inputs are not fully verified"}
    return {
        "allowed": True,
        "allowed_scope": "bounded_route_promotion_release_governance_only",
        "source_allowed_scope": source_policy.get("allowed_scope"),
        "route_ids": route_alignment.get("active_routes"),
        "boundary": boundary_claim.get("boundary"),
        "model_quality_claim": boundary_claim.get("model_quality_claim"),
        "reason": "packet, review, and governance snapshot agree inside the bounded route-promotion scope",
    }


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route promotion release readiness summary is blocked by failed or inconsistent source evidence.",
            "next_action": "repair packet, review, snapshot, route alignment, or bounded-scope evidence before release handoff",
        }
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The route promotion packet, review, and governance snapshot agree as bounded release-readiness evidence.",
        "next_action": "publish the bounded release readiness summary as governance evidence, without widening model-quality claims",
    }


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_release_readiness_summary_ready"
    return "fix_model_capability_route_promotion_release_readiness_summary"


def _unique_sorted(value: Any) -> list[str]:
    return sorted({str(item) for item in string_list(value) if str(item)})


def _failed_count(summary: dict[str, Any]) -> int:
    return int(summary.get("failed_check_count") or 0)


def _as_text(value: Any) -> str:
    return "" if value is None else str(value)


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_READINESS_SUMMARY_TEXT_FILENAME",
    "build_model_capability_route_promotion_release_readiness_summary",
    "locate_route_promotion_governance_snapshot",
    "locate_route_promotion_release_packet",
    "locate_route_promotion_release_packet_review",
    "read_json_report",
    "resolve_exit_code",
]
