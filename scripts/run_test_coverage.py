from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

from minigpt.test_coverage_report import build_test_coverage_report, write_test_coverage_outputs  # noqa: E402

Runner = Callable[..., subprocess.CompletedProcess[Any]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MiniGPT tests with coverage and write coverage evidence.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "test-coverage")
    parser.add_argument("--title", type=str, default="MiniGPT test coverage report")
    parser.add_argument("--source", type=str, default="src/minigpt")
    parser.add_argument("--tests", type=Path, default=ROOT / "tests")
    parser.add_argument("--fail-under", type=float, default=None, help="Optional minimum line coverage percentage required for success.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, runner: Runner = subprocess.run) -> int:
    args = parse_args(argv)
    if args.fail_under is not None and not 0 <= args.fail_under <= 100:
        print("--fail-under must be between 0 and 100", file=sys.stderr)
        return 1
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    coverage_json = out_dir / "coverage.json"
    test_command = [
        sys.executable,
        "-B",
        "-m",
        "coverage",
        "run",
        f"--source={args.source}",
        "-m",
        "unittest",
        "discover",
        "-s",
        str(args.tests),
        "-v",
    ]
    json_command = [sys.executable, "-B", "-m", "coverage", "json", "-o", str(coverage_json)]
    test_return_code = _run(test_command, runner=runner)
    if test_return_code:
        return test_return_code
    json_return_code = _run(json_command, runner=runner)
    if json_return_code:
        return json_return_code
    report = build_test_coverage_report(
        coverage_json,
        project_root=ROOT,
        title=args.title,
        test_command=test_command,
        fail_under=args.fail_under,
    )
    outputs = write_test_coverage_outputs(report, out_dir)
    summary = report["summary"]
    print(f"status={summary['status']}")
    print(f"decision={summary['decision']}")
    print(f"line_coverage_percent={summary['line_coverage_percent']}")
    print(f"covered_lines={summary['covered_lines']}")
    print(f"num_statements={summary['num_statements']}")
    print(f"missing_lines={summary['missing_lines']}")
    print(f"file_count={summary['file_count']}")
    print(f"threshold_enabled={summary['threshold_enabled']}")
    print(f"fail_under={summary['fail_under']}")
    print(f"coverage_gap={summary['coverage_gap']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if summary["status"] != "pass":
        return 2
    return 0


def _run(command: list[str], *, runner: Runner = subprocess.run) -> int:
    completed = runner(command, cwd=ROOT, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
