from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.history import load_records, summarize_records, write_loss_curve_svg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize MiniGPT metrics.jsonl and write a loss curve SVG.")
    parser.add_argument("--history", type=Path, default=ROOT / "runs" / "minigpt" / "metrics.jsonl")
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_path = args.out or args.history.parent / "loss_curve.svg"
    records = load_records(args.history)
    if not records:
        raise SystemExit(f"No history records found: {args.history}")
    write_loss_curve_svg(records, out_path)
    print(json.dumps(summarize_records(records), ensure_ascii=False, indent=2))
    print(f"saved={out_path}")


if __name__ == "__main__":
    main()
