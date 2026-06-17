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

from minigpt.grok_paired_contrast_v1182 import (  # noqa: E402
    build_grok_paired_contrast_report,
    resolve_exit_code,
    write_grok_paired_contrast_outputs,
)
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build paired seed contrasts from a v1181 grokking phase report.")
    parser.add_argument("phase_report", type=Path, help="Path to grok_trajectory_phases_v1181.json or its output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "grok-paired-contrast-v1182")
    parser.add_argument("--min-final-val-gain", type=float, default=0.70)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    prepare_output_dir(args.out_dir, force=args.force)
    report = build_grok_paired_contrast_report(args.phase_report, min_final_val_gain=args.min_final_val_gain)
    outputs = write_grok_paired_contrast_outputs(report, args.out_dir)
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
