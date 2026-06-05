from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic import (  # noqa: E402
    build_loss_suffix_replay_regression_diagnostic,
    locate_baseline_target_only_memory_replay_comparison,
    locate_current_loss_suffix_replay_comparison,
    read_json_report,
    read_sample_text,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_artifacts import (  # noqa: E402
    render_loss_suffix_replay_regression_diagnostic_text,
    write_loss_suffix_replay_regression_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose sample-success versus replay-contract regression for the loss-suffix target-only memory checkpoint.")
    parser.add_argument("--current-replay-comparison", type=Path, required=True)
    parser.add_argument("--baseline-replay-comparison", type=Path, required=True)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-replay-regression-diagnostic",
    )
    parser.add_argument("--require-diagnostic-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    current_path = locate_current_loss_suffix_replay_comparison(args.current_replay_comparison)
    baseline_path = locate_baseline_target_only_memory_replay_comparison(args.baseline_replay_comparison)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_loss_suffix_replay_regression_diagnostic(
        read_json_report(current_path),
        read_json_report(baseline_path),
        read_sample_text(args.sample),
        current_replay_comparison_path=current_path,
        baseline_replay_comparison_path=baseline_path,
        sample_path=args.sample,
    )
    outputs = write_loss_suffix_replay_regression_diagnostic_outputs(report, args.out_dir)
    print(render_loss_suffix_replay_regression_diagnostic_text(report), end="")
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
