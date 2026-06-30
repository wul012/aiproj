from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

from minigpt.evaluation.comparison import build_comparison_report, write_comparison_outputs


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare multiple MiniGPT run directories.")
    parser.add_argument("run_dirs", type=Path, nargs="+")
    parser.add_argument("--name", action="append", default=[], help="Optional display name, repeat once per run")
    parser.add_argument("--baseline", type=str, default=None, help="Baseline run name, path, or 1-based index. Defaults to the first run.")
    parser.add_argument("--out-dir", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    names = args.name or None
    if names is not None and len(names) != len(args.run_dirs):
        raise ValueError("--name must be repeated exactly once per run directory")

    out_dir = args.out_dir or Path(args.run_dirs[0]).parent / "comparison"
    report = build_comparison_report(args.run_dirs, names=names, baseline=args.baseline)
    outputs = write_comparison_outputs(report, out_dir)

    print(f"run_count={report['run_count']}")
    print("baseline=" + json.dumps(report["baseline"], ensure_ascii=False))
    print("best_by_best_val_loss=" + json.dumps(report["best_by_best_val_loss"], ensure_ascii=False))
    print("best_by_eval_loss=" + json.dumps(report["best_by_eval_loss"], ensure_ascii=False))
    print("summary=" + json.dumps(report["summary"], ensure_ascii=False))
    for key, path in outputs.items():
        print(f"saved_{key}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
