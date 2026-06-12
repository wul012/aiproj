from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.report_loader_dedup import (  # noqa: E402
    build_report_loader_dedup_report,
    resolve_exit_code,
    write_report_loader_dedup_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the MiniGPT report loader dedup evidence report.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "report-loader-dedup-v1140")
    parser.add_argument("--require-dedup-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    report = build_report_loader_dedup_report(args.root)
    outputs = write_report_loader_dedup_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"dedup_ready={summary['dedup_ready']}")
    print(f"read_json_report_definition_count={summary['read_json_report_definition_count']}")
    print(f"private_loader_copy_count={summary['private_loader_copy_count']}")
    print(f"migrated_module_count={summary['migrated_module_count']}")
    print(f"next_step={summary['next_step']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_dedup_ready=args.require_dedup_ready)


if __name__ == "__main__":
    raise SystemExit(main())
