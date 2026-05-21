from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dataset_version_comparison import (  # noqa: E402
    build_dataset_version_comparison,
    write_dataset_version_comparison_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare MiniGPT prepared dataset versions.")
    parser.add_argument("versions", nargs="+", type=Path, help="dataset_version.json files or prepared dataset directories")
    parser.add_argument("--name", action="append", default=[], help="Optional display name, repeat once per version")
    parser.add_argument("--baseline", type=str, default=None, help="Baseline name, path, dataset id, or 1-based index. Defaults to the first version.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to sibling dataset-version-comparison")
    parser.add_argument("--title", type=str, default="MiniGPT dataset version comparison")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    names = args.name or None
    if names is not None and len(names) != len(args.versions):
        raise ValueError("--name must be repeated exactly once per dataset version")
    first = Path(args.versions[0])
    out_dir = args.out_dir or (first if first.is_dir() else first.parent).parent / "dataset-version-comparison"
    report = build_dataset_version_comparison(
        args.versions,
        names=names,
        baseline=args.baseline,
        title=args.title,
    )
    outputs = write_dataset_version_comparison_outputs(report, out_dir)
    print(f"version_count={report['version_count']}")
    print("baseline=" + json.dumps(report["baseline"], ensure_ascii=False))
    print("summary=" + json.dumps(report["summary"], ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
