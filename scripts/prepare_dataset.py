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

from minigpt.training.data_prep import build_prepared_dataset, write_prepared_dataset  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare one or more text sources for MiniGPT training.")
    parser.add_argument("sources", nargs="+", type=Path, help="Text files or directories containing .txt files")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--output-name", type=str, default="corpus.txt")
    parser.add_argument("--dataset-name", type=str, default=None, help="Dataset name for versioned output")
    parser.add_argument("--dataset-version", type=str, default=None, help="Dataset version for versioned output")
    parser.add_argument("--dataset-description", type=str, default="", help="Short description stored in dataset_version.json")
    parser.add_argument("--dataset-root", type=Path, default=ROOT / "datasets", help="Root for datasets/<name>/<version> output")
    parser.add_argument("--dedupe-exact-sources", action="store_true", help="Skip exact duplicate source files while preserving skip evidence")
    parser.add_argument("--no-recursive", action="store_true", help="Only read .txt files directly under source directories")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
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
    dataset = build_prepared_dataset(args.sources, recursive=recursive, dedupe_exact_sources=args.dedupe_exact_sources)
    outputs = write_prepared_dataset(
        dataset,
        out_dir,
        output_name=args.output_name,
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_description=args.dataset_description,
        source_roots=args.sources,
        recursive=recursive,
        dedupe_exact_sources=args.dedupe_exact_sources,
    )
    print(f"dataset_id={dataset_name}@{dataset_version}")
    print(f"sources={len(dataset.sources)}")
    print(f"included_sources={dataset.included_source_count}")
    print(f"skipped_sources={dataset.skipped_source_count}")
    print(f"chars={dataset.char_count}")
    print(f"lines={dataset.line_count}")
    print(f"unique_chars={dataset.unique_char_count}")
    print(f"fingerprint={dataset.fingerprint}")
    print(f"out_dir={out_dir}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
