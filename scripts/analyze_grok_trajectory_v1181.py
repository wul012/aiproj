from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.grok_trajectory_phases_v1181 import (  # noqa: E402
    build_grok_trajectory_phase_report,
    resolve_exit_code,
    write_grok_trajectory_phase_outputs,
)
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compress a v1179 grokking report into row-level trajectory phases.")
    parser.add_argument("grok_report", type=Path, help="Path to grok_v1179.json or its output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "grok-trajectory-phases-v1181")
    parser.add_argument("--min-gap-steps", type=int, default=1000)
    parser.add_argument("--low-val-threshold", type=float, default=0.5)
    parser.add_argument("--min-wd-on-low-plateau-rate", type=float, default=0.70)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    prepare_output_dir(args.out_dir, force=args.force)
    report = build_grok_trajectory_phase_report(
        args.grok_report,
        min_gap_steps=args.min_gap_steps,
        low_val_threshold=args.low_val_threshold,
        min_wd_on_low_plateau_rate=args.min_wd_on_low_plateau_rate,
    )
    outputs = write_grok_trajectory_phase_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    return resolve_exit_code(report, require_pass=args.require_pass)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"Output directory already exists: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
