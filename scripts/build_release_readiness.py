from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

from minigpt.governance.release import build_release_readiness_dashboard, write_release_readiness_outputs


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT release readiness dashboard.")
    parser.add_argument("--bundle", type=Path, default=ROOT / "runs" / "release-bundle" / "release_bundle.json")
    parser.add_argument("--gate", type=Path, default=None, help="Optional gate_report.json path")
    parser.add_argument("--audit", type=Path, default=None, help="Optional project_audit.json path")
    parser.add_argument("--request-history-summary", type=Path, default=None, help="Optional request_history_summary.json path")
    parser.add_argument("--maturity", type=Path, default=None, help="Optional maturity_summary.json path")
    parser.add_argument("--ci-workflow-hygiene", type=Path, default=None, help="Optional ci_workflow_hygiene.json path")
    parser.add_argument("--test-coverage-report", type=Path, default=None, help="Optional test_coverage_report.json path")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "release-readiness")
    parser.add_argument("--title", type=str, default="MiniGPT release readiness dashboard")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_release_readiness_dashboard(
        args.bundle,
        gate_path=args.gate,
        audit_path=args.audit,
        request_history_summary_path=args.request_history_summary,
        maturity_path=args.maturity,
        ci_workflow_hygiene_path=args.ci_workflow_hygiene,
        test_coverage_report_path=args.test_coverage_report,
        title=args.title,
    )
    outputs = write_release_readiness_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"bundle={args.bundle}")
    print(f"readiness_status={summary.get('readiness_status')}")
    print(f"decision={summary.get('decision')}")
    print(f"release_status={summary.get('release_status')}")
    print(f"gate_status={summary.get('gate_status')}")
    print(f"audit_status={summary.get('audit_status')}")
    print(f"ci_workflow_status={summary.get('ci_workflow_status')}")
    print(f"ci_workflow_failed_checks={summary.get('ci_workflow_failed_checks')}")
    print(f"ci_workflow_required_order_count={summary.get('ci_workflow_required_order_count')}")
    print(f"ci_workflow_order_violation_count={summary.get('ci_workflow_order_violation_count')}")
    print(f"ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready={summary.get('ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready')}")
    print(f"ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready={summary.get('ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready')}")
    print(f"ci_workflow_archived_path_portability_check_ready={summary.get('ci_workflow_archived_path_portability_check_ready')}")
    print(
        "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready="
        f"{summary.get('ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready')}"
    )
    print(f"request_history_status={summary.get('request_history_status')}")
    print(f"benchmark_history_status={summary.get('benchmark_history_status')}")
    print(f"benchmark_history_entries={summary.get('benchmark_history_entries')}")
    print(f"benchmark_history_ready={summary.get('benchmark_history_ready')}")
    print(
        "benchmark_history_suite_design_non_comparison_ready_entries="
        f"{summary.get('benchmark_history_suite_design_non_comparison_ready_entries')}"
    )
    print(
        "benchmark_history_design_comparison_changed_entries="
        f"{summary.get('benchmark_history_design_comparison_changed_entries')}"
    )
    print(f"benchmark_history_readiness_requirement_status={summary.get('benchmark_history_readiness_requirement_status')}")
    print(f"benchmark_history_readiness_requirement_exit_code={summary.get('benchmark_history_readiness_requirement_exit_code')}")
    print(
        "benchmark_history_readiness_requirement_failed_reasons="
        + json.dumps(summary.get("benchmark_history_readiness_requirement_failed_reasons") or [], ensure_ascii=False)
    )
    print(f"benchmark_history_boundary={summary.get('benchmark_history_latest_boundary')}")
    print(f"test_coverage_status={summary.get('test_coverage_status')}")
    print(f"test_coverage_percent={summary.get('test_coverage_percent')}")
    print(f"test_coverage_fail_under={summary.get('test_coverage_fail_under')}")
    print(f"test_coverage_gap={summary.get('test_coverage_gap')}")
    print(f"maturity_status={summary.get('maturity_status')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report["warnings"]:
        print("warnings=" + json.dumps(report["warnings"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
