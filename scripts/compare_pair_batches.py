from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.pair_trend import build_pair_batch_trend_report, load_pair_batch_report, write_pair_batch_trend_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare saved MiniGPT pair-generation batch reports.")
    parser.add_argument("reports", nargs="+", type=Path, help="Path to pair_generation_batch.json.")
    parser.add_argument("--name", action="append", default=None, help="Display name for a report. Repeat once per report.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "pair_batch_trend")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reports = [load_pair_batch_report(path) for path in args.reports]
    trend = build_pair_batch_trend_report(reports, names=args.name)
    outputs = write_pair_batch_trend_outputs(trend, args.out_dir)
    print(f"reports={trend['report_count']}")
    print(f"cases={trend['case_count']}")
    print(f"changed_generated_equal_cases={trend['changed_generated_equal_cases']}")
    print(f"max_abs_generated_char_delta={trend['max_abs_generated_char_delta']}")
    print(f"out_dir={args.out_dir}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
