from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc
from minigpt.model_capability_required_term_pair_capacity_sweep import (
    REQUIRED_TERM_PAIR_CAPACITY_SWEEP_JSON_FILENAME,
    read_json_report as read_json_report,
)
from minigpt.model_capability_required_term_pair_decoding_sweep_core import (
    DEFAULT_PAIR_DECODING_SWEEP_SEED,
    REQUIRED_TERM_PAIR_DECODING_SWEEP_HTML_FILENAME as REQUIRED_TERM_PAIR_DECODING_SWEEP_HTML_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_SWEEP_JSON_FILENAME as REQUIRED_TERM_PAIR_DECODING_SWEEP_JSON_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_SWEEP_MARKDOWN_FILENAME as REQUIRED_TERM_PAIR_DECODING_SWEEP_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_SWEEP_TEXT_FILENAME as REQUIRED_TERM_PAIR_DECODING_SWEEP_TEXT_FILENAME,
    _decision,
    _input_issues,
    _interpretation_reason,
    _model_quality_claim,
    _next_action,
    _run_decoding_profile,
    _source_baseline,
    normalize_decoding_profiles,
    resolve_exit_code as resolve_exit_code,
    select_pair_decoding_sweep_targets,
    summarize_decoding_profile_probe_rows,
    summarize_pair_decoding_targets,
    summarize_required_term_pair_decoding_sweep,
)
from minigpt.report_utils import as_dict, utc_now


def locate_model_capability_required_term_pair_decoding_sweep_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_CAPACITY_SWEEP_JSON_FILENAME
    return source


def default_pair_decoding_profiles() -> list[dict[str, Any]]:
    return [
        {
            "profile_id": "deterministic-12",
            "label": "v497 deterministic short continuation",
            "max_new_tokens": 12,
            "temperature": 0.2,
            "top_k": 1,
            "seed_offset": 0,
        },
        {
            "profile_id": "deterministic-24",
            "label": "longer deterministic continuation",
            "max_new_tokens": 24,
            "temperature": 0.2,
            "top_k": 1,
            "seed_offset": 100,
        },
        {
            "profile_id": "sample-top5-24",
            "label": "moderate top-k sampling",
            "max_new_tokens": 24,
            "temperature": 0.7,
            "top_k": 5,
            "seed_offset": 200,
        },
        {
            "profile_id": "sample-open-24",
            "label": "open sampling",
            "max_new_tokens": 24,
            "temperature": 0.8,
            "top_k": None,
            "seed_offset": 300,
        },
    ]


def build_model_capability_required_term_pair_decoding_sweep(
    pair_capacity_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seed: int = DEFAULT_PAIR_DECODING_SWEEP_SEED,
    target_limit: int | None = 2,
    decoding_profiles: list[dict[str, Any]] | None = None,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_summary = as_dict(pair_capacity_report.get("summary"))
    profile_source = default_pair_decoding_profiles() if decoding_profiles is None else decoding_profiles
    profiles = normalize_decoding_profiles(profile_source)
    source_base = Path(source_path).parent if source_path else None
    targets = select_pair_decoding_sweep_targets(pair_capacity_report, target_limit=target_limit)
    issues = _input_issues(pair_capacity_report, targets, profiles)

    probe_rows: list[dict[str, Any]] = []
    if not issues:
        for target_index, target in enumerate(targets):
            for profile_index, profile in enumerate(profiles):
                probe_rows.extend(
                    _run_decoding_profile(
                        target,
                        profile,
                        target_index=target_index,
                        profile_index=profile_index,
                        seed=seed,
                        source_base=source_base,
                        device=device,
                        generate_func=generate_func,
                    )
                )

    profile_target_summaries = summarize_decoding_profile_probe_rows(targets, profiles, probe_rows)
    target_summaries = summarize_pair_decoding_targets(targets, profiles, profile_target_summaries)
    summary = summarize_required_term_pair_decoding_sweep(
        targets,
        profiles,
        probe_rows,
        profile_target_summaries,
        target_summaries,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair decoding sweep",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_capacity_sweep": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seed": int(seed),
            "target_limit": target_limit,
            "profile_count": len(profiles),
            "device": device,
            "experiment_boundary": "reuse v497 capacity checkpoints and sweep decoding before adding more training",
        },
        "source_baseline": _source_baseline(source_summary),
        "summary": summary,
        "target_count": len(targets),
        "targets": targets,
        "decoding_profiles": profiles,
        "profile_target_summaries": profile_target_summaries,
        "target_summaries": target_summaries,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


# Execution and aggregation helpers are re-exported from the core module.
