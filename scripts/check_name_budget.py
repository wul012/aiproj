from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path  # type: ignore[import-not-found,no-redef]

ensure_src_path()

from minigpt.name_budget import (  # noqa: E402
    DEFAULT_BASELINE,
    build_name_report,
    write_name_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check the MiniGPT Python name budget.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "runs" / "name-budget")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--no-fail", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_name_report(
        project_root=args.project_root,
        baseline_path=args.baseline,
        update_baseline=args.update_baseline,
    )
    outputs = write_name_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"current_violation_count={summary['current_violation_count']}")
    print(f"new_violation_count={summary['new_violation_count']}")
    print(f"resolved_violation_count={summary['resolved_violation_count']}")
    print(f"outputs={json.dumps(outputs, ensure_ascii=False)}")
    return 0 if args.no_fail or report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
