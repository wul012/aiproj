from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.model_capability_regression_plan import (  # noqa: E402
    build_model_capability_regression_plan,
    locate_cadence_report,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_plan_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a MiniGPT model capability regression from a cadence watch report.")
    parser.add_argument("cadence", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-regression-plan-v1135")
    parser.add_argument("--require-plan-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    cadence_path = locate_cadence_report(args.cadence)
    report = build_model_capability_regression_plan(read_json_report(cadence_path), cadence_path=cadence_path)
    outputs = write_model_capability_regression_plan_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"plan_ready={summary['plan_ready']}")
    print(f"regression_item_count={summary['regression_item_count']}")
    print(f"source_next_action={summary['source_next_action']}")
    print(f"next_step={summary['next_step']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_plan_ready=args.require_plan_ready)


if __name__ == "__main__":
    raise SystemExit(main())
