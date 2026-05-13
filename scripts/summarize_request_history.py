from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.request_history_summary import build_request_history_summary, write_request_history_summary_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize MiniGPT local inference request history.")
    parser.add_argument("--request-log", type=Path, default=ROOT / "runs" / "minigpt" / "inference_requests.jsonl")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "request-history-summary")
    parser.add_argument("--title", type=str, default="MiniGPT request history summary")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_request_history_summary(args.request_log, title=args.title)
    outputs = write_request_history_summary_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"request_log={report['request_log']}")
    print(f"status={summary.get('status')}")
    print(f"total_log_records={summary.get('total_log_records')}")
    print(f"invalid_record_count={summary.get('invalid_record_count')}")
    print(f"timeout_rate={summary.get('timeout_rate')}")
    print(f"error_rate={summary.get('error_rate')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
