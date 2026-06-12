from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.model_capability_regression_suite_readiness import (  # noqa: E402
    build_model_capability_regression_suite_readiness,
    locate_suite_manifest,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_suite_readiness_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check readiness for a MiniGPT model capability regression suite manifest.")
    parser.add_argument("suite", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-regression-suite-readiness-v1138")
    parser.add_argument("--require-readiness-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    suite_path = locate_suite_manifest(args.suite)
    report = build_model_capability_regression_suite_readiness(read_json_report(suite_path), suite_path=suite_path)
    outputs = write_model_capability_regression_suite_readiness_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"readiness_ready={summary['readiness_ready']}")
    print(f"ready_item_count={summary['ready_item_count']}")
    print(f"suite_item_count={summary['suite_item_count']}")
    print(f"next_step={summary['next_step']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_readiness_ready=args.require_readiness_ready)


if __name__ == "__main__":
    raise SystemExit(main())
