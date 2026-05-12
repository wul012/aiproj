from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.playground import write_playground


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a static MiniGPT playground UI for a run directory.")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--title", type=str, default="MiniGPT playground")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_path = args.out or args.run_dir / "playground.html"
    payload = write_playground(args.run_dir, output_path=out_path, title=args.title)
    available = [link for link in payload["links"] if link["exists"]]

    print(f"run_dir={args.run_dir}")
    print(f"saved={out_path}")
    print(f"available_links={len(available)}")
    print(f"sampling_cases={payload['summary']['sampling_cases']}")
    print("commands=" + json.dumps(payload["commands"], ensure_ascii=False))
    if payload["warnings"]:
        print("warnings=" + json.dumps(payload["warnings"], ensure_ascii=False))


if __name__ == "__main__":
    main()
