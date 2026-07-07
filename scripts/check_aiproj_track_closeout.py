from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path  # type: ignore[import-not-found,no-redef]

ensure_src_path()

from minigpt.aiproj_track_closeout import (  # noqa: E402
    DEFAULT_FINAL_EVIDENCE_PATH,
    build_aiproj_track_closeout_report,
    resolve_exit_code,
    write_aiproj_track_closeout_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check MiniGPT production-excellence A-track closeout evidence.")
    parser.add_argument("--final-evidence", type=Path, default=DEFAULT_FINAL_EVIDENCE_PATH)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "runs" / "aiproj-track-closeout")
    parser.add_argument("--require-pass", action="store_true", help="Return 1 when closeout evidence fails.")
    parser.add_argument("--no-fail", action="store_true", help="Always return 0 after writing outputs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_aiproj_track_closeout_report(args.final_evidence, project_root=args.project_root)
    outputs = write_aiproj_track_closeout_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"evidence_doc_count={summary['evidence_doc_count']}")
    print(f"check_count={summary['check_count']}")
    print(f"failed_check_count={summary['failed_check_count']}")
    print(f"outputs={json.dumps(outputs, ensure_ascii=False)}")
    if args.no_fail:
        return 0
    return resolve_exit_code(report, require_pass=args.require_pass or True)


if __name__ == "__main__":
    raise SystemExit(main())
