from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.model_capability_regression_loop_trend import (  # noqa: E402
    build_model_capability_regression_loop_trend,
    load_model_capability_regression_loop_reports,
    resolve_exit_code,
    write_model_capability_regression_loop_trend_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only trend report for the v1135-v1139 regression loop.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-regression-loop-trend-v1141")
    parser.add_argument("--require-loop-closed", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    report = build_model_capability_regression_loop_trend(load_model_capability_regression_loop_reports(args.root))
    outputs = write_model_capability_regression_loop_trend_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"loop_closed={summary['loop_closed']}")
    print(f"stage_count={summary['stage_count']}")
    print(f"ready_stage_count={summary['ready_stage_count']}")
    print(f"artifact_present_count={summary['artifact_present_count']}")
    print(f"closeout_ready={summary['closeout_ready']}")
    print(f"next_step={summary['next_step']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_loop_closed=args.require_loop_closed)


if __name__ == "__main__":
    raise SystemExit(main())
