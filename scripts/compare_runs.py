from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.comparison import build_comparison_report, write_comparison_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare multiple MiniGPT run directories.")
    parser.add_argument("run_dirs", type=Path, nargs="+")
    parser.add_argument("--name", action="append", default=[], help="Optional display name, repeat once per run")
    parser.add_argument("--out-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    names = args.name or None
    if names is not None and len(names) != len(args.run_dirs):
        raise ValueError("--name must be repeated exactly once per run directory")

    out_dir = args.out_dir or Path(args.run_dirs[0]).parent / "comparison"
    report = build_comparison_report(args.run_dirs, names=names)
    outputs = write_comparison_outputs(report, out_dir)

    print(f"run_count={report['run_count']}")
    print("best_by_best_val_loss=" + json.dumps(report["best_by_best_val_loss"], ensure_ascii=False))
    print("best_by_eval_loss=" + json.dumps(report["best_by_eval_loss"], ensure_ascii=False))
    for key, path in outputs.items():
        print(f"saved_{key}={path}")


if __name__ == "__main__":
    main()
