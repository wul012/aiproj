from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (  # noqa: E402
    build_tokenizer_coverage_aware_holdout_suite,
    locate_holdout_gap_diagnostic,
    locate_source_benchmark_suite,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_artifacts import (  # noqa: E402
    render_tokenizer_coverage_aware_holdout_suite_text,
    write_tokenizer_coverage_aware_holdout_suite_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a tokenizer-coverage-aware holdout suite after v897 gap diagnosis.")
    parser.add_argument("--holdout-gap-diagnostic", type=Path, required=True, help="v897 holdout gap diagnostic JSON or output directory.")
    parser.add_argument("--source-benchmark-suite", type=Path, required=True, help="v803 source benchmark suite JSON or output directory.")
    parser.add_argument("--tokenizer", type=Path, required=True, help="Tokenizer JSON whose vocabulary must cover candidate prompts.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-suite",
    )
    parser.add_argument("--require-suite-ready", action="store_true", help="Return exit code 1 when suite construction fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    diagnostic_path = locate_holdout_gap_diagnostic(args.holdout_gap_diagnostic)
    suite_path = locate_source_benchmark_suite(args.source_benchmark_suite)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_tokenizer_coverage_aware_holdout_suite(
        read_json_report(diagnostic_path),
        read_json_report(suite_path),
        tokenizer_path=args.tokenizer,
        holdout_gap_diagnostic_path=diagnostic_path,
        source_benchmark_suite_path=suite_path,
    )
    outputs = write_tokenizer_coverage_aware_holdout_suite_outputs(report, args.out_dir)
    print(render_tokenizer_coverage_aware_holdout_suite_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_suite_ready=args.require_suite_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
