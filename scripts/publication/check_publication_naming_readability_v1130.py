from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.publication_naming_readability import (  # noqa: E402
    build_publication_naming_readability_report,
    resolve_exit_code,
    write_publication_naming_readability_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MiniGPT publication naming readability stopgap policy.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "publication-naming-readability-v1130")
    parser.add_argument("--require-policy-ready", action="store_true")
    parser.add_argument("--require-clean-new-names", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    report = build_publication_naming_readability_report(args.root)
    outputs = write_publication_naming_readability_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"scanned_file_count={summary['scanned_file_count']}")
    print(f"repeated_receipt_index_file_count={summary['repeated_receipt_index_file_count']}")
    print(f"long_name_file_count={summary['long_name_file_count']}")
    print(f"policy_ready={summary['policy_ready']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(
        report,
        require_policy_ready=args.require_policy_ready,
        require_clean_new_names=args.require_clean_new_names,
    )


if __name__ == "__main__":
    raise SystemExit(main())
