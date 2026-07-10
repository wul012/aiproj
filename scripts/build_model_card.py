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

from minigpt.reports.cards import build_model_card, write_model_card_outputs  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build JSON, Markdown, and HTML model cards from a MiniGPT registry.")
    parser.add_argument("--registry", type=Path, default=ROOT / "runs" / "registry" / "registry.json")
    parser.add_argument("--card", action="append", default=[], type=Path, help="Optional experiment_card.json path, repeatable")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to the registry directory")
    parser.add_argument("--title", type=str, default="MiniGPT model card")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir or args.registry.parent
    card = build_model_card(args.registry, card_paths=args.card or None, title=args.title)
    outputs = write_model_card_outputs(card, out_dir)

    print(f"registry={args.registry}")
    print(f"run_count={card['summary']['run_count']}")
    print(f"best_run={card['summary']['best_run_name']}")
    print(f"ready_runs={card['summary']['ready_runs']}")
    print(f"experiment_cards={card['coverage']['experiment_cards_found']}")
    print(f"dataset_snapshot_runs={card['coverage'].get('dataset_snapshot_runs')}")
    print(f"dataset_snapshot_coverage={card['coverage'].get('dataset_snapshot_coverage')}")
    print("dataset_snapshot_summary=" + json.dumps(card.get("dataset_snapshot_summary", {}), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if card["warnings"]:
        print("warnings=" + json.dumps(card["warnings"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
