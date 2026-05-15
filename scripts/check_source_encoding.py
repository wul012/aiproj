from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.source_encoding_hygiene import build_source_encoding_report, write_source_encoding_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MiniGPT Python source encoding hygiene.")
    parser.add_argument("paths", nargs="*", type=Path, default=[ROOT / "src", ROOT / "scripts", ROOT / "tests"])
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "source-encoding-hygiene")
    parser.add_argument("--title", type=str, default="MiniGPT source encoding hygiene")
    parser.add_argument("--no-fail", action="store_true", help="Write the report without returning a non-zero status.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_paths = _collect_python_paths(args.paths)
    report = build_source_encoding_report(source_paths, project_root=ROOT, title=args.title)
    outputs = write_source_encoding_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={summary['status']}")
    print(f"decision={summary['decision']}")
    print(f"source_count={summary['source_count']}")
    print(f"clean_count={summary['clean_count']}")
    print(f"bom_count={summary['bom_count']}")
    print(f"syntax_error_count={summary['syntax_error_count']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if summary["status"] != "pass" and not args.no_fail:
        raise SystemExit(1)


def _collect_python_paths(paths: list[Path]) -> list[Path]:
    collected: list[Path] = []
    for path in paths:
        resolved = path if path.is_absolute() else ROOT / path
        if resolved.is_file():
            if resolved.suffix == ".py":
                collected.append(resolved)
            continue
        if not resolved.exists():
            raise FileNotFoundError(f"Source encoding path does not exist: {resolved}")
        collected.extend(sorted(item for item in resolved.rglob("*.py") if item.is_file()))
    return sorted(dict.fromkeys(collected))


if __name__ == "__main__":
    main()
