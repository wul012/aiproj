from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dataset_card import build_dataset_card, write_dataset_card_outputs  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT dataset card from prepared dataset evidence.")
    parser.add_argument("--dataset-dir", type=Path, required=True, help="Directory containing dataset_version/report/quality files")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to --dataset-dir")
    parser.add_argument("--title", type=str, default="MiniGPT dataset card")
    parser.add_argument("--intended-use", action="append", default=[], help="Custom intended-use bullet, repeatable")
    parser.add_argument("--limitation", action="append", default=[], help="Custom limitation bullet, repeatable")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.dataset_dir
    card = build_dataset_card(
        args.dataset_dir,
        title=args.title,
        intended_use=args.intended_use or None,
        limitations=args.limitation or None,
    )
    outputs = write_dataset_card_outputs(card, out_dir)
    print(f"dataset_dir={card['dataset_dir']}")
    print("dataset=" + json.dumps(card["dataset"], ensure_ascii=False))
    print("summary=" + json.dumps(card["summary"], ensure_ascii=False))
    print(f"quality_status={card['summary'].get('quality_status')}")
    print(f"readiness_status={card['summary'].get('readiness_status')}")
    print(f"warning_count={card['summary'].get('warning_count')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
