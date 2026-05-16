from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.benchmark_scorecard_decision import (  # noqa: E402
    build_benchmark_scorecard_decision,
    write_benchmark_scorecard_decision_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT benchmark scorecard promotion decision from a scorecard comparison.")
    parser.add_argument("comparison", type=Path, help="benchmark_scorecard_comparison.json path or output directory")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to <comparison-parent>/decision")
    parser.add_argument("--min-rubric-score", type=float, default=80.0)
    parser.add_argument("--title", type=str, default="MiniGPT benchmark scorecard promotion decision")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_benchmark_scorecard_decision(
        args.comparison,
        min_rubric_score=args.min_rubric_score,
        title=args.title,
    )
    out_dir = args.out_dir or _default_out_dir(args.comparison)
    outputs = write_benchmark_scorecard_decision_outputs(report, out_dir)
    print(f"decision_status={report['decision_status']}")
    print(f"recommended_action={report['recommended_action']}")
    print("selected_run=" + json.dumps(report["selected_run"], ensure_ascii=False))
    print("summary=" + json.dumps(report["summary"], ensure_ascii=False))
    for key, path in outputs.items():
        print(f"saved_{key}={path}")


def _default_out_dir(path: Path) -> Path:
    if path.is_dir():
        return path / "decision"
    return path.parent / "decision"


if __name__ == "__main__":
    main()
