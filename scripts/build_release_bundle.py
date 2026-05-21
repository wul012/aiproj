from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_bundle import build_release_bundle, write_release_bundle_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT release evidence bundle.")
    parser.add_argument("--registry", type=Path, default=ROOT / "runs" / "registry" / "registry.json")
    parser.add_argument("--model-card", type=Path, default=None, help="Optional model_card.json path")
    parser.add_argument("--audit", type=Path, default=None, help="Optional project_audit.json path")
    parser.add_argument("--request-history-summary", type=Path, default=None, help="Optional request_history_summary.json path")
    parser.add_argument("--benchmark-history", type=Path, default=None, help="Optional benchmark_history.json path")
    parser.add_argument("--ci-workflow-hygiene", type=Path, default=None, help="Optional ci_workflow_hygiene.json path")
    parser.add_argument("--test-coverage-report", type=Path, default=None, help="Optional test_coverage_report.json path")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to runs/release-bundle")
    parser.add_argument("--release-name", type=str, default=None)
    parser.add_argument("--title", type=str, default="MiniGPT release bundle")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.registry.parent.parent / "release-bundle"
    bundle = build_release_bundle(
        args.registry,
        model_card_path=args.model_card,
        audit_path=args.audit,
        request_history_summary_path=args.request_history_summary,
        benchmark_history_path=args.benchmark_history,
        ci_workflow_hygiene_path=args.ci_workflow_hygiene,
        test_coverage_report_path=args.test_coverage_report,
        release_name=args.release_name,
        title=args.title,
    )
    outputs = write_release_bundle_outputs(bundle, out_dir)
    summary = bundle["summary"]

    print(f"registry={args.registry}")
    print(f"release_status={summary['release_status']}")
    print(f"audit_status={summary['audit_status']}")
    print(f"request_history_status={summary.get('request_history_status')}")
    print(f"benchmark_history_status={summary.get('benchmark_history_status')}")
    print(f"benchmark_history_entries={summary.get('benchmark_history_entries')}")
    print(f"benchmark_history_ready={summary.get('benchmark_history_ready')}")
    print(f"benchmark_history_boundary={summary.get('benchmark_history_latest_boundary')}")
    print(f"ci_workflow_status={summary.get('ci_workflow_status')}")
    print(f"ci_workflow_failed_checks={summary.get('ci_workflow_failed_checks')}")
    print(f"ci_workflow_required_order_count={summary.get('ci_workflow_required_order_count')}")
    print(f"ci_workflow_order_violation_count={summary.get('ci_workflow_order_violation_count')}")
    print(f"test_coverage_status={summary.get('test_coverage_status')}")
    print(f"test_coverage_percent={summary.get('test_coverage_percent')}")
    print(f"test_coverage_fail_under={summary.get('test_coverage_fail_under')}")
    print(f"test_coverage_gap={summary.get('test_coverage_gap')}")
    print(f"best_run={summary['best_run_name']}")
    print(f"artifacts={summary['available_artifacts']} available/{summary['missing_artifacts']} missing")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if bundle["warnings"]:
        print("warnings=" + json.dumps(bundle["warnings"], ensure_ascii=False))


if __name__ == "__main__":
    main()
