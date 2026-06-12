from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.publication_receipt_template import (  # noqa: E402
    build_publication_receipt_template_report,
    resolve_exit_code,
    write_publication_receipt_template_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MiniGPT publication receipt template and script layers.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "publication-receipt-template-v1132")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    report = build_publication_receipt_template_report(args.root)
    outputs = write_publication_receipt_template_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"ready_section_count={summary['ready_section_count']}")
    print(f"ready_script_layer_count={summary['ready_script_layer_count']}")
    print(f"template_ready={summary['template_ready']}")
    print(f"failed_count={summary['failed_count']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_pass=args.require_pass)


if __name__ == "__main__":
    raise SystemExit(main())
