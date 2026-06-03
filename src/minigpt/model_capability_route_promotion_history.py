from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, number_or_default, number_or_none, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_JSON_FILENAME = "model_capability_route_promotion_history.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_CSV_FILENAME = "model_capability_route_promotion_history.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_TEXT_FILENAME = "model_capability_route_promotion_history.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_MARKDOWN_FILENAME = "model_capability_route_promotion_history.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_HTML_FILENAME = "model_capability_route_promotion_history.html"


def locate_route_promotion_manifest(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion history input must be a JSON object")
    return dict(payload)


def load_route_promotion_manifest(path: str | Path) -> dict[str, Any]:
    resolved = locate_route_promotion_manifest(path)
    payload = read_json_report(resolved)
    payload["_source_path"] = str(resolved)
    return payload


def build_model_capability_route_promotion_history(
    manifest_paths: list[str | Path],
    *,
    names: list[str] | None = None,
    min_ready_entries: int = 1,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion history",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not manifest_paths:
        raise ValueError("at least one route promotion manifest is required")
    if names is not None and len(names) != len(manifest_paths):
        raise ValueError("names length must match manifest_paths length")
    manifests = [load_route_promotion_manifest(path) for path in manifest_paths]
    entries = [_entry(manifest, _entry_name(manifest, names, index), index, required_boundary) for index, manifest in enumerate(manifests)]
    summary = _summary(entries, required_boundary)
    readiness = _readiness_requirement(summary, min_ready_entries=min_ready_entries)
    status = readiness["status"]
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "entries": entries,
        "summary": summary,
        "readiness_requirement": readiness,
        "recommendations": _recommendations(summary, readiness),
    }


def resolve_exit_code(report: dict[str, Any], *, require_ready_history: bool) -> int:
    requirement = as_dict(report.get("readiness_requirement"))
    return int(requirement.get("exit_code") or 0) if require_ready_history else 0


def _entry(manifest_report: dict[str, Any], name: str, index: int, required_boundary: str) -> dict[str, Any]:
    summary = as_dict(manifest_report.get("summary"))
    manifest = as_dict(manifest_report.get("manifest"))
    history_entry = as_dict(manifest.get("benchmark_history_entry"))
    source_review = as_dict(manifest_report.get("source_acceptance_review"))
    source_review_summary = as_dict(source_review.get("summary"))
    boundary = str(history_entry.get("boundary") or manifest.get("promotion_scope") or "")
    promotion_ready = (
        manifest_report.get("status") == "pass"
        and summary.get("promotion_manifest_ready") is True
        and summary.get("can_feed_benchmark_history") is True
        and history_entry.get("status") == "ready"
        and boundary == required_boundary
    )
    return {
        "index": index,
        "name": name,
        "source_manifest_path": manifest_report.get("_source_path") or "",
        "source_acceptance_review_path": manifest_report.get("source_acceptance_review_path") or "",
        "source_seed_stability_rollup_path": manifest_report.get("source_seed_stability_rollup_path") or "",
        "route_id": history_entry.get("route_id") or manifest.get("route_id"),
        "route_status": manifest.get("route_status"),
        "history_entry_status": history_entry.get("status"),
        "promotion_readiness": "ready" if promotion_ready else "blocked",
        "promotion_manifest_status": manifest_report.get("status"),
        "promotion_manifest_decision": manifest_report.get("decision"),
        "acceptance_review_status": source_review.get("status"),
        "acceptance_review_decision": source_review.get("decision"),
        "boundary": boundary,
        "required_boundary": required_boundary,
        "boundary_matches": boundary == required_boundary,
        "model_quality_claim": history_entry.get("model_quality_claim") or manifest.get("model_quality_claim") or "not_claimed",
        "seed_count": number_or_default(history_entry.get("seed_count"), 0, int),
        "min_pair_full_count": number_or_none(history_entry.get("min_pair_full_count"), int),
        "pair_full_strength_spread": number_or_none(history_entry.get("pair_full_strength_spread"), int),
        "accepted_seed_count": number_or_default(manifest.get("accepted_seed_count"), 0, int),
        "source_ready_replay_count": number_or_default(source_review_summary.get("ready_replay_count"), 0, int),
        "source_min_pair_full_count": number_or_none(source_review_summary.get("min_pair_full_count"), int),
        "source_pair_full_strength_spread": number_or_none(source_review_summary.get("pair_full_strength_spread"), int),
    }


def _entry_name(manifest: dict[str, Any], names: list[str] | None, index: int) -> str:
    if names is not None:
        return names[index]
    manifest_body = as_dict(manifest.get("manifest"))
    route_id = manifest_body.get("route_id") or f"route-{index + 1}"
    return f"{route_id}-promotion-{index + 1}"


def _summary(entries: list[dict[str, Any]], required_boundary: str) -> dict[str, Any]:
    ready = [entry for entry in entries if entry.get("promotion_readiness") == "ready"]
    blocked = [entry for entry in entries if entry.get("promotion_readiness") != "ready"]
    boundary_mismatches = [entry for entry in entries if entry.get("boundary_matches") is not True]
    route_ids = sorted({str(entry.get("route_id")) for entry in entries if entry.get("route_id")})
    claims = sorted({str(entry.get("model_quality_claim")) for entry in entries if entry.get("model_quality_claim")})
    return {
        "entry_count": len(entries),
        "ready_count": len(ready),
        "blocked_count": len(blocked),
        "boundary_mismatch_count": len(boundary_mismatches),
        "required_boundary": required_boundary,
        "route_ids": route_ids,
        "route_id_count": len(route_ids),
        "model_quality_claims": claims,
        "model_quality_claim": claims[0] if len(claims) == 1 else "mixed_or_not_claimed",
        "ready_route_ids": [entry.get("route_id") for entry in ready],
        "blocked_route_ids": [entry.get("route_id") for entry in blocked],
        "min_seed_count": min((int(entry.get("seed_count") or 0) for entry in entries), default=0),
        "max_seed_count": max((int(entry.get("seed_count") or 0) for entry in entries), default=0),
        "min_pair_full_count": min(
            (int(entry.get("min_pair_full_count") or 0) for entry in entries if entry.get("min_pair_full_count") is not None),
            default=0,
        ),
        "max_pair_full_strength_spread": max(
            (int(entry.get("pair_full_strength_spread") or 0) for entry in entries if entry.get("pair_full_strength_spread") is not None),
            default=0,
        ),
    }


def _readiness_requirement(summary: dict[str, Any], *, min_ready_entries: int) -> dict[str, Any]:
    minimum = max(0, int(min_ready_entries))
    failed: list[str] = []
    if int(summary.get("entry_count") or 0) == 0:
        failed.append("missing_route_promotion_entries")
    if int(summary.get("ready_count") or 0) < minimum:
        failed.append("insufficient_ready_route_promotions")
    if int(summary.get("blocked_count") or 0):
        failed.append("blocked_route_promotion_entries")
    if int(summary.get("boundary_mismatch_count") or 0):
        failed.append("route_promotion_boundary_mismatches")
    status = "pass" if not failed else "fail"
    return {
        "status": status,
        "decision": "continue" if status == "pass" else "stop",
        "exit_code": 0 if status == "pass" else 1,
        "min_ready_entries": minimum,
        "ready_count": int(summary.get("ready_count") or 0),
        "entry_count": int(summary.get("entry_count") or 0),
        "failed_reasons": failed,
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_history_ready"
    return "fix_model_capability_route_promotion_history"


def _recommendations(summary: dict[str, Any], readiness: dict[str, Any]) -> list[str]:
    if readiness.get("status") != "pass":
        return ["Fix blocked or boundary-mismatched route promotion entries before using this ledger as model capability history."]
    routes = ", ".join(str(item) for item in summary.get("ready_route_ids", [])) or "none"
    return [
        f"Use the ready route promotion ledger as bounded model capability history for: {routes}.",
        "Keep the tiny pair-probe boundary visible when this ledger is consumed by portfolio or regression reviews.",
    ]


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_TEXT_FILENAME",
    "build_model_capability_route_promotion_history",
    "load_route_promotion_manifest",
    "locate_route_promotion_manifest",
    "read_json_report",
    "resolve_exit_code",
]
