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

from minigpt.grok_wd_law_check_v1184 import (  # noqa: E402
    build_grok_wd_law_check,
    resolve_exit_code,
    write_grok_wd_law_check_outputs,
)
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the v1183 grokking weight-decay dose-response artifact.")
    parser.add_argument("wd_law_report", type=Path, help="Path to grok_wd_law_v1183.json or its output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "grok-wd-law-check-v1184")
    parser.add_argument("--grok-rate-threshold", type=float, default=0.6)
    parser.add_argument("--min-fastest-gap-steps", type=int, default=1000)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    prepare_output_dir(args.out_dir, force=args.force)
    report = build_grok_wd_law_check(
        args.wd_law_report,
        grok_rate_threshold=args.grok_rate_threshold,
        min_fastest_gap_steps=args.min_fastest_gap_steps,
    )
    outputs = write_grok_wd_law_check_outputs(report, args.out_dir)
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
