from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic import (  # noqa: E402
    build_pair_binding_zero_hit_diagnostic,
    locate_pair_binding_replay_comparison,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic_artifacts import (  # noqa: E402
    render_pair_binding_zero_hit_diagnostic_text,
    write_pair_binding_zero_hit_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose zero-hit pair-binding replay.")
    parser.add_argument("--replay-comparison", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-pair-binding-zero-hit-diagnostic")
    parser.add_argument("--require-diagnostic-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_pair_binding_replay_comparison(args.replay_comparison)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_pair_binding_zero_hit_diagnostic(read_json_report(replay_path), replay_comparison_path=replay_path)
    outputs = write_pair_binding_zero_hit_diagnostic_outputs(report, args.out_dir)
    print(render_pair_binding_zero_hit_diagnostic_text(report), end="")
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
