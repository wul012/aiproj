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

from minigpt.reports.cards import build_experiment_card, write_experiment_card_outputs  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build JSON, Markdown, and HTML experiment cards for a MiniGPT run.")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--registry", type=Path, default=None, help="Optional registry.json for rank and tag context")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to the run directory")
    parser.add_argument("--title", type=str, default="MiniGPT experiment card")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
