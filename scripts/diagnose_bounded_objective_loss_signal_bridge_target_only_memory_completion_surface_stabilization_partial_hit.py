from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic import (  # noqa: E402
    build_completion_surface_stabilization_partial_hit_diagnostic,
    locate_completion_surface_stabilization_replay_comparison,
    locate_loss_suffix_replay_regression_diagnostic,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic_artifacts import (  # noqa: E402
    render_completion_surface_stabilization_partial_hit_diagnostic_text,
    write_completion_surface_stabilization_partial_hit_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose completion-surface stabilization partial hits after replay.")
    parser.add_argument("--replay-comparison", type=Path, required=True)
    parser.add_argument("--regression-diagnostic", type=Path, required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-completion-surface-stabilization-partial-hit-diagnostic",
    )
    parser.add_argument("--require-diagnostic-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_completion_surface_stabilization_replay_comparison(args.replay_comparison)
    regression_path = locate_loss_suffix_replay_regression_diagnostic(args.regression_diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_completion_surface_stabilization_partial_hit_diagnostic(
        read_json_report(replay_path),
        read_json_report(regression_path),
        replay_comparison_path=replay_path,
        regression_diagnostic_path=regression_path,
    )
    outputs = write_completion_surface_stabilization_partial_hit_diagnostic_outputs(report, args.out_dir)
    print(render_completion_surface_stabilization_partial_hit_diagnostic_text(report), end="")
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
