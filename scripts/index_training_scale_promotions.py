from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_promotion_index import (  # noqa: E402
    build_training_scale_promotion_index,
    write_training_scale_promotion_index_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index promoted MiniGPT training scale promotion reports for comparison.")
    parser.add_argument("promotions", nargs="+", type=Path, help="training_scale_promotion.json files or promotion directories")
    parser.add_argument("--name", action="append", default=None, help="Display name for each promotion; repeat once per input")
    parser.add_argument("--baseline", type=str, default=None, help="Baseline name or zero-based index among promoted inputs")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "training-scale-promotion-index")
    parser.add_argument("--title", type=str, default="MiniGPT training scale promotion index")
    parser.add_argument("--require-compare-ready", action="store_true", help="Exit non-zero unless at least two promoted runs are ready")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline: str | int | None = args.baseline
    if isinstance(baseline, str) and baseline.isdigit():
        baseline = int(baseline)
    report = build_training_scale_promotion_index(
        args.promotions,
        names=args.name,
        baseline=baseline,
        title=args.title,
    )
    outputs = write_training_scale_promotion_index_outputs(report, args.out_dir)
    summary = report["summary"]
    comparison = report["comparison_inputs"]
    print(f"promotion_count={summary['promotion_count']}")
    print(f"promoted_count={summary['promoted_count']}")
    print(f"review_count={summary['review_count']}")
    print(f"blocked_count={summary['blocked_count']}")
    print(f"comparison_ready_count={summary['comparison_ready_count']}")
    print(f"compare_command_ready={summary['compare_command_ready']}")
    print(f"baseline={comparison.get('baseline_name')}")
    print("compare_command=" + json.dumps(comparison.get("compare_command", []), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.require_compare_ready and not summary["compare_command_ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
