from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_readiness_comparison import (
    build_release_readiness_comparison,
    write_release_readiness_comparison_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare MiniGPT release readiness dashboards.")
    parser.add_argument(
        "--readiness",
        type=Path,
        action="append",
        default=None,
        help="release_readiness.json path. Repeat to compare multiple reports.",
    )
    parser.add_argument("--baseline", type=Path, default=None, help="Optional baseline release_readiness.json path")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "release-readiness-comparison")
    parser.add_argument("--title", type=str, default="MiniGPT release readiness comparison")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    readiness_paths = args.readiness or [ROOT / "runs" / "release-readiness" / "release_readiness.json"]
    report = build_release_readiness_comparison(
        readiness_paths,
        baseline_path=args.baseline,
        title=args.title,
    )
    outputs = write_release_readiness_comparison_outputs(report, args.out_dir)
    summary = report["summary"]
    print("readiness=" + str(summary["readiness_count"]))
    print(f"baseline_status={summary['baseline_status']}")
    print(f"ready={summary['ready_count']}")
    print(f"blocked={summary['blocked_count']}")
    print(f"improved={summary['improved_count']}")
    print(f"regressed={summary['regressed_count']}")
    print(f"changed_panel_deltas={summary['changed_panel_delta_count']}")
    print(f"ci_workflow_regressions={summary.get('ci_workflow_regression_count')}")
    print(f"ci_workflow_order_regressions={summary.get('ci_workflow_order_regression_count')}")
    print(f"max_abs_ci_workflow_order_violation_delta={summary.get('max_abs_ci_workflow_order_violation_delta')}")
    print(f"test_coverage_regressions={summary.get('test_coverage_regression_count')}")
    print(f"benchmark_history_deltas={summary.get('benchmark_history_delta_count')}")
    print(f"benchmark_history_regressions={summary.get('benchmark_history_regression_count')}")
    for row in report.get("rows", []):
        if isinstance(row, dict):
            print(
                "benchmark_history_readiness_requirement="
                + f"{row.get('release_name')}:{row.get('benchmark_history_readiness_requirement_status')}:"
                + f"{row.get('benchmark_history_readiness_requirement_exit_code')}"
            )
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
