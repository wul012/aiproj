from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_comparison import (  # noqa: E402
    build_promoted_training_scale_comparison,
    write_promoted_training_scale_comparison_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare only promoted MiniGPT training scale runs from a promotion index.")
    parser.add_argument("promotion_index", type=Path, help="training_scale_promotion_index.json file or index directory")
    parser.add_argument("--baseline", type=str, default=None, help="Baseline promoted run name or zero-based index")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "promoted-training-scale-comparison")
    parser.add_argument("--title", type=str, default="MiniGPT promoted training scale comparison")
    parser.add_argument("--require-compared", action="store_true", help="Exit non-zero unless promoted runs were compared")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline: str | int | None = args.baseline
    if isinstance(baseline, str) and baseline.isdigit():
        baseline = int(baseline)
    report = build_promoted_training_scale_comparison(
        args.promotion_index,
        baseline=baseline,
        title=args.title,
    )
    outputs = write_promoted_training_scale_comparison_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"comparison_status={report['comparison_status']}")
    print(f"promoted_count={summary.get('promoted_count')}")
    print(f"comparison_ready_count={summary.get('comparison_ready_count')}")
    print(f"compared_run_count={summary.get('compared_run_count')}")
    print(f"baseline={summary.get('baseline_name')}")
    print(f"best_by_readiness={summary.get('best_by_readiness')}")
    if summary.get("blocked_reason"):
        print(f"blocked_reason={summary.get('blocked_reason')}")
    print("summary=" + json.dumps(summary, ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.require_compared and report["comparison_status"] != "compared":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
