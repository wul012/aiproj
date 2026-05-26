from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.project_audit import build_project_audit, write_project_audit_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit MiniGPT registry/model-card readiness.")
    parser.add_argument("--registry", type=Path, default=ROOT / "runs" / "registry" / "registry.json")
    parser.add_argument("--model-card", type=Path, default=None, help="Optional model_card.json path")
    parser.add_argument("--request-history-summary", type=Path, default=None, help="Optional request_history_summary.json path")
    parser.add_argument("--benchmark-history", type=Path, default=None, help="Optional benchmark_history.json path")
    parser.add_argument("--ci-workflow-hygiene", type=Path, default=None, help="Optional ci_workflow_hygiene.json path")
    parser.add_argument("--test-coverage-report", type=Path, default=None, help="Optional test_coverage_report.json path")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to the registry directory")
    parser.add_argument("--title", type=str, default="MiniGPT project audit")
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit non-zero for warn as well as fail")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.registry.parent
    audit = build_project_audit(
        args.registry,
        model_card_path=args.model_card,
        request_history_summary_path=args.request_history_summary,
        benchmark_history_path=args.benchmark_history,
        ci_workflow_hygiene_path=args.ci_workflow_hygiene,
        test_coverage_report_path=args.test_coverage_report,
        title=args.title,
    )
    outputs = write_project_audit_outputs(audit, out_dir)
    summary = audit["summary"]

    print(f"registry={args.registry}")
    print(f"overall_status={summary['overall_status']}")
    print(f"score_percent={summary['score_percent']}")
    print(f"request_history_status={summary.get('request_history_status')}")
    print(f"request_history_records={summary.get('request_history_records')}")
    print(f"benchmark_history_status={summary.get('benchmark_history_status')}")
    print(f"benchmark_history_entries={summary.get('benchmark_history_entries')}")
    print(f"benchmark_history_ready={summary.get('benchmark_history_ready')}")
    print(f"benchmark_history_boundary={summary.get('benchmark_history_latest_boundary')}")
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
    print(f"ci_workflow_status={summary.get('ci_workflow_status')}")
    print(f"ci_workflow_failed_checks={summary.get('ci_workflow_failed_checks')}")
    print(f"ci_baseline_candidate_threshold_boundary_gate_check_ready={summary.get('ci_baseline_candidate_threshold_boundary_gate_check_ready')}")
    print(f"ci_baseline_candidate_threshold_boundary_gate_plan_check_ready={summary.get('ci_baseline_candidate_threshold_boundary_gate_plan_check_ready')}")
    print(f"test_coverage_status={summary.get('test_coverage_status')}")
    print(f"test_coverage_percent={summary.get('test_coverage_percent')}")
    print(f"test_coverage_fail_under={summary.get('test_coverage_fail_under')}")
    print(f"test_coverage_gap={summary.get('test_coverage_gap')}")
    print(f"checks={summary['pass_count']} pass/{summary['warn_count']} warn/{summary['fail_count']} fail")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if audit["warnings"]:
        print("warnings=" + json.dumps(audit["warnings"], ensure_ascii=False))
    if summary["overall_status"] == "fail" or (args.fail_on_warn and summary["overall_status"] == "warn"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
