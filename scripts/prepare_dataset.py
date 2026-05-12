from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.data_prep import build_prepared_dataset, write_prepared_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare one or more text sources for MiniGPT training.")
    parser.add_argument("sources", nargs="+", type=Path, help="Text files or directories containing .txt files")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "dataset")
    parser.add_argument("--output-name", type=str, default="corpus.txt")
    parser.add_argument("--no-recursive", action="store_true", help="Only read .txt files directly under source directories")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = build_prepared_dataset(args.sources, recursive=not args.no_recursive)
    outputs = write_prepared_dataset(dataset, args.out_dir, output_name=args.output_name)
    print(f"sources={len(dataset.sources)}")
    print(f"chars={dataset.char_count}")
    print(f"lines={dataset.line_count}")
    print(f"unique_chars={dataset.unique_char_count}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
