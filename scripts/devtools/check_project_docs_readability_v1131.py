from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.project_docs_readability import (  # noqa: E402
    build_project_docs_readability_report,
    resolve_exit_code,
    write_project_docs_readability_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MiniGPT split documentation readability.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "project-docs-readability-v1131")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    report = build_project_docs_readability_report(args.root)
    outputs = write_project_docs_readability_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"doc_target_count={summary['doc_target_count']}")
    print(f"ready_doc_count={summary['ready_doc_count']}")
    print(f"missing_readme_link_count={summary['missing_readme_link_count']}")
    print(f"failed_count={summary['failed_count']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(report, require_pass=args.require_pass)


if __name__ == "__main__":
    raise SystemExit(main())
