from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.artifact_map import (  # noqa: E402
    DEFAULT_LIMIT,
    build_artifact_map_report,
    resolve_exit_code,
    write_artifact_map_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a MiniGPT versioned artifact map.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "artifact-map-v1134")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    report = build_artifact_map_report(args.root, limit=args.limit)
    outputs = write_artifact_map_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"scanned_version_count={summary['scanned_version_count']}")
    print(f"ready_version_count={summary['ready_version_count']}")
    print(f"missing_summary_count={summary['missing_summary_count']}")
    print(f"missing_screenshot_count={summary['missing_screenshot_count']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_ready=args.require_ready, require_complete=args.require_complete)


if __name__ == "__main__":
    raise SystemExit(main())
