from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.model_capability_regression_followup_closeout import (  # noqa: E402
    build_model_capability_regression_followup_closeout,
    locate_readiness_report,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_followup_closeout_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Close the pre-execution MiniGPT model capability regression follow-up.")
    parser.add_argument("readiness", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-regression-followup-closeout-v1139")
    parser.add_argument("--require-closeout-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    readiness_path = locate_readiness_report(args.readiness)
    report = build_model_capability_regression_followup_closeout(read_json_report(readiness_path), readiness_path=readiness_path)
    outputs = write_model_capability_regression_followup_closeout_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"closeout_ready={summary['closeout_ready']}")
    print(f"ready_item_count={summary['ready_item_count']}")
    print(f"closed_stage={summary['closed_stage']}")
    print(f"next_step={summary['next_step']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_closeout_ready=args.require_closeout_ready)


if __name__ == "__main__":
    raise SystemExit(main())
