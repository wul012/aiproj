from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.json"
)
PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.csv"
)
PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.txt"
)
PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.md"
)
PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.html"
)


def locate_exact_surface_repair_effectiveness_replay_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("exact-surface repair effectiveness comparison input must be a JSON object")
    return dict(payload)


def build_exact_surface_repair_effectiveness_comparison(
    baseline_replay: dict[str, Any],
    repaired_replay: dict[str, Any],
    *,
    baseline_replay_path: str | Path | None = None,
    repaired_replay_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = _comparison_rows(baseline_replay, repaired_replay)
    checks = _checks(baseline_replay, repaired_replay, rows)
    issues = [row for row in checks if row["status"] != "pass"]
    summary = _summary(baseline_replay, repaired_replay, rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness exact-surface repair effectiveness comparison",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_baseline_replay_path": str(baseline_replay_path or ""),
        "source_repaired_replay_path": str(repaired_replay_path or ""),
        "comparison_rows": rows,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _comparison_rows(baseline: dict[str, Any], repaired: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_rows = {str(row.get("spec_id")): row for row in list_of_dicts(baseline.get("replay_rows"))}
    repaired_rows = {str(row.get("spec_id")): row for row in list_of_dicts(repaired.get("replay_rows"))}
    rows: list[dict[str, Any]] = []
    for spec_id in sorted(set(baseline_rows) | set(repaired_rows)):
        before = baseline_rows.get(spec_id, {})
        after = repaired_rows.get(spec_id, {})
        before_hits = int(before.get("default_continuation_hit_count") or 0)
        after_hits = int(after.get("default_continuation_hit_count") or 0)
        rows.append(
            {
                "spec_id": spec_id,
                "prompt": after.get("prompt") or before.get("prompt"),
                "required_for_ready": bool(after.get("required_for_ready") or before.get("required_for_ready")),
                "baseline_pair_full": bool(before.get("replay_pair_full")),
                "repaired_pair_full": bool(after.get("replay_pair_full")),
                "baseline_default_hit_count": before_hits,
                "repaired_default_hit_count": after_hits,
                "default_hit_delta": after_hits - before_hits,
                "pair_full_delta": int(bool(after.get("replay_pair_full"))) - int(bool(before.get("replay_pair_full"))),
            }
        )
    return rows


def _checks(baseline: dict[str, Any], repaired: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("baseline_replay_passed", baseline.get("status") == "pass", baseline.get("status"), "baseline replay must execute cleanly"),
        _check("repaired_replay_passed", repaired.get("status") == "pass", repaired.get("status"), "repaired replay must execute cleanly"),
        _check("comparison_rows_present", bool(rows), len(rows), "comparison requires replay rows"),
        _check("exact_surface_compared", any(row.get("spec_id") == "exact-heldout-pair" for row in rows), [row.get("spec_id") for row in rows], "exact heldout pair surface must be compared"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(baseline: dict[str, Any], repaired: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact = next((row for row in rows if row.get("spec_id") == "exact-heldout-pair"), {})
    baseline_summary = as_dict(baseline.get("summary"))
    repaired_summary = as_dict(repaired.get("summary"))
    improved_rows = [row.get("spec_id") for row in rows if int(row.get("default_hit_delta") or 0) > 0 or int(row.get("pair_full_delta") or 0) > 0]
    regressed_rows = [row.get("spec_id") for row in rows if int(row.get("default_hit_delta") or 0) < 0 or int(row.get("pair_full_delta") or 0) < 0]
    return {
        "baseline_decision": baseline.get("decision"),
        "repaired_decision": repaired.get("decision"),
        "baseline_exact_heldout_pair_full": baseline_summary.get("exact_heldout_pair_full") is True,
        "repaired_exact_heldout_pair_full": repaired_summary.get("exact_heldout_pair_full") is True,
        "baseline_pair_full_count": baseline_summary.get("pair_full_count", 0),
        "repaired_pair_full_count": repaired_summary.get("pair_full_count", 0),
        "exact_default_hit_delta": exact.get("default_hit_delta", 0),
        "exact_pair_full_delta": exact.get("pair_full_delta", 0),
        "improved_surface_ids": improved_rows,
        "regressed_surface_ids": regressed_rows,
        "exact_surface_improved": int(exact.get("default_hit_delta") or 0) > 0 or int(exact.get("pair_full_delta") or 0) > 0,
        "repair_effective": repaired_summary.get("exact_heldout_pair_full") is True,
        "repair_ineffective": repaired_summary.get("exact_heldout_pair_full") is not True and not improved_rows,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_exact_surface_repair_effectiveness_comparison"
    if summary.get("repair_effective"):
        return "pair_readiness_exact_surface_repair_effective_ready_for_promotion_guard"
    if summary.get("exact_surface_improved"):
        return "pair_readiness_exact_surface_repair_partial_improvement"
    return "pair_readiness_exact_surface_repair_ineffective_stop_route"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Replay inputs are not clean enough to compare repair effectiveness.",
            "next_action": "repair replay evidence before route decisions",
        }
    if summary.get("repair_effective"):
        return {
            "model_quality_claim": "pair_probe_replay_ready",
            "reason": "The repaired route passes the exact heldout pair replay.",
            "next_action": "run promotion guard and seed-stability checks",
        }
    if summary.get("exact_surface_improved"):
        return {
            "model_quality_claim": "partial_exact_surface_improvement",
            "reason": "The repair improved exact-surface hits but still did not reach ready status.",
            "next_action": "plan a stricter exact-surface objective or decode-side test",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "The exact-surface repair did not improve independent replay over the fixed-preserving baseline.",
        "next_action": "close the near-exact repair route and consider objective/decoding alternatives",
    }


__all__ = [
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_CSV_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_HTML_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_JSON_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_EFFECTIVENESS_COMPARISON_TEXT_FILENAME",
    "build_exact_surface_repair_effectiveness_comparison",
    "locate_exact_surface_repair_effectiveness_replay_source",
    "read_json_report",
    "resolve_exit_code",
]
