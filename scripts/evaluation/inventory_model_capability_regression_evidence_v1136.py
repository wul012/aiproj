from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.model_capability_regression_inventory import (  # noqa: E402
    build_model_capability_regression_inventory,
    locate_regression_plan,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_inventory_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory existing evidence for a MiniGPT model capability regression plan.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-regression-inventory-v1136")
    parser.add_argument("--require-inventory-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    plan_path = locate_regression_plan(args.plan)
    report = build_model_capability_regression_inventory(read_json_report(plan_path), root=args.root, plan_path=plan_path)
    outputs = write_model_capability_regression_inventory_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"inventory_ready={summary['inventory_ready']}")
    print(f"planned_item_count={summary['planned_item_count']}")
    print(f"ready_item_count={summary['ready_item_count']}")
    print(f"next_step={summary['next_step']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_inventory_ready=args.require_inventory_ready)


if __name__ == "__main__":
    raise SystemExit(main())
