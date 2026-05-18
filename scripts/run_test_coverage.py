from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.test_coverage_report import build_test_coverage_report, write_test_coverage_outputs  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MiniGPT tests with coverage and write coverage evidence.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "test-coverage")
    parser.add_argument("--title", type=str, default="MiniGPT test coverage report")
    parser.add_argument("--source", type=str, default="src/minigpt")
    parser.add_argument("--tests", type=Path, default=ROOT / "tests")
    parser.add_argument("--fail-under", type=float, default=None, help="Optional minimum line coverage percentage required for success.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.fail_under is not None and not 0 <= args.fail_under <= 100:
        raise SystemExit("--fail-under must be between 0 and 100")
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
    _run(test_command)
    _run(json_command)
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
        raise SystemExit(2)


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
