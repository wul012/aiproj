from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.benchmark_scorecard_comparison import (  # noqa: E402
    build_benchmark_scorecard_comparison,
    write_benchmark_scorecard_comparison_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare multiple MiniGPT benchmark scorecards.")
    parser.add_argument("scorecards", type=Path, nargs="+", help="Scorecard JSON path or run directory")
    parser.add_argument("--name", action="append", default=[], help="Optional display name, repeat once per scorecard")
    parser.add_argument("--baseline", type=str, default=None, help="Baseline name, path, run_dir, or 1-based index")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to <first-scorecard-parent>/benchmark-scorecard-comparison")
    parser.add_argument("--title", type=str, default="MiniGPT benchmark scorecard comparison")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    names = args.name or None
    if names is not None and len(names) != len(args.scorecards):
        raise ValueError("--name must be repeated exactly once per scorecard")

    out_dir = args.out_dir or _default_out_dir(args.scorecards[0])
    report = build_benchmark_scorecard_comparison(
        args.scorecards,
        names=names,
        baseline=args.baseline,
        title=args.title,
    )
    outputs = write_benchmark_scorecard_comparison_outputs(report, out_dir)
    print(f"scorecard_count={report['scorecard_count']}")
    print("baseline=" + json.dumps(report["baseline"], ensure_ascii=False))
    print("best_by_overall_score=" + json.dumps(report["best_by_overall_score"], ensure_ascii=False))
    print("best_by_rubric_avg_score=" + json.dumps(report["best_by_rubric_avg_score"], ensure_ascii=False))
    print("summary=" + json.dumps(report["summary"], ensure_ascii=False))
    summary = report["summary"]
    print(f"generation_quality_flag_regression_count={summary.get('generation_quality_flag_regression_count')}")
    print(f"generation_quality_flag_improvement_count={summary.get('generation_quality_flag_improvement_count')}")
    print(f"baseline_generation_quality_dominant_flag={summary.get('baseline_generation_quality_dominant_flag')}")
    for key, path in outputs.items():
        print(f"saved_{key}={path}")


def _default_out_dir(path: Path) -> Path:
    if path.is_dir():
        return path.parent / "benchmark-scorecard-comparison"
    if path.parent.name == "benchmark-scorecard":
        return path.parent.parent.parent / "benchmark-scorecard-comparison"
    return path.parent / "benchmark-scorecard-comparison"


if __name__ == "__main__":
    main()
