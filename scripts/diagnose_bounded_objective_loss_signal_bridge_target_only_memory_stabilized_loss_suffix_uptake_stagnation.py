from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic import (  # noqa: E402
    build_stabilized_loss_suffix_uptake_stagnation_diagnostic,
    locate_completion_surface_stabilization_replay_comparison,
    locate_stabilized_loss_suffix_uptake_replay_comparison,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic_artifacts import (  # noqa: E402
    render_stabilized_loss_suffix_uptake_stagnation_diagnostic_text,
    write_stabilized_loss_suffix_uptake_stagnation_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose whether stabilized loss-suffix uptake replay changed from the prior fixed-l partial state.")
    parser.add_argument("--baseline-replay-comparison", type=Path, required=True)
    parser.add_argument("--current-replay-comparison", type=Path, required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-stabilized-loss-suffix-uptake-stagnation-diagnostic",
    )
    parser.add_argument("--require-diagnostic-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    baseline_path = locate_completion_surface_stabilization_replay_comparison(args.baseline_replay_comparison)
    current_path = locate_stabilized_loss_suffix_uptake_replay_comparison(args.current_replay_comparison)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_stabilized_loss_suffix_uptake_stagnation_diagnostic(
        read_json_report(baseline_path),
        read_json_report(current_path),
        baseline_replay_comparison_path=baseline_path,
        current_replay_comparison_path=current_path,
    )
    outputs = write_stabilized_loss_suffix_uptake_stagnation_diagnostic_outputs(report, args.out_dir)
    print(render_stabilized_loss_suffix_uptake_stagnation_diagnostic_text(report), end="")
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
