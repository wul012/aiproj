from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.registry import build_run_registry, discover_run_dirs, write_registry_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a registry index from MiniGPT run directories.")
    parser.add_argument("run_dirs", type=Path, nargs="*", help="Run directories to register")
    parser.add_argument("--discover", type=Path, default=None, help="Discover run directories under this parent")
    parser.add_argument("--no-recursive", action="store_true", help="Only discover direct child run directories")
    parser.add_argument("--name", action="append", default=[], help="Optional display name, repeat once per run")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "registry")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dirs = list(args.run_dirs)
    if args.discover is not None:
        run_dirs.extend(discover_run_dirs(args.discover, recursive=not args.no_recursive))
    if not run_dirs:
        raise ValueError("provide run directories or --discover")
    names = args.name or None
    if names is not None and len(names) != len(run_dirs):
        raise ValueError("--name must be repeated exactly once per registered run")

    registry = build_run_registry(run_dirs, names=names)
    outputs = write_registry_outputs(registry, args.out_dir)
    print(f"run_count={registry['run_count']}")
    print("best_by_best_val_loss=" + json.dumps(registry["best_by_best_val_loss"], ensure_ascii=False))
    print("loss_leaderboard=" + json.dumps(registry.get("loss_leaderboard", []), ensure_ascii=False))
    print("quality_counts=" + json.dumps(registry["quality_counts"], ensure_ascii=False))
    print("generation_quality_counts=" + json.dumps(registry.get("generation_quality_counts", {}), ensure_ascii=False))
    print("benchmark_rubric_counts=" + json.dumps(registry.get("benchmark_rubric_counts", {}), ensure_ascii=False))
    print("benchmark_rubric_summary=" + json.dumps(registry.get("benchmark_rubric_summary", {}), ensure_ascii=False))
    print("dataset_versions=" + json.dumps(registry.get("dataset_versions", []), ensure_ascii=False))
    print("dataset_dedupe_policy_counts=" + json.dumps(registry.get("dataset_dedupe_policy_counts", {}), ensure_ascii=False))
    print("dataset_snapshot_summary=" + json.dumps(registry.get("dataset_snapshot_summary", {}), ensure_ascii=False))
    print("release_readiness_comparison_counts=" + json.dumps(registry.get("release_readiness_comparison_counts", {}), ensure_ascii=False))
    print("release_readiness_delta_summary=" + json.dumps(registry.get("release_readiness_delta_summary", {}), ensure_ascii=False))
    print(
        "release_readiness_coverage_regressions="
        + json.dumps(registry.get("release_readiness_delta_summary", {}).get("test_coverage_regression_count", 0), ensure_ascii=False)
    )
    print(
        "release_readiness_ci_order_regressions="
        + json.dumps(registry.get("release_readiness_delta_summary", {}).get("ci_workflow_order_regression_count", 0), ensure_ascii=False)
    )
    print(
        "release_readiness_benchmark_history_regressions="
        + json.dumps(registry.get("release_readiness_delta_summary", {}).get("benchmark_history_regression_count", 0), ensure_ascii=False)
    )
    print(
        "release_readiness_benchmark_requirement_status_changes="
        + json.dumps(
            registry.get("release_readiness_delta_summary", {}).get("benchmark_history_readiness_requirement_status_changed_count", 0),
            ensure_ascii=False,
        )
    )
    print(
        "release_readiness_benchmark_requirement_exit_delta_max="
        + json.dumps(
            registry.get("release_readiness_delta_summary", {}).get("max_abs_benchmark_history_readiness_requirement_exit_code_delta"),
            ensure_ascii=False,
        )
    )
    print(
        "release_readiness_benchmark_requirement_failed_reason_added_count="
        + json.dumps(
            registry.get("release_readiness_delta_summary", {}).get("benchmark_history_readiness_requirement_failed_reason_added_count", 0),
            ensure_ascii=False,
        )
    )
    print(
        "release_readiness_benchmark_requirement_failed_reason_removed_count="
        + json.dumps(
            registry.get("release_readiness_delta_summary", {}).get("benchmark_history_readiness_requirement_failed_reason_removed_count", 0),
            ensure_ascii=False,
        )
    )
    print(
        "release_readiness_benchmark_requirement_failed_reason_removed="
        + json.dumps(
            registry.get("release_readiness_delta_summary", {}).get("benchmark_history_readiness_requirement_failed_reason_removed", []),
            ensure_ascii=False,
        )
    )
    print(
        "release_readiness_benchmark_requirement_failed_reason_recovery_delta_count="
        + json.dumps(
            registry.get("release_readiness_delta_summary", {}).get(
                "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count",
                0,
            ),
            ensure_ascii=False,
        )
    )
    print(
        "release_readiness_benchmark_requirement_failed_reason_mixed_delta_count="
        + json.dumps(
            registry.get("release_readiness_delta_summary", {}).get(
                "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count",
                0,
            ),
            ensure_ascii=False,
        )
    )
    print(
        "release_readiness_benchmark_requirement_failed_reason_drift_status_counts="
        + json.dumps(
            registry.get("release_readiness_delta_summary", {}).get(
                "benchmark_history_readiness_requirement_failed_reason_drift_status_counts",
                {},
            ),
            ensure_ascii=False,
        )
    )
    print("tag_counts=" + json.dumps(registry.get("tag_counts", {}), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
