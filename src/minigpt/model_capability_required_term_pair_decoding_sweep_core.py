"""Execution and aggregation core for required-term pair decoding sweeps."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc, _generation_row
from minigpt.report_utils import as_dict, list_of_dicts, resolve_archived_reference_path
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code

REQUIRED_TERM_PAIR_DECODING_SWEEP_JSON_FILENAME = "model_capability_required_term_pair_decoding_sweep.json"
REQUIRED_TERM_PAIR_DECODING_SWEEP_TEXT_FILENAME = "model_capability_required_term_pair_decoding_sweep.txt"
REQUIRED_TERM_PAIR_DECODING_SWEEP_MARKDOWN_FILENAME = "model_capability_required_term_pair_decoding_sweep.md"
REQUIRED_TERM_PAIR_DECODING_SWEEP_HTML_FILENAME = "model_capability_required_term_pair_decoding_sweep.html"

DEFAULT_PAIR_DECODING_SWEEP_SEED = 498


def select_pair_decoding_sweep_targets(
    pair_capacity_report: dict[str, Any],
    *,
    target_limit: int | None = 2,
) -> list[dict[str, Any]]:
    pairs = {str(row.get("pair_id") or ""): row for row in list_of_dicts(pair_capacity_report.get("pairs"))}
    capacity_rows = {
        (str(row.get("pair_id") or ""), str(row.get("variant_id") or "")): row
        for row in list_of_dicts(pair_capacity_report.get("capacity_rows"))
    }
    targets: list[dict[str, Any]] = []
    for summary in list_of_dicts(pair_capacity_report.get("variant_pair_summaries")):
        if summary.get("pair_full_hit") or not summary.get("pair_partial_hit"):
            continue
        pair_id = str(summary.get("pair_id") or "")
        variant_id = str(summary.get("variant_id") or "")
        pair = pairs.get(pair_id, {})
        capacity = capacity_rows.get((pair_id, variant_id), {})
        if not pair or not capacity:
            continue
        targets.append(
            {
                "target_id": _slug(f"{pair_id}-{variant_id}"),
                "pair_id": pair_id,
                "variant_id": variant_id,
                "variant_label": summary.get("variant_label") or capacity.get("variant_label"),
                "capacity_run_id": capacity.get("capacity_run_id"),
                "term_names": [str(term) for term in summary.get("term_names") or pair.get("term_names") or []],
                "hit_terms": [str(term) for term in summary.get("hit_terms") or []],
                "missed_terms": [str(term) for term in summary.get("missed_terms") or []],
                "source_hit_count": int(summary.get("hit_count") or 0),
                "source_hit_rate": summary.get("hit_rate"),
                "terms": list_of_dicts(pair.get("terms")),
                "checkpoint_path": capacity.get("checkpoint_path"),
                "tokenizer_path": capacity.get("tokenizer_path"),
                "checkpoint_exists": bool(capacity.get("checkpoint_exists")),
                "tokenizer_exists": bool(capacity.get("tokenizer_exists")),
                "capacity_max_iters": capacity.get("max_iters"),
                "capacity_n_embd": capacity.get("n_embd"),
                "capacity_repeat": capacity.get("repeat"),
            }
        )
    targets.sort(key=lambda row: (-int(row.get("source_hit_count") or 0), str(row.get("target_id") or "")))
    if target_limit is not None and target_limit >= 0:
        return targets[:target_limit]
    return targets


def normalize_decoding_profiles(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(profiles):
        profile_id = _slug(str(item.get("profile_id") or item.get("id") or f"profile-{index + 1}"))
        if not profile_id or profile_id in seen:
            continue
        seen.add(profile_id)
        normalized.append(
            {
                "profile_id": profile_id,
                "label": str(item.get("label") or profile_id),
                "max_new_tokens": max(1, int(item.get("max_new_tokens") or 12)),
                "temperature": float(item.get("temperature") or 0.2),
                "top_k": _optional_int(item.get("top_k")),
                "seed_offset": int(item.get("seed_offset") or index * 100),
            }
        )
    return normalized


def summarize_required_term_pair_decoding_sweep(
    targets: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    profile_target_summaries: list[dict[str, Any]],
    target_summaries: list[dict[str, Any]],
    *,
    source_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_summary or {}
    probe_hits = sum(1 for row in probe_rows if int(row.get("continuation_hit_count") or 0) > 0)
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in probe_rows)
    full_profile_targets = sum(1 for row in profile_target_summaries if row.get("pair_full_hit"))
    partial_profile_targets = sum(1 for row in profile_target_summaries if row.get("pair_partial_hit"))
    recovered_targets = sum(1 for row in target_summaries if row.get("decoding_full_hit_observed"))
    best = _best_profile_target_summary(profile_target_summaries)
    return {
        "pair_decoding_sweep_decision": _decoding_sweep_decision(
            targets,
            profiles,
            probe_rows,
            full_profile_targets,
            partial_profile_targets,
        ),
        "source_pair_capacity_sweep_decision": source.get("pair_capacity_sweep_decision"),
        "source_capacity_full_hit_observed": bool(source.get("capacity_full_hit_observed")),
        "source_variant_pair_partial_hit_count": int(source.get("variant_pair_partial_hit_count") or 0),
        "target_count": len(targets),
        "profile_count": len(profiles),
        "profile_target_count": len(profile_target_summaries),
        "probe_count": len(probe_rows),
        "continuation_hit_count": continuation_hits,
        "probe_hit_count": probe_hits,
        "probe_success_rate": round(probe_hits / len(probe_rows), 4) if probe_rows else 0.0,
        "profile_target_full_hit_count": full_profile_targets,
        "profile_target_partial_hit_count": partial_profile_targets,
        "profile_target_zero_hit_count": max(0, len(profile_target_summaries) - full_profile_targets - partial_profile_targets),
        "profile_target_full_hit_rate": round(full_profile_targets / len(profile_target_summaries), 4)
        if profile_target_summaries
        else 0.0,
        "decoding_full_hit_target_count": recovered_targets,
        "decoding_full_hit_observed": recovered_targets > 0,
        "best_target_id": best.get("target_id"),
        "best_profile_id": best.get("profile_id"),
        "best_profile_hit_count": best.get("hit_count"),
        "best_profile_pair_full_hit": best.get("pair_full_hit"),
    }


def summarize_decoding_profile_probe_rows(
    targets: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target.get("target_id") or "")
        term_names = [str(term) for term in target.get("term_names") or []]
        for profile in profiles:
            profile_id = str(profile.get("profile_id") or "")
            probes = [
                row
                for row in probe_rows
                if str(row.get("target_id") or "") == target_id and str(row.get("profile_id") or "") == profile_id
            ]
            hit_terms = [str(row.get("term") or "") for row in probes if int(row.get("continuation_hit_count") or 0) > 0]
            rows.append(
                {
                    "target_id": target_id,
                    "pair_id": target.get("pair_id"),
                    "variant_id": target.get("variant_id"),
                    "profile_id": profile_id,
                    "profile_label": profile.get("label"),
                    "term_names": term_names,
                    "hit_terms": hit_terms,
                    "missed_terms": [term for term in term_names if term not in hit_terms],
                    "hit_count": len(hit_terms),
                    "hit_rate": round(len(hit_terms) / len(term_names), 4) if term_names else 0.0,
                    "pair_full_hit": bool(term_names) and len(hit_terms) == len(term_names),
                    "pair_partial_hit": 0 < len(hit_terms) < len(term_names),
                }
            )
    return rows


def summarize_pair_decoding_targets(
    targets: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    profile_target_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target.get("target_id") or "")
        target_rows = [row for row in profile_target_summaries if str(row.get("target_id") or "") == target_id]
        full_profiles = [str(row.get("profile_id") or "") for row in target_rows if row.get("pair_full_hit")]
        partial_profiles = [str(row.get("profile_id") or "") for row in target_rows if row.get("pair_partial_hit")]
        best = _best_profile_target_summary(target_rows)
        rows.append(
            {
                "target_id": target_id,
                "pair_id": target.get("pair_id"),
                "variant_id": target.get("variant_id"),
                "term_names": target.get("term_names") or [],
                "source_hit_terms": target.get("hit_terms") or [],
                "source_missed_terms": target.get("missed_terms") or [],
                "profile_count": len(profiles),
                "full_hit_profiles": full_profiles,
                "partial_hit_profiles": partial_profiles,
                "decoding_full_hit_observed": bool(full_profiles),
                "best_profile_id": best.get("profile_id"),
                "best_profile_hit_count": best.get("hit_count"),
                "best_profile_pair_full_hit": best.get("pair_full_hit"),
            }
        )
    return rows


def _run_decoding_profile(
    target: dict[str, Any],
    profile: dict[str, Any],
    *,
    target_index: int,
    profile_index: int,
    seed: int,
    source_base: Path | None,
    device: str,
    generate_func: GenerateFunc | None,
) -> list[dict[str, Any]]:
    checkpoint = resolve_archived_reference_path(target.get("checkpoint_path"), source_base) or Path("")
    tokenizer = resolve_archived_reference_path(target.get("tokenizer_path"), source_base) or Path("")
    training = {
        "status": "pass",
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "checkpoint_exists": checkpoint.is_file(),
        "tokenizer_exists": tokenizer.is_file(),
    }
    rows: list[dict[str, Any]] = []
    generation_seed = int(seed) + int(profile.get("seed_offset") or 0) + target_index * 1000 + profile_index
    for term_index, term_row in enumerate(list_of_dicts(target.get("terms"))):
        generation = _generation_row(
            {
                **term_row,
                "target_id": target.get("target_id"),
                "pair_id": target.get("pair_id"),
                "variant_id": target.get("variant_id"),
                "profile_id": profile.get("profile_id"),
                "profile_label": profile.get("label"),
                "capacity_run_id": target.get("capacity_run_id"),
                "pair_terms": target.get("term_names") or [],
                "source_hit_terms": target.get("hit_terms") or [],
                "source_missed_terms": target.get("missed_terms") or [],
            },
            training,
            index=term_index,
            max_new_tokens=int(profile["max_new_tokens"]),
            temperature=float(profile["temperature"]),
            top_k=profile.get("top_k"),
            generation_seed=generation_seed,
            device=device,
            generate_func=generate_func,
        )
        rows.append(
            {
                **generation,
                "target_id": target.get("target_id"),
                "pair_id": target.get("pair_id"),
                "variant_id": target.get("variant_id"),
                "profile_id": profile.get("profile_id"),
                "profile_label": profile.get("label"),
                "capacity_run_id": target.get("capacity_run_id"),
                "checkpoint_path": str(checkpoint),
                "tokenizer_path": str(tokenizer),
                "checkpoint_exists": checkpoint.is_file(),
                "tokenizer_exists": tokenizer.is_file(),
            }
        )
    return rows


def _input_issues(report: dict[str, Any], targets: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    source_summary = as_dict(report.get("summary"))
    if not report:
        issues.append("source pair capacity sweep report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source pair capacity sweep report is not pass")
    if report and source_summary.get("pair_capacity_sweep_decision") != "pair_capacity_sweep_partial_only":
        issues.append("source pair capacity sweep is not the expected partial-only decoding target")
    if report and bool(source_summary.get("capacity_full_hit_observed")):
        issues.append("source pair capacity sweep already recovered full-hit behavior")
    if not targets:
        issues.append("source pair capacity sweep has no partial variants to decode")
    if not profiles:
        issues.append("at least one decoding profile is required")
    return issues


def _decoding_sweep_decision(
    targets: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    full_profile_target_count: int,
    partial_profile_target_count: int,
) -> str:
    if not targets:
        return "no_partial_capacity_variants_selected"
    if not profiles:
        return "no_decoding_profiles_configured"
    if not probe_rows:
        return "pair_decoding_sweep_generation_missing"
    if full_profile_target_count > 0:
        return "pair_decoding_sweep_full_hit_recovered"
    if partial_profile_target_count > 0:
        return "pair_decoding_sweep_partial_only"
    return "pair_decoding_sweep_not_recovered"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_decoding_sweep"
    if summary.get("decoding_full_hit_observed"):
        return "required_term_pair_decoding_sweep_recovered"
    if int(summary.get("profile_target_partial_hit_count") or 0) > 0:
        return "required_term_pair_decoding_sweep_partial"
    return "required_term_pair_decoding_sweep_not_recovered"


def _source_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_capacity_sweep_decision": summary.get("pair_capacity_sweep_decision"),
        "variant_pair_full_hit_count": summary.get("variant_pair_full_hit_count"),
        "variant_pair_partial_hit_count": summary.get("variant_pair_partial_hit_count"),
        "capacity_full_hit_observed": summary.get("capacity_full_hit_observed"),
        "best_variant_id": summary.get("best_variant_id"),
        "best_variant_hit_count": summary.get("best_variant_hit_count"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("decoding_full_hit_observed"):
        return "pair_decoding_recovered_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The decoding sweep input failed validation, so no decoding conclusion is available."
    if summary.get("decoding_full_hit_observed"):
        return "At least one decoding profile recovered both required terms from an existing v497 checkpoint."
    if int(summary.get("profile_target_partial_hit_count") or 0) > 0:
        return "Decoding changes still produced only partial pair hits from the existing v497 checkpoints."
    return "No decoding profile emitted required terms in continuation for the selected partial variants."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair the decoding sweep source or profile configuration before changing model capacity"
    if summary.get("decoding_full_hit_observed"):
        return "repeat the recovered decoding profile across seeds before changing corpus design"
    if int(summary.get("profile_target_partial_hit_count") or 0) > 0:
        return "inspect prompt target separation and corpus row design before training larger pair checkpoints"
    return "return to corpus construction because decoding alone did not expose the missing pair terms"


def _best_profile_target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return sorted(
        rows,
        key=lambda row: (
            int(bool(row.get("pair_full_hit"))),
            int(row.get("hit_count") or 0),
            str(row.get("profile_id") or ""),
        ),
        reverse=True,
    )[0]


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "pair-decoding"


__all__ = [
    "DEFAULT_PAIR_DECODING_SWEEP_SEED",
    "REQUIRED_TERM_PAIR_DECODING_SWEEP_HTML_FILENAME",
    "REQUIRED_TERM_PAIR_DECODING_SWEEP_JSON_FILENAME",
    "REQUIRED_TERM_PAIR_DECODING_SWEEP_MARKDOWN_FILENAME",
    "REQUIRED_TERM_PAIR_DECODING_SWEEP_TEXT_FILENAME",
    "normalize_decoding_profiles",
    "resolve_exit_code",
    "select_pair_decoding_sweep_targets",
    "summarize_decoding_profile_probe_rows",
    "summarize_pair_decoding_targets",
    "summarize_required_term_pair_decoding_sweep",
]
