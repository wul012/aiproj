from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic,
    locate_benchmark_suite,
    locate_checkpoint_comparison,
    locate_seed_revision,
    locate_training_revision,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_text,
    write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose prompt/corpus alignment after bounded real replay repair failure.")
    parser.add_argument("--benchmark-suite", type=Path, required=True, help="Bounded benchmark suite JSON or output directory.")
    parser.add_argument("--comparison", type=Path, required=True, help="Repair checkpoint comparison JSON or output directory.")
    parser.add_argument("--seed-revision", type=Path, required=True, help="Repair seed revision JSON or output directory.")
    parser.add_argument("--training-revision", type=Path, required=True, help="Repair training revision JSON or output directory.")
    parser.add_argument("--corpus", type=Path, required=True, help="Seed revision corpus text file.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-failure-alignment-diagnostic")
    parser.add_argument("--require-diagnostic-ready", action="store_true", help="Return exit code 1 when diagnostic is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    suite_path = locate_benchmark_suite(args.benchmark_suite)
    comparison_path = locate_checkpoint_comparison(args.comparison)
    seed_path = locate_seed_revision(args.seed_revision)
    training_path = locate_training_revision(args.training_revision)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic(
        read_json_report(suite_path),
        read_json_report(comparison_path),
        read_json_report(seed_path),
        read_json_report(training_path),
        corpus_path=args.corpus,
        benchmark_suite_path=suite_path,
        comparison_path=comparison_path,
        seed_revision_path=seed_path,
        training_revision_path=training_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_diagnostic_ready=args.require_diagnostic_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
