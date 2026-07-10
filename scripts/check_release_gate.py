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

from minigpt.governance.release import (  # noqa: E402
    DEFAULT_RELEASE_GATE_POLICY_PROFILE,
    build_release_gate,
    exit_code_for_gate,
    release_gate_policy_profiles,
    write_release_gate_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a MiniGPT release bundle against release gate policy.")
    parser.add_argument("--bundle", type=Path, default=ROOT / "runs" / "release-bundle" / "release_bundle.json")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to runs/release-gate")
    parser.add_argument(
        "--policy-profile",
        choices=sorted(release_gate_policy_profiles()),
        default=DEFAULT_RELEASE_GATE_POLICY_PROFILE,
        help="Named release gate policy profile",
    )
    parser.add_argument("--min-audit-score", type=float, default=None, help="Override the selected policy profile")
    parser.add_argument("--min-ready-runs", type=int, default=None, help="Override the selected policy profile")
    parser.add_argument("--title", type=str, default="MiniGPT release gate")
    parser.add_argument(
        "--allow-missing-generation-quality",
        action="store_true",
        help="Override the selected policy profile and do not require generation_quality/non_pass_generation_quality audit checks",
    )
    parser.add_argument(
        "--allow-missing-request-history-summary",
        action="store_true",
        help="Override the selected policy profile and do not require the request_history_summary audit check",
    )
    parser.add_argument(
        "--allow-missing-benchmark-history",
        action="store_true",
        help="Override the selected policy profile and do not require benchmark_history release evidence",
    )
    parser.add_argument(
        "--allow-missing-test-coverage",
        action="store_true",
        help="Override the selected policy profile and do not require the test_coverage_report audit check",
    )
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit non-zero for warn as well as fail")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir or args.bundle.parent.parent / "release-gate"
    require_generation_quality = False if args.allow_missing_generation_quality else None
    require_request_history_summary = False if args.allow_missing_request_history_summary else None
    require_benchmark_history = False if args.allow_missing_benchmark_history else None
    require_test_coverage = False if args.allow_missing_test_coverage else None
    gate = build_release_gate(
        args.bundle,
        policy_profile=args.policy_profile,
        minimum_audit_score=args.min_audit_score,
        minimum_ready_runs=args.min_ready_runs,
        require_generation_quality=require_generation_quality,
        require_request_history_summary=require_request_history_summary,
        require_benchmark_history=require_benchmark_history,
        require_test_coverage=require_test_coverage,
        title=args.title,
    )
    outputs = write_release_gate_outputs(gate, out_dir)
    summary = gate["summary"]

    print(f"bundle={args.bundle}")
    print(f"gate_status={summary['gate_status']}")
    print(f"decision={summary['decision']}")
    print(f"checks={summary['pass_count']} pass/{summary['warn_count']} warn/{summary['fail_count']} fail")
    print(f"release_status={summary['release_status']}")
    print(f"audit_status={summary['audit_status']}")
    print(f"test_coverage_status={summary.get('test_coverage_status')}")
    print(f"test_coverage_percent={summary.get('test_coverage_percent')}")
    print(f"test_coverage_fail_under={summary.get('test_coverage_fail_under')}")
    print(f"test_coverage_gap={summary.get('test_coverage_gap')}")
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
    print(f"policy_profile={gate['policy']['policy_profile']}")
    print(f"minimum_audit_score={gate['policy']['minimum_audit_score']}")
    print(f"minimum_ready_runs={gate['policy']['minimum_ready_runs']}")
    print(f"require_generation_quality={gate['policy']['require_generation_quality_audit_checks']}")
    print(f"require_request_history_summary={gate['policy']['require_request_history_summary_audit_check']}")
    print(f"require_benchmark_history={gate['policy']['require_benchmark_history_gate_check']}")
    print(f"require_test_coverage={gate['policy']['require_test_coverage_audit_check']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if gate["warnings"]:
        print("warnings=" + json.dumps(gate["warnings"], ensure_ascii=False))
    return exit_code_for_gate(gate, fail_on_warn=args.fail_on_warn)


if __name__ == "__main__":
    raise SystemExit(main())
