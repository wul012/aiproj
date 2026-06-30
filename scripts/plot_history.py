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

from minigpt.core.history import load_records, summarize_records, write_loss_curve_svg


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize MiniGPT metrics.jsonl and write a loss curve SVG.")
    parser.add_argument("--history", type=Path, default=ROOT / "runs" / "minigpt" / "metrics.jsonl")
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    out_path = args.out or args.history.parent / "loss_curve.svg"
    records = load_records(args.history)
    if not records:
        raise SystemExit(f"No history records found: {args.history}")
    write_loss_curve_svg(records, out_path)
    print(json.dumps(summarize_records(records), ensure_ascii=False, indent=2))
    print(f"saved={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
