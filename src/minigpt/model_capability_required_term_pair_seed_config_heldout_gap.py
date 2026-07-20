from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_seed_config_heldout_replay import (
    PAIR_SEED_CONFIG_HELDOUT_REPLAY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SEED_CONFIG_HELDOUT_GAP_JSON_FILENAME = "model_capability_required_term_pair_seed_config_heldout_gap.json"
PAIR_SEED_CONFIG_HELDOUT_GAP_CSV_FILENAME = "model_capability_required_term_pair_seed_config_heldout_gap.csv"
PAIR_SEED_CONFIG_HELDOUT_GAP_TEXT_FILENAME = "model_capability_required_term_pair_seed_config_heldout_gap.txt"
PAIR_SEED_CONFIG_HELDOUT_GAP_MARKDOWN_FILENAME = "model_capability_required_term_pair_seed_config_heldout_gap.md"
PAIR_SEED_CONFIG_HELDOUT_GAP_HTML_FILENAME = "model_capability_required_term_pair_seed_config_heldout_gap.html"


def locate_pair_seed_config_heldout_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SEED_CONFIG_HELDOUT_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("seed config held-out replay report must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic(
    heldout_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_rows = list_of_dicts(heldout_report.get("replay_rows"))
    replay_reports = list_of_dicts(heldout_report.get("replay_reports"))
    issues = _input_issues(heldout_report, replay_rows)
    replay_report_index = _replay_report_index(replay_reports)
    gap_rows = [
        _gap_row(row, replay_report_index.get(_row_key(row)))
        for row in replay_rows
        if row.get("replay_pair_full") is not True
    ]
    summary = _summary(replay_rows, gap_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair seed config held-out gap diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_seed_config_heldout_replay": "" if source_path is None else str(source_path),
        "replay_status": heldout_report.get("status"),
        "replay_decision": heldout_report.get("decision"),
        "gap_rows": gap_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _input_issues(heldout_report: dict[str, Any], replay_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if heldout_report.get("status") != "pass":
        issues.append("held-out replay report status is not pass")
    if not replay_rows:
        issues.append("held-out replay report has no replay_rows")
    return issues


def _replay_report_index(replay_reports: list[dict[str, Any]]) -> dict[tuple[str, str, int], dict[str, Any]]:
    index: dict[tuple[str, str, int], dict[str, Any]] = {}
    for entry in replay_reports:
        child = as_dict(entry.get("report"))
        if child:
            index[_entry_key(entry)] = child
    return index


def _entry_key(entry: dict[str, Any]) -> tuple[str, str, int]:
    return (str(entry.get("spec_id") or ""), str(entry.get("config_id") or ""), int(entry.get("seed") or 0))


def _row_key(row: dict[str, Any]) -> tuple[str, str, int]:
    return (str(row.get("spec_id") or ""), str(row.get("selected_config_id") or ""), int(row.get("seed") or 0))


def _gap_row(row: dict[str, Any], child: dict[str, Any] | None) -> dict[str, Any]:
    profiles = _profile_details(as_dict(child))
    best = _best_profile(profiles)
    missed_terms = sorted({term for profile in profiles for term in profile.get("missed_terms", [])})
    return {
        "spec_id": row.get("spec_id"),
        "seed": row.get("seed"),
        "selected_config_id": row.get("selected_config_id"),
        "gap_class": _gap_class(missed_terms, profiles),
        "fixed_prompt": row.get("fixed_prompt"),
        "loss_prompt": row.get("loss_prompt"),
        "top_k": row.get("top_k"),
        "temperature": row.get("temperature"),
        "default_pair_full_variant_count": row.get("default_pair_full_variant_count"),
        "suppression_pair_full_variant_count": row.get("suppression_pair_full_variant_count"),
        "replay_decision": row.get("replay_decision"),
        "source_path": row.get("source_path"),
        "best_profile_id": best.get("profile_id"),
        "best_profile_hit_count": best.get("hit_count", 0),
        "missed_terms": missed_terms,
        "profile_details": profiles,
    }


def _profile_details(child: dict[str, Any]) -> list[dict[str, Any]]:
    if not child:
        return []
    variant_rows = list_of_dicts(child.get("variant_rows"))
    case_rows = list_of_dicts(child.get("case_rows"))
    profiles: list[dict[str, Any]] = []
    for variant in variant_rows:
        profile_id = str(variant.get("profile_id") or "")
        scoped_cases = [case for case in case_rows if case.get("profile_id") == profile_id]
        profiles.append(
            {
                "profile_id": profile_id,
                "pair_full_hit": variant.get("pair_full_hit"),
                "hit_terms": list(variant.get("hit_terms", [])) if isinstance(variant.get("hit_terms"), list) else [],
                "missed_terms": list(variant.get("missed_terms", [])) if isinstance(variant.get("missed_terms"), list) else [],
                "hit_count": len(variant.get("hit_terms", [])) if isinstance(variant.get("hit_terms"), list) else 0,
                "blocked_token_count_total": sum(int(case.get("blocked_token_count") or 0) for case in scoped_cases),
                "case_previews": [_case_preview(case) for case in scoped_cases],
            }
        )
    return profiles


def _case_preview(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "term": case.get("term"),
        "prompt": case.get("prompt"),
        "generation_seed": case.get("generation_seed"),
        "continuation_hit": case.get("continuation_hit"),
        "generated_preview": case.get("generated_preview"),
        "continuation_preview": case.get("continuation_preview"),
    }


def _best_profile(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    if not profiles:
        return {}
    return max(profiles, key=lambda profile: (int(profile.get("hit_count") or 0), str(profile.get("profile_id") or "")))


def _gap_class(missed_terms: list[str], profiles: list[dict[str, Any]]) -> str:
    if not profiles:
        return "missing_replay_sidecar"
    if missed_terms == ["fixed"]:
        return "fixed_term_surface_gap"
    if missed_terms == ["loss"]:
        return "loss_term_surface_gap"
    if missed_terms:
        return "multi_term_surface_gap"
    return "pair_full_summary_gap"


def _summary(replay_rows: list[dict[str, Any]], gap_rows: list[dict[str, Any]]) -> dict[str, Any]:
    spec_gap_counts = _count_by(gap_rows, "spec_id")
    seed_gap_counts = _count_by(gap_rows, "seed")
    config_gap_counts = _count_by(gap_rows, "selected_config_id")
    gap_class_counts = _count_by(gap_rows, "gap_class")
    return {
        "row_count": len(replay_rows),
        "gap_count": len(gap_rows),
        "gap_rate": round(len(gap_rows) / len(replay_rows), 4) if replay_rows else 0.0,
        "non_gap_count": len(replay_rows) - len(gap_rows),
        "spec_gap_counts": spec_gap_counts,
        "seed_gap_counts": seed_gap_counts,
        "config_gap_counts": config_gap_counts,
        "gap_class_counts": gap_class_counts,
        "first_gap_spec_id": gap_rows[0].get("spec_id") if gap_rows else "",
        "first_gap_seed": gap_rows[0].get("seed") if gap_rows else "",
        "first_gap_config_id": gap_rows[0].get("selected_config_id") if gap_rows else "",
        "gap_free": not gap_rows and bool(replay_rows),
    }


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        name = str(row.get(key) or "")
        if name:
            counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_seed_config_heldout_gap_input"
    if summary.get("gap_free"):
        return "required_term_pair_seed_config_heldout_gap_none"
    if summary.get("gap_class_counts") == {"fixed_term_surface_gap": summary.get("gap_count")}:
        return "required_term_pair_seed_config_heldout_gap_fixed_term_surface"
    return "required_term_pair_seed_config_heldout_gap_diagnosed"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The held-out replay source is not structurally ready for gap diagnosis."
        next_action = "repair the held-out replay artifact before planning prompt-surface fixes"
        claim = "not_claimed"
    elif summary.get("gap_free"):
        reason = "The selected seed/config policy has no held-out replay gaps in the inspected report."
        next_action = "expand to fresh prompt surfaces or fresh seeds"
        claim = "targeted_seed_config_heldout_gap_free"
    else:
        reason = "The held-out replay gaps are now localized by prompt surface, seed, config, and missed term."
        next_action = "repair the dominant missed-term surface before adding broader benchmarks"
        claim = "diagnostic_only"
    return {
        "model_quality_claim": claim,
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_SEED_CONFIG_HELDOUT_GAP_CSV_FILENAME",
    "PAIR_SEED_CONFIG_HELDOUT_GAP_HTML_FILENAME",
    "PAIR_SEED_CONFIG_HELDOUT_GAP_JSON_FILENAME",
    "PAIR_SEED_CONFIG_HELDOUT_GAP_MARKDOWN_FILENAME",
    "PAIR_SEED_CONFIG_HELDOUT_GAP_TEXT_FILENAME",
    "build_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic",
    "locate_pair_seed_config_heldout_replay",
    "read_json_report",
    "resolve_exit_code",
]
