from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.experiment_card import build_experiment_card, write_experiment_card_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build JSON, Markdown, and HTML experiment cards for a MiniGPT run.")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--registry", type=Path, default=None, help="Optional registry.json for rank and tag context")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to the run directory")
    parser.add_argument("--title", type=str, default="MiniGPT experiment card")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.run_dir
    card = build_experiment_card(args.run_dir, registry_path=args.registry, title=args.title)
    outputs = write_experiment_card_outputs(card, out_dir)

    print(f"run_dir={args.run_dir}")
    print(f"status={card['summary']['status']}")
    print(f"best_val_loss={card['summary']['best_val_loss']}")
    print(f"rank={card['summary']['best_val_loss_rank']}")
    print(f"recommendations={len(card['recommendations'])}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if card["warnings"]:
        print("warnings=" + json.dumps(card["warnings"], ensure_ascii=False))


if __name__ == "__main__":
    main()
