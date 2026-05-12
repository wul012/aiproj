from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dashboard import write_dashboard


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a static HTML dashboard for a MiniGPT run directory.")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--title", type=str, default="MiniGPT experiment dashboard")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_path = args.out or args.run_dir / "dashboard.html"
    payload = write_dashboard(args.run_dir, output_path=out_path, title=args.title)
    available = [artifact for artifact in payload["artifacts"] if artifact["exists"]]
    print(f"run_dir={args.run_dir}")
    print(f"saved={out_path}")
    print(f"available_artifacts={len(available)}")
    print("summary=" + json.dumps(payload["summary"], ensure_ascii=False))
    if payload["warnings"]:
        print("warnings=" + json.dumps(payload["warnings"], ensure_ascii=False))


if __name__ == "__main__":
    main()
