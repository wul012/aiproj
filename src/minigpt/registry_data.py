from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.registry_rankings import (
    annotate_loss_leaderboard,
    annotate_rubric_leaderboard,
    benchmark_rubric_summary,
    best_registered_run,
    collect_pair_delta_rows,
    collect_release_readiness_delta_rows,
    counts,
    pair_delta_leaderboard,
    pair_delta_summary,
    release_readiness_delta_leaderboard,
    release_readiness_delta_summary,
)
from minigpt.registry_run_summary import (
    REGISTRY_ARTIFACT_PATHS,
    RegisteredRun,
    _as_int,
    _as_optional_float,
    _as_str_list,
    _pick,
    summarize_registered_run,
)


def discover_run_dirs(root: str | Path, recursive: bool = True) -> list[Path]:
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(base)
    if base.is_file():
        raise ValueError(f"run discovery root must be a directory: {base}")
    candidates = base.rglob("run_manifest.json") if recursive else base.glob("*/run_manifest.json")
    runs = sorted({path.parent.resolve(): path.parent for path in candidates}.values(), key=lambda item: str(item))
    return runs


def build_run_registry(run_dirs: list[str | Path], names: list[str] | None = None) -> dict[str, Any]:
    if not run_dirs:
        raise ValueError("at least one run directory is required")
    if names is not None and len(names) != len(run_dirs):
        raise ValueError("names length must match run_dirs length")
    runs = [
        summarize_registered_run(run_dir, None if names is None else names[index])
        for index, run_dir in enumerate(run_dirs)
    ]
    run_rows = [run.to_dict() for run in runs]
    loss_leaderboard = annotate_loss_leaderboard(run_rows)
    rubric_leaderboard = annotate_rubric_leaderboard(run_rows)
    pair_delta_rows = collect_pair_delta_rows(run_dirs, names)
    pair_delta_leaders = pair_delta_leaderboard(pair_delta_rows)
    release_readiness_delta_rows = collect_release_readiness_delta_rows(run_dirs, names)
    release_readiness_delta_leaders = release_readiness_delta_leaderboard(release_readiness_delta_rows)
    return {
        "schema_version": 1,
        "run_count": len(runs),
        "runs": run_rows,
        "best_by_best_val_loss": best_registered_run(runs, "best_val_loss"),
        "loss_leaderboard": loss_leaderboard,
        "benchmark_rubric_leaderboard": rubric_leaderboard,
        "benchmark_rubric_summary": benchmark_rubric_summary(rubric_leaderboard),
        "pair_delta_summary": pair_delta_summary(pair_delta_rows),
        "pair_delta_leaderboard": pair_delta_leaders,
        "release_readiness_delta_summary": release_readiness_delta_summary(release_readiness_delta_rows),
        "release_readiness_delta_leaderboard": release_readiness_delta_leaders,
        "dataset_versions": sorted({run.dataset_version for run in runs if run.dataset_version}),
        "dataset_fingerprints": sorted({run.dataset_fingerprint for run in runs if run.dataset_fingerprint}),
        "dataset_dedupe_policy_counts": counts(run.dataset_dedupe_policy or "missing" for run in runs),
        "dataset_snapshot_summary": _dataset_snapshot_summary(run_rows),
        "quality_counts": counts(run.dataset_quality or "missing" for run in runs),
        "generation_quality_counts": counts(run.generation_quality_status or "missing" for run in runs),
        "benchmark_rubric_counts": counts(run.benchmark_rubric_status or "missing" for run in runs),
        "release_readiness_comparison_counts": counts(run.release_readiness_comparison_status or "missing" for run in runs),
        "pair_report_counts": {
            "pair_batch": sum(1 for run in run_rows if run.get("pair_batch_cases") is not None or run.get("pair_batch_html_exists")),
            "pair_trend": sum(1 for run in run_rows if run.get("pair_trend_reports") is not None or run.get("pair_trend_html_exists")),
        },
        "tag_counts": counts(tag for run in runs for tag in run.tags),
    }


def _dataset_snapshot_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    included = [_as_int(run.get("dataset_included_source_count")) for run in runs]
    skipped = [_as_int(run.get("dataset_skipped_source_count")) for run in runs]
    chars = [_as_int(run.get("dataset_char_count")) for run in runs]
    included_values = [value for value in included if value is not None]
    skipped_values = [value for value in skipped if value is not None]
    char_values = [value for value in chars if value is not None]
    return {
        "run_count": len(runs),
        "snapshot_run_count": sum(
            1
            for run in runs
            if run.get("dataset_dedupe_policy") is not None
            or run.get("dataset_source_order_digest") is not None
            or run.get("dataset_included_source_count") is not None
            or run.get("dataset_skipped_source_count") is not None
            or run.get("dataset_char_count") is not None
        ),
        "missing_snapshot_count": sum(
            1
            for run in runs
            if run.get("dataset_dedupe_policy") is None
            and run.get("dataset_source_order_digest") is None
            and run.get("dataset_included_source_count") is None
            and run.get("dataset_skipped_source_count") is None
            and run.get("dataset_char_count") is None
        ),
        "dataset_version_count": len({run.get("dataset_version") for run in runs if run.get("dataset_version")}),
        "dataset_fingerprint_count": len({run.get("dataset_fingerprint") for run in runs if run.get("dataset_fingerprint")}),
        "dedupe_policy_count": len({run.get("dataset_dedupe_policy") for run in runs if run.get("dataset_dedupe_policy")}),
        "source_order_digest_count": len({run.get("dataset_source_order_digest") for run in runs if run.get("dataset_source_order_digest")}),
        "skipped_source_run_count": sum(1 for value in skipped_values if value > 0),
        "total_included_source_count": sum(included_values) if included_values else None,
        "total_skipped_source_count": sum(skipped_values) if skipped_values else None,
        "total_char_count": sum(char_values) if char_values else None,
    }
