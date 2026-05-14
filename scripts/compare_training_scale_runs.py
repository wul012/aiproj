from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_run_comparison import (  # noqa: E402
    build_training_scale_run_comparison,
    write_training_scale_run_comparison_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare MiniGPT gated training scale run reports.")
    parser.add_argument("runs", nargs="+", type=Path, help="training_scale_run.json files or run directories")
    parser.add_argument("--name", action="append", default=None, help="Display name for each run; repeat once per input")
    parser.add_argument("--baseline", type=str, default=None, help="Baseline run name or zero-based index. Defaults to first run.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "training-scale-run-comparison")
    parser.add_argument("--title", type=str, default="MiniGPT training scale run comparison")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline: str | int | None = args.baseline
    if isinstance(baseline, str) and baseline.isdigit():
        baseline = int(baseline)
    report = build_training_scale_run_comparison(
        args.runs,
        names=args.name,
        baseline=baseline,
        title=args.title,
    )
    outputs = write_training_scale_run_comparison_outputs(report, args.out_dir)
    print(f"run_count={report.get('run_count')}")
    print(f"baseline={report.get('baseline', {}).get('name')}")
    print("summary=" + json.dumps(report.get("summary", {}), ensure_ascii=False))
    print("best_by_readiness=" + json.dumps(report.get("best_by_readiness", {}), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
