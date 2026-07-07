from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path  # type: ignore[import-not-found,no-redef]

ensure_src_path()

from minigpt.file_size_ratchet import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    build_file_size_ratchet_report,
    resolve_exit_code,
    write_file_size_ratchet_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check MiniGPT Python file-size ratchets.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "runs" / "file-size-ratchet")
    parser.add_argument("--require-pass", action="store_true", help="Return 1 when the ratchet fails.")
    parser.add_argument("--no-fail", action="store_true", help="Always return 0 after writing outputs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_file_size_ratchet_report(args.config, project_root=args.project_root)
    outputs = write_file_size_ratchet_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"scanned_file_count={summary['scanned_file_count']}")
    print(f"over_warning_count={summary['over_warning_count']}")
    print(f"over_limit_count={summary['over_limit_count']}")
    print(f"unwaived_over_limit_count={summary['unwaived_over_limit_count']}")
    print(f"waiver_growth_violation_count={summary['waiver_growth_violation_count']}")
    print(f"outputs={json.dumps(outputs, ensure_ascii=False)}")
    if args.no_fail:
        return 0
    return resolve_exit_code(report, require_pass=args.require_pass or True)


if __name__ == "__main__":
    raise SystemExit(main())
