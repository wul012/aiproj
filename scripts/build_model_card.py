from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_card import build_model_card, write_model_card_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build JSON, Markdown, and HTML model cards from a MiniGPT registry.")
    parser.add_argument("--registry", type=Path, default=ROOT / "runs" / "registry" / "registry.json")
    parser.add_argument("--card", action="append", default=[], type=Path, help="Optional experiment_card.json path, repeatable")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to the registry directory")
    parser.add_argument("--title", type=str, default="MiniGPT model card")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.registry.parent
    card = build_model_card(args.registry, card_paths=args.card or None, title=args.title)
    outputs = write_model_card_outputs(card, out_dir)

    print(f"registry={args.registry}")
    print(f"run_count={card['summary']['run_count']}")
    print(f"best_run={card['summary']['best_run_name']}")
    print(f"ready_runs={card['summary']['ready_runs']}")
    print(f"experiment_cards={card['coverage']['experiment_cards_found']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if card["warnings"]:
        print("warnings=" + json.dumps(card["warnings"], ensure_ascii=False))


if __name__ == "__main__":
    main()
