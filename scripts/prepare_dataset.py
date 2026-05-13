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
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--output-name", type=str, default="corpus.txt")
    parser.add_argument("--dataset-name", type=str, default=None, help="Dataset name for versioned output")
    parser.add_argument("--dataset-version", type=str, default=None, help="Dataset version for versioned output")
    parser.add_argument("--dataset-description", type=str, default="", help="Short description stored in dataset_version.json")
    parser.add_argument("--dataset-root", type=Path, default=ROOT / "datasets", help="Root for datasets/<name>/<version> output")
    parser.add_argument("--no-recursive", action="store_true", help="Only read .txt files directly under source directories")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if (args.dataset_name is None) != (args.dataset_version is None):
        raise SystemExit("--dataset-name and --dataset-version must be provided together")
    recursive = not args.no_recursive
    out_dir = args.out_dir
    if out_dir is None:
        if args.dataset_name and args.dataset_version:
            out_dir = args.dataset_root / args.dataset_name / args.dataset_version
        else:
            out_dir = ROOT / "runs" / "dataset"
    dataset_name = args.dataset_name or Path(out_dir).name
    dataset_version = args.dataset_version or "unversioned"
    dataset = build_prepared_dataset(args.sources, recursive=recursive)
    outputs = write_prepared_dataset(
        dataset,
        out_dir,
        output_name=args.output_name,
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_description=args.dataset_description,
        source_roots=args.sources,
        recursive=recursive,
    )
    print(f"dataset_id={dataset_name}@{dataset_version}")
    print(f"sources={len(dataset.sources)}")
    print(f"chars={dataset.char_count}")
    print(f"lines={dataset.line_count}")
    print(f"unique_chars={dataset.unique_char_count}")
    print(f"fingerprint={dataset.fingerprint}")
    print(f"out_dir={out_dir}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
